""" Collection of helper classes and functions to reduce boilerplate code. """
import dataclasses
import functools
import json
import warnings
from dataclasses import _MISSING_TYPE, MISSING
from typing import (Any, Callable, Dict, Iterable, List, Optional, Set, Tuple,
                    Type, Union)

from .utils import Dataclass, K, SimpleValueType, T, V


def field(default: Union[T, _MISSING_TYPE] = MISSING,
          alias: Optional[Union[str, List[str]]] = None,
          *,
          default_factory: Union[Callable[[], T], _MISSING_TYPE] = MISSING,
          init: bool = True,
          repr: bool = True,
          hash: Optional[bool] = None,
          compare: bool = True,
          metadata: Optional[Dict[str, Any]] = None,
          **custom_argparse_args: Any) -> T:
    """Calls the `dataclasses.field` function, and leftover arguments are fed
    directly to the `ArgumentParser.add_argument(*option_strings, **kwargs)`
    method.

    Parameters
    ----------
    alias : Union[str, List[str]], optional
        Additional option_strings to pass to the `add_argument` method, by
        default None
    default : Union[T, _MISSING_TYPE], optional
        The default field value (same as in `dataclasses.field`), by default MISSING
    default_factory : Union[Callable[[], T], _MISSING_TYPE], optional
        (same as in `dataclasses.field`), by default None
    init : bool, optional
        (same as in `dataclasses.field`), by default True
    repr : bool, optional
        (same as in `dataclasses.field`), by default True
    hash : bool, optional
        (same as in `dataclasses.field`), by default None
    compare : bool, optional
        (same as in `dataclasses.field`), by default True
    metadata : Dict[str, Any], optional
        (same as in `dataclasses.field`), by default None

    Returns
    -------
    T
        The value returned by the `dataclasses.field` function.
    """
    _metadata: Dict[str, Any] = metadata if metadata is not None else {}
    if alias:
        _metadata.update({
            "alias": alias if isinstance(alias, list) else [alias]
        })
    if custom_argparse_args:
        _metadata.update({"custom_args": custom_argparse_args})
        
        action = custom_argparse_args.get("action")

        if action == "store_false":
            if default not in {MISSING, True}:
                raise RuntimeError("default should either not be passed or set "
                                   "to True when using the store_false action.")
            default = True  # type: ignore
        
        elif action == "store_true":
            if default not in {MISSING, False}:
                raise RuntimeError("default should either not be passed or set "
                                   "to False when using the store_true action.")
            default = False  # type: ignore

    if default is not MISSING:
        return dataclasses.field(  # type: ignore
            default=default,
            init=init,
            repr=repr,
            hash=hash,
            compare=compare,
            metadata=_metadata
        )
    else:
        return dataclasses.field(  # type: ignore
            default_factory=default_factory,
            init=init,
            repr=repr,
            hash=hash,
            compare=compare,
            metadata=_metadata
        )


def choice(*choices: T, default: T = None, **kwargs: Any) -> T:
    """ Makes a regular attribute, whose value, when parsed from the 
    command-line, can only be one contained in `choices`, with a default value 
    of `default`.

    Returns a regular `dataclasses.field()`, but with metadata which indicates  
    the allowed values.

    Args:
        default (T, optional): The default value of the field. Defaults to None,
        in which case the command-line argument is required.

    Raises:
        ValueError: If the default value isn't part of the given choices.

    Returns:
        T: the result of the usual `dataclasses.field()` function (a dataclass field/attribute).
    """
    if default is not None and default not in choices:
        raise ValueError(
            f"Default value of {default} is not a valid option! (options: {choices})")
    return field(default=default, choices=choices, **kwargs)  # type: ignore


