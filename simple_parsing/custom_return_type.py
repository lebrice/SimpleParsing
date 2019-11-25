from typing import *
from mypy_extensions import TypedDict

from dataclasses import dataclass

@dataclass
class First:
    x: int = 0

@dataclass
class Second:
    y: int = 0

@dataclass
class Third:
    z: int = 0

Dataclass = TypeVar("Dataclass")
# Dataclass = TypedDict("Dataclass", {"a": First, "b": Second, "c": Third})

destination_to_type = {"a": First, "b": Second, "c": Third}
attributes_str = ','.join([f"'{dest}': {T.__name__}" for dest, T in destination_to_type.items()])
type_str = "TypedDict('ReturnType', {" + attributes_str + "})"
ReturnType = eval(type_str)
cast(Type, ReturnType)
print(get_type_hints(ReturnType, globals(), locals()))
import typing

def foo(destination_to_type: Dict[str, Type]) -> ReturnType:
    import typing
    from argparse import Namespace
    result = Namespace()
    cast(ReturnType, result)
    for destination, object_type in destination_to_type.items():
        setattr(result, destination, object_type())
        # cast(object_type, getattr(result, destination))
    return result


result = foo(destination_to_type)
print(result.a)
print(result.b)
print(result.c)