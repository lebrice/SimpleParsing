"""Utility functions used in various parts of the simple_parsing package."""
from __future__ import annotations

import argparse
import builtins
import dataclasses
import enum
import hashlib
import inspect
import itertools
import re
import sys
import types
import typing
from collections import OrderedDict, defaultdict
from collections import abc as c_abc
from dataclasses import _MISSING_TYPE, MISSING, Field
from enum import Enum
from logging import getLogger
from typing import (
    Any,
    Callable,
    ClassVar,
    Container,
    Dict,
    ForwardRef,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Set,
    Tuple,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import Literal, Protocol, TypeGuard, get_args, get_origin

# There are cases where typing.Literal doesn't match typing_extensions.Literal:
# https://github.com/python/typing_extensions/pull/148
try:
    from typing import Literal as LiteralAlt
except ImportError:
    LiteralAlt = Literal  # type: ignore


# NOTE: Copied from typing_inspect.
def is_typevar(t) -> bool:
    return type(t) is TypeVar


def get_bound(t):
    if is_typevar(t):
        return getattr(t, "__bound__", None)
    else:
        raise TypeError(f"type is not a `TypeVar`: {t}")


def is_forward_ref(t) -> TypeGuard[typing.ForwardRef]:
    return isinstance(t, typing.ForwardRef)


def get_forward_arg(fr: ForwardRef) -> str:
    return getattr(fr, "__forward_arg__")


logger = getLogger(__name__)

builtin_types = [
    getattr(builtins, d) for d in dir(builtins) if isinstance(getattr(builtins, d), type)
]

K = TypeVar("K")
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")
W = TypeVar("W")


class Dataclass(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field]]


def is_dataclass_instance(obj: Any) -> TypeGuard[Dataclass]:
    return dataclasses.is_dataclass(obj) and dataclasses.is_dataclass(type(obj))


def is_dataclass_type(obj: Any) -> TypeGuard[type[Dataclass]]:
    return inspect.isclass(obj) and dataclasses.is_dataclass(obj)


DataclassT = TypeVar("DataclassT", bound=Dataclass)

SimpleValueType = Union[bool, int, float, str]
SimpleIterable = Union[List[SimpleValueType], Dict[Any, SimpleValueType], Set[SimpleValueType]]

PossiblyNestedDict = Dict[K, Union[V, "PossiblyNestedDict[K, V]"]]
PossiblyNestedMapping = Mapping[K, Union[V, "PossiblyNestedMapping[K, V]"]]


def is_subparser_field(field: Field) -> bool:
    if is_union(field.type) and not is_choice(field):
        type_arguments = get_type_arguments(field.type)
        return all(map(dataclasses.is_dataclass, type_arguments))
    return bool(field.metadata.get("subparsers", {}))


