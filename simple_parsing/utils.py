"""Utility functions used in various parts of the simple_parsing package."""
import argparse
import builtins
import dataclasses
import functools
import json
import re
import warnings
from abc import ABC
from collections import abc as c_abc
from collections import defaultdict
from dataclasses import _MISSING_TYPE, MISSING, Field, dataclass
from enum import Enum
from functools import partial
from inspect import isclass
from typing import (Any, Callable, Container, Dict, Iterable, List, Mapping,
                    MutableMapping, Optional, Set, Tuple, Type, TypeVar, Union)

import typing_inspect as tpi

from simple_parsing.logging_utils import get_logger

logger = get_logger(__file__)

builtin_types = [getattr(builtins, d) for d in dir(
    builtins) if isinstance(getattr(builtins, d), type)]

K = TypeVar("K")
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")
W = TypeVar("W")

Dataclass = TypeVar("Dataclass")
DataclassType = Type[Dataclass]

SimpleValueType = Union[bool, int, float, str]
SimpleIterable = Union[List[SimpleValueType],
                       Dict[Any, SimpleValueType], Set[SimpleValueType]]



def is_subparser_field(field: Field) -> bool:
    if is_union(field.type) and not is_choice(field):
        type_arguments = get_type_arguments(field.type)
        return all(map(dataclasses.is_dataclass, type_arguments))
    return bool(field.metadata.get("subparsers", {}))


class InconsistentArgumentError(RuntimeError):
    """
    Error raised when the number of arguments provided is inconsistent when parsing multiple instances from command line.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def camel_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


TRUE_STRINGS: List[str] = ['yes', 'true', 't', 'y', '1']
FALSE_STRINGS: List[str] = ['no', 'false', 'f', 'n', '0']


def str2bool(raw_value: Union[str, bool]) -> bool:
    """
    Taken from https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    """
    if isinstance(raw_value, bool):
        return raw_value
    v = raw_value.strip().lower()
    if v in TRUE_STRINGS:
        return True
    elif v in FALSE_STRINGS:
        return False
    else:
        raise argparse.ArgumentTypeError(
            f"Boolean value expected for argument, received '{raw_value}'")


def get_item_type(container_type: Type[Container[T]]) -> T:
    """Returns the `type` of the items in the provided container `type`.
    
    When no type annotation is found, or no item type is found, returns
    `typing.Any`.
    NOTE: If a type with multiple arguments is passed, only the first type
    argument is returned.
    
    >>> import typing
    >>> from typing import List, Tuple
    >>> get_item_type(list)
    typing.Any
    >>> get_item_type(List)
    typing.Any
    >>> get_item_type(tuple)
    typing.Any
    >>> get_item_type(Tuple)
    typing.Any
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
    if container_type in {list, set, tuple, List, Set, Tuple, Dict, Mapping, MutableMapping}:
        # the built-in `list` and `tuple` types don't have annotations for their item types.
        return Any
    type_arguments = getattr(container_type, "__args__", None)
    if type_arguments:
        return type_arguments[0]
    else:
        return Any


def get_argparse_type_for_container(container_type: Type) -> Union[Type, Callable[[str], bool]]:
    """Gets the argparse 'type' option to be used for a given container type.
    When an annotation is present, the 'type' option of argparse is set to that type.
    if not, then the default value of 'str' is returned.

    Arguments:
        container_type {Type} -- A container type (ideally a typing.Type such as List, Tuple, along with an item annotation: List[str], Tuple[int, int], etc.)

    Returns:
        typing.Type -- the type that should be used in argparse 'type' argument option.
    """
    T = get_item_type(container_type)
    if T is bool:
        return str2bool
    if T is Any:
        return str
    return T


def _mro(t: Type) -> List[Type]:
    if hasattr(t, "__mro__"):
        return t.__mro__
    elif tpi.get_origin(t) is type:
        return []
    elif hasattr(t, "mro") and callable(t.mro):
        return t.mro()
    return []


def is_list(t: Type) -> bool:
    """returns True when `t` is a List type.

    Args:
        t (Type): a type.

    Returns:
        bool: True if `t` is list or a subclass of list.
    
    >>> from typing import *
    >>> is_list(list)
    True
    >>> is_list(tuple)
    False
    >>> is_list(List)
    True
    >>> is_list(List[int])
    True
    >>> is_list(List[Tuple[int, str, None]])
    True
    >>> is_list(Optional[List[int]])
    False
    >>> class foo(List[int]):
    ...   pass
    ...
    >>> is_list(foo)
    True
    """
    return list in _mro(t)


def is_tuple(t: Type) -> bool:
    """returns True when `t` is a tuple type.

    Args:
        t (Type): a type.

    Returns:
        bool: True if `t` is tuple or a subclass of tuple.
    
    >>> from typing import *
    >>> is_tuple(list)
    False
    >>> is_tuple(tuple)
    True
    >>> is_tuple(Tuple)
    True
    >>> is_tuple(Tuple[int])
    True
    >>> is_tuple(Tuple[int, str, None])
    True
    >>> class foo(tuple):
    ...   pass
    ...
    >>> is_tuple(foo)
    True
    """
    return tuple in _mro(t)


