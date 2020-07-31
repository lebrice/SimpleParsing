import copy
import inspect
import json
import warnings
from collections import OrderedDict
from dataclasses import MISSING, Field, asdict, dataclass, fields, is_dataclass
from functools import singledispatch
from pathlib import Path
from typing import *
from typing import IO, TypeVar

import typing_inspect as tpi

from ...logging_utils import get_logger
from ...utils import get_type_arguments, is_dict, is_list, is_union
from .decoding import (_decoding_fns, decode_field, get_decoding_fn,
                       register_decoding_fn)
from .encoding import SimpleJsonEncoder, encode

logger = get_logger(__file__)

Dataclass = TypeVar("Dataclass")
D = TypeVar("D", bound="Serializable")

try:
    import yaml
    def ordered_dict_constructor(loader: yaml.Loader, node: yaml.Node):
        value = loader.construct_sequence(node)
        return OrderedDict(*value)

    def ordered_dict_representer(dumper: yaml.Dumper, instance: OrderedDict) -> yaml.Node:
        node = dumper.represent_sequence("OrderedDict", instance.items())
        return node

    yaml.add_representer(OrderedDict, ordered_dict_representer)
    yaml.add_constructor("OrderedDict", ordered_dict_constructor)
    yaml.add_constructor("tag:yaml.org,2002:python/object/apply:collections.OrderedDict", ordered_dict_constructor)

except ImportError:
    pass


