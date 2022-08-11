"""Simple, extendable mechanism for encoding pracitaclly anything to string.

Just register a new encoder for a given type like so:

from simple_parsing.helpers.serialization import encode
import numpy as np
@encode.register
def encode_ndarray(obj: np.ndarray) -> str:
    return obj.tostring()
"""
import copy
import json
from argparse import Namespace
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from functools import singledispatch
from logging import getLogger
from os import PathLike
from typing import Any, Dict, Hashable, List, Set, Tuple, Union

logger = getLogger(__name__)


class SimpleJsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        return encode(o)


"""
# NOTE: This code is commented because of static typing check error.
# The problem is incompatibility of mypy and singledispatch.
# See mypy issues for more info:
# https://github.com/python/mypy/issues/8356
# https://github.com/python/mypy/issues/2904
# https://github.com/python/mypy/issues/9112#issuecomment-725316936

class Dataclass(Protocol):
    # see dataclasses.is_dataclass implementation with _FIELDS
    __dataclass_fields__: Dict[str, Field[Any]]


T = TypeVar("T", bool, int, None, str)


@overload
def encode(obj: Dataclass) -> Dict[str, Any]: ...

@overload
def encode(obj: Union[List[Any], Set[Any], Tuple[Any, ...]]) -> List[Any]:
    ...

@overload
def encode(obj: Mapping[Any, Any]) -> Dict[Any, Any]: ...

@overload
def encode(obj: T) -> T: ...
"""


@singledispatch
def encode(obj: Any) -> Any:
    """Encodes an object into a json/yaml-compatible primitive type.

    This called to convert field attributes when calling `to_dict()` on a
    `DictSerializable` instance (including JsonSerializable and YamlSerializable).

    This is used as the 'default' keyword argument to `json.dumps` and
    `json.dump`, and is called when an object is encountered that `json` doesn't
    know how to serialize.

    To register a type as JsonSerializable, you can just register a custom
    serialization function. (There should be no need to do it for dataclasses,
    since that is supported by this function), use @encode.register
    (see the docs for singledispatch).
    """
    try:
        if is_dataclass(obj):
            # logger.debug(f"encoding object {obj} of class {type(obj)}")
            d: Dict[str, Any] = dict()
            for field in fields(obj):
                value = getattr(obj, field.name)
                try:
                    d[field.name] = encode(value)
                except TypeError as e:
                    logger.error(f"Unable to encode field {field.name}: {e}")
                    raise e
            return d
        else:
            # logger.debug(f"Deepcopying object {obj} of type {type(obj)}")
            return copy.deepcopy(obj)
    except Exception as e:
        logger.debug(f"Cannot encode object {obj}: {e}")
        raise e


@encode.register(list)
@encode.register(tuple)
# @encode.register(Sequence) # Would also encompass `str!`
@encode.register(set)
def encode_list(obj: Union[List[Any], Set[Any], Tuple[Any, ...]]) -> List[Any]:
    # TODO: Here we basically say "Encode all these types as lists before serializing"
    # That's ok for JSON, but YAML can serialize stuff directly though.
    # TODO: Also, with this, we also need to convert back to the right type when
    # deserializing, which is totally doable for the fields of dataclasses,
    # but maybe not for other stuff.
    return list(map(encode, obj))


@encode.register(Mapping)
def encode_dict(obj: Mapping) -> Dict[Any, Any]:
    constructor = type(obj)
    result = constructor()
    for k, v in obj.items():
        k_ = encode(k)
        v_ = encode(v)
        if isinstance(k_, Hashable):
            result[k_] = v_
        else:
            # If the encoded key isn't "Hashable", then we store it as a list of tuples
            if isinstance(result, dict):
                result = list(result.items())
            result.append((k_, v_))
    return result

    return type(obj)((encode(k), encode(v)) for k, v in obj.items())


@encode.register(PathLike)
def encode_path(obj: PathLike) -> str:
    return obj.__fspath__()


@encode.register(Namespace)
def encode_namespace(obj: Namespace) -> Any:
    return encode(vars(obj))


@encode.register(Enum)
def encode_enum(obj: Enum) -> str:
    return obj.name