def is_dict(t: Type) -> bool:
    """returns True when `t` is a dict type or annotation.

    Args:
        t (Type): a type.

    Returns:
        bool: True if `t` is dict or a subclass of dict.
    
    >>> from typing import *
    >>> from collections import OrderedDict
    >>> is_dict(dict)
    True
    >>> is_dict(OrderedDict)
    True
    >>> is_dict(tuple)
    False
    >>> is_dict(Dict)
    True
    >>> is_dict(Dict[int, float])
    True
    >>> is_dict(Dict[Any, Dict])
    True
    >>> is_dict(Optional[Dict])
    False
    >>> is_dict(Mapping[str, int])
    True
    >>> class foo(Dict):
    ...   pass
    ...
    >>> is_dict(foo)
    True
    """
    mro = _mro(t)
    return dict in mro or Mapping in mro or c_abc.Mapping in mro


def is_set(t: Type) -> bool:
    """returns True when `t` is a set type or annotation.

    Args:
        t (Type): a type.

    Returns:
        bool: True if `t` is set or a subclass of set.
    
    >>> from typing import *
    >>> is_set(set)
    True
    >>> is_set(Set)
    True
    >>> is_set(tuple)
    False
    >>> is_set(Dict)
    False
    >>> is_set(Set[int])
    True
    >>> is_set(Set["something"])
    True
    >>> is_set(Optional[Set])
    False
    >>> class foo(Set):
    ...   pass
    ...
    >>> is_set(foo)
    True
    """
    mro = _mro(t)
    return set in _mro(t)



def is_dataclass_type(t: Type) -> bool:
    """Returns wether t is a dataclass type or a TypeVar of a dataclass type.

    Args:
        t (Type): Some type.

    Returns:
        bool: Wether its a dataclass type.
    """
    return dataclasses.is_dataclass(t) or (
        tpi.is_typevar(t) and dataclasses.is_dataclass(tpi.get_bound(t))
    )


def is_enum(t: Type) -> bool:
    return Enum in _mro(t)


def is_bool(t: Type) -> bool:
    return bool in _mro(t)


def is_tuple_or_list(t: Type) -> bool:
    return is_list(t) or is_tuple(t)


def is_union(t: Type) -> bool:
    """Returns wether or not the given Type annotation is a variant (or subclass) of typing.Union

    Args:
        t (Type): some type annotation

    Returns:
        bool: Wether this type represents a Union type.

    >>> from typing import *
    >>> is_union(Union[int, str])
    True
    >>> is_union(Union[int, str, float])
    True
    >>> is_union(Tuple[int, str])
    False
    """
    return getattr(t, "__origin__", "") == Union


def is_choice(field: Field) -> bool:
    return bool(field.metadata.get("custom_args", {}).get("choices", {}))


def is_optional(t: Type) -> bool:
    """Returns True if the given Type is a variant of the Optional type.
    
    Parameters
    ----------
    - t : Type
    
        a Type annotation (or "live" type)
    
    Returns
    -------
    bool
        Wether or not this is an Optional.

    >>> from typing import Union, Optional, List
    >>> is_optional(str)
    False
    >>> is_optional(Optional[str])
    True
    >>> is_optional(Union[str, None])
    True
    >>> is_optional(Union[str, List])
    False
    >>> is_optional(Union[str, List, int, float, None])
    True
    """
    return is_union(t) and type(None) in get_type_arguments(t)


def is_tuple_or_list_of_dataclasses(t: Type) -> bool:
    return is_tuple_or_list(t) and is_dataclass_type(get_item_type(t))


def contains_dataclass_type_arg(t: Type) -> bool:
    if is_dataclass_type(t):
        return True
    elif is_tuple_or_list_of_dataclasses(t):
        return True
    elif is_union(t):
        return any(
            contains_dataclass_type_arg(arg)
            for arg in get_type_arguments(t)
        )
    return False


def get_dataclass_type_arg(t: Type) -> Optional[Type]:
    if not contains_dataclass_type_arg(t):
        return None
    if is_dataclass_type(t):
        return t
    elif is_tuple_or_list(t) or is_union(t):
        return next(filter(None, (
            get_dataclass_type_arg(arg)
            for arg in get_type_arguments(t)
        )), None)
    return None


def get_type_arguments(container_type: Type) -> List[Type]:
    return getattr(container_type, "__args__", [])


def get_type_name(some_type: Type):
    result = getattr(some_type, "__name__", str(some_type))
    type_arguments = get_type_arguments(some_type)
    if type_arguments:
        result += f"[{','.join(get_type_name(T) for T in type_arguments)}]"
    return result


def get_container_nargs(container_type: Type) -> Union[int, str]:
    if is_tuple(container_type):
        type_arguments = getattr(container_type, "__args__", [])
        if type_arguments and Ellipsis not in type_arguments:
            nargs = len(type_arguments)
            # if nargs == 1:
            #     # a `Tuple[int]` annotation can be interpreted as "a tuple of an unknown number of ints"?.
            #     return "*"
            return nargs

    return "*"


