"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
import argparse
import collections
import dataclasses
import enum
import inspect
from collections import namedtuple
from typing import *

from . import utils


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
    @dataclass
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
    def add_arguments(cls, parser: argparse.ArgumentParser, multiple=False):
        """
        Adds corresponding command-line arguments for this class to the given parser.
        # TODO: Add support for Booleans, List, Tuples, and Enums.
        Arguments:
            parser {argparse.ArgumentParser} -- The base argument parser to use
            multiple {bool} -- Wether we wish to eventually parse multiple instances of this class or not.
        """
        group = parser.add_argument_group(cls.__qualname__, description=cls.__doc__)
        for f in dataclasses.fields(cls):
            arg_options: Dict[str, Any] = {
                "type": f.type,
            }
            doc = utils.get_attribute_docstring(cls, f.name)
            if doc is not None:
                if doc.docstring_below:
                    arg_options["help"] = doc.docstring_below
                elif doc.comment_above:
                    arg_options["help"] = doc.comment_above
                elif doc.comment_inline:
                    arg_options["help"] = doc.comment_inline
            
            if f.default is dataclasses.MISSING:
                arg_options["required"] = True
            else:
                arg_options["default"] = f.default
            
            if enum.Enum in f.type.mro():
                arg_options["choices"] = list(e.name for e in f.type)
                arg_options["type"] = str # otherwise we can't parse the enum, as we get a string.
                if "default" in arg_options:
                    default_value = arg_options["default"]
                    # if the default value is the Enum object, we make it a string
                    if isinstance(default_value, enum.Enum):
                        arg_options["default"] = default_value.name

            if multiple or f.type in {list, tuple}:
                arg_options["nargs"] = "*"
            
            group.add_argument(f"--{f.name}", **arg_options)


    @classmethod
    def from_args(cls, args: argparse.Namespace) -> object:
        """Creates an instance of this class using results of `parser.parse_args()`
        
        Arguments:
            args {argparse.Namespace} -- The result of a call to `parser.parse_args()`
        
        Returns:
            object -- an instance of this class
        """
        args_dict = vars(args) 
        print("args dict:", args_dict)
        constructor_args: Dict[str, Any] = {}
        for f in dataclasses.fields(cls):
            if enum.Enum in f.type.mro():
                constructor_args[f.name] = f.type[args_dict[f.name]]
            else:
                constructor_args[f.name] = args_dict[f.name]
        return cls(**constructor_args) #type: ignore

    @classmethod
    def from_args_multiple(cls, args: argparse.Namespace, num_instances_to_parse: int) -> List[object]:
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

        for field_name, values in constructor_arguments.items():
            if isinstance(values, list):
                if len(values) not in {1, num_instances_to_parse}:
                    raise InconsistentArgumentError(
                        f"The field '{field_name}' contains {len(values)} values, but either 1 or {num_instances_to_parse} values were expected.")
                if len(values) == 1:
                    constructor_arguments[field_name] = values[0]

        # convert from a dict of lists to a list of dicts.
        arguments_per_instance: List[Dict[str, Any]] = [
            {
                field_name: field_values[i] if isinstance(field_values, list) else field_values
                for field_name, field_values in constructor_arguments.items()
            } for i in range(num_instances_to_parse) 
        ]
        return [
            cls(**arguments_dict) #type: ignore
            for arguments_dict in arguments_per_instance
        ]
