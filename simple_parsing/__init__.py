"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
import argparse
import collections
import dataclasses
import enum
import inspect
from collections import namedtuple
import typing
from typing import *

from . import utils
from . import docstring

T = TypeVar("T", bound="ParseableFromCommandLine")

class InconsistentArgumentError(RuntimeError):
    """
    Error raised when the number of arguments provided is inconsistent when parsing multiple instances from command line.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ParseableFromCommandLine():
    """
    When applied to a dataclass, this enables creating an instance of that class and populating the attributes from the command-line.
    Each class is visually separated into a different argument group. The class docstring is used for the group description, while the 'attribute docstrings'
    are used for the help text of the arguments. See the example script for a more visual description.

    Example:
    ```
    @dataclass()
    class Options(ParseableFromCommandLine):
        a: int
        b: int = 10

    parser = argparse.ArgumentParser()
    Options.add_arguments(parser)

    args = parser.parse_args("--a 5")
    options = Options.from_args(args)
    print(options) 
    >>> Options(a=5, b=10)
    ```
    """
    @classmethod
    def add_arguments(cls: Type[T], parser: argparse.ArgumentParser, multiple=False):
        """
        Adds corresponding command-line arguments for this class to the given parser.

        Arguments:
            parser {argparse.ArgumentParser} -- The base argument parser to use
            multiple {bool} -- Wether we wish to eventually parse multiple instances of this class or not.
        
        
        #TODO: Double-Check this mechanism, just to make sure this is natural and makes sense.
        
        NOTE: about boolean (flag-like) arguments:
        If the argument is present with no value, then the opposite of the default value should be used.
        For example, say there is an argument called "--no-cache", with a default value of False.
        - When we don't pass the argument, (i.e, $> python example.py) the value should be False.
        - When we pass the argument, (i.e, $> python example.py --no-cache), the value should be True.
        - When we pass the argument with a value, ex: "--no-cache true" or "--no-cache false", the given value should be used 
        """
        group = parser.add_argument_group(cls.__qualname__, description=cls.__doc__)
        for f in dataclasses.fields(cls):
            name = f"--{f.name}"
            arg_options: Dict[str, Any] = { 
                "type": f.type,
            }

            doc = docstring.get_attribute_docstring(cls, f.name)
            if doc is not None:
                if doc.docstring_below:
                    arg_options["help"] = doc.docstring_below
                elif doc.comment_above:
                    arg_options["help"] = doc.comment_above
                elif doc.comment_inline:
                    arg_options["help"] = doc.comment_inline
            
            if f.default is dataclasses.MISSING:
                if f.default_factory is dataclasses.MISSING:
                    arg_options["required"] = True
                else:
                    arg_options["default"] = f.default_factory()
            else:
                arg_options["default"] = f.default

            # if multiple and "default" in arg_options:
            #     arg_options["default"] = [arg_options["default"]]    
            
            print(f"adding argument for field {f.name} with type {f.type}. Multiple is {multiple}, default value is {arg_options.get('default', None)}")
            
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
                    # TODO: figure out exactly how to handle this one.
                    arg_options["type"] = utils._parse_multiple_containers(f.type)
                    # arg_options["type"] = str
                    # arg_options["action"] = "append"
                else:
                    arg_options["type"] = T             
            
            elif f.type is bool:
                arg_options["default"] = False if f.default is dataclasses.MISSING else f.default
                arg_options["type"] = utils.str2bool
                arg_options["nargs"] = '?'
                if f.default is dataclasses.MISSING:
                    arg_options["required"] = True
            elif multiple:
                arg_options["nargs"] = "*"
            
            group.add_argument(name, **arg_options)

 
    @classmethod
    def from_args(cls: T, args: argparse.Namespace) -> T:
        """Creates an instance of this class using results of `parser.parse_args()`
        
        Arguments:
            args {argparse.Namespace} -- The result of a call to `parser.parse_args()`
        
        Returns:
            object -- an instance of this class
        """
        args_dict = vars(args) 
        # print("args dict:", args_dict)
        constructor_args: Dict[str, Any] = {}
        for f in dataclasses.fields(cls):
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
        return cls(**constructor_args) #type: ignore

    @classmethod
    def from_args_multiple(cls: Type[T], args: argparse.Namespace, num_instances_to_parse: int) -> List[T]:
        """Parses multiple instances of this class from the command line, and returns them.
        Each argument may have either 0 values (when applicable), 1, or {num_instances_to_parse}. 
        NOTE: If only one value is provided, every instance will be populated with the same value.

        Arguments:
            args {argparse.Namespace} -- The
            num_instances_to_parse {int} -- Number of instances that are to be created from the given parsedarguments
        
        Raises:
            cls.InconsistentArgumentError: [description]
        
        Returns:
            List -- A list of populated instances of this class.
        """
        args_dict: Dict[str, Any] = vars(args)
        # keep the arguments and values relevant to this class.
        constructor_arguments: Dict[str, Union[Any, List]] = {
            f.name: args_dict[f.name]
            for f in dataclasses.fields(cls)
        }
        # print("Constructor arguments:", constructor_arguments)
        arguments_per_instance: List[Dict[str, Any]] = []
        for i in range(num_instances_to_parse):
            ith_arguments_dict: Dict[str, Any] = {}
            for field_name, field_values in constructor_arguments.items():
                if len(field_values) == 1:
                    ith_arguments_dict[field_name] = field_values[0]
                elif len(field_values) == num_instances_to_parse:
                    ith_arguments_dict[field_name] = field_values[i]
                else:
                    raise InconsistentArgumentError(
                        f"The field '{field_name}' contains {len(values)} values, but either 1 or {num_instances_to_parse} values were expected.")
            arguments_per_instance.append(ith_arguments_dict)

        return list(
            cls(**arguments_dict) #type: ignore
            for arguments_dict in arguments_per_instance
        )