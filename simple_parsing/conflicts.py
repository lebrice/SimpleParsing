import argparse
import enum
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import *

from . import utils
from .utils import Dataclass
from .wrappers import DataclassWrapper, FieldWrapper

logger = logging.getLogger(__name__)

class ConflictResolution(enum.Enum):
    """Determines prefixing when adding the same dataclass more than once.

    
    - NONE:
        Dissallow using the same dataclass in two different destinations without
        explicitly setting a distinct prefix for at least one of them.

    - EXPLICIT:
        When adding arguments for a dataclass that is already present, the
        argparse arguments for each class will use their full absolute path as a
        prefix.

    - ALWAYS_MERGE:
        When adding arguments for a dataclass that has previously been added,
        the arguments for both the old and new destinations will be set using
        the same option_string, and the passed values for the old and new
        destinations will correspond to the first and second values,
        respectively.
        NOTE: This changes the argparse type for that argument into a list of
        the original item type.
    
    - AUTO (default):
        Prefixes for each destination are created automatically, using the first
        discriminative prefix that can differentiate between all the conflicting
        arguments.
    """
    NONE = -1
    EXPLICIT = 0
    ALWAYS_MERGE = 1
    AUTO = 2


class ConflictResolutionError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Conflict(NamedTuple):
    dataclass: Type
    prefix: str
    wrappers: List[DataclassWrapper]


class ConflictResolver:
    def __init__(self, conflict_resolution = ConflictResolution.AUTO):
        self._wrappers: List[DataclassWrapper] = []
        self.conflict_resolution = conflict_resolution

    def resolve_conflicts(self, wrappers: List[DataclassWrapper]) -> List[DataclassWrapper]:
        for wrapper in wrappers:
            self._register(wrapper)
        
        while self._conflict_exists(self._wrappers):
            conflict = self._get_conflicting_group(self._wrappers)
            assert conflict is not None
            logger.debug(
                "The following wrappers are in conflict, as they share the " +
                "same dataclass and prefix:\n" +
                "\n".join(str(w) for w in wrappers) +
                f"(Conflict Resolution mode is {self.conflict_resolution})"
            )

            if self.conflict_resolution == ConflictResolution.NONE:           
                raise ConflictResolutionError(
                    "The following wrappers are in conflict, as they share the "
                    "same dataclass and prefix:\n" +
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
        return self._wrappers

    def _register(self, new_wrapper: DataclassWrapper):
        logger.debug(f"Registering new DataclassWrapper: {new_wrapper}")
        self._wrappers.append(new_wrapper) 
        self._wrappers.extend(new_wrapper.descendants)       
        return new_wrapper

    def _unregister(self, wrapper: DataclassWrapper):
        logger.debug(f"Unregistering DataclassWrapper {wrapper}")
        self._wrappers.remove(wrapper)
        for child in wrapper.descendants:
            logger.debug(f"\tAlso Unregistering Child DataclassWrapper {child}")
            self._wrappers.remove(child)

    def _fix_conflict_explicit(self, conflict: Conflict):
        logger.debug(f"fixing explicit conflict: {conflict}")
        if conflict.prefix != "":
            raise ConflictResolutionError(
                "Wrappers for the same dataclass can't have the same "
                "user-set prefix when in EXPLICIT mode!"
            )
        # remove all wrappers for that prefix
        for wrapper in conflict.wrappers:
            self._unregister(wrapper)
            wrapper.explicit = True
            self._register(wrapper)

    def _fix_conflict_auto(self, conflict: Conflict):
        prefixes: List[List[str]] = [
            wrapper.dest.split(".") for wrapper in conflict.wrappers
        ]
        logger.debug(f"conflicting prefixes: {prefixes}")

        prefix_dict = utils.trie(prefixes)
        
        logger.debug(f"Prefix dict: {prefix_dict}")
        dest_to_wrapper = {
            wrapper.dest: wrapper for wrapper in conflict.wrappers
        }
        prefix_to_wrapper: Dict[str, DataclassWrapper] = {}
        for dest, wrapper in dest_to_wrapper.items():
            parts = dest.split(".")
            _prefix_dict = prefix_dict
            while len(parts) > 1:
                _prefix_dict = _prefix_dict[parts[0]]  # type: ignore
                parts = parts[1:]
            prefix = _prefix_dict[parts[0]]
            prefix_to_wrapper[prefix] = wrapper  # type: ignore
        
        for prefix, wrapper in prefix_to_wrapper.items():
            logger.debug(
                f"Wrapper for attribute {wrapper.dest} has prefix '{prefix}'."
            )
            self._unregister(wrapper)
            wrapper.prefix = prefix + "."
            self._register(wrapper)

    def _fix_conflict_merge(self, conflict: Conflict):
        """Fix conflicts using the merging approach.

        The first wrapper is kept, and the rest of the wrappers are absorbed
        into the first wrapper.
        
        # TODO: check that the ordering of arguments is still preserved!
        
        Parameters
        ----------
        conflict : Conflict
            The conflict NamedTuple. 
        """
        assert len(conflict.wrappers) > 1
        first_wrapper: DataclassWrapper = conflict.wrappers[0]
        self._unregister(first_wrapper)

        for wrapper in conflict.wrappers[1:]:
            self._unregister(wrapper)
            first_wrapper.merge(wrapper)
        
        assert first_wrapper.multiple
        self._register(first_wrapper)

    def _get_conflicting_group(self, all_wrappers: List[DataclassWrapper]) -> Optional[Conflict]:
        """Return the conflicting DataclassWrappers which share argument names.

        TODO: maybe return the list of fields, rather than the dataclasses?
        """
        conflicts: Dict[str, List[FieldWrapper]] = defaultdict(list)
        for wrapper in all_wrappers:
            for field in wrapper.fields:
                for option in field.option_strings:    
                    conflicts[option].append(field)
        
        for argument_name, fields in conflicts.items():
            if len(fields) > 1:
                # the dataclasses of the fields that share the same name.
                wrappers: List[DataclassWrapper] = [f.parent for f in fields]
                dataclasses = [wrapper.dataclass for wrapper in wrappers]
                prefixes = [wrapper.prefix for wrapper in wrappers]
                return Conflict(dataclasses[0], prefixes[0], wrappers)
        return None

    def _conflict_exists(self, all_wrappers: List[DataclassWrapper]) -> bool:
        """Return True whenever a conflict exists. (same argument names). """
        arg_names: Set[str] = set()
        for wrapper in all_wrappers:
            for field in wrapper.fields:
                for option in field.option_strings:
                    if option in arg_names:
                        return True
                    arg_names.add(option)
        return False
