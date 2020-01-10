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
from typing import *

from . import utils
from .conflicts import ConflictResolution, ConflictResolver
from .utils import DataclassType
from .wrappers import DataclassWrapper, FieldWrapper

logger = logging.getLogger(__name__)


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, conflict_resolution: ConflictResolution = ConflictResolution.AUTO, *args, **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = utils.Formatter
        super().__init__(*args, **kwargs)

        self.conflict_resolution = conflict_resolution
        # constructor arguments for the dataclass instances. (a Dict[dest, [attribute, value]])
        self.constructor_arguments: Dict[str, Dict[str, Any]] = collections.defaultdict(dict)

        self._conflict_resolver = ConflictResolver(self.conflict_resolution)
        self._wrappers: List[DataclassWrapper] = []

        self._preprocessing_done: bool = False


    def add_arguments(self, dataclass: DataclassType, dest: str, prefix="", default=None):
        """Adds corresponding command-line arguments for this class to the parser.
        
        Arguments:
            dataclass {DataclassType} -- The dataclass for which to add fields as arguments in the parser
        
        Keyword Arguments:
            dest {str} -- The destination attribute of the `argparse.Namespace` where the dataclass instance will be stored after calling `parse_args()`
            prefix {str} -- An optional prefix to add prepend to the names of the argparse arguments which will be generated for this dataclass.
            This can be useful when registering multiple distinct instances of the same dataclass.

        """
        for wrapper in self._wrappers:
            if wrapper.dest == dest:
                self.error(textwrap.dedent(f"""\
                    Destination attribute {dest} is already used for dataclass of type {dataclass}.
                    Make sure all destinations are unique.
                    """))
        new_wrapper: DataclassWrapper[DataclassType] = DataclassWrapper(dataclass, dest, _prefix=prefix, default=default)
        self._wrappers.append(new_wrapper)

    def parse_known_args(self, args=None, namespace=None):
        # NOTE: since the usual ArgumentParser.parse_args() calls parse_known_args,
        # we therefore just need to overload the parse_known_args method to support both.
        self._preprocessing()
        parsed_args, unparsed_args = super().parse_known_args(args, namespace)
        parsed_args = self._postprocessing(parsed_args)
        return parsed_args, unparsed_args

    def _preprocessing(self) -> None:
        """Resolve potential conflicts before actually adding all the required arguments."""
        logger.debug("\nPREPROCESSING\n")
        if self._preprocessing_done:
            return

        self._wrappers = self._conflict_resolver.resolve_conflicts(self._wrappers)
        
        # Create one argument group per dataclass
        for wrapper in self._wrappers:
            logger.debug(f"Adding arguments for dataclass: {wrapper.dataclass} at destinations {wrapper.destinations}")                
            wrapper.add_arguments(parser=self)
        
        self._preprocessing_done = True


    def _postprocessing(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        """Instantiate the dataclasses from the parsed arguments and set them to their destination attribute in the namespace
        
        Arguments:
            parsed_args {argparse.Namespace} -- the result of calling super().parse_args(...) or super().parse_known_args(...)
        
        Returns:
            argparse.Namespace -- The namespace, with the added attributes for each dataclass.
            TODO: Try and maybe return a nicer, typed version of parsed_args (a Namespace subclass maybe?)  
        """
        logger.debug("\nPOST PROCESSING\n")
        logger.debug(f"(raw) parsed args: {parsed_args}")
        
        # create the constructor arguments for each instance by consuming all the relevant attributes from `parsed_args` 
        parsed_args = self._consume_constructor_arguments(parsed_args)
        logger.debug(f"leftover arguments: {parsed_args}")
        
        parsed_args = self._set_instances_in_namespace(parsed_args)
        return parsed_args

    def _set_instances_in_namespace(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        """We now have all the constructor arguments for each instance.
        We can now sort out the dependencies, create the instances, and set them as attributes of the Namespace.
        
        Since the dataclasses might have nested children, and we need to pass all the constructor arguments when
        calling the dataclass constructors, we create the instances in a "bottom-up" fashion,
        creating the deepest objects first, and then setting their value in the `constructor_arguments` dict.

        Args:
            parsed_args (argparse.Namespace): the "raw" Namespace that comes out of the parser.parse_known_args() call.
        
        Returns:
            argparse.Namespace: The transformed namespace.
        """
        # sort the wrappers so as to construct the leaf nodes first.
        sorted_wrappers: List[DataclassWrapper] = sorted(self._wrappers, key=lambda w: w.nesting_level, reverse=True)
        
        for wrapper in sorted_wrappers:
            for destination in wrapper.destinations:
                logger.debug(f"wrapper name: {wrapper.attribute_name}, destination: {destination}")
                
                # instantiate the dataclass by passing the constructor arguments to the constructor.
                # NOTE: for now, this might prevent users from having required InitVars in their dataclasses,
                # as we can't pass the value to the constructor. Might be fine though.
                constructor = wrapper.dataclass
                constructor_args = self.constructor_arguments[destination]
                instance = constructor(**constructor_args)
                
                if wrapper._parent is not None:
                    parent_key, attribute_in_parent = utils.split_parent_and_child(destination)
                    logger.debug(f"Setting a value at attribute {attribute_in_parent} in parent {parent_key}.")
                    self.constructor_arguments[parent_key][attribute_in_parent] = instance
                    
                    # TODO: not needed, but might be a good thing to do?
                    # self.constructor_arguments.pop(destination) # remove the 'args dict' for this child class.
                else:
                    # if this destination is not a nested class, we set the attribute
                    # on the returned Namespace.
                    logger.debug(f"setting attribute '{destination}' on the Namespace to a value of {instance}")
                    assert not hasattr(parsed_args, destination), f"Namespace should not already have a '{destination}' attribute! (namespace: {parsed_args}) "
                    setattr(parsed_args, destination, instance)
        return parsed_args

    def _consume_constructor_arguments(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        """Create the constructor arguments for each instance by consuming all the attributes from `parsed_args` 
        
        Here we imitate a custom action, by having the FieldWrappers be callables
        
        Args:
            parsed_args (argparse.Namespace): the argparse.Namespace returned from super().parse_args().
        
        Returns:
            argparse.Namespace: The namespace, without the consumed arguments.
        """
        parsed_arg_values = vars(parsed_args)
        for wrapper in self._wrappers:
            for field in wrapper.fields:
                if not field.field.init:
                    continue
                values = parsed_arg_values.get(field.dest, field.defaults)
                # call the "action" for the given attribute.
                # this sets the right value in the `self.constructor_arguments` dictionary.
                field(parser=self, namespace=parsed_args, values=values, option_string=None)

        # "Clean up" the Namespace by returning a new Namespace without the consumed attributes.
        deleted_values: Dict[str, Any] = {}
        for wrapper in self._wrappers:
            for field in wrapper.fields:
                deleted_values[field.dest] = parsed_arg_values.pop(field.dest, None)
        leftover_args = argparse.Namespace(**parsed_arg_values)
        logger.debug(f"deleted values: {deleted_values}")
        logger.debug(f"leftover args: {leftover_args}")
        return leftover_args
