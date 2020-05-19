
import dataclasses
import json
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

from ..utils import Dataclass
import os
logger = logging.getLogger(str(Path(__file__).absolute()))

D = TypeVar("D", bound="JsonSerializable")


class SimpleEncoder(json.JSONEncoder):
    def default(self, o: Any):
        return encode(o)


@singledispatch
def encode(obj: Any) -> Union[Dict, List, int, str, bool, None]:
    """ Encodes an object into a json-compatible primitive type.
    
    This is used as the 'default' keyword argument to `json.dumps` and
    `json.dump`, and is called when an object is encountered that `json` doesn't
    know how to serialize. 
    
    To register a type as JsonSerializable, you can just register a custom
    serialization function. (There should be no need to do it for dataclasses, 
    since that is supported by this function), use @encode.register (see the docs for singledispatch).    
    """
    try:
        if is_dataclass(obj):
            d: Dict = dict()
            for field in fields(obj):
                value = getattr(obj, field.name)
                d[field.name] = encode(value) 
            return d
        # elif isinstance(obj, Mapping):
        #     return {
        #         k: encode(val) for k, val in obj.items() 
        #     }
        # elif hasattr(obj, "__dict__"):
        #     return obj.__dict__
        else:
            return obj
    except Exception as e:
        logger.debug(f"Cannot encode object {obj}: {e}")
        raise e

@dataclass
class JsonSerializable:
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
    subclasses: ClassVar[List[Type["JsonSerializable"]]] = []
    
    # decode_into_subclasses: ClassVar[Dict[Type["JsonSerializable"], bool]] = defaultdict(bool)
    decode_into_subclasses: ClassVar[bool] = False

    def __init_subclass__(cls, decode_into_subclasses: bool=None):
        logger.debug(f"Registering a new JsonSerializable subclass: {cls}")
        super().__init_subclass__()
        if decode_into_subclasses is None:
            # if decode_into_subclasses is None, we will use the value of the
            # parent class, if it is also a subclass of JsonSerializable.
            # Skip the class itself as well as object.
            parents = cls.mro()[1:-1] 
            logger.debug(f"parents: {parents}")

            for parent in parents:
                if parent in JsonSerializable.subclasses:
                    assert issubclass(parent, JsonSerializable)
                    decode_into_subclasses = parent.decode_into_subclasses
                    logger.debug(f"Parent class {parent} has decode_into_subclasses = {decode_into_subclasses}")
                    break
        
        cls.decode_into_subclasses = decode_into_subclasses or False
        if cls not in JsonSerializable.subclasses:
            JsonSerializable.subclasses.append(cls)

    def to_dict(self) -> Dict:
        """ Serializes this dataclass to a dict. """
        # NOTE: This is better than using `dataclasses.asdict` when there are 'Tensor' fields, since those don't
        # support the deepcopy protocol.
        return json.loads(json.dumps(self, default=encode))
    
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
        dump_kwargs.setdefault("cls", SimpleEncoder)
        json.dump(self.to_dict(), fp, **dump_kwargs)

    def dumps(self, **dumps_kwargs) -> str:
        dumps_kwargs.setdefault("cls", SimpleEncoder)
        return json.dumps(self, **dumps_kwargs)
    
    @classmethod
    def load(cls: Type[D], fp: IO[str], drop_extra_fields: bool=None, **load_kwargs) -> D:
        return cls.from_dict(json.load(fp, **load_kwargs), drop_extra_fields=drop_extra_fields)
    
    @classmethod
    def loads(cls: Type[D], s: str, drop_extra_fields: bool=None, **loads_kwargs) -> D:
        return cls.from_dict(json.loads(s, **loads_kwargs), drop_extra_fields=drop_extra_fields)

    def save_json(self, path: Union[str, Path], **dump_kwargs) -> None:
        with open(path, "w") as fp:
            self.dump(fp, **dump_kwargs)
    
    @classmethod
    def load_json(cls: Type[D], path: Union[str, Path], **load_kwargs) -> D:
        with open(path) as fp:
            return cls.load(fp, **load_kwargs)


