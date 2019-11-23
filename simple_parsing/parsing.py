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

        # # a set to check which arguments have been added so far.
        # self.added_arguments: Set[str] = set()

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
        logging.debug("added wrapper:\n", wrapper, "\n")

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
        
        logging.debug(f"Registering dataclass {dataclass} destination: '{dest}' prefix: '{prefix}'")
        # construct the wrapper and all its children.
        new_wrapper = DataclassWrapper(dataclass, dest)
        new_wrapper.prefix = prefix

        existing_wrapper = self._wrappers[dataclass].get(prefix)
        if existing_wrapper is not None:
            # there is already a DataclassWrapper for this dataclass and with this prefix.
            # we therefore have to handle this conflict.
            new_wrapper = self._handle_confict(existing_wrapper, new_wrapper)

        self._wrappers[dataclass][prefix] = new_wrapper        
        for child_wrapper in new_wrapper.descendants:
            assert new_wrapper.prefix == prefix
            self._wrappers[child_wrapper.dataclass][prefix] = new_wrapper

        return new_wrapper


    def _preprocessing(self):
        logging.debug("\nPREPROCESSING\n")
        # Create one argument group per dataclass type
        for dataclass in self._wrappers:
            for prefix, wrapper in self._wrappers[dataclass].items():
                logging.debug(f"Adding arguments for dataclass: {dataclass}, multiple={wrapper.multiple}")                
                wrapper.add_arguments(parser=self)


    def _postprocessing(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        """Instantiate the dataclasses from the parsed arguments and add them to their destination key in the namespace
        
        Arguments:
            parsed_args {argparse.Namespace} -- the result of calling super().parse_args()
        
        Returns:
            argparse.Namespace -- The namespace, with the added attributes for each dataclass.
            TODO: Try and maybe return a nicer, typed version of parsed_args (a Namespace subclass maybe?)  
        """
        logging.debug("\nPOST PROCESSING\n")
        logging.debug(f"parsed args: {parsed_args}")
        
        # create the constructor arguments for each instance by consuming all the attributes from `parsed_args` 
        parsed_args = self._populate_constructor_arguments(parsed_args)
        
        # we now have all the constructor arguments for each instance.
        # we can now sort out the different dependencies, and create the instances.
        wrappers: Dict[str, DataclassWrapper] = self._wrapper_for_every_destination
        # we construct the 'tree' of dependencies from the bottom up,
        # starting with nodes that are children.
        destinations = self.constructor_arguments.keys()
        nesting_level = lambda destination_attribute: destination_attribute.count(".")
        
        for destination in sorted(destinations, key=nesting_level, reverse=True):
            constructor = wrappers[destination].instantiate_dataclass
            constructor_args = self.constructor_arguments[destination]
            # create the dataclass instance.
            instance = constructor(constructor_args)

            parts = destination.split(".")
            parent = ".".join(parts[:-1])
            attribute_in_parent = parts[-1]
            
            if parent:
                # if this instance is an attribute in another dataclass,
                # we set the value in the parent's constructor arguments
                # at the associated attribute to this instance.
                self.constructor_arguments[parent][attribute_in_parent] = instance
            else:
                # if this destination is a top-level attribute, we set the attribute
                # on the returned parsed_args.
                logging.debug(f"setting attribute '{destination}' on the parsed_args to a value of {instance}")
                assert not hasattr(parsed_args, destination), "Namespace should not already have a '{destination}' attribute! (namespace: {parsed_args}) "
                setattr(parsed_args, destination, instance)
        
        logging.debug(f"Final parsed args: {parsed_args}")
        
        return parsed_args

    def _populate_constructor_arguments(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        """Create the constructor arguments for each instance by consuming all the attributes from `parsed_args` 
        
        Args:
            parsed_args (argparse.Namespace): the argparse.Namespace returned from super().parse_args().
        
        Returns:
            argparse.Namespace: The namespace, without the consumed arguments.
        """
        wrappers: Dict[str, DataclassWrapper] = self._wrapper_for_every_destination
        # TODO: it would be cleaner if the CustomAction was working!
        # Imitate implementing a custom action:
        parsed_arg_values = vars(parsed_args)
        for wrapper in wrappers.values():
            for field in wrapper.fields:
                values = parsed_arg_values.get(field.dest, field.default)
                # call the action manually.
                # this sets the right value in the `self.constructor_arguments` dictionary.
                field(parser=self, namespace=parsed_args, values=values, option_string=None)

        #Clean up the 'parsed_args' by deleting all the consumed attributes.
        deleted_values: Dict[str, Any] = {
            field.dest: parsed_arg_values.pop(field.dest, None) for field in wrapper.fields for wrapper in wrappers.values()
        }
        logging.debug("deleted values:", deleted_values)
        parsed_args = argparse.Namespace(**parsed_arg_values)
        return parsed_args


    def _handle_confict(self, existing_wrapper: DataclassWrapper, new_wrapper: DataclassWrapper) -> DataclassWrapper:
        logging.debug(f"Handling conflict. ConflictResolutionMode is {self.conflict_resolution}")
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
            # logging.debug("MERGING")
            # logging.debug("Parent:", existing_wrapper._parent)
            # logging.debug("existing wrapper destinations:", existing_wrapper.destinations)
            # logging.debug("new wrapper destinations:", new_wrapper.destinations)
            existing_wrapper.merge(new_wrapper)
            # logging.debug("(updated) existing wrapper:\n", existing_wrapper)
            del new_wrapper
            new_wrapper = existing_wrapper
            # we'll allow adding another dataclass that will share the same argument. 
            # the dataclass will be marked as 'multiple' now, if it wasn't already.

        elif self.conflict_resolution == ConflictResolution.EXPLICIT:
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
            logging.debug("auto")
            # IDEA: find the simplest way to tell appart every instance of the classes, and use that as a prefix.
            raise NotImplementedError("Auto conflict resolution isn't implemented yet.")
        
        return new_wrapper

    @property
    def _wrapper_for_every_destination(self) -> Dict[str, DataclassWrapper[DataclassType]]:
        """Returns a dictionary where for every key (a destination), we return the associated DataclassWrapper.
        NOTE: multiple destinations can share the same DataclassWrapper instance.
        
        Returns:
            Dict[str, DataclassWrapper[Dataclass]] -- [description]
        """
        wrapper_for_destination: Dict[str, DataclassWrapper[DataclassType]] = {}
        for dataclass in self._wrappers.keys():
            for prefix, wrapper in self._wrappers[dataclass].items():
                for dest in wrapper.destinations:
                    wrapper_for_destination[dest] = wrapper
        return wrapper_for_destination
        