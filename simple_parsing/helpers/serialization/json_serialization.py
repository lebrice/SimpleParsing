
import dataclasses
import json
import yaml
import logging
from collections import OrderedDict, defaultdict
from functools import singledispatch
from dataclasses import dataclass, is_dataclass, fields, Field
from pathlib import Path
from typing import *
from typing import IO
import warnings
import typing_inspect
from typing_inspect import is_generic_type, is_optional_type, get_args
from textwrap import shorten
import os
logger = logging.getLogger(__file__)

from .decoding import register_decoding_fn
from .encoding import encode, SimpleJsonEncoder
from .serializable import DictSerializable, from_dict

Dataclass = TypeVar("Dataclass")

D = TypeVar("D", bound="JsonSerializable")
T = TypeVar("T")



@dataclass
class JsonSerializable(DictSerializable, decode_into_subclasses=True):
    """
    Enables reading and writing a Dataclass to a JSON file.

    >>> from dataclasses import dataclass
    >>> from simple_parsing.helpers import JsonSerializable
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

    def dump(self, fp: IO[str], dump_fn=json.dump, **kwargs) -> None:
        kwargs.setdefault("cls", SimpleJsonEncoder)
        dump_fn(self.to_dict(), fp, **kwargs)

    def dumps(self, dump_fn=json.dumps, **kwargs) -> str:
        kwargs.setdefault("cls", SimpleJsonEncoder)
        return dump_fn(self.to_dict(), **kwargs)
    
    @classmethod
    def load(cls: Type[D], fp: Union[Path, str, IO[str]], drop_extra_fields: bool=None, load_fn=json.load, **kwargs) -> D:
        if isinstance(fp, str):
            fp = Path(fp)
        if isinstance(fp, Path):
            fp = fp.open()
        d = load_fn(fp, **kwargs)
        return cls.from_dict(d, drop_extra_fields=drop_extra_fields)

    @classmethod
    def loads(cls: Type[D], s: str, drop_extra_fields: bool=None, load_fn=json.loads, **kwargs) -> D:
        d = load_fn(s, **kwargs)
        return cls.from_dict(d, drop_extra_fields=drop_extra_fields)

    def save_json(self, path: Union[str, Path], **dump_kwargs) -> None:
        with open(path, "w") as fp:
            self.dump(fp, **dump_kwargs)
    
    @classmethod
    def load_json(cls: Type[D], path: Union[str, Path], **load_kwargs) -> D:
        with open(path) as fp:
            return cls.load(fp, **load_kwargs)


@encode.register
def encode_json(obj: JsonSerializable) -> Dict:
    return json.loads(json.dumps(obj))
