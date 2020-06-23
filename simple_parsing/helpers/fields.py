""" Utility functions that simplify defining field of dataclasses. 
"""
import argparse
import dataclasses
import functools
import json
import warnings
from dataclasses import _MISSING_TYPE, MISSING
from typing import (Any, Callable, Dict, Iterable, List, Optional, Set, Tuple,
                    Type, Union, overload)

from simple_parsing.utils import (Dataclass, K, SimpleValueType, T, V,
                                  get_type_arguments, is_union)

from ..logging_utils import get_logger

logger = get_logger(__file__)

def field(default: Union[T, _MISSING_TYPE] = MISSING,
          alias: Optional[Union[str, List[str]]] = None,
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
    """Calls the `dataclasses.field` function, and leftover arguments are fed
    directly to the `ArgumentParser.add_argument(*option_strings, **kwargs)`
    method.

    Parameters
    ----------
    default : Union[T, _MISSING_TYPE], optional
        The default field value (same as in `dataclasses.field`), by default MISSING
    alias : Union[str, List[str]], optional
        Additional option_strings to pass to the `add_argument` method, by
        default None. When passing strings which do not start by "-" or "--", 
        will be prefixed with "-" if the string is one character and by "--"
        otherwise.
    
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


def choice(*choices: T, default: T = None, **kwargs: Any) -> T:
    """ Makes a regular attribute, whose value, when parsed from the 
    command-line, can only be one contained in `choices`, with a default value 
    of `default`.

    Returns a regular `dataclasses.field()`, but with metadata which indicates  
    the allowed values.

    (New:) If `choices` is a dictionary, then passing the 'key' will result in
    the corresponding value being used. The values may be objects, for example.

    Args:
        default (T, optional): The default value of the field. Defaults to None,
        in which case the command-line argument is required.

    Raises:
        ValueError: If the default value isn't part of the given choices.

    Returns:
        T: the result of the usual `dataclasses.field()` function (a dataclass field/attribute).
    """
    assert len(choices) > 0, "Choice requires at least one positional argument!"
    if isinstance(choices[0], dict):
        if len(choices) > 1:
            raise ValueError(f"'choices' should be either a list of values or "
                             f"a single dictionary. (Received {choices})")
        choice_dict = choices[0]

        # if the choices is a dict, the options are the keys
        choices = tuple(choice_dict.keys())

        # save the info about the choice_dict in the field metadata.
        metadata = kwargs.setdefault("metadata", {})
        metadata["choice_dict"] = choice_dict
        if default is not None and default in choice_dict:
            return field(default_factory=functools.partial(choice_dict.get, default), choices=choices, **kwargs)  # type: ignore


    if default is not None and default not in choices:
        raise ValueError(f"Default value of {default} is not a valid option! "
                         f"(options: {choices})")
    
    return field(default=default, choices=choices, **kwargs)  # type: ignore



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


class SimpleHelpFormatter(argparse.ArgumentDefaultsHelpFormatter,
                          argparse.MetavarTypeHelpFormatter,
                          argparse.RawDescriptionHelpFormatter):
    """Little shorthand for using some useful HelpFormatters from argparse.
    
    This class inherits from argparse's `ArgumentDefaultHelpFormatter`,
    `MetavarTypeHelpFormatter` and `RawDescriptionHelpFormatter` classes.

    This produces the following resulting actions:
    - adds a "(default: xyz)" for each argument with a default
    - uses the name of the argument type as the metavar. For example, gives
      "-n int" instead of "-n N" in the usage and description of the arguments.
    - Conserves the formatting of the class and argument docstrings, if given.
    """

    def _get_default_metavar_for_optional(self, action):
        try:
            return super()._get_default_metavar_for_optional(action)
        except:
            return self._get_metavar_for_type(action.type, optional=True)


    def _get_default_metavar_for_positional(self, action):
        try:
            return super()._get_default_metavar_for_positional(action)
        except:
            return self._get_metavar_for_type(action.type, optional=False)

    def _get_metavar_for_type(self, t: Type, optional: bool=False) -> str:
        if hasattr(t, "__name__"):
            return t.__name__
        elif is_union(t):
            type_args = list(get_type_arguments(t))
            
            none_type = type(None)
            while none_type in type_args:  # type: ignore
                type_args.remove(none_type)  # type: ignore
            
            string = ""
            if optional:
                string += "["
            middle = []
            for t_ in type_args:
                middle.append(self._get_metavar_for_type(t_, optional=optional))
            string += "|".join(middle)
            if optional:
                string += "]"
            return string
        else:
            return str(t)

Formatter = SimpleHelpFormatter

def subparsers(subcommands: Dict[str, Type[Dataclass]]) -> Any:
    return field(metadata={
        "subparsers": subcommands,
    })