def from_dict(cls: Type[Dataclass], d: Dict[str, Any], drop_extra_fields: bool=None) -> Dataclass:
    d = d.copy()
    non_init_values: Dict[str, Any] = {}

    for field in dataclasses.fields(cls):
        name: str = field.name
        if name not in d:
            logger.debug(f"Couldn't find the field '{name}' inside the dict {d}")
            continue
        if not field.init and field.name in d: 
            logger.debug(f"Field {name} has `init=False`, but is present in the dict.")
            # TODO: Should we set the value on the parsed instance after?
            # Pop the value and keep it inside the 'non_init_values' dict.
            non_init_values[name] = d.pop(name)
            continue

        field_value = d[name]

        if dataclasses.is_dataclass(field.type):
            # nested cls:
            args: Dict = field_value
            nested_instance = from_dict(field.type, args)
            d[field.name] = nested_instance
        
        if is_generic_type(field.type):
            origin = typing_inspect.get_origin(field.type)
            args = typing_inspect.get_args(field.type)
            logger.debug(f"field {field} has origin: {origin}, args: {args}")
            
            if issubclass(origin, (dict, Mapping)):
                # The cls field has a 
                field_value_dict: Dict = field_value
                K_, V_ = get_k_and_v_types(field.type)
                logger.debug(f"Field {name} has a Dict[{K_}, {V_}] annotation.")
                
                if V_ is not None and is_dataclass(V_):
                    # V_ is a cls type, so we recursively parse V_ from v.
                    logger.debug(f"Value is a cls type.")
                    
                    # What we know: The object has a key 'name' that has a type of
                    # Dict[K, <some_dataclass>]. We want to check that all the
                    # values in that dict are either None or dicts themselves.
                    # If they are dicts, then we can parse each object
                    # individually by recursively calling from_dict.
                    
                    # Modify the dict in-place
                    for k, v in field_value_dict.items():
                        if isinstance(v, dict):
                            logger.debug(
                                f"Recursing: Will try to parse the dict at key "
                                f"{k} into an instance of {V_}.")
                            field_value_dict[k] = from_dict(V_, v)
                        else:
                            logger.warning(
                                f"The field '{name}' (which is a dict) has a "
                                f"value of {v} at key {k}, which should have "
                                f"been a dict...\n"
                                f"Returning the value unchanged..")
                    d[name] = field_value_dict
            
            elif issubclass(origin, (list, List)):
                field_value_list: List = field_value
                V_ = get_list_item_type(field.type)

                logger.debug(f"Field has a List[{V_}] annotation.")
                if V_ is not None and is_dataclass(V_):
                    logger.debug(f"Value is a cls type.")
                    # Modify the list in-place.
                    for i, dict_in_list in enumerate(field_value_list):
                        if isinstance(dict_in_list, dict):
                            logger.debug(
                                f"Recursing for field '{name}' which is a List "
                                f"of {V_}, index = {i}")
                            field_value_list[i] = from_dict(V_, dict_in_list) 
                        else:
                            logger.debug(
                                f"The field '{name}' (which is a list of {V_}) "
                                f"has a value of {dict_in_list} at index {i}, "
                                f"which should have been a dict..."
                            )
                    d[name] = field_value_list

    field_names: Set[str] = set(f.name for f in dataclasses.fields(cls))
    
    non_init_field_names: Set[str] = set(non_init_values.keys())
    init_field_names: Set[str] = field_names - non_init_field_names

    logger.debug(f"Init fields: {init_field_names}")
    logger.debug(f"non-init fields: {non_init_field_names}")
    
    object_keys: Set[str] = set(d.keys())
    # If there are object keys that aren't init fields
    if object_keys > init_field_names:
        if drop_extra_fields:
            extra_keys: List[str] = []
            for key, value in d.items():
                if key not in init_field_names:
                    extra_keys.append(key)
            for k in extra_keys:
                v = d.pop(k)
                logger.warning(f"Dropped key {key} that had a value of {v}")
        else:
            # TODO: Use the first JsonSerializable derived class that has all the required fields.

            logger.debug(f"The field names and object keys dont match: {field_names} != {object_keys}")  
            missing_field_names: Set[str] = object_keys.difference(field_names)
            logger.debug(f"Missing field names: {missing_field_names}")  

            derived_classes: List[Type[JsonSerializable]] = []
            # Find all the "registered" subclasses of `cls`.
            for subclass in JsonSerializable.subclasses:
                if issubclass(subclass, cls) and subclass is not cls:
                    derived_classes.append(subclass)
            logger.debug(f"All JsonSerializable derived classes of {cls} available: {derived_classes}")

            # Sort the derived classes by how closely they are related to the parent class
            for child_class in derived_classes:
                logger.debug(child_class.__name__, child_class.mro()) 
                field_names = set(f.name for f in dataclasses.fields(child_class))
                if object_keys <= field_names:
                    logger.debug(f"Using child class {child_class} instead of {cls}, since it has all the required fields.")
                    cls = child_class
                    break
    try:
        return cls(**d)  # type: ignore
    except TypeError as e:
        warnings.warn(f"Unable to parse a dataclass of type {cls} from given dict with keys {d.keys()}: {e}")
        return d

def get_k_and_v_types(dict_type: Type[Dict]) -> Tuple[Optional[Type], Optional[Type]]:
    args = get_args(dict_type)
    if len(args) != 2:
        logger.debug(f"Weird.. the type {dict_type} doesn't have 2 args: {args}")
        return None, None
    K_ = args[0]
    V_ = args[1]
    logger.debug(f"K_: {K_}, V_: {V_}")
    if isinstance(V_, tuple):
        V_ = get_first_non_None_type(V_)
    elif typing_inspect.is_optional_type(V_):
        logger.debug(f"V_ is optional: {V_}")
        V_ = get_first_non_None_type(V_)
    return K_, V_


def get_list_item_type(list_type: Type[List]) -> Optional[Type]:
    logger.debug(f"list type: {list_type}")
    args = get_args(list_type)
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

    if typing_inspect.is_optional_type(V_):
        logger.debug(f"item type is still optional!")
        V_ = get_first_non_None_type(V_)
        logger.debug(f"Args (once again..) {V_}")

    assert not isinstance(V_, tuple), V_
    return V_


def get_first_non_None_type(optional_type: Union[Type, Tuple[Type, ...]]) -> Optional[Type]:
    if not isinstance(optional_type, tuple):
        optional_type = get_args(optional_type)
    for arg in optional_type:
        if arg is not Union and arg is not type(None):
            logger.debug(f"arg: {arg} is not union? {arg is not Union} arg is not type(None)? {arg is not type(None)}")
            return arg
    return None


def is_dataclass_or_optional_dataclass_type(t: Type) -> bool:
    """ Returns wether `t` is a dataclass type or an Optional[<dataclass type>].
    """
    return is_dataclass(t) or (is_optional_type(t) and
        is_dataclass(get_args(t)[0])
    )