class InconsistentArgumentError(RuntimeError):
    """Error raised when the number of arguments provided is inconsistent when parsing multiple
    instances from command line."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def camel_case(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


TRUE_STRINGS: list[str] = ["yes", "true", "t", "y", "1"]
FALSE_STRINGS: list[str] = ["no", "false", "f", "n", "0"]


def str2bool(raw_value: str | bool) -> bool:
    """Taken from https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-
    argparse."""
    if isinstance(raw_value, bool):
        return raw_value
    v = raw_value.strip().lower()
    if v in TRUE_STRINGS:
        return True
    elif v in FALSE_STRINGS:
        return False
    else:
        raise argparse.ArgumentTypeError(
            f"Boolean value expected for argument, received '{raw_value}'"
        )


def get_item_type(container_type: type[Container[T]]) -> T:
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
    if container_type in {
        list,
        set,
        tuple,
        List,
        Set,
        Tuple,
        Dict,
        Mapping,
        MutableMapping,
    }:
        # the built-in `list` and `tuple` types don't have annotations for their item types.
        return Any
    type_arguments = getattr(container_type, "__args__", None)
    if type_arguments:
        return type_arguments[0]
    else:
        return Any


def get_argparse_type_for_container(
    container_type: type[Container[T]],
) -> type[T] | Callable[[str], T]:
    """Gets the argparse 'type' option to be used for a given container type. When an annotation is
    present, the 'type' option of argparse is set to that type. if not, then the default value of
    'str' is returned.

    Arguments:
        container_type {Type} -- A container type (ideally a typing.Type such as List, Tuple, along with an item annotation: List[str], Tuple[int, int], etc.)

    Returns:
        typing.Type -- the type that should be used in argparse 'type' argument option.

    TODO: This overlaps in a weird way with `get_parsing_fn`, which returns the 'type'
    to use for a given annotation! This function however doesn't deal with 'weird' item
    types, it just returns the first annotation.
    """
    T = get_item_type(container_type)
    if T is bool:
        return str2bool
    if T is Any:
        return str
    if is_enum(T):
        # IDEA: Fix this weirdness by first moving all this weird parsing logic into the
        # field wrapper class, and then split it up into different subclasses of FieldWrapper,
        # each for a different type of field.
        from simple_parsing.wrappers.field_parsing import parse_enum

        return parse_enum(T)
    return T


def _mro(t: type) -> list[type]:
    # TODO: This is mostly used in 'is_tuple' and such, and should be replaced with
    # either the built-in 'get_origin' from typing, or from typing-inspect.
    if t is None:
        return []
    if hasattr(t, "__mro__"):
        return t.__mro__
    elif get_origin(t) is type:
        return []
    elif hasattr(t, "mro") and callable(t.mro):
        return t.mro()
    return []


def is_literal(t: type) -> bool:
    """Returns True with `t` is a Literal type.

    >>> from typing_extensions import Literal
    >>> from typing import *
    >>> is_literal(list)
    False
    >>> is_literal("foo")
    False
    >>> is_literal(Literal[True, False])
    True
    >>> is_literal(Literal[1,2,3])
    True
    >>> is_literal(Literal["foo", "bar"])
    True
    >>> is_literal(Optional[Literal[1,2]])
    False
    """
    return get_origin(t) in (Literal, LiteralAlt)


def is_list(t: type) -> bool:
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


def is_tuple(t: type) -> bool:
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
    >>> is_tuple(List[int])
    False
    """
    return tuple in _mro(t)


def is_dict(t: type) -> bool:
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


def is_set(t: type) -> bool:
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
    return set in _mro(t)


def is_dataclass_type_or_typevar(t: type) -> bool:
    """Returns whether t is a dataclass type or a TypeVar of a dataclass type.

    Args:
        t (Type): Some type.

    Returns:
        bool: Whether its a dataclass type.
    """
    return dataclasses.is_dataclass(t) or (
        is_typevar(t) and dataclasses.is_dataclass(get_bound(t))
    )


def is_enum(t: type) -> bool:
    if inspect.isclass(t):
        return issubclass(t, enum.Enum)
    return Enum in _mro(t)


def is_bool(t: type) -> bool:
    return bool in _mro(t)


def is_tuple_or_list(t: type) -> bool:
    return is_list(t) or is_tuple(t)


def is_union(t: type) -> bool:
    """Returns whether or not the given Type annotation is a variant (or subclass) of typing.Union.

    Args:
        t (Type): some type annotation

    Returns:
        bool: Whether this type represents a Union type.

    >>> from typing import *
    >>> is_union(Union[int, str])
    True
    >>> is_union(Union[int, str, float])
    True
    >>> is_union(Tuple[int, str])
    False
    """
    if sys.version_info[:2] >= (3, 10) and isinstance(t, types.UnionType):
        return True
    return getattr(t, "__origin__", "") == Union