def list_field(*default_items: SimpleValueType, **kwargs) -> List[T]:
    """shorthand function for setting a `list` attribute on a dataclass,
    so that every instance of the dataclass doesn't share the same list.

    Accepts any of the arguments of the `dataclasses.field` function.

    Returns:
        List[T]: a `dataclasses.field` of type `list`, containing the `default_items`. 
    """
    default = kwargs.pop("default", None)
    if isinstance(default, list):
        # can't have that. field wants a default_factory.
        # we just give back a copy of the list as a default factory,
        # but this should be discouraged.
        from copy import deepcopy
        kwargs["default_factory"] = lambda: deepcopy(default)
    return mutable_field(list, default_items, **kwargs)


def dict_field(default_items: Union[Dict[K, V], Iterable[Tuple[K, V]]]=None, **kwargs) -> Dict[K, V]:
    """shorthand function for setting a `dict` attribute on a dataclass,
    so that every instance of the dataclass doesn't share the same `dict`.

    NOTE: Do not use keyword arguments as you usually would with a dictionary
    (as in something like `dict_field(a=1, b=2, c=3)`). Instead pass in a
    dictionary instance with the items: `dict_field(dict(a=1, b=2, c=3))`.
    The reason for this is that the keyword arguments are interpreted as custom
    argparse arguments, rather than arguments of the `dict` function!) 

    Also accepts any of the arguments of the `dataclasses.field` function.

    Returns:
        Dict[K, V]: a `dataclasses.Field` of type `Dict[K, V]`, containing the `default_items`. 
    """
    if default_items is None:
        default_items = {}
    elif isinstance(default_items, dict):
        default_items = default_items.items()
    return mutable_field(dict, default_items, **kwargs)


def set_field(*default_items: T, **kwargs) -> Set[T]:
    return mutable_field(set, default_items, **kwargs)


def mutable_field(_type: Type[T], *args, init: bool = True, repr: bool = True, hash: bool = None, compare: bool = True, metadata: Dict[str, Any] = None, **kwargs) -> T:
    # TODO: Check wether some of the keyword arguments are destined for the `field` function, or for the partial?    
    default_factory = kwargs.pop("default_factory", functools.partial(_type, *args))
    return field(default_factory=default_factory, init=init, repr=repr, hash=hash, compare=compare, metadata=metadata, **kwargs)


MutableField = mutable_field


def subparsers(subcommands: Dict[str, Type], default=None) -> Any:
    if default is not None and default not in subcommands:
        raise ValueError(
            f"Default value of {default} is not a valid subparser! (subcommand: {subcommands})")
    return field(default=default, metadata={
        "subparsers": subcommands,
        "default": default,
    })


def from_dict(dataclass: Type[Dataclass], d: Dict[str, Any]) -> Dataclass:
    for field in dataclasses.fields(dataclass):
        if dataclasses.is_dataclass(field.type):
            # nested dataclass:
            args_dict = d[field.name]
            nested_instance = from_dict(field.type, args_dict)
            d[field.name] = nested_instance
    return dataclass(**d)  # type: ignore


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

    def save_json(self, path: str):
        with open(path, "w") as f:
            dict_ = dataclasses.asdict(self)
            json.dump(dict_, f, indent=1)

    @classmethod
    def load_json(cls, path: str):
        with open(path) as f:
            args_dict = json.load(f)
        return from_dict(cls, args_dict)