@dataclass
class Serializable:
    """Makes a dataclass serializable to and from dictionaries.

    Supports JSON and YAML files for now.

    >>> from dataclasses import dataclass
    >>> from simple_parsing.helpers import Serializable
    >>> @dataclass
    ... class Config(Serializable):
    ...   a: int = 123
    ...   b: str = "456"
    ... 
    >>> config = Config()
    >>> config
    Config(a=123, b='456')
    >>> config.to_dict()
    {"a": 123, "b": 456}
    >>> config_ = Config.from_dict({"a": 123, "b": 456})
    Config(a=123, b='456')
    >>> assert config == config_
    """
    subclasses: ClassVar[List[Type[D]]] = []
    decode_into_subclasses: ClassVar[bool] = False

    def __init_subclass__(cls, decode_into_subclasses: bool=None, add_variants: bool=True):
        logger.debug(f"Registering a new Serializable subclass: {cls}")
        super().__init_subclass__()
        if decode_into_subclasses is None:
            # if decode_into_subclasses is None, we will use the value of the
            # parent class, if it is also a subclass of Serializable.
            # Skip the class itself as well as object.
            parents = cls.mro()[1:-1] 
            logger.debug(f"parents: {parents}")

            for parent in parents:
                if parent in Serializable.subclasses and parent is not Serializable:
                    decode_into_subclasses = parent.decode_into_subclasses
                    logger.debug(f"Parent class {parent} has decode_into_subclasses = {decode_into_subclasses}")
                    break

        cls.decode_into_subclasses = decode_into_subclasses or False
        if cls not in Serializable.subclasses:
            Serializable.subclasses.append(cls)

        encode.register(cls, cls.to_dict)
        register_decoding_fn(cls, cls.from_dict)

    def to_dict(self, dict_factory:Type[Dict]=dict, recurse: bool=True) -> Dict:
        """ Serializes this dataclass to a dict.
        
        NOTE: This 'extends' the `asdict()` function from
        the `dataclasses` package, allowing us to not include some fields in the
        dict, or to perform some kind of custom encoding (for instance,
        detaching `Tensor` objects before serializing the dataclass to a dict).
        """
        d: Dict[str, Any] = dict_factory()
        for f in fields(self):
            name = f.name
            value = getattr(self, name)
            T = f.type

            # Do not include in dict if some corresponding flag was set in metadata.
            include_in_dict = f.metadata.get("to_dict", True)
            if not include_in_dict:
                continue

            custom_encoding_fn = f.metadata.get("encoding_fn")
            if custom_encoding_fn:
                # Use a custom encoding function if there is one.
                d[name] = custom_encoding_fn(value)
                continue

            encoding_fn = encode
            if isinstance(value, Serializable) and recurse:
                try:
                    encoded = value.to_dict(dict_factory=dict_factory, recurse=recurse)
                except TypeError as e:
                    encoded = value.to_dict()
                logger.debug(f"Encoded Serializable field {name}: {encoded}")
            else:
                try:
                    encoded = encoding_fn(value)
                except Exception as e:
                    logger.error(f"Unable to encode value {value} of type {type(value)}! Leaving it as-is. (exception: {e})")
                    encoded = value
            d[name] = encoded
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
        if drop_extra_fields is None:
            drop_extra_fields = not cls.decode_into_subclasses
        return from_dict(cls, obj, drop_extra_fields=drop_extra_fields)

    def dump(self, fp: IO[str], dump_fn=json.dump, **kwargs) -> None:
        # Convert `self` into a dict.
        d = self.to_dict()
        # Serialize that dict to the file, using dump_fn.
        dump_fn(d, fp, **kwargs)
    
    def dump_json(self, fp: IO[str], dump_fn=json.dump, **kwargs) -> str:
        return self.dump(fp, dump_fn=dump_fn, **kwargs)

    def dump_yaml(self, fp: IO[str], dump_fn=None, **kwargs) -> str:
        import yaml
        if dump_fn is None:
            dump_fn = yaml.dump
        return self.dump(fp, dump_fn=dump_fn, **kwargs)

    def dumps(self, dump_fn=json.dumps, **kwargs) -> str:
        d = self.to_dict()
        return dump_fn(d, **kwargs)

    def dumps_json(self, dump_fn=json.dumps, **kwargs) -> str:
        kwargs.setdefault("cls", SimpleJsonEncoder)
        return self.dumps(dump_fn=dump_fn, **kwargs)

    def dumps_yaml(self, dump_fn=None, **kwargs) -> str:
        import yaml
        if dump_fn is None:
            dump_fn = yaml.dump
        return self.dumps(dump_fn=dump_fn, **kwargs)

    @classmethod
    def load(cls: Type[D], path: Union[Path, str, IO[str]], drop_extra_fields: bool=None, load_fn=None, **kwargs) -> D:
        """Loads an instance of `cls` from the given file.
        
        Args:
            cls (Type[D]): A dataclass type to load.
            path (Union[Path, str, IO[str]]): Path or Path string or open file.
            drop_extra_fields (bool, optional): Wether to drop extra fields or 
                to decode the dictionary into the first subclass with matching
                fields. Defaults to None, in which case we use the value of
                `cls.decode_into_subclasses`. 
                For more info, see `cls.from_dict`.
            load_fn ([type], optional): Which loading function to use. Defaults
                to None, in which case we try to use the appropriate loading
                function depending on `path.suffix`:
                {
                    ".yml": yaml.full_load,
                    ".yaml": yaml.full_load,
                    ".json": json.load,
                    ".pth": torch.load,
                    ".pkl": pickle.load,
                }

        Raises:
            RuntimeError: If the extension of `path` is unsupported.

        Returns:
            D: An instance of `cls`.
        """
        if isinstance(path, str):
            path = Path(path)

        if load_fn is None and isinstance(path, Path):
            if path.name.endswith((".yml", ".yaml")):
                return cls.load_yaml(path, drop_extra_fields=drop_extra_fields, **kwargs)
            elif path.name.endswith(".json"):
                return cls.load_json(path, drop_extra_fields=drop_extra_fields, **kwargs)
            elif path.name.endswith(".pth"):
                import torch
                load_fn = torch.loads
            elif path.name.endswith(".npy"):
                import numpy as np
                load_fn = np.load
            elif path.name.endswith(".pkl"):
                import pickle
                load_fn = pickle.load
            warnings.warn(RuntimeWarning(
                f"Not sure how to deserialize contents of {path} to a dict, as no "
                f" load_fn was passed explicitly. Will try to use {load_fn} as the "
                f"load function, based on the path name."    
            )) 

        if load_fn is None:
            raise RuntimeError(
                f"Unable to determine what function to use in order to load "
                f"path {path} into a dictionary, since no load_fn was passed, "
                f"and the path doesn't have an unfamiliar extension.."
            )

        if isinstance(path, Path):
            path = path.open()
        return cls._load(path, load_fn=load_fn, drop_extra_fields=drop_extra_fields, **kwargs)

    @classmethod
    def _load(cls: Type[D], fp: IO[str], drop_extra_fields: bool=None, load_fn=json.load, **kwargs) -> D:
        # Load a dict from the file.
        d = load_fn(fp, **kwargs)
        # Convert the dict into an instance of the class.
        return cls.from_dict(d, drop_extra_fields=drop_extra_fields)

    @classmethod
    def load_json(cls: Type[D], path: Union[str, Path], drop_extra_fields: bool=None, load_fn=json.load, **kwargs) -> D:
        """Loads an instance from the corresponding json-formatted file.

        Args:
            cls (Type[D]): A dataclass type to load.
            path (Union[str, Path]): Path to a json-formatted file.
            load_fn ([type], optional): Loading function to use. Defaults to json.load.

        Returns:
            D: an instance of the dataclass.
        """
        return cls.load(path, drop_extra_fields=drop_extra_fields, load_fn=load_fn, **kwargs)

    @classmethod
    def load_yaml(cls: Type[D], path: Union[str, Path], drop_extra_fields: bool=None, load_fn=None, **kwargs) -> D:
        """Loads an instance from the corresponding yaml-formatted file.

        Args:
            cls (Type[D]): A dataclass type to load.
            path (Union[str, Path]): Path to a yaml-formatted file.
            load_fn ([type], optional): Loading function to use. Defaults to
                None, in which case `yaml.full_load` is used.

        Returns:
            D: an instance of the dataclass.
        """
        import yaml
        if load_fn is None:
            load_fn = yaml.full_load
        return cls.load(path, load_fn=load_fn, drop_extra_fields=drop_extra_fields, **kwargs)

    def save(self, path: Union[str, Path], dump_fn=None, **kwargs) -> None:
        if not isinstance(path, Path):
            path = Path(path)

        if dump_fn is None and isinstance(path, Path):
            if path.name.endswith((".yml", ".yaml")):
                return self.save_yaml(path, **kwargs)
            elif path.name.endswith(".json"):
                return self.save_json(path, **kwargs)
            elif path.name.endswith(".pth"):
                import torch
                dump_fn = torch.save
            elif path.name.endswith(".npy"):
                import numpy as np
                dump_fn = np.save
            elif path.name.endswith(".pkl"):
                import pickle
                dump_fn = pickle.dump
            warnings.warn(RuntimeWarning(
                f"Not 100% sure how to deserialize contents of {path} to a "
                f"file as no dump_fn was passed explicitly. Will try to use "
                f"{dump_fn} as the serialization function, based on the path "
                f"suffix. ({path.suffix})" 
            ))

        if dump_fn is None:
            raise RuntimeError(
                f"Unable to determine what function to use in order to dump "
                f"path {path} into a dictionary, since no dump_fn was passed, "
                f"and the path doesn't have an unfamiliar extension: "
                f"({path.suffix})"
            )
        self._save(path, dump_fn=dump_fn, **kwargs)

    def _save(self, path: Union[str, Path], dump_fn=json.dump, **kwargs) -> None:    
        d = self.to_dict()
        logger.debug(f"saving to path {path}")
        with open(path, "w") as fp:
            dump_fn(d, fp, **kwargs)

    def save_yaml(self, path: Union[str, Path], dump_fn=None, **kwargs) -> None:
        import yaml
        if dump_fn is None:
            dump_fn = yaml.dump
        self.save(path, dump_fn=dump_fn, **kwargs)

    def save_json(self, path: Union[str, Path], dump_fn=json.dump, **kwargs) -> None:
        self.save(path, dump_fn=dump_fn, **kwargs)


    @classmethod
    def loads(cls: Type[D], s: str, drop_extra_fields: bool=None, load_fn=json.loads, **kwargs) -> D:
        d = load_fn(s, **kwargs)
        return cls.from_dict(d, drop_extra_fields=drop_extra_fields)

    @classmethod
    def loads_json(cls: Type[D], s: str, drop_extra_fields: bool=None, load_fn=json.loads, **kwargs) -> D:
        return cls.loads(s, drop_extra_fields=drop_extra_fields, load_fn=load_fn, **kwargs)

    @classmethod
    def loads_yaml(cls: Type[D], s: str, drop_extra_fields: bool=None, load_fn=None, **kwargs) -> D:
        import yaml
        if load_fn is None:
            load_fn = yaml.full_load
        return cls.loads(s, drop_extra_fields=drop_extra_fields, load_fn=load_fn, **kwargs)


