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
        
        wrapper: DataclassWrapper[Dataclass] = self._wrappers.setdefault(dataclass, DataclassWrapper(dataclass, self))

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
        """Instantiate the dataclasses from the parsed arguments and add them to their destination key in the namespace
        
        Arguments:
            parsed_args {argparse.Namespace} -- the result of calling super().parse_args()
        
        Returns:
            argparse.Namespace -- The namespace, with the added attributes for each dataclass.
            TODO: Try and maybe return a nicer, typed version of parsed_args (a Namespace subclass maybe?)  
        """
        logging.debug("\nPOST PROCESSING\n")
        constructor_arguments_for_each_dataclass: Dict[str, Dict[str, Any]] = {}
        wrapper_for_each_destination: Dict[str, DataclassWrapper] = {}
        for dataclass, destinations in self._args_to_add.items():
            wrapper: DataclassWrapper = self._wrappers[dataclass]
            logging.debug(f"postprocessing: {parsed_args} {wrapper} {destinations}")
            
            total_num_instances = len(destinations)
            logging.debug(f"total number of instances: {total_num_instances}")
            constructor_arguments_list: List[Dict[str, Any]] = wrapper.get_constructor_arguments(parsed_args, total_num_instances)

            for destination, instance_arguments in zip(destinations, constructor_arguments_list):
                logging.debug(f"attribute {destination} will have arguments: {instance_arguments}")
                constructor_arguments_for_each_dataclass[destination] = instance_arguments
                wrapper_for_each_destination[destination] = wrapper
        
        # we now have all the constructor arguments for each instance.
        # we can now sort out the different dependencies, and create the instances.
        
        print("all arguments:", constructor_arguments_for_each_dataclass)

        nesting_level = lambda destination_attribute: destination_attribute.count(".")
        nested_first = sorted(constructor_arguments_for_each_dataclass.keys(), key=nesting_level, reverse=True)
        for destination in nested_first:
            constructor = wrapper_for_each_destination[destination].instantiate_dataclass
            constructor_args = constructor_arguments_for_each_dataclass[destination]    

            instance = constructor(constructor_args)

            if "." in destination:
                # if this destination is a nested child of another,
                # we set this instance in the corresponding constructor arguments,
                # such that the required parameters are set
                parts = destination.split(".")
                parent = ".".join(parts[:-1])
                attribute_in_parent = parts[-1]
                constructor_arguments_for_each_dataclass[parent][attribute_in_parent] = instance
            else:
                # if this destination is not a nested child, we set the attribute
                # on the returned parsed_args.
                setattr(parsed_args, destination, instance)

        return parsed_args

    def _sort_out_dependencies(self):
        """PLAN: 
        - instantiate the dataclasses without children first.
            - if there aren't any, there must be some kind of cyclic dependency?
        """



    def _get_destination_attributes_string(self, destinations: List[str]) -> str:
        names = destinations
        names_string =f""" [{', '.join(f"'{name}'" for name in names)}]"""
        return names_string