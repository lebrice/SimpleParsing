"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
import argparse
import collections
import dataclasses
import enum
import inspect
import logging
import re
import textwrap
import typing
import warnings
from collections import defaultdict, namedtuple
from typing import *

from . import docstring, utils
from .wrappers import DataclassWrapper, FieldWrapper

Dataclass = TypeVar("Dataclass")

class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = utils.Formatter
        super().__init__(*args, **kwargs)

        self._wrappers: Dict[Type[Dataclass], DataclassWrapper[Dataclass]] = {}
        self._args_to_add: Dict[Type[Dataclass], List[str]] = {}

    def add_arguments(self, dataclass: Type[Dataclass], dest: str):
        """Adds corresponding command-line arguments for this class to the parser.
        
        Arguments:
            dataclass {Type} -- The dataclass for which to add fields as arguments in the parser
        
        Keyword Arguments:
            dest {str} -- The destination attribute of the `argparse.Namespace` where the dataclass instance will be stored after calling `parse_args()`
        """
        self._register_dataclass(dataclass, dest)

    def parse_known_args(self, args=None, namespace=None):
        # NOTE: since the usual ArgumentParser.parse_args() calls parse_known_args, we therefore just need to overload the parse_known_args method.
        self._preprocessing()
        parsed_args, unparsed_args = super().parse_known_args(args, namespace)
        return self._postprocessing(parsed_args), unparsed_args
        
    def _register_dataclass(self, dataclass: Type[Dataclass], dest: str):
        """Recursively registers the given dataclass and all their children
        (nested) dataclass attributes to be parsed later.
        
        Arguments:
            dataclass {Type[T]} -- The dataclass to register
            dest {Destination} -- a Destination NamedTuple used to keep track of where to store the resulting instance and the number of instances.
        """
        
        if dataclass in self._args_to_add.keys():
            print("ALREADY PRESENT")
            logging.debug(f"The dataclass {dataclass} is already registered. Marking it as 'multiple'.")
            self._wrappers[dataclass].multiple = True
        else:
            print("NEW DATACLASS")
        
        destinations = self._args_to_add.setdefault(dataclass, [])
        if dest in destinations:
            self.error(f"Destination attribute {dest} is already used for dataclass of type {dataclass}. Make sure all destinations are unique!")
        destinations.append(dest)
        
        wrapper = self._wrappers.setdefault(dataclass, DataclassWrapper(dataclass, self))

        for wrapped_field in wrapper.fields:
            field = wrapped_field.field

            # handle potential nesting.
            if dataclasses.is_dataclass(field.type):
                child_dataclass = field.type
                child_attribute = f"{dest}.{field.name}"
                child_dest = child_attribute

                logging.debug(f"adding child dataclass of type {child_dataclass} at attribute {child_attribute}")
                self._register_dataclass(child_dataclass, child_dest)

            elif utils.is_tuple_or_list_of_dataclasses(field.type):
                self.error(textwrap.dedent(f"""\
                Nesting using attributes which are containers of a dataclass isn't supported (yet).
                """))

    def _preprocessing(self):
        logging.debug("\nPREPROCESSING\n")

        # Create one argument group per dataclass type
        for wrapper in self._wrappers.values():
            dataclass = wrapper.dataclass

            logging.debug(f"dataclass: {dataclass}, multiple={wrapper.multiple}")
            
            destinations = self._args_to_add[dataclass]
            names_string = self._get_destination_attributes_string(destinations)
            group = self.add_argument_group(
                dataclass.__qualname__ + names_string,
                description=dataclass.__doc__
            )
            
            for wrapped_field in wrapper.fields:                
                assert not wrapped_field.is_tuple_or_list_of_dataclasses, "This should have been prevented."
                if wrapped_field.is_dataclass:
                    # not adding arguments for a dataclass field.
                    continue

                if wrapped_field.arg_options:
                    name = f"--{wrapped_field.field.name}"
                    group.add_argument(name, **wrapped_field.arg_options)


    def _postprocessing(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        logging.debug("\nPOST PROCESSING\n")
        # TODO: Try and maybe return a nicer, typed version of parsed_args (a Namespace subclass?)       
        # Instantiate the dataclasses from the parsed arguments and add them to their destination key in the namespace
        for dataclass, destinations in self._args_to_add.items():
            wrapped_dataclass = self._wrappers[dataclass]
            logging.debug(f"postprocessing: {parsed_args} {wrapped_dataclass} {destinations}")
            
            total_num_instances = len(destinations)
            logging.debug(f"total number of instances: {total_num_instances}")
            if total_num_instances == 1:
                dataclass_instances = wrapped_dataclass.instantiate(parsed_args, 1)
            else:
                dataclass_instances = wrapped_dataclass.instantiate(parsed_args, total_num_instances)
            
            for destination in destinations:
                instance = dataclass_instances.pop(0) # take the leftmost dataclass.
                logging.debug(f"setting attribute {destination} in parsed_args to a value of {instance} (single)")
                utils.setattr_recursive(parsed_args, destination, instance)
        
        return parsed_args

    def _get_destination_attributes_string(self, destinations: List[str]) -> str:
        names = destinations
        names_string =f""" [{', '.join(f"'{name}'" for name in names)}]"""
        return names_string