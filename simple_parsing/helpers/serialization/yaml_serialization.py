import logging
from dataclasses import asdict, dataclass, fields, is_dataclass, MISSING
from typing import ClassVar, List, Type, TypeVar, Dict, IO, Union, Any
from pathlib import Path
from collections import OrderedDict
import yaml

from .json_serialization import from_dict as from_dict_general
from .decoding import register_decoding_fn

logger = logging.getLogger(__file__)

D = TypeVar("D", bound="YamlSerializable")
Dataclass = TypeVar("Dataclass")


def from_dict(cls: Type[Dataclass], d: Dict[str, Any], drop_extra_fields: bool=None) -> Dataclass:
    return from_dict_general(cls, d, drop_extra_fields=drop_extra_fields, Serializable=YamlSerializable)


def ordered_dict_constructor(loader: yaml.Loader, node: yaml.Node):
    logger.debug(f"node: {node}")
    value = loader.construct_sequence(node)
    logger.debug(f"value: {value}")
    value = list(value)
    logger.debug(f"value list: {value}")
    value = OrderedDict(*value)
    logger.debug(f"value (again): {value}")
    return value

yaml.add_constructor(u"tag:yaml.org,2002:python/object/apply:collections.OrderedDict", ordered_dict_constructor)

@dataclass
class YamlSerializable:
    """
    Enables reading and writing a Dataclass to a yml file.

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
    subclasses: ClassVar[List[Type["YamlSerializable"]]] = []
    
    # decode_into_subclasses: ClassVar[Dict[Type["JsonSerializable"], bool]] = defaultdict(bool)
    decode_into_subclasses: ClassVar[bool] = False

    def __init_subclass__(cls, decode_into_subclasses: bool=None, add_variants: bool=True):
        logger.debug(f"Registering a new YamlSerializable subclass: {cls}")
        super().__init_subclass__()
        if decode_into_subclasses is None:
            # if decode_into_subclasses is None, we will use the value of the
            # parent class, if it is also a subclass of JsonSerializable.
            # Skip the class itself as well as object.
            parents = cls.mro()[1:-1] 
            logger.debug(f"parents: {parents}")

            for parent in parents:
                if parent in YamlSerializable.subclasses and parent is not YamlSerializable:
                    assert issubclass(parent, YamlSerializable)
                    decode_into_subclasses = parent.decode_into_subclasses
                    logger.debug(f"Parent class {parent} has decode_into_subclasses = {decode_into_subclasses}")
                    break
        
        cls.decode_into_subclasses = decode_into_subclasses or False
        if cls not in YamlSerializable.subclasses:
            YamlSerializable.subclasses.append(cls)

        register_decoding_fn(cls, cls.from_dict, add_variants=add_variants)
    
    # @staticmethod
    # def _fix_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    #     new_d: Dict[str, Any] = {}
    #     for k, v in d.items():
    #         if isinstance(v, OrderedDict) and not v:
    #             v = OrderedDict()
    #         elif isinstance(v, Dict):
    #             v = YamlSerializable._fix_dict(v)
    #         new_d[k] = v
    #     return new_d

    def to_dict(self) -> Dict:
        """ Serializes this dataclass to a dict. """
        # NOTE: This is better than using `dataclasses.asdict` when there are 'Tensor' fields, since those don't
        # support the deepcopy protocol.
        d: Dict[str, Any] = asdict(self)
        for f in fields(self):
            name = f.name
            value = getattr(self, name)
            T = f.type

            # TODO: Do not include in dict if some corresponding flag was set in metadata!
            include_in_dict = f.metadata.get("to_dict", True)
            if not include_in_dict:
                d.pop(name)

            d_value = d[name]
            default_value = dataclass
            from typing_inspect import get_origin, is_generic_type
            
            if issubclass(T, YamlSerializable):
                d[name] = value.to_dict()
        return d
    
    @classmethod
    def from_dict(cls: Type[D], obj: Dict, drop_extra_fields: bool=None) -> D:
        """ Parses an instance of `cls` from the given dict.
        
        NOTE: If the `decode_into_subclasses` class attribute is set to True (or
        if `decode_into_subclasses=True` was passed in the class definition),
        then if there are keys in the dict that aren't fields of the dataclass,
        this will decode the dict into an instance the first subclass of `cls`
        which has all required field names present in the dictionary.
        
        Passing `drop_extra_fields=None` (default) will use the class attribute
        described above.
        Passing `drop_extra_fields=True` will decode the dict into an instance
        of `cls` and drop the extra keys in the dict.
        Passing `drop_extra_fields=False` forces the above-mentioned behaviour.
        """
        drop_extra_fields = drop_extra_fields or not cls.decode_into_subclasses
        return from_dict(cls, obj, drop_extra_fields=drop_extra_fields)
    
    def dump(self, fp: IO[str], **dump_kwargs) -> None:
        yaml.dump(self.to_dict(), fp, **dump_kwargs)

    def dumps(self, **dump_kwargs) -> str:
        return yaml.dump(self.to_dict(), **dump_kwargs)
    
    @classmethod
    def load(cls: Type[D], fp: IO[str], drop_extra_fields: bool=None, **load_kwargs) -> D:
        load_kwargs.setdefault("Loader", yaml.FullLoader)
        return cls.from_dict(yaml.load(fp, **load_kwargs), drop_extra_fields=drop_extra_fields)
    
    @classmethod
    def loads(cls: Type[D], s: str, drop_extra_fields: bool=None, **load_kwargs) -> D:
        load_kwargs.setdefault("Loader", yaml.FullLoader)
        return cls.from_dict(yaml.load(s, **load_kwargs), drop_extra_fields=drop_extra_fields)

    def save_yaml(self, path: Union[str, Path], **dump_kwargs) -> None:
        with open(path, "w") as fp:
            self.dump(fp, **dump_kwargs)
    
    @classmethod
    def load_yaml(cls: Type[D], path: Union[str, Path], **load_kwargs) -> D:
        with open(path) as fp:
            return cls.load(fp, **load_kwargs)