class FlattenedAccess:
    """ Allows flattened access to the attributes of all children dataclasses.

    This is meant to simplify the adoption of dataclasses for argument hierarchies,
    rather than a single-level dictionary.
    Dataclasses allow for easy, neatly separated arguments, but suffer from 2 potential drawbacks:
    - When using a highly nested structure, having long accesses is annoying
    - The dictionary access syntax is often more natural than using getattr()
        when reading an attribute whose name is a variable.
    """
    
    def attributes(self,
                   recursive: bool=True,
                   prefix: str="") -> Iterable[Tuple[str, Any]]:
        """Returns an Iterator over the attributes of the dataclass.
        
        [extended_summary]
        
        Parameters
        ----------
        - dataclass : Dataclass
        
            A dataclass type or instance.
        - recursive : bool, optional, by default True
        
            Wether or not to recurse and yield all the elements of the children
            dataclass attributes.
        - prefix : str, optional, by default ""
        
            A prefix to prepend to all the attribute names before yielding them.
        
        Returns
        -------
        Iterable[Tuple[str, Any]]
            An iterable of attribute names and values.
        
        Yields
        -------
        Iterable[Tuple[str, Any]]
            A Tuple of the form <Attribute name, attribute_value>.
        """
        for field in dataclasses.fields(self):
            if field.name not in self.__dict__:
                # the dataclass isn't yet instantiated, or the attr was deleted.
                continue
            # get the field value (without needless recursion)
            field_value = self.__dict__[field.name]
            
            yield prefix + field.name, field_value
            if recursive and dataclasses.is_dataclass(field_value):
                yield from FlattenedAccess.attributes(
                    field_value,
                    recursive=True,
                    prefix=prefix + field.name + "."
                )

    def __getattr__(self, name: str):
        """Retrieves the attribute on self, or recursively on the children.
        
        NOTE: `__getattribute__` is always called before `__getattr__`, hence we
        always get here because `self` does not have an attribute of `name`.
        """
        # potential parents and corresponding values.
        parents: List[str] = []
        values: List[Any] = []

        for attr_name, attr_value in FlattenedAccess.attributes(self):
            # if the attribute name's last part ends with `name`, we add it to
            # some list of potential parent attributes.
            name_parts = name.split(".")
            dest_parts = attr_name.split(".")
            if dest_parts[-len(name_parts):] == name_parts:
                parents.append(attr_name)
                values.append(attr_value)
        
        if not parents:
            raise AttributeError(
                f"{type(self)} object has no attribute '{name}', "
                "and neither does any of its children attributes."
            )
        elif len(parents) > 1:
            raise AttributeError(
                f"Ambiguous Attribute access: name '{name}' may refer to:\n" + 
                "\n".join(f"- '{parent}' (with a value of: '{value}')"
                    for parent, value in zip(parents, values)
                )
            )
        else:
            return values[0]

    def __setattr__(self, name: str, value: Any):
        """Write the attribute in self or in the children that has it.

        If more than one child has attributes that match the given one, an
        `AttributeError` is raised. 
        """
        # potential parents and corresponding values.
        parents: List[str] = []
        values: List[Any] = []

        field_names = {field.name for field in dataclasses.fields(self)}
        if name in field_names:
            object.__setattr__(self, name, value)
            return

        for attr_name, attr_value in self.attributes():
            # if the attribute name of the attribute ends with `name`, we add it
            # to some list of potential parent attributes.
            name_parts = name.split(".")
            dest_parts = attr_name.split(".")
            if dest_parts[-len(name_parts):] == name_parts:
                parents.append(attr_name)
                values.append(attr_value)
        
        if not parents:
            # We set the value on the dataclass directly, since it wasn't found.
            warnings.warn(UserWarning(f"Setting a new attribute '{name}' on the"
                f" dataclass, but it does not have a field of the same name. \n"
                f"(Consider adding a field '{name}' of type {type(value)} to "
                f"{type(self)})"))            
            object.__setattr__(self, name, value)

        elif len(parents) > 1:
            # more than one parent (ambiguous).
            raise AttributeError(
                f"Ambiguous Attribute access: name '{name}' may refer to:\n" + 
                "\n".join(f"- '{parent}' (with a value of: '{value}')"
                    for parent, value in zip(parents, values)
                )
            )
        else:
            # We recursively set the attribute.
            attr_name = parents[0]
            lineage = attr_name.split(".")[:-1]
            parent: object = self
            for parent_name in lineage:
                # NOTE: we can't use getattr, otherwise we would recurse.
                parent = object.__getattribute__(parent, parent_name)
            # destination attribute name
            dest_name = name.split(".")[-1]   
            # Set the attribute on the parent.
            object.__setattr__(parent, dest_name, value) 

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)
    
    def asdict(self) -> Dict:
        return dataclasses.asdict(self)