def is_homogeneous_tuple_type(t: type[tuple]) -> bool:
    """Returns whether the given Tuple type is homogeneous: if all items types are the same.

    This also includes Tuple[<some_type>, ...]

    Returns
    -------
    bool

    >>> from typing import *
    >>> is_homogeneous_tuple_type(Tuple)
    True
    >>> is_homogeneous_tuple_type(Tuple[int, int])
    True
    >>> is_homogeneous_tuple_type(Tuple[int, str])
    False
    >>> is_homogeneous_tuple_type(Tuple[int, str, float])
    False
    >>> is_homogeneous_tuple_type(Tuple[int, ...])
    True
    >>> is_homogeneous_tuple_type(Tuple[Tuple[int, str], ...])
    True
    >>> is_homogeneous_tuple_type(Tuple[List[int], List[str]])
    False
    """
    if not is_tuple(t):
        return False
    type_arguments = get_type_arguments(t)
    if not type_arguments:
        return True
    assert isinstance(type_arguments, tuple), type_arguments
    if len(type_arguments) == 2 and type_arguments[1] is Ellipsis:
        return True
    # Tuple[str, str, str] -> True
    # Tuple[str, str, float] -> False
    # TODO: Not sure if this will work with more complex item times (like nested tuples)
    return len(set(type_arguments)) == 1


def is_choice(field: Field) -> bool:
    return bool(field.metadata.get("custom_args", {}).get("choices", {}))


def is_optional(t: type) -> bool:
    """Returns True if the given Type is a variant of the Optional type.

    Parameters
    ----------
    - t : Type

        a Type annotation (or "live" type)

    Returns
    -------
    bool
        Whether or not this is an Optional.

    >>> from typing import Union, Optional, List, Literal
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
    >>> is_optional(Literal["a", None, "b"])
    True
    >>> is_optional(Literal["a", 1])
    False
    """
    if is_union(t) and type(None) in get_type_arguments(t):
        return True
    elif is_literal(t) and None in get_type_arguments(t):
        return True
    else:
        return False


def is_tuple_or_list_of_dataclasses(t: type) -> bool:
    return is_tuple_or_list(t) and is_dataclass_type_or_typevar(get_item_type(t))


def contains_dataclass_type_arg(t: type) -> bool:
    if is_dataclass_type_or_typevar(t):
        return True
    elif is_tuple_or_list_of_dataclasses(t):
        return True
    elif is_union(t):
        return any(contains_dataclass_type_arg(arg) for arg in get_type_arguments(t))
    return False


def get_dataclass_type_arg(t: type) -> type | None:
    if not contains_dataclass_type_arg(t):
        return None
    if is_dataclass_type_or_typevar(t):
        return t
    elif is_tuple_or_list(t) or is_union(t):
        return next(
            filter(None, (get_dataclass_type_arg(arg) for arg in get_type_arguments(t))),
            None,
        )
    return None


def get_type_arguments(container_type: type) -> tuple[type, ...]:
    # return getattr(container_type, "__args__", ())
    return get_args(container_type)


def get_type_name(some_type: type):
    result = getattr(some_type, "__name__", str(some_type))
    type_arguments = get_type_arguments(some_type)
    if type_arguments:
        result += f"[{','.join(get_type_name(T) for T in type_arguments)}]"
    return result


def get_container_nargs(container_type: type) -> int | str:
    """Gets the value of 'nargs' appropriate for the given container type.

    Parameters
    ----------
    container_type : Type
        Some container type.

    Returns
    -------
    Union[int, str]
        [description]
    """
    if is_tuple(container_type):
        # TODO: Should a `Tuple[int]` annotation be interpreted as "a tuple of an
        # unknown number of ints"?.
        type_arguments: tuple[type, ...] = get_type_arguments(container_type)
        if not type_arguments:
            return "*"
        if len(type_arguments) == 2 and type_arguments[1] is Ellipsis:
            return "*"

        total_nargs: int = 0
        for item_type in type_arguments:
            # TODO: Handle the 'nargs' for nested container types!
            if is_list(item_type) or is_tuple(item_type):
                # BUG: If it's a container like Tuple[Tuple[int, str], Tuple[int, str]]
                # we could do one of two things:
                #
                # - Option 1: Use nargs=4 and re-organize/split values in
                #   post-processing.
                # item_nargs: Union[int, str] = get_container_nargs(item_type)
                # if isinstance(item_nargs, int):
                #     total_nargs += item_nargs
                # else:
                #     return "*"
                #
                # This is a bit confusing, and IMO it might be best to just do
                # - Option 2: Use `nargs='*'` and use a custom parsing function that
                #   will convert entries appropriately..
                return "*"
            total_nargs += 1
        return total_nargs

    if is_list(container_type):
        return "*"
    raise NotImplementedError(f"Not sure what 'nargs' should be for type {container_type}")


