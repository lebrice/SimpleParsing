"""Utility functions"""
import argparse
import dataclasses
import functools
import re
from collections import defaultdict
from dataclasses import dataclass, field, MISSING, Field
from typing import *
from enum import Enum
import logging

logger = logging.getLogger(__name__)


T = TypeVar("T")
Dataclass = TypeVar("Dataclass")
DataclassType = Type[Dataclass]
# DataclassType = Type[Dataclass]

def MutableField(default: T, init=True, repr=True, hash=None, compare=True, metadata=None) -> T:
    return field(default_factory=lambda: default, init=init, repr=repr, hash=hash, compare=compare, metadata=metadata) 

# Flag = NewType("Flag", bool)
Flag = bool
class InconsistentArgumentError(RuntimeError):
    """
    Error raised when the number of arguments provided is inconsistent when parsing multiple instances from command line.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.MetavarTypeHelpFormatter):
    """Little shorthand for using both of argparse's ArgumentDefaultHelpFormatter and MetavarTypeHelpFormatter classes.
    """
    pass


@dataclass
class DependenciesGraph:
    children: Dict[str, List[str]]
    parent: Dict[str, str]

def dependency_graph(destinations: List[str]) -> DependenciesGraph:
    destination_to_parent: Dict[str, str] = {}
    destination_to_children: Dict[str, List[str]] = defaultdict(list)

    destinations = sorted(destinations, key=lambda attribute: attribute.count("."))
    for destination in destinations:
        parts = destination.split(".")
        destination_to_parent[destination] = ".".join(parts[:-1])
        
        destination_to_children[".".join(parts[:-1])].append(destination)
        
    return DependenciesGraph(destination_to_children, destination_to_parent)



def _sort_dependencies(args_to_add: Dict[Dataclass, List[str]]):
    """
    Idea: sort the order in which we instantiate the dataclasses such that we take care of the dependencies

    Things to keep in mind:
    1- We currently have to parse all instances for any given dataclass at the same time
    2- We need to pass the (already parsed) child dataclass instances to their parents's somehow, so that they can be used in the constructor if are required.
    
    """

    dataclass_to_destinations = args_to_add.copy()
    destinations_to_dataclass = {}

    for dataclass, destinations in dataclass_to_destinations.items():
        for destination in destinations:
            destinations_to_dataclass[destination] = dataclass
    destinations = sorted(destinations_to_dataclass.keys(), key=lambda attribute: attribute.count("."))

    while destinations:
        highest_priority = destinations[0]
        associated_dataclass = destinations_to_dataclass[destination]
        all_destinations_for_class = dataclass_to_destinations[dataclass]
        
        yield dataclass, all_destinations_for_class

        for parsed_destination in all_destinations_for_class:
            destinations.remove(parsed_destination)



def list_field(default = None, init: bool =True, repr=True, hash: bool = None, compare: bool =True, metadata: Dict[str, Any] = None) -> dataclasses.Field:
    """Shorthand for writing a `dataclasses.field()` that will hold a list of values.
    """
    return dataclasses.field(default_factory=lambda: default, init=init, repr=repr, hash=hash, compare=compare, metadata=metadata)

def camel_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

TRUE_STRINGS: List[str] = ['yes', 'true', 't', 'y', '1']
FALSE_STRINGS: List[str] = ['no', 'false', 'f', 'n', '0']

def str2bool(v: str) -> bool:
    """
    Taken from https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    """
    if isinstance(v, bool):
        return v
    v = v.strip()
    if v.lower() in TRUE_STRINGS:
        return True
    elif v.lower() in FALSE_STRINGS:
        return False
    else:
        raise argparse.ArgumentTypeError(f"Boolean value expected for argument, received '{v}'")


def get_item_type(container_type: Type[Container[T]]) -> T:
    """Returns the `type` of the items in the provided container `type`. When no type annotation is found, or no item type is found, returns `typing.Any`.
    >>> import typing
    >>> get_item_type(typing.List)

    >>> get_item_type(typing.List[int])
    <class 'int'>
    >>> get_item_type(typing.List[str])
    <class 'str'>
    >>> get_item_type(typing.List[float])
    <class 'float'>
    >>> get_item_type(List[float])
    <class 'float'>
    >>> get_item_type(List[Tuple])
    typing.Tuple
    >>> get_item_type(List[Tuple[int, int]])
    typing.Tuple[int, int]
    >>> get_item_type(Tuple[int, str])
    <class 'int'>
    >>> get_item_type(Tuple[str, int])
    <class 'str'>
    >>> get_item_type(Tuple[str, str, str, str])
    <class 'str'>

    Arguments:
        list_type {Type} -- A type, preferably one from the Typing module (List, Tuple, etc).
    
    Returns:
        Type -- the type of the container's items, if found, else Any.
    """
    if container_type in {list, tuple}:
        # the built-in `list` and `tuple` types don't have annotations for their item types.
        return Type[Any]
    return getattr(container_type, "__args__", (Type[Any],))[0]
    

def get_argparse_type_for_container(container_type: Type) -> Type:
    """Gets the argparse 'type' option to be used for a given container type.
    When an annotation is present, the 'type' option of argparse is set to that type.
    if not, then the default value of 'str' is returned.
    
    Arguments:
        container_type {Type} -- A container type (ideally a typing.Type such as List, Tuple, along with an item annotation: List[str], Tuple[int, int], etc.)
    
    Returns:
        typing.Type -- the type that should be used in argparse 'type' argument option.
    """
    T = get_item_type(container_type)
    return T if T is not None else str

def _mro(t: Type) -> List[Type]:
    return getattr(t, "mro", lambda: [])()

def is_subtype_of(some_type: Type):
    def func(field: Field) -> bool:
        return some_type in _mro(field.type)
    return  func


def is_list(t: Type) -> bool:
    return list in _mro(t)

def is_tuple(t: Type) -> bool:
    return tuple in _mro(t)

def is_enum(t: Type) -> bool:
    return Enum in _mro(t)

def is_bool(t: Type) -> bool:
    return bool in _mro(t)

def is_tuple_or_list(t: Type) -> bool:
    return is_list(t) or is_tuple(t)

def is_tuple_or_list_of_dataclasses(t: Type) -> bool:
    return is_tuple_or_list(t) and dataclasses.is_dataclass(get_item_type(t))

def _parse_multiple_containers(tuple_or_list: type, append_action: bool = False) -> Callable[[str], List[Any]]:
    T = get_argparse_type_for_container(tuple_or_list)
    factory = tuple if is_tuple(tuple_or_list) else list
    
    result = factory()

    def parse_fn(v: str) -> List[Any]:
        # nonlocal result
        # print(f"Parsing a {tuple_or_list} of {T}s, value is: {v}, type is {type(v)}")
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = v[1:-1]
        
        separator = " "
        for sep in [","]: # TODO: maybe add support for other separators?
            if sep in v:
                separator = sep
        str_values = [v.strip() for v in v.split(separator)]
        T_values = [T(v_str) for v_str in str_values]
        values = factory(v for v in T_values)
        # print("values:", values)
        if append_action:
            result += values
            return result
        else:
            return values
    return parse_fn


def _parse_container(tuple_or_list: type,) -> Callable[[str], List[Any]]:
    T = get_argparse_type_for_container(tuple_or_list)
    factory = tuple if is_tuple(tuple_or_list) else list

    def parse_fn(v: str) -> List[Any]:
        # TODO: maybe we could use the fact we know this isn't for a list of lists to make this better somehow.
        logger.debug(f"Parsing a {tuple_or_list} of {T}s, value is: '{v}', type is {type(v)}")
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = v[1:-1]
        
        separator = " "
        for sep in [","]: # TODO: maybe add support for other separators?
            if sep in v:
                separator = sep
        str_values = [v.strip() for v in v.split(separator)]
        T_values = [T(v_str) for v_str in str_values]
        values = factory(v for v in T_values)
        logger.debug(f"returning values: {values}")
        return values

    return parse_fn

def setattr_recursive(obj: object, attribute_name: str, value: Any):
    if "." not in attribute_name:
        setattr(obj, attribute_name, value)
    else:
        parts = attribute_name.split(".")
        child_object = getattr(obj, parts[0])
        setattr_recursive(child_object, ".".join(parts[1:]), value)


def parent_and_child(destination: str) -> Tuple[str, str]:
    splits = destination.split(".")
    parent = ".".join(splits[:-1])
    attribute_in_parent = splits[-1]
    return parent, attribute_in_parent


def get_nesting_level(possibly_nested_list):
    if not isinstance(possibly_nested_list, (list, tuple)):
        return 0
    elif len(possibly_nested_list) == 0:
        return 1
    else:
        return 1 + max(
            get_nesting_level(item) for item in possibly_nested_list
        )




if __name__ == "__main__":
    import doctest
    doctest.testmod()