@dataclass
class SimpleSerializable(Serializable, decode_into_subclasses=True):
    pass


def get_dataclass_type_from_forward_ref(forward_ref: Type, Serializable=Serializable) -> Optional[Type]:
    arg = tpi.get_forward_arg(forward_ref)
    potential_classes: List[Type] = []

    for serializable_class in Serializable.subclasses:
        if serializable_class.__name__ == arg:
            potential_classes.append(serializable_class)

    if not potential_classes:
        logger.warning(
            f"Unable to find a corresponding type for forward ref "
            f"{forward_ref} inside the registered {Serializable} subclasses. "
            f"(Consider adding {Serializable} as a base class to <{arg}>? )."
        )
        return None
    elif len(potential_classes) > 1:
        logger.warning(
            f"More than one potential {Serializable} subclass was found for "
            f"forward ref '{forward_ref}'. The appropriate dataclass will be "
            f"selected based on the matching fields. \n"
            f"Potential classes: {potential_classes}"
        )
        return Serializable
    else:
        assert len(potential_classes) == 1
        return potential_classes[0]


def get_actual_type(field_type: Type) -> Type:
    if is_union(field_type):
        logger.debug(f"field has union type: {field_type}")
        t = get_first_non_None_type(field_type)
        logger.debug(f"First non-none type: {t}")
        if t is not None:
            field_type = t

    if tpi.is_forward_ref(field_type):
        logger.debug(f"field_type {field_type} is a forward ref.")
        dc = get_dataclass_type_from_forward_ref(field_type)
        logger.debug(f"Found the corresponding type: {dc}")
        if dc is not None:
            field_type = dc
    return field_type