def _parse_multiple_containers(
    container_type: type, append_action: bool = False
) -> Callable[[str], list[Any]]:
    T = get_argparse_type_for_container(container_type)
    factory = tuple if is_tuple(container_type) else list

    result = factory()

    def parse_fn(value: str):
        nonlocal result
        logger.debug(f"parsing multiple {container_type} of {T}s, value is: '{value}'")
        values = _parse_container(container_type)(value)
        logger.debug(f"parsing result is '{values}'")

        if append_action:
            result += values
            return result
        else:
            return values

    return parse_fn


def _parse_container(container_type: type[Container]) -> Callable[[str], list[Any]]:
    T = get_argparse_type_for_container(container_type)
    factory = tuple if is_tuple(container_type) else list
    import ast

    def _parse(value: str) -> list[Any]:
        logger.debug(f"Parsing a {container_type} of {T}s, value is: '{value}'")
        try:
            values = _parse_literal(value)
        except Exception as e:
            logger.debug(f"Exception while trying to parse '{value}' as a literal: {type(e)}: {e}")
            # if it doesn't work, fall back to the parse_fn.
            values = _fallback_parse(value)

        # we do the default 'argparse' action, which is to add the values to a bigger list of values.
        # result.extend(values)
        logger.debug(f"returning values: {values}")
        return values

    def _parse_literal(value: str) -> list[Any] | Any:
        """try to parse the string to a python expression directly.

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

    def _fallback_parse(v: str) -> list[Any]:
        v = " ".join(v.split())
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


def getattr_recursive(obj: object, attribute_name: str):
    if "." not in attribute_name:
        return getattr(obj, attribute_name)
    else:
        child_attr, _, rest_of_attribute_name = attribute_name.partition(".")
        child_object = getattr(obj, child_attr)
        return getattr_recursive(child_object, rest_of_attribute_name)


def split_dest(destination: str) -> tuple[str, str]:
    parent, _, attribute_in_parent = destination.rpartition(".")
    return parent, attribute_in_parent


def get_nesting_level(possibly_nested_list):
    if not isinstance(possibly_nested_list, (list, tuple)):
        return 0
    elif len(possibly_nested_list) == 0:
        return 1
    else:
        return 1 + max(get_nesting_level(item) for item in possibly_nested_list)


def default_value(field: dataclasses.Field) -> T | _MISSING_TYPE:
    """Returns the default value of a field in a dataclass, if available. When not available,
    returns `dataclasses.MISSING`.

    Args:
        field (dataclasses.Field): The dataclasses.Field to get the default value of.

    Returns:
        Union[T, _MISSING_TYPE]: The default value for that field, if present, or None otherwise.
    """
    if field.default is not dataclasses.MISSING:
        return field.default
    elif field.default_factory is not dataclasses.MISSING:  # type: ignore
        constructor = field.default_factory  # type: ignore
        return constructor()
    else:
        return dataclasses.MISSING


def trie(sentences: list[list[str]]) -> dict[str, str | dict]:
    """Given a list of sentences, creates a trie as a nested dicts of word strings.

    Args:
        sentences (List[List[str]]): a list of sentences

    Returns:
        Dict[str, Union[str, Dict[str, ...]]]: A tree where each node is a word in a sentence.
        Sentences which begin with the same words share the first nodes, etc.
    """
    first_word_to_sentences: dict[str, list[list[str]]] = defaultdict(list)
    for sentence in sentences:
        first_word = sentence[0]
        first_word_to_sentences[first_word].append(sentence)

    return_dict: dict[str, str | dict] = {}
    for first_word, sentences in first_word_to_sentences.items():
        if len(sentences) == 1:
            return_dict[first_word] = ".".join(sentences[0])
        else:
            sentences_without_first_word = [sentence[1:] for sentence in sentences]
            return_dict[first_word] = trie(sentences_without_first_word)
    return return_dict


def keep_keys(d: dict, keys_to_keep: Iterable[str]) -> tuple[dict, dict]:
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


def compute_identity(size: int = 16, **sample) -> str:
    """Compute a unique hash out of a dictionary.

    Parameters
    ----------
    size: int
        size of the unique hash

    **sample:
        Dictionary to compute the hash from
    """
    sample_hash = hashlib.sha256()

    for k, v in sorted(sample.items()):
        sample_hash.update(k.encode("utf8"))

        if isinstance(v, dict):
            sample_hash.update(compute_identity(size, **v).encode("utf8"))
        else:
            sample_hash.update(str(v).encode("utf8"))

    return sample_hash.hexdigest()[:size]


def dict_intersection(*dicts: dict[K, V]) -> Iterable[tuple[K, tuple[V, ...]]]:
    common_keys = set(dicts[0])
    for d in dicts:
        common_keys.intersection_update(d)
    for key in common_keys:
        yield (key, tuple(d[key] for d in dicts))


def field_dict(dataclass: Dataclass) -> dict[str, Field]:
    result: dict[str, Field] = OrderedDict()
    for field in dataclasses.fields(dataclass):
        result[field.name] = field
    return result


def zip_dicts(*dicts: dict[K, V]) -> Iterable[tuple[K, tuple[V | None, ...]]]:
    # If any attributes are common to both the Experiment and the State,
    # copy them over to the Experiment.
    keys = set(itertools.chain(*dicts))
    for key in keys:
        yield (key, tuple(d.get(key) for d in dicts))


def dict_union(*dicts: dict[K, V], recurse: bool = True, dict_factory=dict) -> dict[K, V]:
    """Simple dict union until we use python 3.9.

    If `recurse` is True, also does the union of nested dictionaries.
    NOTE: The returned dictionary has keys sorted alphabetically.
    >>> a = {'a': 1, 'b': 2, 'c': 3}
    >>> b = {'c': 5, 'd': 6, 'e': 7}
    >>> dict_union(a, b)
    {'a': 1, 'b': 2, 'c': 5, 'd': 6, 'e': 7}
    >>> a = {'a': 1, 'b': {'c': 2, 'd': 3}}
    >>> b = {'a': 2, 'b': {'c': 3, 'e': 6}}
    >>> dict_union(a, b)
    {'a': 2, 'b': {'c': 3, 'd': 3, 'e': 6}}
    """
    result: dict = dict_factory()
    if not dicts:
        return result
    assert len(dicts) >= 1
    all_keys: set[str] = set()
    all_keys.update(*dicts)
    all_keys = sorted(all_keys)

    # Create a neat generator of generators, to save some memory.
    all_values: Iterable[tuple[V, Iterable[K]]] = (
        (k, (d[k] for d in dicts if k in d)) for k in all_keys
    )
    for k, values in all_values:
        sub_dicts: list[dict] = []
        new_value: V = None
        n_values = 0
        for v in values:
            if isinstance(v, dict) and recurse:
                sub_dicts.append(v)
            else:
                # Overwrite the new value for that key.
                new_value = v
            n_values += 1

        if len(sub_dicts) == n_values and recurse:
            # We only get here if all values for key `k` were dictionaries,
            # and if recurse was True.
            new_value = dict_union(*sub_dicts, recurse=True, dict_factory=dict_factory)

        result[k] = new_value
    return result


def flatten(nested: PossiblyNestedMapping[K, V]) -> dict[tuple[K, ...], V]:
    """Flatten a dictionary of dictionaries. The returned dictionary's keys are tuples, one entry
    per layer.

    >>> flatten({"a": {"b": 2, "c": 3}, "c": {"d": 3, "e": 4}})
    {('a', 'b'): 2, ('a', 'c'): 3, ('c', 'd'): 3, ('c', 'e'): 4}
    """
    flattened: dict[tuple[K, ...], V] = {}
    for k, v in nested.items():
        if isinstance(v, c_abc.Mapping):
            for subkeys, subv in flatten(v).items():
                collision_key = (k, *subkeys)
                assert collision_key not in flattened
                flattened[collision_key] = subv
        else:
            flattened[(k,)] = v
    return flattened


def unflatten(flattened: Mapping[tuple[K, ...], V]) -> PossiblyNestedDict[K, V]:
    """Unflatten a dictionary back into a possibly nested dictionary.

    >>> unflatten({('a', 'b'): 2, ('a', 'c'): 3, ('c', 'd'): 3, ('c', 'e'): 4})
    {'a': {'b': 2, 'c': 3}, 'c': {'d': 3, 'e': 4}}
    """
    nested: PossiblyNestedDict[K, V] = {}
    for keys, value in flattened.items():
        sub_dictionary = nested
        for part in keys[:-1]:
            assert isinstance(sub_dictionary, dict)
            sub_dictionary = sub_dictionary.setdefault(part, {})
        assert isinstance(sub_dictionary, dict)
        sub_dictionary[keys[-1]] = value
    return nested


def flatten_join(nested: PossiblyNestedMapping[str, V], sep: str = ".") -> dict[str, V]:
    """Flatten a dictionary of dictionaries. Joins different nesting levels with `sep` as
    separator.

    >>> flatten_join({'a': {'b': 2, 'c': 3}, 'c': {'d': 3, 'e': 4}})
    {'a.b': 2, 'a.c': 3, 'c.d': 3, 'c.e': 4}
    >>> flatten_join({'a': {'b': 2, 'c': 3}, 'c': {'d': 3, 'e': 4}}, sep="/")
    {'a/b': 2, 'a/c': 3, 'c/d': 3, 'c/e': 4}
    """
    return {sep.join(keys): value for keys, value in flatten(nested).items()}


def unflatten_split(
    flattened: Mapping[str, V], sep: str = ".", recursive: bool = False
) -> PossiblyNestedDict[str, V]:
    """Unflatten a dict into a possibly nested dict. Keys are split using `sep`.

    >>> unflatten_split({'a.b': 2, 'a.c': 3, 'c.d': 3, 'c.e': 4})
    {'a': {'b': 2, 'c': 3}, 'c': {'d': 3, 'e': 4}}

    >>> unflatten_split({'a': 2, 'b.c': 3})
    {'a': 2, 'b': {'c': 3}}

    NOTE: This function expects the input to be flat. It does *not* unflatten nested dicts:
    >>> unflatten_split({"a": {"b.c": 2}})
    {'a': {'b.c': 2}}
    """
    return unflatten({tuple(key.split(sep)): value for key, value in flattened.items()})


@overload
def getitem_recursive(d: PossiblyNestedDict[K, V], keys: Iterable[K]) -> V:
    ...


@overload
def getitem_recursive(d: PossiblyNestedDict[K, V], keys: Iterable[K], default: T) -> V | T:
    ...


def getitem_recursive(
    d: PossiblyNestedDict[K, V], keys: Iterable[K], default: T | _MISSING_TYPE = MISSING
) -> V | T:
    if default is not MISSING:
        return flatten(d).get(tuple(keys), default)
    return flatten(d)[tuple(keys)]


def all_subclasses(t: type[T]) -> set[type[T]]:
    immediate_subclasses = t.__subclasses__()
    return set(immediate_subclasses).union(*[all_subclasses(s) for s in immediate_subclasses])


if __name__ == "__main__":
    import doctest

    doctest.testmod()
