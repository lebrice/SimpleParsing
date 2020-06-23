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
from dataclasses import fields, is_dataclass
from functools import singledispatch
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple, TypeVar, Union, overload

from ...logging_utils import get_logger

Dataclass = TypeVar("Dataclass")

logger = get_logger(__file__)


class SimpleJsonEncoder(json.JSONEncoder):
    def default(self, o: Any):
        return encode(o)

T = TypeVar("T", bound=Union[List, int, str, bool, None])
@overload
def encode(obj: Dataclass) -> Dict: ...
@overload
def encode(obj: Dict) -> Dict: ...
@overload
def encode(obj: List) -> List: ...
@overload
def encode(obj: Tuple) -> Tuple: ...
@overload
def encode(obj: T) -> T: ...

@singledispatch
def encode(obj: Any) -> Union[Dict, List, int, str, bool, None]:
    """ Encodes an object into a json/yaml-compatible primitive type.

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
            logger.debug(f"encoding object {obj} of class {type(obj)}")
            d: Dict = dict()
            for field in fields(obj):
                value = getattr(obj, field.name)
                try:
                    d[field.name] = encode(value) 
                except TypeError as e:
                    logger.error(f"Unable to encode field {field.name}: {e}")
                    raise e
            return d
        else:
            logger.debug(f"Deepcopying object {obj} of type {type(obj)}")
            return copy.deepcopy(obj)
    except Exception as e:
        logger.debug(f"Cannot encode object {obj}: {e}")
        raise e

@encode.register(list)
def encode_list(obj: List) -> Sequence:
    return list(map(encode, obj))

@encode.register(tuple)
def encode_tuple(obj: List) -> Sequence:
    return tuple(map(encode, obj))

@encode.register(dict)
def encode_dict(obj: dict) -> Dict:
    return type(obj)((encode(k), encode(v))
                        for k, v in obj.items())

@encode.register(Path)
def encode_using_str(obj: Any) -> str:
    return str(obj)
