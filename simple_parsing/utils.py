"""Utility functions"""
import argparse
import builtins
import dataclasses
import functools
import json
import logging
import re
from collections import defaultdict
from dataclasses import MISSING, Field, dataclass, field
from enum import Enum
from functools import partial
from typing import *

logger = logging.getLogger(__name__)

builtin_types = [getattr(builtins, d) for d in dir(builtins) if isinstance(getattr(builtins, d), type)]

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

Dataclass = TypeVar("Dataclass")
DataclassType = Type[Dataclass]

SimpleValueType = Union[bool, int, float, str]
SimpleIterable = Union[List[SimpleValueType], Dict[Any, SimpleValueType], Set[SimpleValueType]]


def list_field(*default_items: SimpleValueType, **kwargs) -> List[T]:
    """shorthand function for setting a `list` attribute on a dataclass,
    so that every instance of the dataclass doesn't share the same list.

    Accepts any of the arguments of the `dataclasses.field` function.

    Returns:
        List[T]: a `dataclasses.field` of type `list`, containing the `default_items`. 
    """
    return MutableField(list, default_items, **kwargs)


def dict_field(*default_items: Tuple[K, V], **kwargs) -> Dict[K, V]:
    return MutableField(dict, default_items, **kwargs)


def set_field(*default_items: T, **kwargs) -> Set[T]:
    return MutableField(set, default_items, **kwargs)


def MutableField(_type: Type[T], *args, init: bool = True, repr: bool = True, hash: bool = None, compare: bool = True, metadata: Dict[str, Any] = None, **kwargs) -> T:
    return field(default_factory=partial(_type, *args, **kwargs), init=init, repr=repr, hash=hash, compare=compare, metadata=metadata)

def choice(*options: T, default=None) -> T:
    if default is not None and default not in options:
        raise ValueError(f"Default value of {default} is not a valid option! (options: {options})")
    return field(default=default, metadata={"choices": options})


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
    """Returns the `type` of the items in the provided container `type`. When no type annotation is found, or no item type is found, returns `typing.Type[typing.Any]`.
    Note, if a Tuple container type is passed, only the first argument to the type is actually used.
    >>> import typing
    >>> from typing import List, Tuple
    >>> get_item_type(list)
    typing.Type[typing.Any]
    >>> get_item_type(List)
    typing.Type[typing.Any]
    >>> get_item_type(tuple)
    typing.Type[typing.Any]
    >>> get_item_type(Tuple)
    typing.Type[typing.Any]
    >>> get_item_type(List[int])
    <class 'int'>
    >>> get_item_type(List[str])
    <class 'str'>
    >>> get_item_type(List[float])
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
    type_arguments = getattr(container_type, "__args__", [str])
    if type_arguments:
        return type_arguments[0]
    else:
        return Type[Any]

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
    return T if T is not Type[Any] else str



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



def default_value(field: dataclasses.Field) -> Optional[Any]:
    """Returns the default value of a dataclass field, if available.

    Args:
        field (dataclasses.Field[T]): The dataclasses.Field to get the default value of.

    Returns:
        Optional[T]: The default value for that field, if present, or None otherwise.
    """

    if field.default is not dataclasses.MISSING:
        return field.default
    elif field.default_factory is not dataclasses.MISSING:  # type: ignore
        return field.default_factory()  # type: ignore
    else:
        return None


class JsonSerializable:
    """
    Enables reading and writing a Dataclass to a JSON file.
    
    >>> from dataclasses import dataclass
    >>> from simple_parsing.utils import JsonSerializable
    >>> @dataclass
    ... class Config(JsonSerializable):
    ...   a: int = 123
    ...   b: str = "456"
    ... 
    >>> config = Config()
    >>> config
    Config(a=123, b='456')
    >>> config.save_json("config.json")
    >>> config_ = Config.load_json("config.json")
    >>> config_
    Config(a=123, b='456')
    >>> assert config == config_
    >>> import os
    >>> os.remove("config.json")
    """

    def save_json(self, path: str):
        with open(path, "w") as f:
            dict_ = dataclasses.asdict(self)
            json.dump(dict_, f, indent=1)

    @staticmethod
    def from_dict(dataclass: Type[Dataclass], d: Dict[str, Any]) -> Dataclass:
        for field in dataclasses.fields(dataclass):
            if dataclasses.is_dataclass(field.type):
                # nested dataclass:
                args_dict = d[field.name]
                nested_instance = JsonSerializable.from_dict(field.type, args_dict)
                d[field.name] = nested_instance
        return dataclass(**d) # type: ignore

    @classmethod
    def load_json(cls, path: str):
        with open(path) as f:
            args_dict = json.load(f)
        return JsonSerializable.from_dict(cls, args_dict)




if __name__ == "__main__":
    import doctest
    doctest.testmod()
