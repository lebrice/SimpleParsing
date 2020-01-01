import argparse
import enum
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import *

from . import utils
from .utils import Dataclass, DataclassType, MutableField
from .wrappers import DataclassWrapper, FieldWrapper

logger = logging.getLogger(__name__)

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


class ConflictResolutionError(argparse.ArgumentError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Conflict(NamedTuple):
    dataclass: Type
    prefix: str
    wrappers: List



class ConflictResolver:
    def __init__(self, conflict_resolution: ConflictResolution = ConflictResolution.AUTO):
        self._wrappers: List[DataclassWrapper] = []
        self.conflict_resolution = conflict_resolution

    def resolve_conflicts(self, wrappers: List[DataclassWrapper]) -> List[DataclassWrapper]:
        for wrapper in wrappers:
            self._register(wrapper)
        
        while self._conflict_exists(self._wrappers):
            conflict = self._get_conflicting_group(self._wrappers)
            assert conflict is not None
            dataclass, prefix, wrappers = conflict
            logger.info(f"The following {len(wrappers)} wrappers are in conflict, as they share the same dataclass and prefix:\n" + "\n".join(str(w) for w in wrappers))
            logger.debug(f"(Conflict Resolution mode is {self.conflict_resolution})")
            if self.conflict_resolution == ConflictResolution.NONE:           
                raise ConflictResolutionError(
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
        return self._wrappers

    def _register(self, new_wrapper: DataclassWrapper[DataclassType]):
        logger.debug(f"Registering new DataclassWrapper: {new_wrapper}")
        self._wrappers.append(new_wrapper) 
        self._wrappers.extend(new_wrapper.descendants)       
        return new_wrapper

    def _unregister(self, wrapper: DataclassWrapper[DataclassType]):
        logger.debug(f"Unregistering DataclassWrapper {wrapper}")
        self._wrappers.remove(wrapper)
        for child in wrapper.descendants:
            logger.debug(f"\tAlso Unregistering Child DataclassWrapper {child}")
            self._wrappers.remove(child)


    def _fix_conflict_explicit(self, conflict):
        logger.debug(f"fixing explicit conflict: {conflict}")
        dataclass, prefix, wrappers = conflict
        assert prefix == "", "Wrappers for the same dataclass can't have the same user-set prefix when in EXPLICIT mode!"
        # remove all wrappers for that prefix
        for wrapper in wrappers:
            self._unregister(wrapper)
            wrapper.explicit = True
            self._register(wrapper)


    def _fix_conflict_auto(self, conflict):
        # logger.debug("fixing conflict: ", conflict)
        dataclass, prefix, wrappers = conflict
        prefixes: List[List[str]] = [wrapper.dest.split(".") for wrapper in wrappers]
        logger.debug(f"conflicting prefixes: {prefixes}")

        prefix_dict = utils.trie(prefixes)
        
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
            self._unregister(wrapper)
            wrapper.prefix = prefix + "."
            self._register(wrapper)


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
            self._unregister(wrapper)
            if first_wrapper is None:
                first_wrapper = wrapper
            else:
                first_wrapper.merge(wrapper)
        
        assert first_wrapper.multiple
        self._register(first_wrapper)

    


    def _get_conflicting_group(self, all_wrappers: List[DataclassWrapper]) -> Optional[Conflict]:
        """Return the dataclass, prefix, and the list of DataclassWrappers which share argument names

        TODO: maybe return the list of conflicting fields, rather than the entire dataclass?
        """
        conflicts: Dict[str, List[FieldWrapper]] = defaultdict(list)
        for wrapper in all_wrappers:
            for field in wrapper.fields:
                # TODO: figure out a better "identifier" to use?
                conflicts[field.option_strings[0]].append(field)
        
        for argument_name, fields in conflicts.items():
            if len(fields) > 1:
                # the dataclasses of the fields that share the same name.
                wrappers: List[DataclassWrapper] = [field.parent for field in fields]
                dataclasses = [wrapper.dataclass for wrapper in wrappers]
                prefixes = [wrapper.prefix for wrapper in wrappers]
                return dataclasses[0], prefixes[0], wrappers
        return None


    def _conflict_exists(self, all_wrappers: List[DataclassWrapper]) -> bool:
        """Return True whenever a conflict exists (arguments share the same name."""
        arg_names: Set[str] = set()
        for wrapper in all_wrappers:
            for field in wrapper.fields:
                if field.option_strings[0] in arg_names:
                    return True
                arg_names.add(field.option_strings[0])
        return False