def from_dict(cls: Type[Dataclass], d: Dict[str, Any], drop_extra_fields: bool=None) -> Dataclass:
    """Parses an instance of the dataclass `cls` from the dict `d`.

    Args:
        cls (Type[Dataclass]): A `dataclass` type.
        d (Dict[str, Any]): A dictionary of `raw` values, obtained for example
            when deserializing a json file into an instance of class `cls`. 
        drop_extra_fields (bool, optional): Wether or not to drop extra
            dictionary keys (dataclass fields) when encountered. There are three
            options:
            - True:
                The extra keys are dropped, and this function returns an
                instance of `cls`.
            - False:
                The extra keys (if any) are kept, and we search through the
                subclasses of `cls` for the first dataclass which has all the
                required fields. 
            - None (default):
                `drop_extra_fields = not cls.decode_into_subclasses`.

    Raises:
        RuntimeError: If an error is encountered while instantiating the class.

    Returns:
        Dataclass: An instance of the dataclass `cls`.
    """
    if d is None:
        return None
    obj_dict: Dict[str, Any] = d.copy()

    init_args: Dict[str, Any] = {}
    non_init_args: Dict[str, Any] = {}
        
    if drop_extra_fields is None:
        drop_extra_fields = not getattr(cls, "decode_into_subclasses", False)
        logger.debug(f"drop_extra_fields is None. Using cls attribute.")

        if cls is Serializable:
            # Passing `Serializable` means that we want to find the right
            # subclass depending on the keys.
            # We set the value to False when `Serializable` is passed, since
            # we use this mechanism when we don't know which dataclass to use.
            logger.debug(f"cls is `Serializable`, drop_extra_fields = False.")
            drop_extra_fields = False

    logger.debug(f"from_dict for {cls}, drop extra fields: {drop_extra_fields}")

    for field in fields(cls):
        name = field.name
        field_type = field.type
        if name not in obj_dict:
            if field.metadata.get("to_dict", True) and field.default is MISSING and field.default_factory is MISSING:
                logger.warning(
                    f"Couldn't find the field '{name}' in the dict with keys "
                    f"{list(d.keys())}"
                )
            continue

        raw_value = obj_dict.pop(name)
        field_value = decode_field(field, raw_value)

        if field.init:
            init_args[name] = field_value
        else:
            non_init_args[name] = field_value
    
    extra_args = obj_dict
    
    # If there are arguments left over in the dict after taking all fields.
    if extra_args:
        if drop_extra_fields:
            logger.warning(f"Dropping extra args {extra_args}")
            extra_args.clear()
        
        elif issubclass(cls, Serializable):
            # Use the first Serializable derived class that has all the required
            # fields.
            logger.debug(f"Missing field names: {extra_args.keys()}")

            # Find all the "registered" subclasses of `cls`. (from Serializable)
            derived_classes: List[Type[Serializable]] = []
            for subclass in Serializable.subclasses:
                if issubclass(subclass, cls) and subclass is not cls:
                    derived_classes.append(subclass)
            logger.debug(f"All serializable derived classes of {cls} available: {derived_classes}")

            from itertools import chain
            # All the arguments that the dataclass should be able to accept in
            # its 'init'.
            req_init_field_names = set(chain(extra_args, init_args))
            
            # Sort the derived classes by their number of init fields, so that
            # we choose the first one with all the required fields.
            derived_classes.sort(key=lambda dc: len(get_init_fields(dc)))

            for child_class in derived_classes:
                logger.debug(f"child class: {child_class.__name__}, mro: {child_class.mro()}") 
                child_init_fields: Dict[str, Field] = get_init_fields(child_class)
                child_init_field_names = set(child_init_fields.keys())
                
                if child_init_field_names >= req_init_field_names:
                    # `child_class` is the first class with all required fields.
                    logger.debug(f"Using class {child_class} instead of {cls}")
                    return from_dict(child_class, d, drop_extra_fields=False)
    
    init_args.update(extra_args)
    try:
        instance = cls(**init_args)  # type: ignore
    except TypeError as e:
        # raise RuntimeError(f"Couldn't instantiate class {cls} using init args {init_args}.")
        raise RuntimeError(f"Couldn't instantiate class {cls} using init args {init_args.keys()}: {e}")

    for name, value in non_init_args.items():
        logger.debug(f"Setting non-init field '{name}' on the instance.")
        setattr(instance, name, value)
    return instance


