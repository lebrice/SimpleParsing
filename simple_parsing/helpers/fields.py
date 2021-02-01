""" Utility functions that simplify defining field of dataclasses. 
"""
import argparse
import dataclasses
import enum
import functools
import inspect
import json
import warnings
from collections import OrderedDict
from dataclasses import _MISSING_TYPE, MISSING
from enum import Enum
from typing import (Any, Callable, Dict, Iterable, List, Optional, Set, Tuple,
                    Type, TypeVar, Union, overload)

from simple_parsing.utils import (Dataclass, SimpleValueType,
                                  get_type_arguments, is_optional, is_tuple,
                                  is_union, str2bool)

from ..logging_utils import get_logger

logger = get_logger(__file__)

E = TypeVar("E", bound=Enum)
K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")


def field(default: Union[T, _MISSING_TYPE] = MISSING,
          alias: Optional[Union[str, List[str]]] = None,
          cmd: bool = True,
          *,
          to_dict: bool=True,
          encoding_fn: Callable[[T], Any]=None,
          decoding_fn: Callable[[Any], T]=None,
          # dataclasses.field arguments
          default_factory: Union[Callable[[], T], _MISSING_TYPE] = MISSING,
          init: bool = True,
          repr: bool = True,
          hash: Optional[bool] = None,
          compare: bool = True,
          metadata: Optional[Dict[str, Any]] = None,
          **custom_argparse_args: Any) -> T:
    """Extension of the `dataclasses.field` function.
    
    Adds the ability to customize how this field's command-line options are
    created, as well as how it is serialized / deseralized (if the containing 
    dataclass inherits from `simple_parsing.Serializable`.

    Leftover arguments are fed directly to the
    `ArgumentParser.add_argument(*option_strings, **kwargs)` method.

    Parameters
    ----------
    default : Union[T, _MISSING_TYPE], optional
        The default field value (same as in `dataclasses.field`), by default MISSING
    alias : Union[str, List[str]], optional
        Additional option_strings to pass to the `add_argument` method, by
        default None. When passing strings which do not start by "-" or "--", 
        will be prefixed with "-" if the string is one character and by "--"
        otherwise.
    cmd: bool, optional
        Wether to add command-line arguments for this field or not. Defaults to
        True.
    
    ## Serialization-related Keyword Arguments:

    to_dict : bool
        Wether to include this field in the dictionary when calling `to_dict()`.
        Defaults to True.
        Only has an effect when the dataclass containing this field is
        `Serializable`.
    encoding_fn : Callable[[T], Any], optional
        Function to apply to this field's value when encoding the dataclass to a
        dict. Only has an effect when the dataclass containing this field is
        `Serializable`.
    decoding_fn : Callable[[Any], T]. optional
        Function to use in order to recover a the value of this field from a
        serialized entry in a dictionary (inside `cls.from_dict`).
        Only has an effect when the dataclass containing this field is
        `Serializable`.
    
    ## Keyword Arguments of `dataclasses.field`

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
        _metadata["alias"] = alias if isinstance(alias, list) else [alias]
    _metadata.update(dict(to_dict=to_dict))
    if encoding_fn is not None:
        _metadata.update(dict(encoding_fn=encoding_fn))
    if decoding_fn is not None:
        _metadata.update(dict(decoding_fn=decoding_fn))
    _metadata["cmd"] = cmd

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
    elif not isinstance(default_factory, dataclasses._MISSING_TYPE):
        return dataclasses.field(
            default_factory=default_factory,
            init=init,
            repr=repr,
            hash=hash,
            compare=compare,
            metadata=_metadata
        )
    else:
        return dataclasses.field(
            init=init,
            repr=repr,
            hash=hash,
            compare=compare,
            metadata=_metadata
        )


@overload
def choice(*choices: T, default: T=None, **kwargs) -> T:
    pass

@overload
def choice(choices: Type[E], default: E, **kwargs) -> E:
    pass

@overload
def choice(choices: Dict[K, V], default: K, **kwargs) -> V:
    pass

def choice(*choices: T, default: T = None, **kwargs: Any) -> T:
    """ Makes a field which can be chosen from the set of choices from the
    command-line.

    Returns a regular `dataclasses.field()`, but with metadata which indicates  
    the allowed values.

    (New:) If `choices` is a dictionary, then passing the 'key' will result in
    the corresponding value being used. The values may be objects, for example.
    Similarly for Enum types, passing a type of enum will  

    Args:
        default (T, optional): The default value of the field. Defaults to None,
        in which case the command-line argument is required.

    Raises:
        ValueError: If the default value isn't part of the given choices.

    Returns:
        T: the result of the usual `dataclasses.field()` function (a dataclass field/attribute).
    """
    assert len(choices) > 0, "Choice requires at least one positional argument!"

    if len(choices) == 1:
        choices = choices[0]
        if inspect.isclass(choices) and issubclass(choices, Enum):
            # If given an enum, construct a mapping from names to values.
            choice_enum: Type[Enum] = choices
            choices = OrderedDict(
                (e.name, e) for e in choice_enum
            )
            if default is not None and not isinstance(default, choice_enum):
                if default in choices:
                    warnings.warn(UserWarning(
                        f"Setting default={default} could perhaps be ambiguous "
                        f"(enum names vs enum values). Consider using the enum "
                        f"value {choices[default]} instead."
                    ))
                    default = choices[default]
                else:
                    raise ValueError(f"'default' arg should be of type {choice_enum}, but got {default}")

        if isinstance(choices, dict):
            # if the choices is a dict, the options are the keys
            # save the info about the choice_dict in the field metadata.
            metadata = kwargs.setdefault("metadata", {})
            choice_dict = choices
            # save the choice_dict in metadata so that we can recover the values in postprocessing.
            metadata["choice_dict"] = choice_dict
            choices = list(choice_dict.keys())
        
            # TODO: If the choice dict is given, then add encoding/decoding functions that just
            # get/set the right key.
            def _encoding_fn(value: Any) -> str:
                """ Custom encoding function that will simply represent the value as the
                the key in the dict rather than the value itself.
                """
                if value in choice_dict.keys():
                    return value
                elif value in choice_dict.values():
                    return [k for k, v in choice_dict.items() if v == value][0]
                return value        
            kwargs.setdefault("encoding_fn", _encoding_fn)
            
            def _decoding_fn(value: Any) -> str:
                """ Custom decoding function that will retrieve the value from the
                stored key in the dictionary.
                """
                return choice_dict.get(value, value)
    
            kwargs.setdefault("decoding_fn", _decoding_fn)

            
    return field(
        default=default,
        choices=choices,
        **kwargs
    )


def list_field(*default_items: T, **kwargs) -> List[T]:
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


def subparsers(subcommands: Dict[str, Type[Dataclass]], **kwargs) -> Any:
    return field(metadata={
        "subparsers": subcommands,
    }, **kwargs)


def flag(default: bool, **kwargs):
    """ Creates a boolean field with a default value of `default` and nargs='?'.
    """
    action = "store_true" if default is False else "store_false"
    return field(default=default, nargs="?", action=action, type=str2bool, **kwargs)
