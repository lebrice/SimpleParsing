"""Abstact Wrapper base-class for the FieldWrapper and DataclassWrapper."""

from abc import ABC
from dataclasses import dataclass
from typing import Generic, Optional, List, Type

from ..utils import T

class Wrapper(Generic[T]):
    def __init__(self, wrapped: Type[T], name: str):
        pass
        # self.wrapped = wrapped
        # self.name: str = name
        # self._dest: Optional[str] = None
        # self.parent: Optional[Wrapper] = None
        # wrapped: T
        # name: str
        # _dest: Optional[str]

    @property
    def dest(self) -> str:
        """Where the attribute will be stored in the Namespace."""
        lineage_names: List[str] = [w.name for w in self.lineage()]
        self._dest = ".".join(reversed([self.name] + lineage_names))
        assert self._dest is not None
        return self._dest

    def lineage(self) -> List["Wrapper"]:
        lineage: List[Wrapper] = []
        parent = self.parent
        while parent is not None:
            lineage.append(parent)
            parent = parent.parent
        return lineage   

    @property
    def nesting_level(self) -> int:
        return len(self.lineage())
        level = 0
        parent = self.parent
        while parent is not None:
            parent = parent.parent
            level += 1
        return level
    # @property
    # def dest(self) -> str:
    #     """Where the attribute will be stored in the Namespace."""
    #     if self._dest is not None:
    #         return self._dest
    #     from . import DataclassWrapper
    #     lineage_names: List[str] = [w.name for w in self.lineage()]
    #     self._dest = ".".join(reversed([self.name] + lineage_names))

    #     # TODO: If a custom `dest` was passed, and it is a `Field` instance,
    #     # find the corresponding FieldWrapper and use its `dest` instead of ours.
    #     if self.dest_field:
    #         self._dest = self.dest_field.dest
    #         self.custom_arg_options.pop("dest", None)

    #     assert self._dest is not None
    #     return self._dest

    # def lineage(self) -> List:
    #     from . import DataclassWrapper
    #     lineage: List[DataclassWrapper] = []
    #     parent = self.parent
    #     while parent is not None:
    #         lineage.append(parent)
    #         parent = parent.parent
    #     return lineage
