"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
import argparse
import collections
import dataclasses
import enum
import inspect
from collections import namedtuple, defaultdict
import typing
from typing import *
import re
import warnings

from . import utils
from . import docstring


class InconsistentArgumentError(RuntimeError):
    """
    Error raised when the number of arguments provided is inconsistent when parsing multiple instances from command line.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

T = TypeVar("T")

class Dest(NamedTuple):
    attribute: str
    is_multiple: bool

class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = utils.Formatter
        super().__init__(*args, **kwargs)

        self._args_to_add: Dict[Type, List[Dest]] = {}
    
    def add_arguments(self, dataclass: Type, dest: str):
        """Adds corresponding command-line arguments for this class to the parser.
        
        Arguments:
            dataclass {Type} -- The dataclass for which to add fields as arguments in the parser
        
        Keyword Arguments:
            dest {str} -- The destination key where filled dataclass will be stored after parsing
        """
        
        #TODO: Double-Check this mechanism, just to make sure this is natural and makes sense.
        # NOTE: about boolean (flag-like) arguments:
        # If the argument is present with no value, then the opposite of the default value should be used.
        # For example, say there is an argument called "--no-cache", with a default value of False.
        # - When we don't pass the argument, (i.e, $> python example.py) the value should be False.
        # - When we pass the argument, (i.e, $> python example.py --no-cache), the value should be True.
        # - When we pass the argument with a value, ex: "--no-cache true" or "--no-cache false", the given value should be used 
        
        # Here we store args to add instead of adding them directly in order to handle the case where
        # multiple of the same dataclass are added as arguments
        self._register_dataclass(dataclass, dest)


    def _register_dataclass(self, dataclass, dest, is_multiple = False):
        destinations = self._args_to_add.setdefault(dataclass, [])
        if dest in destinations:
            raise RuntimeError(f"Destination attribute {dest} is already used for dataclass of type {dataclass}. Make sure all destinations are unique!")
        destinations.append(Dest(dest, is_multiple=is_multiple))
        
        for field in dataclasses.fields(dataclass):
            if dataclasses.is_dataclass(field.type):
                child_dataclass = field.type
                child_dest = f"{dest}.{field.name}"
                print(f"adding child dataclass of type {child_dataclass} at attribute {child_dest}")
                self._register_dataclass(child_dataclass, child_dest)

            elif utils.is_tuple_or_list_of_dataclasses(field.type):
                child_dataclass = utils.get_item_type(field.type)
                child_dest = f"{dest}.{field.name}"
                print(f"adding child dataclass of type {child_dataclass} at attribute {child_dest}")            
                self._register_dataclass(child_dataclass, child_dest, is_multiple=True)
    

    def parse_args(self, args=None, namespace=None):
        self._preprocessing()
        parsed_args = super().parse_args(args, namespace)
        return self._postprocessing(parsed_args)

    def _preprocessing(self):
        print("\nPREPROCESSING\n")
        for dataclass_to_add, destinations in self._args_to_add.items():
            print("\ndataclass to add: ", dataclass_to_add, "destinations:", destinations)
            multiple = len(destinations) > 1 or destinations[0].is_multiple
            self._add_arguments(dataclass_to_add, multiple=multiple)

    def _postprocessing(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        print("\nPOST PROCESSING\n")
        # TODO: Try and maybe teturn a nicer, typed version of parsed_args (a Namespace subclass?)       
        # Instantiate the dataclasses from the parsed arguments and add them to their destination key in the namespace
        for dataclass, destinations_attributes in self._args_to_add.items():
            if len(destinations_attributes) == 1:
                dataclass_instance = self._instantiate_dataclass(dataclass, parsed_args)
                dest = destinations_attributes[0]
                utils.setattr_recursive(parsed_args, dest.attribute, dataclass_instance)
            else:
                dataclass_instances = self._instantiate_dataclasses(dataclass, parsed_args, len(destinations_attributes))
                for dataclass_instance, dest in zip(dataclass_instances, destinations_attributes):
                    utils.setattr_recursive(parsed_args, dest.attribute, dataclass_instance)
        return parsed_args


    def _add_arguments(self, dataclass: Type[T], multiple=False):
        print(f"dataclass: {dataclass}, multiple={multiple}")

        names = self._args_to_add[dataclass]
        names_string =f""" [{', '.join(f"'{name}'" for name in names)}]"""
        group = self.add_argument_group(
            dataclass.__qualname__ + names_string,
            description=dataclass.__doc__
        )
        for f in dataclasses.fields(dataclass):
            print(f)
            if not f.init:
                continue

            elif dataclasses.is_dataclass(f.type):
                child_dataclass = f.type
                print(f"Adding arguments for a child dataclass of type {f.type} (parent is {dataclass})")
                multiple = len(self._args_to_add[child_dataclass]) > 1
                # self._add_arguments(f.type, multiple=multiple)
                continue

            elif utils.is_tuple_or_list_of_dataclasses(f.type):
                child_dataclass = utils.get_item_type(f.type)
                print(f"Adding arguments for a list of child dataclass of type {child_dataclass} (parent is {dataclass})")
                # self._add_arguments(child_dataclass, True)
                continue
                # warnings.warn(UserWarning("Nesting a list of dataclasses isn't supported yet!"))

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
        # print("args dict:", args_dict)
        constructor_args: Dict[str, Any] = {}

        for f in dataclasses.fields(dataclass):
            if not f.init:
                continue
            
            if dataclasses.is_dataclass(f.type):
                child_dataclass = f.type
                constructor_args[f.name] = self._instantiate_dataclass(f.type, args_dict)
            
            elif utils.is_tuple_or_list_of_dataclasses(f.type):
                child_dataclass = utils.get_item_type(f.type)
                container = utils.get_argparse_container_type(f.type)

                # TODO: how do we know how many should be instantiated?
                constructor_args[f.name] = container(self._instantiate_dataclasses(child_dataclass, args_dict, 1))
                raise UserWarning("Nesting a list of dataclasses isn't supported yet!")

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
                    raise argparse.ArgumentTypeError(f"bool argument {f.name} isn't bool: {value}")

            else:
                constructor_args[f.name] = args_dict[f.name]
        return dataclass(**constructor_args) #type: ignore
    
    def _instantiate_dataclasses(self, dataclass: Type[T], args: Union[Dict[str, Any], argparse.Namespace], num_instances_to_parse: int) -> List[T]:
        """Creates multiple instances of the dataclass using results of `parser.parse_args()`"""
        num_instances_to_parse = len(self._args_to_add[dataclass])
        args_dict: Dict[str, Any] = vars(args) if isinstance(args, argparse.Namespace) else args

        instances: List[dataclass] = [] # type: ignore
        for i in range(num_instances_to_parse):
            constructor_arguments: Dict[str, Union[Any, List]] = {}
            for f in dataclasses.fields(dataclass):
                if not f.init:
                    continue
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
