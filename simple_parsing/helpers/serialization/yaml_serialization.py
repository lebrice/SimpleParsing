import logging
from dataclasses import asdict, dataclass, fields, is_dataclass, MISSING
from typing import ClassVar, List, Type, TypeVar, Dict, IO, Union, Any
from pathlib import Path
from collections import OrderedDict
import yaml
import inspect

from .decoding import register_decoding_fn
from .serializable import DictSerializable, from_dict

logger = logging.getLogger(__file__)

D = TypeVar("D", bound="YamlSerializable")
Dataclass = TypeVar("Dataclass")


def ordered_dict_constructor(loader: yaml.Loader, node: yaml.Node):
    logger.info(f"node: {node}")
    value = loader.construct_sequence(node)
    logger.info(f"value: {value}")
    return OrderedDict(value)

def ordered_dict_representer(dumper: yaml.Dumper, instance: OrderedDict) -> yaml.Node:
    node = dumper.represent_sequence("OrderedDict", instance.items())
    # logger.info(f"Represented node: {node}")
    return node

yaml.add_representer(OrderedDict, ordered_dict_representer)
yaml.add_constructor("OrderedDict", ordered_dict_constructor)


@dataclass
class YamlSerializable(DictSerializable):
    """
    Enables reading and writing a Dataclass to a yml file.

    >>> from dataclasses import dataclass
    >>> from simple_parsing.helpers.yaml_serialization import YamlSerializable
    >>> @dataclass
    ... class Config(YamlSerializable):
    ...   a: int = 123
    ...   b: str = "456"
    ... 
    >>> config = Config()
    >>> config
    Config(a=123, b='456')
    >>> config.save("config.yaml")
    >>> config_ = Config.load_yaml("config.yaml")
    >>> config_
    Config(a=123, b='456')
    >>> assert config == config_
    >>> import os; os.remove("config.yaml") # Just cleaning up
    """
    
    def dump(self, fp: IO[str], dump_fn=yaml.dump, **kwargs) -> None:
        dump_fn(self.to_dict(), fp, **kwargs)

    def dumps(self, dump_fn=yaml.dump, **kwargs) -> str:
        return dump_fn(self.to_dict(), **kwargs)
    
    @classmethod
    def load(cls: Type[D], fp: Union[Path, str, IO[str]], drop_extra_fields: bool=None, load_fn=yaml.load, **kwargs) -> D:
        if isinstance(fp, str):
            fp = Path(fp)
        if isinstance(fp, Path):
            fp = fp.open()
        kwargs.setdefault("Loader", yaml.FullLoader)
        d = load_fn(fp, **kwargs)
        return cls.from_dict(d, drop_extra_fields=drop_extra_fields)

    @classmethod
    def loads(cls: Type[D], s: str, drop_extra_fields: bool=None, load_fn=yaml.load, **kwargs) -> D:
        kwargs.setdefault("Loader", yaml.FullLoader)
        d = load_fn(s, **kwargs)
        return cls.from_dict(d, drop_extra_fields=drop_extra_fields)

    def save(self, path: Union[str, Path], **dump_kwargs) -> None:
        with open(path, "w") as fp:
            self.dump(fp, **dump_kwargs)

    def save_yaml(self, path: Union[str, Path], **dump_kwargs) -> None:
        self.save(path)
    
    @classmethod
    def load_yaml(cls: Type[D], path: Union[str, Path], **load_kwargs) -> D:
        return cls.load(path, **load_kwargs)
