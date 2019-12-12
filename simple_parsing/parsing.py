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


# logging.basicConfig(level=logging.WARN)
# logger = logging.getLogger("simple_parsing")
logger = logging.getLogger(__name__)

from . import docstring, utils
from .wrappers import DataclassWrapper, FieldWrapper
from .utils import Dataclass, DataclassType, MutableField

Conflict = Tuple[DataclassType, str, List[DataclassWrapper]]

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
    def __init__(self, conflict_resolution: ConflictResolution = ConflictResolution.AUTO, *args, **kwargs):
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = utils.Formatter
        super().__init__(*args, **kwargs)
        # the kind of prefixing mechanism to use.
        self.conflict_resolution = conflict_resolution

        # two-level dictionary that maps from (dataclass, string_prefix) -> DataclassWrapper. 
        self._wrappers: Dict[DataclassType, Dict[str, List[DataclassWrapper]]] = defaultdict(lambda: defaultdict(list))

        self._fixed_wrappers: Dict[DataclassType, Dict[str, DataclassWrapper]]

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
        for prefix, wrappers in self._wrappers[dataclass].items():
            destinations = [wrapper.dest for wrapper in wrappers]
            if dest in destinations:
                self.error(textwrap.dedent(f"""\
                    Destination attribute {dest} is already used for dataclass of type {dataclass}.
                    Make sure all destinations are unique.
                    """))
        new_wrapper: DataclassWrapper[DataclassType] = DataclassWrapper(dataclass, dest)
        new_wrapper.prefix = prefix
        wrapper = self._register_dataclass(new_wrapper)
        logger.debug(f"added wrapper:\n{wrapper}\n")

    def parse_known_args(self, args=None, namespace=None):
        # NOTE: since the usual ArgumentParser.parse_args() calls parse_known_args, we therefore just need to overload the parse_known_args method.
        self._preprocessing()
        parsed_args, unparsed_args = super().parse_known_args(args, namespace)
        return self._postprocessing(parsed_args), unparsed_args

    def _register_dataclass(self, new_wrapper: DataclassWrapper[DataclassType]) -> DataclassWrapper[DataclassType]:
        """registers the given dataclass to be parsed later.
        
        Arguments:
            dataclass {Type[Dataclass]} -- The dataclass to register
            dest {str} -- a string which is to be used to  NamedTuple used to keep track of where to store the resulting instance and the number of instances.
        """
        logger.debug(f"Registering new DataclassWrapper: {new_wrapper}")
        self._wrappers[new_wrapper.dataclass][new_wrapper.prefix].append(new_wrapper)        
        for child in new_wrapper.descendants:
            self._wrappers[child.dataclass][child.prefix].append(child)
        return new_wrapper

    def _unregister_dataclass(self, wrapper: DataclassWrapper[DataclassType]):
        logger.debug(f"Unregistering DataclassWrapper {wrapper}")
        self._remove(wrapper)
        for child in wrapper.descendants:
            logger.debug(f"\tAlso Unregistering Child DataclassWrapper {child}")
            self._remove(child)
    
    def _remove(self, wrapper: DataclassWrapper):
        self._wrappers[wrapper.dataclass][wrapper.prefix].remove(wrapper)
        if len(self._wrappers[wrapper.dataclass][wrapper.prefix]) == 0:
            self._wrappers[wrapper.dataclass].pop(wrapper.prefix)
    
    def _preprocessing(self):
        logger.debug("\nPREPROCESSING\n")

        self._fixed_wrappers = self._fix_conflicts()
        # logger.debug(f"Fixed wrappers: {self._fixed_wrappers}")
        # Create one argument group per dataclass type
        for dataclass in self._fixed_wrappers:
            for prefix, wrapper in self._fixed_wrappers[dataclass].items():
                logger.debug(f"Adding arguments for dataclass: {dataclass} at destinations {wrapper.destinations}, multiple={wrapper.multiple}, prefix = '{wrapper.prefix}'")                
                wrapper.add_arguments(parser=self)


    def _postprocessing(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        """Instantiate the dataclasses from the parsed arguments and add them to their destination key in the namespace
        
        Arguments:
            parsed_args {argparse.Namespace} -- the result of calling super().parse_args()
        
        Returns:
            argparse.Namespace -- The namespace, with the added attributes for each dataclass.
            TODO: Try and maybe return a nicer, typed version of parsed_args (a Namespace subclass maybe?)  
        """
        logger.debug("\nPOST PROCESSING\n")
        logger.debug(f"parsed args: {parsed_args}")
        
        # create the constructor arguments for each instance by consuming all the attributes from `parsed_args` 
        parsed_args = self._consume_constructor_arguments(parsed_args)
        logger.debug(f"leftover arguments: {parsed_args}")
        
        logger.debug(f"Constructor arguments:")
        for key, args_dict in self.constructor_arguments.items():
            logger.debug(f"\t{key}: {args_dict}")

        self._set_instances_in_args(parsed_args)

        logger.debug(f"Final parsed args:")
        for key, value in vars(parsed_args).items():
            logger.debug(f"\t{key}: {value}")
           
        return parsed_args

    def _set_instances_in_args(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        
        # we now have all the constructor arguments for each instance.
        # we can now sort out the different dependencies, and create the instances.
        wrappers: Dict[str, DataclassWrapper] = self._wrapper_for_every_destination
        # we construct the 'tree' of dependencies from the bottom up,
        # starting with nodes that are children.
        destinations = self.constructor_arguments.keys()
        nesting_level = lambda destination_attribute: destination_attribute.count(".")

        for destination, wrapper in sorted(wrappers.items(), key=lambda k_v: k_v[1].nesting_level, reverse=True):
            logger.debug(f"wrapper name: {wrapper.attribute_name}, destination: {destination}")
            constructor = wrapper.instantiate
            constructor_args = self.constructor_arguments[destination]
            # create the dataclass instance.
            instance = constructor(constructor_args)
            
            if wrapper._parent is not None:
                parts = destination.split(".")
                parent = ".".join(parts[:-1])
                attribute_in_parent = parts[-1]
                # if this instance is an attribute in another dataclass,
                # we set the value in the parent's constructor arguments
                # at the associated attribute to this instance.
                self.constructor_arguments[parent][attribute_in_parent] = instance
                # self.constructor_arguments.pop(destination) # remove the 'args dict' for this child class.
                logger.debug(f"Setting a value at attribute {attribute_in_parent} in parent {parent}.")
            else:
                # if this destination is a top-level attribute, we set the attribute
                # on the returned parsed_args.
                logger.debug(f"setting attribute '{destination}' on the parsed_args to a value of {instance}")
                assert not hasattr(parsed_args, destination), "Namespace should not already have a '{destination}' attribute! (namespace: {parsed_args}) "
                setattr(parsed_args, destination, instance)
        return parsed_args

    def _consume_constructor_arguments(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        """Create the constructor arguments for each instance by consuming all the attributes from `parsed_args` 
        
        Args:
            parsed_args (argparse.Namespace): the argparse.Namespace returned from super().parse_args().
        
        Returns:
            argparse.Namespace: The namespace, without the consumed arguments.
        """
        wrappers: Dict[str, DataclassWrapper] = self._wrapper_for_every_destination
        parsed_arg_values = vars(parsed_args)
        # TODO: it would be cleaner if the CustomAction was working!
        # Here we imitate a custom action, by having the FieldWrappers be callables
        for wrapper in wrappers.values():
            for field in wrapper.fields:
                if not field.field.init:
                    continue
                values = parsed_arg_values.get(field.dest, field.defaults)
                # call the action manually.
                # this sets the right value in the `self.constructor_arguments` dictionary.
                field(parser=self, namespace=parsed_args, values=values, option_string=None)
                
        #Clean up the 'parsed_args' by deleting all the consumed attributes.
        deleted_values: Dict[str, Any] = {}
        for wrapper in wrappers.values():
            for field in wrapper.fields:
                deleted_values[field.dest] = parsed_arg_values.pop(field.dest, None)
        leftover_args = argparse.Namespace(**parsed_arg_values)
        logger.debug(f"deleted values: {deleted_values}")
        logger.debug(f"leftover args: {leftover_args}")
        return leftover_args

    def _get_conflicting_group(self, all_wrappers: Dict[DataclassType, Dict[str, List[DataclassWrapper[DataclassType]]]]) -> Optional[Conflict]:
        """Return the dataclass, prefix, and conflicing DataclassWrappers.
        """
        for dataclass in all_wrappers.keys():
            for prefix in all_wrappers[dataclass].keys():
                wrappers = all_wrappers[dataclass][prefix].copy()
                if len(wrappers) >= 2:
                    return dataclass, prefix, wrappers
        return None


    def _conflict_exists(self, all_wrappers: Dict[DataclassType, Dict[str, List[DataclassWrapper[DataclassType]]]]) -> bool:
        """Return True whenever a conflict exists (multiple DataclassWrappers share the same dataclass and prefix."""
        for dataclass in all_wrappers.keys():
            for prefix, wrappers in all_wrappers[dataclass].items():
                assert all(wrapper.prefix == prefix for wrapper in wrappers), "Misplaced DataclassWrapper!"
                if len(wrappers) >= 2:
                    return True
        return False

    def _fix_conflicts(self) ->  Dict[DataclassType, Dict[str, DataclassWrapper]]:
        while self._conflict_exists(self._wrappers):
            conflict = self._get_conflicting_group(self._wrappers)
            assert conflict is not None
            dataclass, prefix, wrappers = conflict
            logger.info(f"The following {len(wrappers)} wrappers are in conflict, as they share the same dataclass and prefix:\n" + "\n".join(str(w) for w in wrappers))
            logger.debug(f"(Conflict Resolution mode is {self.conflict_resolution})")
            if self.conflict_resolution == ConflictResolution.NONE:           
                self.error(
                    "The following wrappers are in conflict, as they share the same dataclass and prefix:\n" +
                    "\n".join(str(w) for w in wrappers) +
                    f"(Conflict Resolution mode is {self.conflict_resolution})"
                )
                    
            elif self.conflict_resolution == ConflictResolution.EXPLICIT:
                self._fix_conflict_explicit(conflict)

            elif self.conflict_resolution == ConflictResolution.ALWAYS_MERGE:
                self._fix_conflict_merge(conflict)

            elif self.conflict_resolution == ConflictResolution.AUTO:
                self._fix_conflict_auto(conflict)

        assert not self._conflict_exists(self._wrappers)
        fixed_wrappers: Dict[DataclassType, Dict[str, DataclassWrapper[DataclassType]]] = defaultdict(dict)
        for dataclass in self._wrappers:
            for prefix, wrappers in self._wrappers[dataclass].items():
                assert len(wrappers) == 1
                wrapper = wrappers[0]
                assert wrapper.prefix == prefix 
                fixed_wrappers[dataclass][prefix] = wrapper 
        return fixed_wrappers

    def _fix_conflict_explicit(self, conflict):
        # logger.debug("fixing explicit conflict: ", conflict)
        dataclass, prefix, wrappers = conflict
        assert prefix == "", "Wrappers for the same dataclass can't have the same user-set prefix when in EXPLICIT mode!"
        # remove all wrappers for that prefix
        for wrapper in wrappers:
            self._unregister_dataclass(wrapper)
            wrapper.explicit = True
            self._register_dataclass(wrapper)
        assert not self._wrappers[dataclass][prefix], self._wrappers[dataclass][prefix]
        # remove the prefix from the dict so we don't have to deal with empty lists.
        self._wrappers[dataclass].pop(prefix)

    def _fix_conflict_auto(self, conflict):
        # logger.debug("fixing conflict: ", conflict)
        dataclass, prefix, wrappers = conflict
        prefixes: List[List[str]] = [wrapper.dest.split(".") for wrapper in wrappers]
        # IDEA:
        # while the prefixes are the same, starting from the left, remove the first word.
        # Stop when they become different.


        sentences: Dict[int, List[str]] = {
            i: sentence for i, sentence in enumerate(prefixes)   
        }
        index_prefixes = {
            i: "" for i, sentence in enumerate(prefixes)
        }
        logger.debug(f"conflicting prefixes: {prefixes}")
        # TODO: do something here with the prefixes.
        def differentiate(prefixes: List[List[str]]):
            result: Dict[str, List[List[str]]] = defaultdict(list)
            for sentence in prefixes:
                first_word = sentence[0]
                result[first_word].append(sentence)

            return_dict = {}
            for first_word, sentences in result.items():
                if len(sentences) == 1:
                    return_dict[first_word] = ".".join(sentences[0])
                else:
                    sentences_without_first_word = [sentence[1:] for sentence in sentences]
                    return_dict[first_word] = differentiate(sentences_without_first_word)
            return return_dict

        prefix_dict = differentiate(prefixes)
        logger.debug(f"Prefix dict: {prefix_dict}")
        dest_to_wrapper: Dict[str, DataclassWrapper] = { wrapper.dest: wrapper for wrapper in wrappers }
        prefix_to_wrapper: Dict[str, DataclassWrapper] = {}
        for dest, wrapper in dest_to_wrapper.items():
            parts = dest.split(".")
            _prefix_dict = prefix_dict
            while len(parts) > 1:
                _prefix_dict = _prefix_dict[parts[0]]
                parts = parts[1:]
            prefix = _prefix_dict[parts[0]]
            prefix_to_wrapper[prefix] = wrapper
        
        for prefix, wrapper in prefix_to_wrapper.items():
            logger.debug(f"Wrapper for attribute {wrapper.dest} has prefix '{prefix}'.")
            self._unregister_dataclass(wrapper)
            wrapper.prefix = prefix + "."
            self._register_dataclass(wrapper)


    def _fix_conflict_merge(self, conflict):
        """Fix conflicts using the merging approach:
        The first wrapper is kept, and the rest of the wrappers are absorbed into the first wrapper.

        # TODO: check that the ordering of arguments is still preserved!
        
        Args:
            conflict ([type]): [description]
        """
        dataclass, prefix, wrappers = conflict
        assert len(wrappers) > 1
        first_wrapper: DataclassWrapper = None
        for wrapper in wrappers:
            self._unregister_dataclass(wrapper)
            if first_wrapper is None:
                first_wrapper = wrapper
            else:
                first_wrapper.merge(wrapper)
        
        assert first_wrapper.multiple
        self._register_dataclass(first_wrapper)

    
    @property
    def _wrapper_for_every_destination(self) -> Dict[str, DataclassWrapper[DataclassType]]:
        """Returns a dictionary where for every key (a destination), we return the associated DataclassWrapper.
        NOTE: multiple destinations can share the same DataclassWrapper instance.
        
        Returns:
            Dict[str, DataclassWrapper[Dataclass]] -- [description]
        """
        wrapper_for_destination: Dict[str, DataclassWrapper[DataclassType]] = {}
        for dataclass in self._fixed_wrappers.keys():
            for prefix, wrapper in self._fixed_wrappers[dataclass].items():
                logger.debug(f"prefix: '{prefix}', wrapper destinations: {wrapper.destinations}")
                for dest in wrapper.destinations:
                    assert dest not in wrapper_for_destination, f"There is already a wrapper for destination '{dest}': {wrapper_for_destination[dest]}"
                    wrapper_for_destination[dest] = wrapper
                    logger.debug(f"Setting a wrapper for destination {dest}")
        return wrapper_for_destination
        