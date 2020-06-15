"""Simple, extendable mechanism for encoding pracitaclly anything to string.

Just register a new encoder for a given type like so:

from simple_parsing.helpers.serialization import encode
import numpy as np
@encode.register
def encode_ndarray(obj: np.ndarray) -> str:
    return obj.tostring()
"""
import json
from functools import singledispatch
from typing import Dict, List, Union, Any, TypeVar, overload, Tuple, Sequence
from dataclasses import is_dataclass, fields
import logging
import copy
Dataclass = TypeVar("Dataclass")

logger = logging.getLogger(__file__)


class SimpleJsonEncoder(json.JSONEncoder):
    def default(self, o: Any):
        return encode(o)

T = TypeVar("T", bound=Union[List, int, str, bool, None])
# @overload
# def encode(obj: Dataclass) -> Dict: ...
# @overload
# def encode(obj: Dict) -> Dict: ...
# @overload
# def encode(obj: List) -> List: ...
# @overload
# def encode(obj: Tuple) -> Tuple: ...
# @overload
# def encode(obj: T) -> T: ...

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
                d[field.name] = encode(value) 
            return d
        else:
            logger.debug(f"Deepcopying object {obj} of type {type(obj)}")
            return copy.deepcopy(obj)
    except Exception as e:
        logger.debug(f"Cannot encode object {obj}: {e}")
        raise e

@encode.register(list)
@encode.register(tuple)
def encode_sequence(obj: Sequence) -> Sequence:
    return type(obj)(map(encode, obj))

@encode.register(dict)
def encode_dict(obj: dict) -> Dict:
    return type(obj)((encode(k), encode(v))
                        for k, v in obj.items())
