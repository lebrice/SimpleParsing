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


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = utils.Formatter
        super().__init__(*args, **kwargs)

        self._args_to_add: Dict[Type, List[str]] = defaultdict(list)
    
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
        self._args_to_add[dataclass].append(dest)
        for field in dataclasses.fields(dataclass):
            if dataclasses.is_dataclass(field.type):
                warnings.warn(UserWarning("Nesting isn't supported yet!"))
                # TODO: interesting problem, the nested dataclasses should be set as attributes to the dataclasses, so what would the 'dest' be in such a case?
            elif utils.is_tuple_or_list(field.type) and dataclasses.is_dataclass(utils.get_item_type(field.type)):
                warnings.warn(UserWarning("Nesting isn't supported yet!"))
    
    def _add_arguments(self, dataclass: Type, multiple=False):
        names = self._args_to_add[dataclass]
        names_string =f""" [{', '.join(f"'{name}'" for name in names)}]"""
        group = self.add_argument_group(
            dataclass.__qualname__ + names_string,
            description=dataclass.__doc__
        )
        for f in dataclasses.fields(dataclass):
            if not f.init:
                continue
            elif dataclasses.is_dataclass(f.type):
                warnings.warn(UserWarning("Nesting isn't supported yet!"))
                continue
                # self._add_arguments(f.type, multiple)
            elif utils.is_tuple_or_list(f.type) and dataclasses.is_dataclass(utils.get_item_type(f.type)):
                warnings.warn(UserWarning("Nesting isn't supported yet! (container of dataclasses)"))
                continue
                # T = utils.get_item_type(f.type)
                # self._add_arguments(T, True)

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

    def _instantiate_dataclass(self, dataclass: Type, args: argparse.Namespace):
        """Creates an instance of the dataclass using results of `parser.parse_args()`"""
        args_dict = vars(args) if isinstance(args, argparse.Namespace) else args
        # print("args dict:", args_dict)
        constructor_args: Dict[str, Any] = {}
        for f in dataclasses.fields(dataclass):
            if not f.init:
                continue
            if dataclasses.is_dataclass(f.type):
                raise UserWarning("Nesting isn't supported yet!")

            if enum.Enum in f.type.mro():
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
    
    def _instantiate_dataclasses(self, dataclass: Type, args: argparse.Namespace, num_instances_to_parse: int):
        """Creates multiple instances of the dataclass using results of `parser.parse_args()`"""
        args_dict: Dict[str, Any] = vars(args)

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


    def parse_args(self, args=None, namespace=None):
        # Add (for real this time!) the dataclasses, handling the case where the same dataclass was added multiple times
        # with different 'dest' strings
        for dataclass_to_add, destinations in self._args_to_add.items():
            self._add_arguments(dataclass_to_add, multiple=len(destinations) > 1)

        # Parse the arguments normally
        parsed_args = super().parse_args(args, namespace)

        # TODO: get a nice typed version of parsed_args (a Namespace)       

        # Instantiate the dataclasses from the parsed arguments and add them to their destination key in the namespace
        for dataclass_to_add, destinations in self._args_to_add.items():
            if len(destinations) == 1:
                dataclass_instance = self._instantiate_dataclass(dataclass_to_add, parsed_args)
                setattr(parsed_args, destinations[0], dataclass_instance)
            else:
                dataclass_instances = self._instantiate_dataclasses(dataclass_to_add, parsed_args, len(destinations))
                for dataclass_instance, dest in zip(dataclass_instances, destinations):
                    setattr(parsed_args, dest, dataclass_instance)

        return parsed_args
