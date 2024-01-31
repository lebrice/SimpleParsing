from __future__ import annotations

import enum
from collections import defaultdict
from logging import getLogger
from typing import NamedTuple

from .wrappers import DataclassWrapper, FieldWrapper

logger = getLogger(__name__)


class ConflictResolution(enum.Enum):
    """Determines prefixing when adding the same dataclass more than once.

    - NONE:
        Disallow using the same dataclass in two different destinations without
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
    option_string: str
    wrappers: list[FieldWrapper]


def unflatten(possibly_related_wrappers: list[DataclassWrapper]) -> list[DataclassWrapper]:
    return [wrapper for wrapper in possibly_related_wrappers if wrapper.parent is None]


class ConflictResolver:
    def __init__(self, conflict_resolution=ConflictResolution.AUTO):
        self.conflict_resolution = conflict_resolution
        self.max_attempts = 50

    def resolve_and_flatten(self, wrappers: list[DataclassWrapper]) -> list[DataclassWrapper]:
        """Given the list of all dataclass wrappers, find and resolve any conflicts between fields.

        Returns the new list of (possibly mutated in-place) dataclass wrappers. This returned list
        is flattened, i.e. it contains all the dataclass wrappers and their children.
        """
        from simple_parsing.parsing import _assert_no_duplicates, _flatten_wrappers

        wrappers = wrappers.copy()

        _assert_no_duplicates(wrappers)
        wrappers_flat = _flatten_wrappers(wrappers)

        dests = [w.dest for w in wrappers_flat]
        assert len(dests) == len(set(dests)), f"shouldn't be any duplicates: {wrappers_flat}"

        conflict = self.get_conflict(wrappers_flat)

        # current and maximum number of attempts. When reached, raises an error.
        cur_attempts = 0
        while conflict:
            message: str = (
                "The following wrappers are in conflict, as they share the "
                + f"'{conflict.option_string}' option string:"
                + ("\n".join(str(w) for w in conflict.wrappers))
                + f"(Conflict Resolution mode is {self.conflict_resolution})"
            )
            logger.debug(message)

            if self.conflict_resolution == ConflictResolution.NONE:
                raise ConflictResolutionError(message)

            elif self.conflict_resolution == ConflictResolution.EXPLICIT:
                self._fix_conflict_explicit(conflict)

            elif self.conflict_resolution == ConflictResolution.ALWAYS_MERGE:
                wrappers_flat = self._fix_conflict_merge(conflict, wrappers_flat)

            elif self.conflict_resolution == ConflictResolution.AUTO:
                self._fix_conflict_auto(conflict)

            conflict = self.get_conflict(wrappers_flat)
            cur_attempts += 1
            if cur_attempts == self.max_attempts:
                raise ConflictResolutionError(
                    f"Reached maximum number of attempts ({self.max_attempts}) "
                    "while trying to solve the conflicting argument names. "
                    "This is either a bug, or there is something weird going "
                    "on with your class hierarchy/argument names... \n"
                    "In any case, Please help us by submitting an issue on "
                    "the Github repo at "
                    "https://github.com/lebrice/SimpleParsing/issues, "
                    "or by using the following link: "
                    "https://github.com/lebrice/SimpleParsing/issues/new?"
                    "assignees=lebrice&"
                    "labels=bug"
                    "&template=bug_report.md"
                    "&title=BUG: ConflictResolutionError"
                )

        assert not self._conflict_exists(wrappers_flat)
        return wrappers_flat

    def resolve(self, wrappers: list[DataclassWrapper]) -> list[DataclassWrapper]:
        return unflatten(self.resolve_and_flatten(wrappers))

    def get_conflict(
        self, wrappers: list[DataclassWrapper] | list[FieldWrapper]
    ) -> Conflict | None:
        field_wrappers: list[FieldWrapper] = []
        for w in wrappers:
            if isinstance(w, DataclassWrapper):
                field_wrappers.extend(w.fields)
                # logger.debug(f"Wrapper {w.dest} has fields {w.fields}")
            else:
                field_wrappers.append(w)

        assert len(field_wrappers) == len(set(field_wrappers)), "duplicates?"

        # TODO: #49: Also consider the conflicts with regular argparse arguments.
        conflicts: dict[str, list[FieldWrapper]] = defaultdict(list)
        for field_wrapper in field_wrappers:
            for option_string in field_wrapper.option_strings:
                conflicts[option_string].append(field_wrapper)
                # logger.debug(f"conflicts[{option_string}].append({repr(field_wrapper)})")

        for option_string, field_wrappers in conflicts.items():
            if len(field_wrappers) > 1:
                return Conflict(option_string, field_wrappers)
        return None

    def _add(
        self,
        wrapper: DataclassWrapper | FieldWrapper,
        wrappers: list[DataclassWrapper],
    ) -> list[DataclassWrapper]:
        """Add the given wrapper and all its descendants to the list of wrappers."""
        if isinstance(wrapper, FieldWrapper):
            wrapper = wrapper.parent
        assert isinstance(wrapper, DataclassWrapper)
        logger.debug(f"Adding new DataclassWrapper: {wrapper}")
        wrappers.append(wrapper)
        wrappers.extend(wrapper.descendants)

        return wrappers

    def _remove(
        self,
        wrapper: DataclassWrapper | FieldWrapper,
        wrappers: list[DataclassWrapper],
    ):
        """Remove the given wrapper and all its descendants from the list of wrappers."""
        if isinstance(wrapper, FieldWrapper):
            wrapper = wrapper.parent
        assert isinstance(wrapper, DataclassWrapper)
        logger.debug(f"Removing DataclassWrapper {wrapper}")
        wrappers.remove(wrapper)
        for child in wrapper.descendants:
            logger.debug(f"\tAlso removing Child DataclassWrapper {child}")
            wrappers.remove(child)
        # TODO: Should we also remove the reference to this wrapper from its parent?
        for other_wrapper in wrappers:
            if wrapper in other_wrapper._children:
                other_wrapper._children.remove(wrapper)
        return wrappers

    def _fix_conflict_explicit(self, conflict: Conflict):
        """Fixes conflicts between arguments following the "Explicit" approach.

        The Explicit approach gives a prefix to each argument which points to
        exactly where the argument is stored in the resulting Namespace. There
        can therefore not be any confusion between arguments, at the cost of
        having lengthy option strings.

        Parameters
        ----------
        - conflict : Conflict

            The conflict to hangle/fix.

        Raises
        ------
        ConflictResolutionError
            If its impossibe to fix the conflict.
        """
        logger.debug(f"fixing explicit conflict: {conflict}")

        if any(w.prefix for w in conflict.wrappers):
            raise ConflictResolutionError(
                "When in 'Explicit' mode, there shouldn't be a need for any user-set prefixes."
                "Just let the ArgumentParser set the explicit prefixes for all fields, and there won't be a conflict."
            )
        # TODO: Only set an explicit prefix on the fields that are in conflict

        # Check that there is no conflict between the fields after setting the explicit prefix.
        # If there is, that means that this conflict can't be fixed automatically, and a manual prefix should be set by the user.
        for field_wrapper in conflict.wrappers:
            explicit_prefix = field_wrapper.parent.dest + "."
            field_wrapper.prefix = explicit_prefix

        another_conflict = self.get_conflict(conflict.wrappers)
        if another_conflict and another_conflict.option_string == conflict.option_string:
            raise ConflictResolutionError(
                f"There is a conflict over the '{conflict.option_string}' "
                "option string, even after adding an explicit prefix to all "
                "the conflicting fields! \n"
                "To solve this, You can either use a different argument name, "
                "a different destination, or pass a differentiating prefix to "
                "`parser.add_arguments(<dataclass>, dest=destination, "
                "prefix=prefix)`"
            )

    def _fix_conflict_auto(self, conflict: Conflict):
        """Fixes a conflict using the AUTO method.

        Tries to find a discriminating prefix of minimal length for all the conflicting fields, using roughly the following pseudocode:

        1.  Sort the field wrappers by ascending nesting level.
            ("parent/root" wrappers first, children "leaf" wrappers last)
        2.  If the first wrapper is less nested than the others, remove it from the list (don't change its prefix)
        3.  For all the remaining wrappers, add one more "word" from their lineage (dest attribute) to their prefix,
            starting from the end and moving towards the parent.
        4.  If there is no conflict left, exit, else, return to step 1 with the new conflict.
            (This is performed implicitly by the method that calls this function, since it loops while there is a conflict).

        Parameters
        ----------
        - conflict : Conflict

            The Conflict NamedTuple containing the conflicting option_string, as well as the conflicting `FieldWrapper`s.

        Raises
        ------
        ConflictResolutionError
            If its impossibe to fix the conflict.
        """
        field_wrappers = sorted(conflict.wrappers, key=lambda w: w.nesting_level)
        logger.debug(f"Conflict with options string '{conflict.option_string}':")
        for i, field in enumerate(field_wrappers):
            logger.debug(f"Field wrapper #{i+1}: {field} nesting level: {field.nesting_level}.")

        assert (
            len(set(field_wrappers)) >= 2
        ), "Need at least 2 (distinct) FieldWrappers to have a conflict..."

        first_wrapper = field_wrappers[0]
        second_wrapper = field_wrappers[1]
        if first_wrapper.nesting_level < second_wrapper.nesting_level:
            # IF the first field_wrapper is a 'parent' of the following field_wrappers, then it maybe doesn't need an additional prefix.
            logger.debug(
                f"The first FieldWrapper is less nested than the others, removing it. ({first_wrapper})"
            )
            field_wrappers.remove(first_wrapper)

        # add one more word to each of the remaining field_wrappers.
        for field_wrapper in field_wrappers:
            # Get the current and explicit (maximum) prefix:
            current_prefix = field_wrapper.prefix
            explicit_prefix = field_wrapper.parent.dest + "."

            logger.debug(f"current prefix: {current_prefix}, explicit prefix: {explicit_prefix}")
            if current_prefix == explicit_prefix:
                # We can't add any more words to the prefix of this FieldWrapper,
                # as it has already a prefix equivalent to its full destination...
                raise ConflictResolutionError(
                    " ".join(
                        [
                            f"Cannot fix the conflict for the Options string {conflict.option_string},",
                            f"as the field {field_wrapper} already has the most explicit",
                            "prefix possible, and thus we can't add an additional",
                            "discriminating word to its prefix.",
                            "\n Consider modifying either the destination or the prefix",
                            "passed to `parser.add_arguments(<dataclass>, dest=destination, prefix=prefix)",
                        ]
                    )
                )

            # find the next 'word' to add to the prefix.
            available_words = list(filter(bool, explicit_prefix.split(".")))
            used_words = list(filter(bool, current_prefix.split(".")))
            assert len(available_words) > len(
                used_words
            ), "There should at least one word we haven't used yet!"
            logger.debug(f"Available words: {available_words}, used_words: {used_words}")

            n_available_words = len(available_words)
            n_used_words = len(used_words)
            word_to_add = available_words[(n_available_words - 1) - n_used_words]
            logger.debug(f"Word to be added: {word_to_add}")
            field_wrapper.prefix = word_to_add + "." + current_prefix
            logger.debug(f"New prefix: {field_wrapper.prefix}")

    def _fix_conflict_merge(self, conflict: Conflict, wrappers_flat: list[DataclassWrapper]):
        """Fix conflicts using the merging approach.

        The first wrapper is kept, and the rest of the wrappers are absorbed
        into the first wrapper.

        # TODO: check that the ordering of arguments is still preserved!

        Parameters
        ----------
        conflict : Conflict
            The conflict NamedTuple.
        """
        fields = sorted(conflict.wrappers, key=lambda w: w.nesting_level)
        logger.debug(f"Conflict with options string '{conflict.option_string}':")
        for field in fields:
            logger.debug(f"Field wrapper: {field} nesting level: {field.nesting_level}.")

        assert len(conflict.wrappers) > 1

        # Merge all the fields into the first one.
        first_wrapper: FieldWrapper = fields[0]
        wrappers = wrappers_flat.copy()

        first_containing_dataclass: DataclassWrapper = first_wrapper.parent
        original_parent = first_containing_dataclass.parent
        wrappers = self._remove(first_containing_dataclass, wrappers)

        for wrapper in conflict.wrappers[1:]:
            containing_dataclass = wrapper.parent
            wrappers = self._remove(containing_dataclass, wrappers)
            first_containing_dataclass.merge(containing_dataclass)

        assert first_containing_dataclass.multiple
        wrappers = self._add(first_containing_dataclass, wrappers)
        if original_parent:
            original_parent._children.append(first_containing_dataclass)
        return wrappers

    def _get_conflicting_group(self, all_wrappers: list[DataclassWrapper]) -> Conflict | None:
        """Return the conflicting DataclassWrappers which share argument names.

        TODO: maybe return the list of fields, rather than the dataclasses?
        """
        conflicts: dict[str, list[FieldWrapper]] = defaultdict(list)
        for wrapper in all_wrappers:
            for field in wrapper.fields:
                for option in field.option_strings:
                    conflicts[option].append(field)

        for option_string, fields in conflicts.items():
            if len(fields) > 1:
                # the dataclasses of the fields that share the same name.
                # wrappers: List[DataclassWrapper] = [f.parent for f in fields]
                # dataclasses = [wrapper.dataclass for wrapper in wrappers]
                # prefixes = [wrapper.prefix for wrapper in wrappers]
                # return Conflict(dataclasses[0], prefixes[0], wrappers)
                return Conflict(option_string, fields)
        return None

    def _conflict_exists(self, all_wrappers: list[DataclassWrapper]) -> bool:
        """Return True whenever a conflict exists.

        (option strings overlap).
        """
        arg_names: set[str] = set()
        for wrapper in all_wrappers:
            for field in wrapper.fields:
                for option in field.option_strings:
                    if option in arg_names:
                        return True
                    arg_names.add(option)
        return False
