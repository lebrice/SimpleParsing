"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
import argparse
import collections
import dataclasses
import enum
import inspect
import re
import textwrap
import typing
import warnings
from collections import defaultdict, namedtuple
from typing import *

from . import docstring, utils
import logging

class InconsistentArgumentError(RuntimeError):
    """
    Error raised when the number of arguments provided is inconsistent when parsing multiple instances from command line.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

T = TypeVar("T")

@dataclasses.dataclass
class Destination():
    """
    Represents where a parsed dataclass should be stored inside the `parsed_args` namespace.
    """
    attribute: str
    num_instances_to_parse: int = 1
    ## Maybe TODO: add typing for T here.
    # instances: List[Any] = dataclasses.field(default_factory=list)

nesting_isnt_supported_yet = lambda field: UserWarning(f"Nesting a list of dataclasses isn't supported yet. Field {field.name} will be set to its default value.")

class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = utils.Formatter
        super().__init__(*args, **kwargs)

        self._args_to_add: Dict[Type[T], List[Destination]] = {}


    
    def add_arguments(self, dataclass: Type, dest: str):
        """Adds corresponding command-line arguments for this class to the parser.
        
        Arguments:
            dataclass {Type} -- The dataclass for which to add fields as arguments in the parser
        
        Keyword Arguments:
            dest {str} -- The destination attribute of the `argparse.Namespace` where the dataclass instance will be stored after calling `parse_args()`
        """
        # Here we store args to add instead of adding them directly in order to handle the case where
        # multiple of the same dataclass are added as arguments
        self._register_dataclass(dataclass, Destination(attribute=dest, num_instances_to_parse=1))

    def parse_known_args(self, args=None, namespace=None):
        # NOTE: since the usual ArgumentParser.parse_args() calls parse_known_args, we therefore just need to overload the parse_known_args method.
        self._preprocessing()
        parsed_args, unparsed_args = super().parse_known_args(args, namespace)
        return self._postprocessing(parsed_args), unparsed_args
        
    def _register_dataclass(self, dataclass: Type[T], dest: Destination):
        """Recursively registers the given dataclass and all their children (nested) dataclass attributes to be parsed later.
        
        Arguments:
            dataclass {Type[T]} -- The dataclass to register
            dest {Destination} -- a Destination NamedTuple used to keep track of where to store the resulting instance and the number of instances.
        """
        destinations = self._args_to_add.setdefault(dataclass, [])
        if dest in destinations:
            self.error(f"Destination attribute {dest} is already used for dataclass of type {dataclass}. Make sure all destinations are unique!")
        destinations.append(dest)
        
        for field in dataclasses.fields(dataclass):
            if dataclasses.is_dataclass(field.type):
                child_dataclass = field.type
                child_attribute = f"{dest.attribute}.{field.name}"
                child_dest = Destination(child_attribute)
                logging.debug(f"adding child dataclass of type {child_dataclass} at attribute {child_attribute}")
                self._register_dataclass(child_dataclass, child_dest)

            elif utils.is_tuple_or_list_of_dataclasses(field.type):
                child_dataclass = utils.get_item_type(field.type)
                child_attribute = f"{dest.attribute}.{field.name}"
                
                # TODO: Perhaps if the Tuple[dataclass, dataclass, etc] annotation is used, we could infer the number of instances to be parsed?
                if field.default_factory is dataclasses.MISSING or len(field.default_factory()) == 0: # type: ignore
                    self.error(textwrap.dedent(f"""\
                    A non-empty default factory has to be set for container attributes whose items are dataclasses.
                    The item dataclass should not contain any required attributes.
                    (for example: `{field.name} = field(default_factory=lambda: [{dataclass()}]))`
                    """))

                num_instances_to_be_parsed = len(field.default_factory()) # type: ignore
                child_dest = Destination(child_attribute, num_instances_to_parse=num_instances_to_be_parsed)
                logging.debug(f"adding child dataclass of type {child_dataclass} at dest {child_dest}.")
                self._register_dataclass(child_dataclass, child_dest)
    

    def _preprocessing(self):
        logging.debug("\nPREPROCESSING\n")
        for dataclass_to_add, destinations in self._args_to_add.items():
            logging.debug("\ndataclass to add: ", dataclass_to_add, "destinations:", destinations)
            total_num_instances = sum(dest.num_instances_to_parse for dest in destinations)
            self._add_arguments(dataclass_to_add, total_num_instances)

    def _postprocessing(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        logging.debug("\nPOST PROCESSING\n")
        # TODO: Try and maybe return a nicer, typed version of parsed_args (a Namespace subclass?)       
        # Instantiate the dataclasses from the parsed arguments and add them to their destination key in the namespace
        for dataclass, destinations in self._args_to_add.items():
            # each attribute to set on the parsed_args may be a single dataclass, or a list of dataclasses.  
            total_num_instances = sum(dest.num_instances_to_parse for dest in destinations)
            logging.debug(f"postprocessing: {parsed_args} {dataclass} {destinations}")
            
            # parse all the instances of the required class all at the same time (flattening the nesting tree)
            # BUG: If there are multiple instances of the children class, then the number of instances
            if total_num_instances == 1:
                dataclass_instances = [self._instantiate_dataclass(dataclass, parsed_args)]
            else:
                logging.debug(f"total number of instances: {total_num_instances}")
                dataclass_instances = self._instantiate_dataclasses(dataclass, parsed_args, total_num_instances)
            
            for destination in destinations:
                if destination.num_instances_to_parse == 1:
                    instance = dataclass_instances.pop(0) # take the leftmost dataclass.
                    logging.debug(f"setting attribute {destination.attribute} in parsed_args to a value of {instance}")
                    utils.setattr_recursive(parsed_args, destination.attribute, instance)
                else:
                    # TODO: we are using lists, whereas it might be a tuple or some other container.
                    instances = [dataclass_instances.pop(0) for _ in range(destination.num_instances_to_parse)]
                    logging.debug(f"setting attribute {destination.attribute} in parsed_args to a value of {instances}")
                    utils.setattr_recursive(parsed_args, destination.attribute, instances)
        return parsed_args


    def _add_arguments(self, dataclass: Type[T], total_num_instances = 1):
        # TODO: maybe using the number of instances to parse we could set the `nargs` option more accurately
        multiple = total_num_instances > 1
        logging.debug(f"dataclass: {dataclass}, multiple={multiple}")
        names_string = self._get_destination_attributes_string(dataclass)
        group = self.add_argument_group(
            dataclass.__qualname__ + names_string,
            description=dataclass.__doc__
        )
        for f in dataclasses.fields(dataclass):
            logging.debug(f)
            if not f.init:
                continue

            elif dataclasses.is_dataclass(f.type):
                continue

            elif utils.is_tuple_or_list_of_dataclasses(f.type):
                continue

            name = f"--{f.name}"
            arg_options: Dict[str, Any] = { 
                "type": f.type,
            }

            doc = docstring.get_attribute_docstring(dataclass, f.name)
            if doc is not None:
                if doc.docstring_below:
                    arg_options["help"] = doc.docstring_below
                elif doc.comment_above:
                    arg_options["help"] = doc.comment_above
                elif doc.comment_inline:
                    arg_options["help"] = doc.comment_inline
            
            if f.default is not dataclasses.MISSING:
                arg_options["default"] = f.default
            elif f.default_factory is not dataclasses.MISSING: # type: ignore
                arg_options["default"] = f.default_factory() # type: ignore
            else:
                arg_options["required"] = True
                        
            if enum.Enum in f.type.mro():
                arg_options["choices"] = list(e.name for e in f.type)
                arg_options["type"] = str # otherwise we can't parse the enum, as we get a string.
                if "default" in arg_options:
                    default_value = arg_options["default"]
                    # if the default value is the Enum object, we make it a string
                    if isinstance(default_value, enum.Enum):
                        arg_options["default"] = default_value.name
            
            elif utils.is_tuple_or_list(f.type):
                # Check if typing.List or typing.Tuple was used as an annotation, in which case we can automatically convert items to the desired item type.
                # NOTE: we only support tuples with a single type, for simplicity's sake. 
                T = utils.get_argparse_container_type(f.type)
                arg_options["nargs"] = "*"
                if multiple:
                    arg_options["type"] = utils._parse_multiple_containers(f.type)
                else:
                    # TODO: Supporting the `--a '1 2 3'`, `--a [1,2,3]`, and `--a 1 2 3` at the same time is syntax is kinda hard, and I'm not sure if it's really necessary.
                    # right now, we support --a '1 2 3' '4 5 6' and --a [1,2,3] [4,5,6] only when parsing multiple instances.
                    # arg_options["type"] = utils._parse_container(f.type)
                    arg_options["type"] = T
            
            elif f.type is bool:
                arg_options["default"] = False if f.default is dataclasses.MISSING else f.default
                arg_options["type"] = utils.str2bool
                arg_options["nargs"] = "*" if multiple else "?"
                if f.default is dataclasses.MISSING:
                    arg_options["required"] = True
            
            if multiple:
                required = arg_options.get("required", False)
                if required:
                    arg_options["nargs"] = "+"
                else:
                    arg_options["nargs"] = "*"
                    arg_options["default"] = [arg_options["default"]]

            group.add_argument(name, **arg_options)

    def _instantiate_dataclass(self, dataclass: Type[T], args: Union[Dict[str, Any], argparse.Namespace]) -> T:
        """Creates an instance of the dataclass using results of `parser.parse_args()`"""
        args_dict = vars(args) if isinstance(args, argparse.Namespace) else args
        logging.debug(f"args dict: {args_dict}")
        constructor_args: Dict[str, Any] = {}

        for f in dataclasses.fields(dataclass):
            if not f.init:
                continue
            
            if dataclasses.is_dataclass(f.type):
                child_dataclass = f.type
                constructor_args[f.name] = self._instantiate_dataclass(f.type, args_dict)
            
            elif utils.is_tuple_or_list_of_dataclasses(f.type):
                child_dataclass = utils.get_item_type(f.type)
                container = list if utils.is_list(f.type) else tuple

                assert f.default_factory is not dataclasses.MISSING and len(f.default_factory()) != 0 #type: ignore

                num_instances_to_parse = len(f.default_factory()) #type: ignore
                instances = self._instantiate_dataclasses(child_dataclass, args_dict, num_instances_to_parse)
                
                logging.debug("instances:", instances)

                constructor_args[f.name] = instances 

            elif enum.Enum in f.type.mro():
                constructor_args[f.name] = f.type[args_dict[f.name]]
            
            elif utils.is_tuple(f.type):
                constructor_args[f.name] = tuple(args_dict[f.name])
            
            elif utils.is_list(f.type):
                constructor_args[f.name] = list(args_dict[f.name])

            elif f.type is bool:
                value = args_dict[f.name]
                constructor_args[f.name] = value
                default_value = False if f.default is dataclasses.MISSING else f.default
                if value is None:
                    constructor_args[f.name] = not default_value
                elif isinstance(value, bool):
                    constructor_args[f.name] = value
                else:
                    self.error(f"bool argument {f.name} isn't bool: {value}")

            else:
                constructor_args[f.name] = args_dict[f.name]

        instance: T = dataclass(**constructor_args) #type: ignore
        return instance

    def _instantiate_dataclasses(self, dataclass: Type[T], args: Union[Dict[str, Any], argparse.Namespace], num_instances_to_parse: int) -> List[T]:
        """Creates multiple instances of the dataclass using results of `parser.parse_args()`"""
        args_dict: Dict[str, Any] = vars(args) if isinstance(args, argparse.Namespace) else args
        instances: List[T] = []
        
        logging.debug(dataclass, args_dict, num_instances_to_parse)
        logging.debug(f"args: {args}")
        for i in range(num_instances_to_parse):
            constructor_arguments: Dict[str, Union[Any, List]] = {}
            for f in dataclasses.fields(dataclass):
                if not f.init:
                    continue
                assert f.name in args_dict, f"{f.name} is not in the arguments dict: {args_dict}"
                value = args_dict[f.name]
                assert isinstance(value, list), f"all fields should have gotten a list default value... ({value})"
                if len(value) == 1:
                    constructor_arguments[f.name] = value[0]
                elif len(value) == num_instances_to_parse:
                    constructor_arguments[f.name] = value[i]
                else:
                    raise InconsistentArgumentError(
                        f"The field '{f.name}' contains {len(value)} values, but either 1 or {num_instances_to_parse} values were expected."
                    )
            instances.append(self._instantiate_dataclass(dataclass, constructor_arguments))
        return instances

    def _get_destination_attributes_string(self, dataclass: Type[T]) -> str:
        destinations = self._args_to_add[dataclass]
        names = [
            dest.attribute + (f"[{dest.num_instances_to_parse}]" if dest.num_instances_to_parse > 1 else "") for dest in destinations
        ]
        names_string =f""" [{', '.join(f"'{name}'" for name in names)}]"""
        return names_string