def get_key_and_value_types(dict_type: Type[Dict], Serializable=Serializable) -> Tuple[Optional[Type], Optional[Type]]:
    args = get_type_arguments(dict_type)

    if len(args) != 2:
        logger.debug(f"Weird.. the type {dict_type} doesn't have 2 args: {args}")
        return None, None
    K_ = args[0]
    V_ = args[1]
    # Get rid of Unions or ForwardRefs or Optionals
    V_ = get_actual_type(V_)

    logger.debug(f"K_: {K_}, V_: {V_}")
    if isinstance(V_, tuple):
        V_ = get_first_non_None_type(V_)
    elif tpi.is_optional_type(V_):
        logger.debug(f"V_ is optional: {V_}")
        V_ = get_first_non_None_type(V_)
    return K_, V_


def get_list_item_type(list_type: Type[List]) -> Optional[Type]:
    logger.debug(f"list type: {list_type}")
    args = tpi.get_args(list_type)
    logger.debug(f"args = {args}")
    
    if not args:
        return None

    assert isinstance(args, tuple), args
    if isinstance(args[0], tuple):
        args = args[0]
    assert isinstance(args, tuple), args
    logger.debug(f"args tuple: {args}")
    V_ = get_first_non_None_type(args)
    logger.debug(f"item type: {V_}")
    assert V_ is not None
    V_ = get_actual_type(V_)

    assert not isinstance(V_, tuple), V_
    return V_


def get_init_fields(dataclass: Type) -> Dict[str, Field]:
    result: Dict[str, Field] = {}
    for field in fields(dataclass):
        if field.init:
            result[field.name] = field
    return result


def get_first_non_None_type(optional_type: Union[Type, Tuple[Type, ...]]) -> Optional[Type]:
    if not isinstance(optional_type, tuple):
        optional_type = tpi.get_args(optional_type)
    for arg in optional_type:
        if arg is not Union and arg is not type(None):
            logger.debug(f"arg: {arg} is not union? {arg is not Union}")
            logger.debug(f"arg is not type(None)? {arg is not type(None)}")
            return arg
    return None


def is_dataclass_or_optional_dataclass_type(t: Type) -> bool:
    """ Returns wether `t` is a dataclass type or an Optional[<dataclass type>].
    """
    return is_dataclass(t) or (tpi.is_optional_type(t) and
        is_dataclass(tpi.get_args(t)[0])
    )
