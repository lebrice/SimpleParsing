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
        for prefix, wrappers in self._wrappers[dataclass]:
            destinations = [wrapper.dest for dest in wrappers]
            if dest in destinations:
                self.error(textwrap.dedent(f"""\
                    Destination attribute {dest} is already used for dataclass of type {dataclass}.
                    Make sure all destinations are unique.
                    """))
        new_wrapper: DataclassWrapper[DataclassType] = DataclassWrapper(dataclass, dest)
        new_wrapper.prefix = prefix
        wrapper = self._register_dataclass(new_wrapper)
        logger.debug("added wrapper:\n", wrapper, "\n")

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
        print(f"Registering new DataclassWrapper: {new_wrapper}")
        self._wrappers[new_wrapper.dataclass][new_wrapper.prefix].append(new_wrapper)        
        for child in new_wrapper.descendants:
            self._wrappers[child.dataclass][child.prefix].append(child)
        return new_wrapper

    def _unregister_dataclass(self, wrapper: DataclassWrapper[DataclassType]):
        print(f"Unregistering DataclassWrapper {wrapper}")
        self._remove(wrapper)
        for child in wrapper.descendants:
            print(f"\tAlso Unregistering Child DataclassWrapper {child}")
            self._remove(child)
    
    def _remove(self, wrapper: DataclassWrapper):
        self._wrappers[wrapper.dataclass][wrapper.prefix].remove(wrapper)
        if len(self._wrappers[wrapper.dataclass][wrapper.prefix]) == 0:
            self._wrappers[wrapper.dataclass].pop(wrapper.prefix)
    
    def _preprocessing(self):
        logger.debug("\nPREPROCESSING\n")

        self._fixed_wrappers = self._fix_conflicts()
        print("Fixed wrappers:", self._fixed_wrappers)
        # Create one argument group per dataclass type
        for dataclass in self._fixed_wrappers:
            for prefix, wrapper in self._fixed_wrappers[dataclass].items():
                print(f"Adding arguments for dataclass: {dataclass}, multiple={wrapper.multiple}, prefix = '{wrapper.prefix}'")                
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
        parsed_args = self._populate_constructor_arguments(parsed_args)
        print("constructor arguments:", self.constructor_arguments)
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
                logger.debug(f"setting attribute '{destination}' on the parsed_args to a value of {instance}")
                assert not hasattr(parsed_args, destination), "Namespace should not already have a '{destination}' attribute! (namespace: {parsed_args}) "
                setattr(parsed_args, destination, instance)
        
        logger.debug(f"Final parsed args: {parsed_args}")
        
        return parsed_args

    def _populate_constructor_arguments(self, parsed_args: argparse.Namespace) -> argparse.Namespace:
        """Create the constructor arguments for each instance by consuming all the attributes from `parsed_args` 
        
        Args:
            parsed_args (argparse.Namespace): the argparse.Namespace returned from super().parse_args().
        
        Returns:
            argparse.Namespace: The namespace, without the consumed arguments.
        """
        wrappers: Dict[str, DataclassWrapper] = self._wrapper_for_every_destination
        print("wrappers:", wrappers)
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
        logger.debug("deleted values:", deleted_values)
        parsed_args = argparse.Namespace(**parsed_arg_values)
        return parsed_args

    def _get_conflicting_group(self, all_wrappers: Dict[DataclassType, Dict[str, List[DataclassWrapper[DataclassType]]]]) -> Optional[Tuple[DataclassType, str, List[DataclassWrapper]]]:
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
            print(f"The following {len(wrappers)} wrappers are in conflict, as they share the same dataclass and prefix:", *wrappers, sep="\n")
            print(f"(Conflict Resolution mode is {self.conflict_resolution})")
            if self.conflict_resolution == ConflictResolution.NONE:           
                self.error(
                    "The following wrappers are in conflict, as they share the same dataclass and prefix:\n" +
                    "\n".join(str(w) for w in wrappers) +
                    f"(Conflict Resolution mode is {self.conflict_resolution})"
                )
                    
            elif self.conflict_resolution == ConflictResolution.EXPLICIT:
                self._fix_conflict_explicit(conflict)

            elif self.conflict_resolution == ConflictResolution.ALWAYS_MERGE:
                logging.warning(textwrap.dedent(f"""\
                    Each attribute of this dataclass will be marked as 'Multiple', and will be set in the order they were defined.
                    """))
                self._fix_conflict_merge(conflict)

            elif self.conflict_resolution == ConflictResolution.AUTO:
                raise NotImplementedError("Auto conflict resolution isn't implemented yet.")

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
        # print("fixing explicit conflict: ", conflict)

        dataclass, prefix, wrappers = conflict
        assert prefix == "", "Wrappers for the same dataclass can't have the same user-set prefix when in EXPLICIT mode!"
        # remove all wrappers for that prefix
        for wrapper in wrappers:
            self._unregister_dataclass(wrapper)
            wrapper.prefix = wrapper.attribute_name + "."
            self._register_dataclass(wrapper)
        assert not self._wrappers[dataclass][prefix], self._wrappers[dataclass][prefix]
        # remove the prefix from the dict so we don't have to deal with empty lists.
        self._wrappers[dataclass].pop(prefix)


    def _fix_conflict_merge(self, conflict):
        dataclass, prefix, wrappers = conflict
        assert len(wrappers) > 1
        first_wrapper: DataclassWrapper = None
        for wrapper in wrappers:
            self._unregister_dataclass(wrapper)
            if first_wrapper is None:
                first_wrapper = wrapper
            else:
                first_wrapper = first_wrapper.merge(wrapper)
        
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
                for dest in wrapper.destinations:
                    wrapper_for_destination[dest] = wrapper
        return wrapper_for_destination
        