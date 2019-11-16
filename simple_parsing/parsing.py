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

        self._wrappers: Dict[Type[Dataclass], Dict[str, DataclassWrapper[Dataclass]]] = defaultdict(dict)
        self._destinations: Dict[Type[Dataclasss], Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))

    def add_arguments(self, dataclass: Type[Dataclass], dest: str, argument_names_prefix=""):
        """Adds corresponding command-line arguments for this class to the parser.
        
        Arguments:
            dataclass {Type[Dataclass]} -- The dataclass for which to add fields as arguments in the parser
        
        Keyword Arguments:
            dest {str} -- The destination attribute of the `argparse.Namespace` where the dataclass instance will be stored after calling `parse_args()`
            argument_names_prefix {str} -- An optional prefix to add prepend to the names of the argparse arguments which will be generated for this dataclass.
            This can be useful when registering multiple distinct instances of the same dataclass.
        """
        self._register_dataclass(dataclass, dest, prefix=argument_names_prefix)
    
    def parse_known_args(self, args=None, namespace=None):
        # NOTE: since the usual ArgumentParser.parse_args() calls parse_known_args, we therefore just need to overload the parse_known_args method.
        self._preprocessing()
        parsed_args, unparsed_args = super().parse_known_args(args, namespace)
        return self._postprocessing(parsed_args), unparsed_args

    def _register_dataclass(self, dataclass: Type[Dataclass], dest: str, prefix: str = ""):
        """Recursively registers the given dataclass and all their children
         (nested) dataclass attributes to be parsed later.
        
        Arguments:
            dataclass {Type[Dataclass]} -- The dataclass to register
            dest {str} -- a string which is to be used to  NamedTuple used to keep track of where to store the resulting instance and the number of instances.
        """
        
        print("Registering dataclass ", dataclass, "destination:", dest, "prefix: ", prefix)

        wrapper = self._get_or_create_wrapper_for(dataclass, prefix)
        destinations = self._get_destinations_for(dataclass, prefix)
        if dest in destinations:
            self.error(f"Destination attribute {dest} is already used for dataclass of type {dataclass}. Make sure all destinations are unique!")
        destinations.append(dest)

        for wrapped_field in wrapper.fields:
            # handle potential nesting.
            if wrapped_field.is_dataclass:
                child_dataclass = wrapped_field.field.type
                child_attribute_dest = f"{dest}.{wrapped_field.field.name}"
                logging.debug(f"adding child dataclass of type {child_dataclass} at attribute {child_attribute_dest}")
                logging.debug(f"wrapper is multiple: {wrapper.multiple}, wrapper prefix: {wrapper.prefix}")
                # TODO: Problem: If this is the first dataclass of this type that we see, then we would normally say it doesn't need a prefix.
                # However, if we see a second instance of this class as we recurse, then we would probably like to have a distinct prefix for each of them.. 
                if prefix:
                    child_prefix = prefix
                else:
                    child_prefix = wrapped_field.field.name + "_"
               
                self._register_dataclass(child_dataclass, child_attribute_dest, child_prefix)

            elif wrapped_field.is_tuple_or_list_of_dataclasses:
                self.error(textwrap.dedent(f"""\
                Nesting using attributes which are containers of a dataclass isn't supported (yet).
                """))

    def _preprocessing(self):
        logging.debug("\nPREPROCESSING\n")

        # Create one argument group per dataclass type
        for dataclass in self._wrappers:
            for prefix, wrapper in self._wrappers[dataclass].items():
                
                logging.debug(f"dataclass: {dataclass}, multiple={wrapper.multiple}")
                
                destinations = self._destinations[dataclass][prefix]
                names_string = self._get_destination_attributes_string(destinations)
                group = self.add_argument_group(
                    dataclass.__qualname__ + names_string,
                    description=dataclass.__doc__
                )
                
                for wrapped_field in wrapper.fields:
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
            constructor = wrappers[destination].instantiate_dataclass
            constructor_args = constructor_arguments[destination]    

            instance = constructor(constructor_args)

            if "." in destination:
                # if this destination is a nested child of another,
                # we set this instance in the corresponding constructor arguments,
                # such that the required parameters are set
                parts = destination.split(".")
                parent = ".".join(parts[:-1])
                attribute_in_parent = parts[-1]
                constructor_arguments[parent][attribute_in_parent] = instance
            else:
                # if this destination is not a nested child, we set the attribute
                # on the returned parsed_args.
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
        if prefix not in self._wrappers[dataclass]:
            wrapper = DataclassWrapper(dataclass, _prefix=prefix)
            self._wrappers[dataclass][prefix] = wrapper
        else:
            wrapper = self._wrappers[dataclass][prefix]
            logging.debug(f"The dataclass {dataclass} is already registered. Marking it as 'multiple'.")
            wrapper.multiple = True
        return wrapper

    def _get_destinations_for(self, dataclass: Type[Dataclass], prefix: str) -> List[str]:
        """Retrieves the list of attribute destinations for the given dataclass and prefix.
        
        Arguments:
            dataclass {Type[Dataclass]} -- the type of the dataclass to look for
            prefix {str} -- the prefix for that dataclass' arguments.
        
        Returns:
            List[str] -- the list of attribute strings, representing the final location of the instances in the parsed argparse.Namespace.
        """
        return self._destinations[dataclass][prefix]

    def _get_constructor_arguments_for_every_destination(self, parsed_args: argparse.Namespace)-> Dict[str, Dict[str, Any]]:
        constructor_arguments: Dict[str, Dict[str, Any]] = {}

        for dataclass in self._destinations:
            for prefix, destinations in self._destinations[dataclass].items():
                # get the associated wrapper
                wrapper = self._wrappers[dataclass][prefix]

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
        for dataclass in self._destinations:
            for prefix, destinations in self._destinations[dataclass].items():
                wrapper = self._wrappers[dataclass][prefix]
                for dest in destinations:
                    wrapper_for_destination[dest] = wrapper
        return wrapper_for_destination
        


    def _get_destination_attributes_string(self, destinations: List[str]) -> str:
        names = destinations
        names_string =f""" [{', '.join(f"'{name}'" for name in names)}]"""
        return names_string