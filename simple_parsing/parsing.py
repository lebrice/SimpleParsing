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
DataclassType = Type[Dataclass]

class ConflictResolution(enum.Enum):
    """Used to determine which action to take when adding arguments for the same dataclass in two different destinations.
    
    - NONE: Dissallow using the same dataclass in two different destinations without explicitly setting a distinct prefix for at least one of them.
    - EXPLICIT: When adding arguments for a dataclass that is already present, the argparse arguments for each class will use their full absolute path as a prefix.
    - ALWAYS_MERGE: When adding arguments for a dataclass that is already present, the arguments for the first and second destinations will be set using the same name, 
        and the values for each will correspond to the first and second passed values, respectively.
        This will change the argparse type for that argument into a list of the original item type.
    - AUTO: TODO:
    
    """
    NONE = -1
    EXPLICIT = 0
    ALWAYS_MERGE = 1
    AUTO = 2

class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, conflict_resolution: ConflictResolution = ConflictResolution.NONE, *args, **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = utils.Formatter
        super().__init__(*args, **kwargs)
        # the kind of prefixing mechanism to use.
        self.conflict_resolution = conflict_resolution

        # two-level dictionary that maps from (dataclass, string_prefix) -> DataclassWrapper. 
        self._wrappers: Dict[DataclassType, Dict[str, DataclassWrapper[DataclassType]]] = defaultdict(dict)

        # the dictionary that maps from destination to DataclassWrapper.
        self._destinations: Dict[str, DataclassWrapper[DataclassType]] = {}

    def add_arguments(self, dataclass: DataclassType, dest: str, prefix=""):
        """Adds corresponding command-line arguments for this class to the parser.
        
        Arguments:
            dataclass {DataclassType} -- The dataclass for which to add fields as arguments in the parser
        
        Keyword Arguments:
            dest {str} -- The destination attribute of the `argparse.Namespace` where the dataclass instance will be stored after calling `parse_args()`
            prefix {str} -- An optional prefix to add prepend to the names of the argparse arguments which will be generated for this dataclass.
            This can be useful when registering multiple distinct instances of the same dataclass.

        """
        wrapper = self._register_dataclass(dataclass, dest, prefix=prefix)
        logging.debug("adding wrapper:\n", wrapper, "\n")

        # iterate over the wrapper and its children (nested) wrappers.
        for child_wrapper in iter(wrapper):
            logging.debug(f"adding wrapper {child_wrapper.dataclass}, prefix: '{child_wrapper.prefix}', destinations: {child_wrapper._destinations}")
            

            if child_wrapper.prefix in self._wrappers[child_wrapper.dataclass]:
                logging.debug("a wrapper for this already exists, merging them together.")
                other = self._wrappers[child_wrapper.dataclass][child_wrapper.prefix]
                other._destinations.extend(child_wrapper._destinations)
                other._children.extend(child_wrapper._children)
                other.multiple = True
                del child_wrapper
                child_wrapper = other
            
            self._wrappers[child_wrapper.dataclass][child_wrapper.prefix] = child_wrapper

    def parse_known_args(self, args=None, namespace=None):
        # NOTE: since the usual ArgumentParser.parse_args() calls parse_known_args, we therefore just need to overload the parse_known_args method.
        self._preprocessing()
        parsed_args, unparsed_args = super().parse_known_args(args, namespace)
        return self._postprocessing(parsed_args), unparsed_args

    def _register_dataclass(self, dataclass: DataclassType, dest: str, prefix: str = "", parent=None) -> DataclassWrapper[DataclassType]:
        """registers the given dataclass to be parsed later.
        
        Arguments:
            dataclass {Type[Dataclass]} -- The dataclass to register
            dest {str} -- a string which is to be used to  NamedTuple used to keep track of where to store the resulting instance and the number of instances.
        """
        
        print(f"Registering dataclass {dataclass} destination: '{dest}' prefix: '{prefix}'")

        if dest in self._destinations.keys():
            self.error(textwrap.dedent(f"""\
                Destination attribute {dest} is already used for dataclass of type {dataclass}.
                Make sure all destinations are unique.
                """))
       
        if dataclass in self._wrappers.keys():
            print("here")
            # we've already seen this dataclass.
            # we get the prefixes that are already used.
            existing_prefixes = self._wrappers[dataclass].keys()
            if prefix in existing_prefixes:
                existing_wrapper = self._wrappers[dataclass][prefix]
                if self.conflict_resolution == ConflictResolution.NONE:
                    print("none")
                    self.error(textwrap.dedent(f"""\
                    Dataclass of type {dataclass} is already registered under destination {dest} and with prefix '{prefix}'.
                    (Conflict Resolution mode is {self.conflict_resolution})
                    """))

                elif self.conflict_resolution == ConflictResolution.EXPLICIT:
                    print("explicit")
                    # We don't allow any ambiguous use.
                    # Every wrapper will have a prefix that will be equal to the full path to each of its arguments.
                    logging.warning(textwrap.dedent(f"""\
                    Dataclass of type {dataclass} is already registered under destination {dest} and with prefix '{prefix}'.
                    A prefix of '{dest}.' will be used for every argument of this new class.
                    (Conflict Resolution mode is {self.conflict_resolution})
                    """))
                    prefix = dest + "."

                elif self.conflict_resolution == ConflictResolution.AUTO:
                    print("auto")
                    # we'll allow adding another dataclass that will share the same argument. 
                    # the dataclass will be marked as 'multiple' now, if it wasn't already.
                    if not existing_wrapper.multiple:
                        logging.warning(textwrap.dedent(f"""\
                        Dataclass of type {dataclass} is already registered under destination {dest} and with prefix '{prefix}'.
                        Each attribute of this dataclass will be marked as 'Multiple', and will be set in the order they were defined.
                        (Conflict Resolution mode is {self.conflict_resolution})
                        """))

        wrapper = DataclassWrapper(dataclass, _prefix=prefix)
        destinations = wrapper._destinations
        


        if parent is not None:
            logging.debug(f"Parent prefix: '{parent.prefix}', parent multiple: {parent.multiple}")
            wrapper._parent = parent

        if dest in destinations:
            self.error(textwrap.dedent(f"""\
                Destination attribute {dest} is already used for dataclass of type {dataclass} with prefix '{prefix}'.
                Make sure all destinations are unique, or use a different prefix!
                """))
        destinations.append(dest)
        
        for wrapped_field in wrapper.fields:
            
            # handle nesting.
            if wrapped_field.is_dataclass:
                child_dataclass = wrapped_field.field.type
                child_attribute_dest = f"{dest}.{wrapped_field.field.name}"
                logging.debug(f"adding child dataclass of type {child_dataclass} at attribute {child_attribute_dest}")
                logging.debug(f"wrapper is multiple: {wrapper.multiple}, wrapper prefix: '{wrapper.prefix}'")               
                child_prefix = prefix
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
    
    def _get_wrapper_for_every_destination(self) -> Dict[str, DataclassWrapper[DataclassType]]:
        """Returns a dictionary where for every key (a destination), we return the associated DataclassWrapper.
        NOTE: multiple destinations can share the same DataclassWrapper instance.
        
        Returns:
            Dict[str, DataclassWrapper[Dataclass]] -- [description]
        """
        wrapper_for_destination: Dict[str, DataclassWrapper[DataclassType]] = {}
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