def _parse_multiple_containers(container_type: type, append_action: bool = False) -> Callable[[str], List[Any]]:
    T = get_argparse_type_for_container(container_type)
    factory = tuple if is_tuple(container_type) else list

    result = factory()

    def parse_fn(value: str):
        logger.debug(
            f"parsing multiple {container_type} of {T}s, value is: '{value}'")
        values = _parse_container(container_type)(value)
        logger.debug(f"parsing result is '{values}'")

        if append_action:
            result += values
            return result
        else:
            return values
    return parse_fn


def _parse_container(container_type: Type[Container]) -> Callable[[str], List[Any]]:
    T = get_argparse_type_for_container(container_type)
    factory = tuple if is_tuple(container_type) else list
    import ast

    result: List[Any] = []

    def _parse(value: str) -> List[Any]:
        logger.debug(f"Parsing a {container_type} of {T}s, value is: '{value}'")
        try:
            values = _parse_literal(value)
        except Exception as e:
            logger.debug(
                f"Exception while trying to parse '{value}' as a literal: {type(e)}: {e}")
            # if it doesnt work, fall back to the parse_fn.
            values = _fallback_parse(value)

        # we do the default 'argparse' action, which is to add the values to a bigger list of values.
        # result.extend(values)
        logger.debug(f"returning values: {values}")
        return values

    def _parse_literal(value: str) -> Union[List[Any], Any]:
        """ try to parse the string to a python expression directly.
        (useful for nested lists or tuples.)
        """
        literal = ast.literal_eval(value)
        logger.debug(f"Parsed literal: {literal}")
        if not isinstance(literal, (list, tuple)):
            # we were passed a single-element container, like "--some_list 1", which should give [1].
            # We therefore return the literal itself, and argparse will append it.
            return T(literal)
        else:
            container = literal
            values = factory(T(v) for v in container)
            return values

    def _fallback_parse(v: str) -> List[Any]:
        v = ' '.join(v.split())
        if v.startswith("[") and v.endswith("]"):
            v = v[1:-1]

        separator = " "
        for sep in [","]:  # TODO: maybe add support for other separators?
            if sep in v:
                separator = sep

        str_values = [v.strip() for v in v.split(separator)]
        T_values = [T(v_str) for v_str in str_values]
        values = factory(v for v in T_values)
        return values

    _parse.__name__ = T.__name__
    return _parse


def setattr_recursive(obj: object, attribute_name: str, value: Any):
    if "." not in attribute_name:
        setattr(obj, attribute_name, value)
    else:
        parts = attribute_name.split(".")
        child_object = getattr(obj, parts[0])
        setattr_recursive(child_object, ".".join(parts[1:]), value)


def split_dest(destination: str) -> Tuple[str, str]:
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


def default_value(field: dataclasses.Field) -> Union[T, _MISSING_TYPE]:
    """Returns the default value of a field in a dataclass, if available.
    When not available, returns `dataclasses.MISSING`.

    Args:
        field (dataclasses.Field): The dataclasses.Field to get the default value of.

    Returns:
        Union[T, _MISSING_TYPE]: The default value for that field, if present, or None otherwise.
    """
    if field.default is not dataclasses.MISSING:
        return field.default
    elif field.default_factory is not dataclasses.MISSING:  # type: ignore
        constructor = field.default_factory # type: ignore
        return constructor()
    else:
        return dataclasses.MISSING


def trie(sentences: List[List[str]]) -> Dict[str, Union[str, Dict]]:
    """Given a list of sentences, creates a trie as a nested dicts of word strings.

    Args:
        sentences (List[List[str]]): a list of sentences

    Returns:
        Dict[str, Union[str, Dict[str, ...]]]: A tree where each node is a word in a sentence.
        Sentences which begin with the same words share the first nodes, etc. 
    """
    first_word_to_sentences: Dict[str, List[List[str]]] = defaultdict(list)
    for sentence in sentences:
        first_word = sentence[0]
        first_word_to_sentences[first_word].append(sentence)

    return_dict: Dict[str, Union[str, Dict]] = {}
    for first_word, sentences in first_word_to_sentences.items():
        if len(sentences) == 1:
            return_dict[first_word] = ".".join(sentences[0])
        else:
            sentences_without_first_word = [
                sentence[1:] for sentence in sentences]
            return_dict[first_word] = trie(sentences_without_first_word)
    return return_dict


def keep_keys(d: Dict, keys_to_keep: Iterable[str]) -> Tuple[Dict, Dict]:
    """Removes all the keys in `d` that aren't in `keys`.

    Parameters
    ----------
    d : Dict
        Some dictionary.
    keys_to_keep : Iterable[str]
        The set of keys to keep

    Returns
    -------
    Tuple[Dict, Dict]
        The same dictionary (with all the unwanted keys removed) as well as a
        new dict containing only the removed item.

    """
    d_keys = set(d.keys())  # save a copy since we will modify the dict.
    removed = {}
    for key in d_keys:
        if key not in keys_to_keep:
            removed[key] = d.pop(key)
    return d, removed


if __name__ == "__main__":
    import doctest
    doctest.testmod()
