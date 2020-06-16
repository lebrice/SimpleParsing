import logging
from dataclasses import asdict, dataclass, fields, is_dataclass, MISSING
from typing import ClassVar, List, Type, TypeVar, Dict, IO, Union, Any
from pathlib import Path
from collections import OrderedDict
import inspect

from .decoding import register_decoding_fn
from .serializable import Serializable, from_dict, D

logger = logging.getLogger(__file__)
import yaml

class YamlSerializable(Serializable):
    """Convenience class, just sets different `load_fn` and `dump_fn` defaults
    for the `dump`, `dumps`, `load`, `loads` methods.

    Requires the pyyaml package.
    """
    def dump(self, fp: IO[str], dump_fn=yaml.dump, **kwargs) -> None:
        dump_fn(self.to_dict(), fp, **kwargs)

    def dumps(self, dump_fn=yaml.dump, **kwargs) -> str:
        return dump_fn(self.to_dict(), **kwargs)

    @classmethod
    def load(cls: Type[D], path: Union[Path, str, IO[str]], drop_extra_fields: bool=None, load_fn=yaml.full_load, **kwargs) -> D:
        return super().load(path, drop_extra_fields=drop_extra_fields, load_fn=load_fn, **kwargs)

    @classmethod
    def loads(cls: Type[D], s: str, drop_extra_fields: bool=None, load_fn=yaml.full_load, **kwargs) -> D:
        return super().loads(s, drop_extra_fields=drop_extra_fields, load_fn=load_fn, **kwargs)

    @classmethod
    def _load(cls: Type[D], fp: IO[str], drop_extra_fields: bool=None, load_fn=yaml.full_load, **kwargs) -> D:
        return super()._load(fp, drop_extra_fields=drop_extra_fields, load_fn=load_fn, **kwargs)