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
from .utils import Dataclass, DataclassType


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
        self._wrappers: Dict[DataclassType, Dict[str, DataclassWrapper]] = defaultdict(dict)

        # the dictionary that maps from destination to DataclassWrapper.
        self._destinations: Dict[str, DataclassWrapper] = {}

        self.constructor_arguments: Dict[str, Dict[str, Any]] = defaultdict(dict)


    def add_arguments(self, dataclass: DataclassType, dest: str, prefix=""):
        """Adds corresponding command-line arguments for this class to the parser.
        
        Arguments:
            dataclass {DataclassType} -- The dataclass for which to add fields as arguments in the parser
        
        Keyword Arguments:
            dest {str} -- The destination attribute of the `argparse.Namespace` where the dataclass instance will be stored after calling `parse_args()`
            prefix {str} -- An optional prefix to add prepend to the names of the argparse arguments which will be generated for this dataclass.
            This can be useful when registering multiple distinct instances of the same dataclass.

        """
        
        if dest in self._destinations.keys():
            self.error(textwrap.dedent(f"""\
                Destination attribute {dest} is already used for dataclass of type {dataclass}.
                Make sure all destinations are unique.
                """))

        wrapper = self._register_dataclass(dataclass, dest, prefix=prefix)
        logging.debug("adding wrapper:\n", wrapper, "\n")

        # iterate over the wrapper and its children (nested) wrappers.
        for child_wrapper in iter(wrapper):
            logging.debug(f"adding wrapper {child_wrapper.dataclass}, prefix: '{child_wrapper.prefix}', destinations: {child_wrapper.destinations}")
            self._wrappers[child_wrapper.dataclass][child_wrapper.prefix] = child_wrapper

    def parse_known_args(self, args=None, namespace=None):
        # NOTE: since the usual ArgumentParser.parse_args() calls parse_known_args, we therefore just need to overload the parse_known_args method.
        self._preprocessing()
        parsed_args, unparsed_args = super().parse_known_args(args, namespace)
        return self._postprocessing(parsed_args), unparsed_args

    def _register_dataclass(self, dataclass: DataclassType, dest: str, prefix: str = "") -> DataclassWrapper[DataclassType]:
        """registers the given dataclass to be parsed later.
        
        Arguments:
            dataclass {Type[Dataclass]} -- The dataclass to register
            dest {str} -- a string which is to be used to  NamedTuple used to keep track of where to store the resulting instance and the number of instances.
        """
        
        print(f"Registering dataclass {dataclass} destination: '{dest}' prefix: '{prefix}'")

        new_wrapper = DataclassWrapper(dataclass)
        new_wrapper.prefix = prefix
        new_wrapper.destinations.append(dest)

        if dataclass in self._wrappers.keys():
            # we've already seen this dataclass.
            existing_prefixes = self._wrappers[dataclass].keys()
            if prefix in existing_prefixes:
                # there is already a DataclassWrapper for this dataclass and with this prefix.
                # we therefore have to handle potential this conflict.
                existing_wrapper = self._wrappers[dataclass][prefix]
                new_wrapper = self._handle_confict(existing_wrapper, new_wrapper)

        return new_wrapper


    def _handle_confict(self, existing_wrapper: DataclassWrapper, new_wrapper: DataclassWrapper) -> DataclassWrapper:
        dataclass = new_wrapper.dataclass
        dest = new_wrapper.destinations
        prefix = new_wrapper.prefix

        if self.conflict_resolution == ConflictResolution.NONE:
            self.error(textwrap.dedent(f"""\
            Dataclass of type {dataclass} is already registered under destination {dest} and with prefix '{prefix}'.
            (Conflict Resolution mode is {self.conflict_resolution})
            """))
        
        elif self.conflict_resolution == ConflictResolution.ALWAYS_MERGE:
            if not existing_wrapper.multiple:
                logging.warning(textwrap.dedent(f"""\
                Dataclass of type {dataclass} is already registered under destination {dest} and with prefix '{prefix}'.
                Each attribute of this dataclass will be marked as 'Multiple', and will be set in the order they were defined.
                (Conflict Resolution mode is {self.conflict_resolution})
                """))            
            existing_wrapper.merge(new_wrapper)
            del new_wrapper
            new_wrapper = existing_wrapper
            # we'll allow adding another dataclass that will share the same argument. 
            # the dataclass will be marked as 'multiple' now, if it wasn't already.

        elif self.conflict_resolution == ConflictResolution.EXPLICIT:
            print("explicit")
            # We don't allow any ambiguous use.
            # Every wrapper will have a prefix that will be equal to the full path to each of its arguments.
            logging.warning(textwrap.dedent(f"""\
            Dataclass of type {dataclass} is already registered under destination {dest} and with prefix '{prefix}'.
            A prefix of '{dest}.' will be used for every argument of this new class.
            (Conflict Resolution mode is {self.conflict_resolution})
            """))
            # TODO: handle this, we need to also update the existing wrapper's prefixes.
            assert not existing_wrapper.multiple, "the existing wrapper can't be multiple, since we're using EXPLICIT conflict resolution mode..."
            assert len(existing_wrapper.destinations) == 1, f"Should have had only one entry: {existing_wrapper.destinations}"
            existing_wrapper.prefix = existing_wrapper.destinations[0] + "."
            new_wrapper.prefix = new_wrapper.destinations[0] + "."

        elif self.conflict_resolution == ConflictResolution.AUTO:
            print("auto")
            # IDEA: find the simplest way to tell appart every instance of the classes, and use that as a prefix.
            raise NotImplementedError("Auto conflict resolution isn't implemented yet.")
            
        return new_wrapper

    def _preprocessing(self):
        logging.debug("\nPREPROCESSING\n")
        logging.debug("PREPROCESSING")




        # Create one argument group per dataclass type
        for dataclass in self._wrappers:
            for prefix, wrapper in self._wrappers[dataclass].items():
                logging.debug(f"dataclass: {dataclass}, multiple={wrapper.multiple}")
                
                wrapper.add_arguments(parser=self)

                # group = self.add_argument_group(
                #     dataclass.__qualname__ + names_string,
                #     description=dataclass.__doc__
                # )
                
                # for wrapped_field in wrapper.fields:
                #     logging.debug(f"arg options: {wrapped_field.name}, {wrapped_field.arg_options}")
                #     if wrapped_field.arg_options:
                #         name = f"--{wrapped_field.name}"
                #         wrapped_field.
                #         # group.add_argument(
                #         #     name_or_flags: str,
                #         #     action: Union[str, Type[Action]],
                #         #     nargs: Union[int, str],
                        #     const: Any,
                        #     default: Any,
                        #     type: Union[Unknown, FileType],
                        #     choices: Iterable[_T],
                        #     required: bool,
                        #     help: str,
                        #     metavar: Union[str, Tuple[str]],
                        #     dest: str,
                        #     version: str
                        # ) -> Actionname, )

    def _postprocessing(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        """Instantiate the dataclasses from the parsed arguments and add them to their destination key in the namespace
        
        Arguments:
            parsed_args {argparse.Namespace} -- the result of calling super().parse_args()
        
        Returns:
            argparse.Namespace -- The namespace, with the added attributes for each dataclass.
            TODO: Try and maybe return a nicer, typed version of parsed_args (a Namespace subclass maybe?)  
        """
        logging.debug("\nPOST PROCESSING\n")
        constructor_arguments = self.constructor_arguments

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

    def _get_wrapper_for_every_destination(self) -> Dict[str, DataclassWrapper[DataclassType]]:
        """Returns a dictionary where for every key (a destination), we return the associated DataclassWrapper.
        NOTE: multiple destinations can share the same DataclassWrapper instance.
        
        Returns:
            Dict[str, DataclassWrapper[Dataclass]] -- [description]
        """
        wrapper_for_destination: Dict[str, DataclassWrapper[DataclassType]] = {}
        for dataclass in self._wrappers:
            for prefix, wrapper in self._wrappers[dataclass].items():
                destinations = wrapper.destinations
                for dest in destinations:
                    wrapper_for_destination[dest] = wrapper
        return wrapper_for_destination
        