"""Utility functions"""
import argparse
import dataclasses
import re
from dataclasses import dataclass
from typing import *


class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.MetavarTypeHelpFormatter):
    """Little shorthand for using both of argparse's ArgumentDefaultHelpFormatter and MetavarTypeHelpFormatter classes.
    """
    pass


def camel_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def str2bool(v: str) -> bool:
    """
    Taken from https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    """
    if isinstance(v, bool):
        return v
    v = v.strip()
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError(f"Boolean value expected for argument, received '{v}'")

T = TypeVar("T")

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
        Type -- the type of the container's items, if found, else None.
    """
    if container_type in {list, tuple}:
        # the built-in `list` and `tuple` types don't have annotations for their item types.
        return Type[Any]
    return getattr(container_type, "__args__", tuple([Any]))[0]
    

def get_argparse_container_type(container_type: Type) -> Type:
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


def is_list(t: Type) -> bool:
    parent_classes = t.mro()
    return list in parent_classes


def is_tuple(t: Type) -> bool:
    parent_classes = t.mro()
    return tuple in parent_classes


def is_tuple_or_list(t: Type) -> bool:
    return is_list(t) or is_tuple(t)


def is_tuple_or_list_of_dataclasses(t: Type) -> bool:
    return is_tuple_or_list(t) and dataclasses.is_dataclass(get_item_type(t))



def _parse_multiple_containers(tuple_or_list: type,) -> Callable[[str], List[Any]]:
    T = get_argparse_container_type(tuple_or_list)
    factory = tuple if is_tuple(tuple_or_list) else list

    def parse_fn(v: str) -> List[Any]:
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
        return values

    return parse_fn


def _parse_container(tuple_or_list: type,) -> Callable[[str], List[Any]]:
    T = get_argparse_container_type(tuple_or_list)
    factory = tuple if is_tuple(tuple_or_list) else list

    def parse_fn(v: str) -> List[Any]:
        # TODO: maybe we could use the fact we know this isn't for a list of lists to make this better somehow.
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
        return values

    return parse_fn



if __name__ == "__main__":
    import doctest
    doctest.testmod()
