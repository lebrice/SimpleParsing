from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, Iterable, TypeVar

from refactored_parsing.types import DataclassT

T = TypeVar("T")


@dataclass(frozen=True, unsafe_hash=True)
class Node(Generic[T]):
    value: T
    parent: Node[T] | None = None
    children: tuple[Node[T], ...] = ()

    def lineage(self) -> Iterable[Node[T]]:
        node = self
        while node is not None:
            yield node
            node = node.parent

    # def descendants(self) -> Iterable[Node[T]]:


@dataclass
class A:
    foo: int = 123


@dataclass
class Config:
    a: A


@dataclass(frozen=True, unsafe_hash=True)
class Tree(Generic[T]):
    edges: list[tuple[str, str]]


def get_dc_tree(dataclass: DataclassT) -> Node[DataclassT]:
    ...


# parent = Node(value=Config, parent=None, children=[])
# a_node = Node(value=A)
# config_node = Node(value=Config, children=(a_node,))
# a_node.parent = config_node

# assert get_dc_tree(Config) == {
#     "": Config,
#     "a": A,
# }
