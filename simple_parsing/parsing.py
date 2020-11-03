"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
import argparse
import collections
import dataclasses
import enum
import inspect
import re
import sys
import textwrap
import typing
import warnings
from argparse import HelpFormatter, Namespace
from collections import defaultdict
from typing import (Any, ClassVar, Dict, List, Sequence, Text, Type, Union,
                    overload)

from . import utils
from .conflicts import ConflictResolution, ConflictResolver
from .help_formatter import SimpleHelpFormatter
from .logging_utils import get_logger
from .utils import Dataclass, split_dest
from .wrappers import DataclassWrapper, FieldWrapper

logger = get_logger(__file__)


class ParsingError(RuntimeError, SystemExit):
    pass


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args,
                 conflict_resolution: ConflictResolution=ConflictResolution.AUTO,
                 add_option_string_dash_variants: bool=False,
                 add_dest_to_option_strings: bool=True,
                 formatter_class: Type[HelpFormatter]=SimpleHelpFormatter,
                 **kwargs):
        """Creates an ArgumentParser instance.

        Parameters
        ----------
        - conflict_resolution : ConflictResolution, optional

            What kind of prefixing mechanism to use when reusing dataclasses
            (argument groups).
            For more info, check the docstring of the `ConflictResolution` Enum.

        - add_option_string_dash_variants : bool, optional

            Wether or not to add option_string variants where the underscores in
            attribute names are replaced with dashes.
            For example, when set to `True`, "--no-cache" and "--no_cache" can
            both be used to point to the same attribute `no_cache` on some
            dataclass.
        
        - add_dest_to_option_strings: bool, optional

            Wether or not to add the `dest` of each field to the list of option
            strings for the argument.
            When True (default), each field can be referenced using either the
            auto-generated option string or the full 'destination' of the field
            in the resulting namespace.
            When False, only uses the auto-generated option strings.
            
            The auto-generated option strings are usually just the field names,
            except when there are multiple arguments with the same name. In this
            case, the conflicts are resolved as determined by the value of
            `conflict_resolution` and each field ends up with a unique option
            string.

        - formatter_class : Type[HelpFormatter], optional

            The formatter class to use. By default, uses
            `simple_parsing.SimpleHelpFormatter`, which is a combination of the
            `argparse.ArgumentDefaultsHelpFormatter`,
            `argparse.MetavarTypeHelpFormatter` and
            `argparse.RawDescriptionHelpFormatter` classes.
        """
        kwargs["formatter_class"] = formatter_class
        super().__init__(*args, **kwargs)

        self.conflict_resolution = conflict_resolution
        # constructor arguments for the dataclass instances.
        # (a Dict[dest, [attribute, value]])
        self.constructor_arguments: Dict[str, Dict] = defaultdict(dict)

        self._conflict_resolver = ConflictResolver(self.conflict_resolution)
        self._wrappers: List[DataclassWrapper] = []

        self._preprocessing_done: bool = False
        FieldWrapper.add_dash_variants = add_option_string_dash_variants
        FieldWrapper.add_dest_to_option_strings = add_dest_to_option_strings

    @overload
    def add_arguments(self, dataclass: Type[Dataclass], dest: str, prefix: str="", default: Dataclass=None):
        pass
    
    @overload
    def add_arguments(self, dataclass: Dataclass, dest: str, prefix: str=""):
        pass

    def add_arguments(self,
                      dataclass: Union[Type[Dataclass], Dataclass],
                      dest: str,
                      prefix: str="",
                      default: Dataclass = None):
        """Adds command-line arguments for the fields of `dataclass`.

        Parameters
        ----------
        dataclass : Union[Dataclass, Type[Dataclass]]
            The dataclass whose fields are to be parsed from the commnad-line.
            If an instance of a dataclass is given, it is used as the default
            value if none is provided.
        dest : str
            The destination attribute of the `argparse.Namespace` where the
            dataclass instance will be stored after calling `parse_args()`
        prefix : str, optional
            An optional prefix to add prepend to the names of the argparse
            arguments which will be generated for this dataclass.
            This can be useful when registering multiple distinct instances of
            the same dataclass, by default ""
        default : Dataclass, optional
            An instance of the dataclass type to get default values from, by
            default None
        """
        for wrapper in self._wrappers:
            if wrapper.dest == dest:
                raise argparse.ArgumentError(
                    argument=None,
                    message=f"Destination attribute {dest} is already used for "
                    f"dataclass of type {dataclass}. Make sure all destinations"
                    f" are unique."
                )
        if not isinstance(dataclass, type):
            default = dataclass if default is None else default
            dataclass = type(dataclass)

        new_wrapper = DataclassWrapper(
            dataclass,
            dest,
            prefix=prefix,
            default=default
        )
        self._wrappers.append(new_wrapper)

    def parse_known_args(self,
                         args: Sequence[Text] = None,
                         namespace: Namespace = None,
                         attempt_to_reorder: bool=False):
        # NOTE: since the usual ArgumentParser.parse_args() calls
        # parse_known_args, we therefore just need to overload the
        # parse_known_args method to support both.
        if args is None:
            # args default to the system args
            args = sys.argv[1:]
        else:
            # make sure that args are mutable
            args = list(args)
        self._preprocessing()

        parsed_args, unparsed_args = super().parse_known_args(args, namespace)

        if unparsed_args and self._subparsers and attempt_to_reorder:
            logger.warning(
                f"Unparsed arguments when using subparsers. Will "
                f"attempt to automatically re-order the unparsed arguments "
                f"{unparsed_args}."
            )
            index_in_start = args.index(unparsed_args[0])
            # Simply 'cycle' the args to the right ordering.
            new_start_args = args[index_in_start:] + args[:index_in_start]
            parsed_args, unparsed_args = super().parse_known_args(new_start_args)

        parsed_args = self._postprocessing(parsed_args)
        return parsed_args, unparsed_args

    def print_help(self, file=None):
        self._preprocessing()
        return super().print_help(file)

    def equivalent_argparse_code(self) -> str:
        """Returns the argparse code equivalent to that of `simple_parsing`. 
        
        TODO: Could be fun, pretty sure this is useless though.
        
        Returns
        -------
        str
            A string containing the auto-generated argparse code.
        """
        self._preprocessing()
        code = f"parser = ArgumentParser()"
        for wrapper in self._wrappers:
            code += "\n"
            code += wrapper.equivalent_argparse_code()
            code += "\n"
        code += "args = parser.parse_args()\n"
        code += "print(args)\n"
        return code

    def _resolve_conflicts(self) -> None:
        self._wrappers = self._conflict_resolver.resolve(self._wrappers)

    def _preprocessing(self) -> None:
        """Resolve potential conflicts and actual add all the arguments."""
        logger.debug("\nPREPROCESSING\n")
        if self._preprocessing_done:
            return

        self._resolve_conflicts()

        # Create one argument group per dataclass
        for wrapper in self._wrappers:
            logger.debug(
                f"Adding arguments for dataclass: {wrapper.dataclass} "
                f"at destinations {wrapper.destinations}"
            )
            wrapper.add_arguments(parser=self)
        self._preprocessing_done = True

    def _postprocessing(self, parsed_args: Namespace) -> Namespace:
        """Process the namespace by extract the fields and creating the objects.

        Instantiate the dataclasses from the parsed arguments and set them at
        their destination attribute in the namespace.

        Parameters
        ----------
        parsed_args : Namespace
            the result of calling `super().parse_args(...)` or
            `super().parse_known_args(...)`.
            TODO: Try and maybe return a nicer, typed version of parsed_args.  


        Returns
        -------
        Namespace
            The original Namespace, with all the arguments corresponding to the
            dataclass fields removed, and with the added dataclass instances.
            Also keeps whatever arguments were added in the traditional fashion,
            i.e. with `parser.add_argument(...)`. 
        """
        logger.debug("\nPOST PROCESSING\n")
        logger.debug(f"(raw) parsed args: {parsed_args}")
        # create the constructor arguments for each instance by consuming all
        # the relevant attributes from `parsed_args`
        parsed_args = self._consume_constructor_arguments(parsed_args)
        parsed_args = self._set_instances_in_namespace(parsed_args)
        return parsed_args

    def _set_instances_in_namespace(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        """Create the instances set them at their destination in the namespace.

        We now have all the constructor arguments for each instance.
        We can now sort out the dependencies, create the instances, and set them
        as attributes of the Namespace.

        Since the dataclasses might have nested children, and we need to pass
        all the constructor arguments when calling the dataclass constructors,
        we create the instances in a "bottom-up" fashion, creating the deepest
        objects first, and then setting their value in the
        `constructor_arguments` dict.

        Parameters
        ----------
        parsed_args : argparse.Namespace
            The 'raw' Namespace that is produced by `parse_args`.

        Returns
        -------
        argparse.Namespace
            The transformed namespace with the instances set at their 
            corresponding destinations.
        """
        # sort the wrappers so as to construct the leaf nodes first.
        sorted_wrappers: List[DataclassWrapper] = sorted(
            self._wrappers,
            key=lambda w: w.nesting_level,
            reverse=True
        )

        for wrapper in sorted_wrappers:
            for destination in wrapper.destinations:
                # instantiate the dataclass by passing the constructor arguments
                # to the constructor.
                # TODO: for now, this might prevent users from having required
                # InitVars in their dataclasses, as we can't pass the value to
                # the constructor. Might be fine though.
                constructor = wrapper.dataclass
                constructor_args = self.constructor_arguments[destination]

                # If the dataclass wrapper is marked as 'optional' and all the
                # constructor args are None, then the instance is None.
                # TODO: How to discern the case where all values ARE none, and
                # the case where the instance is to be None?
                if wrapper.optional:
                    all_default_or_none = True
                    for field_wrapper in wrapper.fields:
                        arg_value = constructor_args[field_wrapper.name]
                        default_value = field_wrapper.default
                        logger.debug(f"field {field_wrapper.name}, arg value: {arg_value}, default value: {default_value}")
                        if arg_value != default_value:
                            all_default_or_none = False
                            break
                    logger.debug(f"All fields were either default or None: {all_default_or_none}")

                    if all_default_or_none:
                        instance = None
                    else:
                        instance = constructor(**constructor_args)
                else:
                    instance = constructor(**constructor_args)

                if wrapper.parent is not None:
                    parent_key, attr = utils.split_dest(destination)
                    logger.debug(
                        f"Setting a value of {instance} at attribute {attr} in "
                        f"parent at key {parent_key}."
                    )
                    self.constructor_arguments[parent_key][attr] = instance

                else:
                    # if this destination is not a nested class, we set the
                    # attribute on the returned Namespace.
                    logger.debug(
                        f"setting attribute '{destination}' on the Namespace "
                        f"to a value of {instance}"
                    )
                    assert not hasattr(parsed_args, destination), (
                        f"Namespace should not already have a '{destination}' "
                        f"attribute! (namespace: {parsed_args}) "
                    )
                    setattr(parsed_args, destination, instance)

                # TODO: not needed, but might be a good thing to do?
                # remove the 'args dict' for this child class.
                self.constructor_arguments.pop(destination)

        assert not self.constructor_arguments
        return parsed_args

    def _consume_constructor_arguments(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        """Create the constructor arguments for each instance.

        Creates the arguments by consuming all the attributes from
        `parsed_args`.
        Here we imitate a custom action, by having the FieldWrappers be
        callables that set their value in the `constructor_args` attribute.

        Parameters
        ----------
        parsed_args : argparse.Namespace
            the argparse.Namespace returned from super().parse_args().

        Returns
        -------
        argparse.Namespace
            The namespace, without the consumed arguments.
        """
        parsed_arg_values = vars(parsed_args)
        for wrapper in self._wrappers:
            for field in wrapper.fields:
                if not field.field.init:
                    # The field isn't an argument of the dataclass constructor.
                    continue
                values = parsed_arg_values.get(field.dest, field.default)

                # call the "action" for the given attribute. This sets the right
                # value in the `self.constructor_arguments` dictionary.
                field(parser=self, namespace=parsed_args, values=values)

        # "Clean up" the Namespace by returning a new Namespace without the
        # consumed attributes.
        deleted_values: Dict[str, Any] = {}
        for wrapper in self._wrappers:
            for field in wrapper.fields:
                value = parsed_arg_values.pop(field.dest, None)
                deleted_values[field.dest] = value

        leftover_args = argparse.Namespace(**parsed_arg_values)
        if deleted_values:
            logger.debug(f"deleted values: {deleted_values}")
            logger.debug(f"leftover args: {leftover_args}")
        return leftover_args
