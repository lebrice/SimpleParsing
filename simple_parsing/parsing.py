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

        # two-level dictionary that maps from (dataclass, string_prefix) -> DataclassWrapper. 
        self._wrappers: Dict[Type[Dataclass], Dict[str, DataclassWrapper[Dataclass]]] = defaultdict(dict)

    def add_arguments(self, dataclass: Type[Dataclass], dest: str, prefix=""):
        """Adds corresponding command-line arguments for this class to the parser.
        
        Arguments:
            dataclass {Type[Dataclass]} -- The dataclass for which to add fields as arguments in the parser
        
        Keyword Arguments:
            dest {str} -- The destination attribute of the `argparse.Namespace` where the dataclass instance will be stored after calling `parse_args()`
            prefix {str} -- An optional prefix to add prepend to the names of the argparse arguments which will be generated for this dataclass.
            This can be useful when registering multiple distinct instances of the same dataclass.

        """
        top_level_wrapper = self._register_dataclass(dataclass, dest, prefix=prefix)
        
        # now we have a tree structure.
        for wrapper in iter(top_level_wrapper):
            logging.debug("adding wrapper:\n", wrapper, "\n")
            logging.debug(f"adding wrapper {wrapper.dataclass}, prefix: '{wrapper.prefix}', destinations: {wrapper._destinations}")
            if wrapper.prefix in self._wrappers[wrapper.dataclass]:
                logging.debug("a wrapper for this already exists!")
                other = self._wrappers[wrapper.dataclass][wrapper.prefix]
                other._destinations.extend(wrapper._destinations)
                other._children.extend(wrapper._children)
                other.multiple = True
                del wrapper
                wrapper = other
            self._wrappers[wrapper.dataclass][wrapper.prefix] = wrapper


    def parse_known_args(self, args=None, namespace=None):
        # NOTE: since the usual ArgumentParser.parse_args() calls parse_known_args, we therefore just need to overload the parse_known_args method.
        self._preprocessing()
        parsed_args, unparsed_args = super().parse_known_args(args, namespace)
        return self._postprocessing(parsed_args), unparsed_args

    def _register_dataclass(self, dataclass: Type[Dataclass], dest: str, prefix: str = "", parent=None) -> DataclassWrapper:
        """Recursively registers the given dataclass and all their children
         (nested) dataclass attributes to be parsed later.
        
        Arguments:
            dataclass {Type[Dataclass]} -- The dataclass to register
            dest {str} -- a string which is to be used to  NamedTuple used to keep track of where to store the resulting instance and the number of instances.
        """
        
        logging.debug("Registering dataclass ", dataclass, "destination:", dest, "prefix: ", prefix)
        wrapper = DataclassWrapper(dataclass, _prefix=prefix)
        destinations = wrapper._destinations
        
        if parent is not None:
            logging.debug(f"Parent prefix: '{parent.prefix}', parent multiple: {parent.multiple}")
            wrapper._parent = parent

        if dest in destinations:
            self.error(f"Destination attribute {dest} is already used for dataclass of type {dataclass} with prefix '{prefix}'. Make sure all destinations are unique, or use a different prefix!")
        destinations.append(dest)
        
        for wrapped_field in wrapper.fields:
            
            # handle nesting.
            if wrapped_field.is_dataclass:
                child_dataclass = wrapped_field.field.type
                child_attribute_dest = f"{dest}.{wrapped_field.field.name}"
                logging.debug(f"adding child dataclass of type {child_dataclass} at attribute {child_attribute_dest}")
                logging.debug(f"wrapper is multiple: {wrapper.multiple}, wrapper prefix: '{wrapper.prefix}'")
                # TODO: Problem: If this is the first dataclass of this type that we see, then we would normally say it doesn't need a prefix.
                # However, if we see a second instance of this class as we recurse, then we would probably like to have a distinct prefix for each of them.. 
                # this kinda-sorta works.
                if prefix:
                    child_prefix = prefix
                else:
                    child_prefix = prefix
                    # child_prefix = wrapped_field.field.name + "_"
                # recurse.
                child_wrapper = self._register_dataclass(child_dataclass, child_attribute_dest, child_prefix, parent=wrapper)
                wrapper._children.append(child_wrapper)

            elif wrapped_field.is_tuple_or_list_of_dataclasses:
                self.error(textwrap.dedent(f"""\
                Nesting using attributes which are containers of a dataclass isn't supported (yet).
                """))

        if parent is None:
            logging.debug("Top-level is done, children:")
            logging.debug([child.prefix for child in wrapper._children])
        return wrapper

    def _preprocessing(self):
        logging.debug("\nPREPROCESSING\n")
        logging.debug("PREPROCESSING")
        # Create one argument group per dataclass type
        for dataclass in self._wrappers:
            for prefix, wrapper in self._wrappers[dataclass].items():
                
                logging.debug(f"dataclass: {dataclass}, multiple={wrapper.multiple}")
                
                destinations = wrapper._destinations
                names_string = self._get_destination_attributes_string(destinations)
                group = self.add_argument_group(
                    dataclass.__qualname__ + names_string,
                    description=dataclass.__doc__
                )
                
                for wrapped_field in wrapper.fields:
                    logging.debug(f"arg options: {wrapped_field.name}, {wrapped_field.arg_options}")
                    if wrapped_field.arg_options:
                        name = f"--{wrapped_field.name}"
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
        constructor_arguments = self._get_constructor_arguments_for_every_destination(parsed_args)
        wrappers: Dict[str, DataclassWrapper] = self._get_wrapper_for_every_destination()  
        # we now have all the constructor arguments for each instance.
        # we can now sort out the different dependencies, and create the instances.
        
        logging.debug("all arguments:", constructor_arguments)
        destinations = constructor_arguments.keys()
        
        nesting_level = lambda destination_attribute: destination_attribute.count(".")
        
        for destination in sorted(destinations, key=nesting_level, reverse=True):
            # idea: we will construct the 'tree' of dependencies from the bottom up.
            
            constructor = wrappers[destination].instantiate_dataclass
            constructor_args = constructor_arguments[destination]    
            logging.debug(f"destination: '{destination}', constructor_args: {constructor_args}")
            

            if "." in destination:
                # if this destination is a nested child of another,
                # we set this instance in the corresponding constructor arguments,
                # such that the required parameters are set
                parts = destination.split(".")
                parent = ".".join(parts[:-1])
                attribute_in_parent = parts[-1]
                logging.debug(f"Destination is child in parent {parent} at attribute {attribute_in_parent}")
                instance = constructor(constructor_args)
                constructor_arguments[parent][attribute_in_parent] = instance
            else:
                # if this destination is not a nested child, we set the attribute
                # on the returned parsed_args.
                logging.debug(f"Constructing instance for destination {destination}")
                instance = constructor(constructor_args)
                setattr(parsed_args, destination, instance)

        return parsed_args

    def _get_or_create_wrapper_for(self, dataclass: Type[Dataclass], prefix: str) -> DataclassWrapper[Dataclass]:
        """create a wrapper for this dataclass and with this prefix if it doesn't exist already, otherwise retrieve it.
        
        Arguments:
            dataclass {Type[Dataclass]} -- [description]
            prefix {str} -- [description]
        
        Returns:
            DataclassWrapper[Dataclass] -- [description]
        """
        

    def _get_constructor_arguments_for_every_destination(self, parsed_args: argparse.Namespace)-> Dict[str, Dict[str, Any]]:
        constructor_arguments: Dict[str, Dict[str, Any]] = {}

        for dataclass in self._wrappers:
            for prefix, wrapper in self._wrappers[dataclass].items():
                # get all the destinations:
                destinations = wrapper._destinations
                logging.debug(f"postprocessing: {parsed_args} {wrapper} {destinations}")
            
                total_num_instances = len(destinations)
                logging.debug(f"total number of instances: {total_num_instances}")
                constructor_arguments_list: List[Dict[str, Any]] = wrapper.get_constructor_arguments(parsed_args, total_num_instances)

                for destination, instance_arguments in zip(destinations, constructor_arguments_list):
                    logging.debug(f"attribute {destination} will have arguments: {instance_arguments}")
                    constructor_arguments[destination] = instance_arguments
                    # wrappers[destination] = wrapper
        return constructor_arguments
    
    def _get_wrapper_for_every_destination(self) -> Dict[str, DataclassWrapper[Dataclass]]:
        """Returns a dictionary where for every key (a destination), we return the associated DataclassWrapper.
        NOTE: multiple destinations can share the same DataclassWrapper instance.
        
        Returns:
            Dict[str, DataclassWrapper[Dataclass]] -- [description]
        """
        wrapper_for_destination: Dict[str, DataclassWrapper[Dataclass]] = {}
        for dataclass in self._wrappers:
            for prefix, wrapper in self._wrappers[dataclass].items():
                destinations = wrapper._destinations
                for dest in destinations:
                    wrapper_for_destination[dest] = wrapper
        return wrapper_for_destination
        


    def _get_destination_attributes_string(self, destinations: List[str]) -> str:
        names = destinations
        names_string =f""" [{', '.join(f"'{name}'" for name in names)}]"""
        return names_string
