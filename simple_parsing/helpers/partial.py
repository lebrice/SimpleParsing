""" A Partial helper that can be used to add arguments for an arbitrary class or callable. """
from __future__ import annotations

import dataclasses
import inspect
import typing
from dataclasses import make_dataclass
from functools import cache, lru_cache, singledispatch, wraps
from logging import getLogger as get_logger
from typing import (
    Any,
    Callable,
    Generic,
    Hashable,
    Sequence,
    TypeVar,
    _ProtocolMeta,
    get_type_hints,
    overload,
)

from typing_extensions import ParamSpec

import simple_parsing

__all__ = ["Partial", "config_dataclass_for", "infer_type_annotation_from_default"]

C = TypeVar("C", bound=Callable)
P = ParamSpec("P", covariant=True)
T = TypeVar("T", bound="Any")
_C = TypeVar("_C", bound=Callable[..., Any])

logger = get_logger(__name__)


@singledispatch
def infer_type_annotation_from_default(default: Any) -> Any | type:
    if isinstance(default, (int, str, float, bool)):
        return type(default)
    if isinstance(default, tuple):
        return typing.Tuple[tuple(infer_type_annotation_from_default(d) for d in default)]
    if isinstance(default, list):
        if not default:
            return list
        # Assuming that all items have the same type.
        return typing.List[infer_type_annotation_from_default(default[0])]
    if isinstance(default, dict):
        if not default:
            return dict
    raise NotImplementedError(
        f"Don't know how to infer type annotation to use for default of {default}"
    )


@singledispatch
def adjust_default(default: Any) -> Any:
    """Used the adjust the default value of a parameter that we extract from the signature.

    IF in some libraries, the signature has a special default value, that we shouldn't use as the
    default, e.g. "MyLibrary.REQUIRED" or something, then a handler can be registered here to
    convert it to something else.
    """
    return default


@overload
def cache_when_possible(fn: _C, /) -> _C:
    ...


@overload
def cache_when_possible(*, cache_fn=lru_cache) -> Callable[[_C], _C]:
    ...


@overload
def cache_when_possible(fn: _C, /, *, cache_fn: Callable = lru_cache) -> _C:
    ...


def cache_when_possible(
    fn: _C | None = None, /, *, cache_fn: Callable = lru_cache
) -> _C | Callable[[_C], _C]:

    if fn is None:

        def _wrapper(_fn: _C) -> _C:
            return cache_when_possible(_fn, cache_fn=cache_fn)

        return _wrapper

    cache_wrapper = cache_fn
    cached_fn = cache_fn(fn)

    @wraps(fn)
    def _switch(*args, **kwargs):
        if all(isinstance(arg, Hashable) for arg in args) and all(
            isinstance(arg, Hashable) for arg in kwargs.values()
        ):
            return cached_fn(*args, **kwargs)
        return fn(*args, **kwargs)

    return _switch


@cache_when_possible(cache_fn=cache)
def config_dataclass_for(
    cls: Callable[P, T],
    ignore_args: str | Sequence[str] = (),
    *_: P.args,
    **defaults: P.kwargs,
) -> type[Partial[T]]:
    """Create a dataclass that contains the arguments for the constructor of `cls`.

    Example:

    ```python
    AdamConfig = create_config_dataclass_for_type(torch.optim.Adam)
    ```

    """
    if isinstance(ignore_args, str):
        ignore_args = (ignore_args,)
    else:
        ignore_args = tuple(ignore_args)

    assert isinstance(defaults, dict)

    signature = inspect.signature(cls)

    fields: list[tuple[str, type, dataclasses.Field]] = []

    class_annotations = get_type_hints(cls)

    class_docstring_help = _parse_args_from_docstring(cls.__doc__ or "")
    if inspect.isclass(cls):
        class_constructor_help = _parse_args_from_docstring(cls.__init__.__doc__ or "")
    else:
        class_constructor_help = {}

    for name, parameter in signature.parameters.items():
        default = defaults.get(name, parameter.default)
        if default is parameter.empty:
            default = dataclasses.MISSING
        default = adjust_default(default)

        if name in ignore_args:
            logger.debug(f"Ignoring argument {name}")
            continue

        # if parser and any(action.dest == name for action in parser._actions):
        #     # There's already an argument with this name, e.g. `lr`.
        #     continue

        if parameter.annotation is not inspect.Parameter.empty:
            field_type = parameter.annotation
        elif name in class_annotations:
            field_type = class_annotations[name]
        elif default is not dataclasses.MISSING:
            # Infer the type from the default value.
            # try:
            # # BUG: There is a default of '<required parameter>'.
            # if str(default) == "<required parameter>":
            #     breakpoint()
            field_type = infer_type_annotation_from_default(default)
            # except:
            #     field_type = Any
        else:
            logger.warning(
                f"Don't know what the type of field {name} is! (consider adding a backup argument type using the `backup_arg_types` argument."
            )
            field_type = Any
            # assert False, (default, type(parameter.default))

        class_help_entries = {v for k, v in class_docstring_help.items() if k.startswith(name)}
        init_help_entries = {v for k, v in class_constructor_help.items() if k.startswith(name)}
        help_entries = init_help_entries or class_help_entries
        if help_entries:
            help_str = help_entries.pop()
        else:
            help_str = ""

        if default is dataclasses.MISSING:
            field = simple_parsing.field(help=help_str, required=True)
            # insert since fields without defaults need to go first.
            fields.insert(0, (name, field_type, field))
            logger.debug(f"Adding required field: {fields[0]}")
        else:
            field = simple_parsing.field(default=default, help=help_str)
            fields.append((name, field_type, field))
            logger.debug(f"Adding optional field: {fields[-1]}")

    cls_name = cls.__name__ + "Config"
    config_class = make_dataclass(cls_name=cls_name, bases=(Partial,), fields=fields)
    config_class._target_ = cls

    config_class.__doc__ = (
        f"Auto-Generated configuration dataclass for {cls.__module__}.{cls.__qualname__}\n"
        + cls.__doc__
    )

    return config_class


def _parse_args_from_docstring(docstring: str) -> dict[str, str]:
    """Taken from `pytorch_lightning.utilities.argparse`."""
    arg_block_indent = None
    current_arg = ""
    parsed = {}
    for line in docstring.split("\n"):
        stripped = line.lstrip()
        if not stripped:
            continue
        line_indent = len(line) - len(stripped)
        if stripped.startswith(("Args:", "Arguments:", "Parameters:")):
            arg_block_indent = line_indent + 4
        elif arg_block_indent is None:
            continue
        elif line_indent < arg_block_indent:
            break
        elif line_indent == arg_block_indent:
            current_arg, arg_description = stripped.split(":", maxsplit=1)
            parsed[current_arg] = arg_description.lstrip()
        elif line_indent > arg_block_indent:
            parsed[current_arg] += f" {stripped}"
    return parsed


try:
    # This only seems to be necessary for the SGD optimizer.
    from torch.optim.optimizer import _RequiredParameter

    @adjust_default.register(_RequiredParameter)
    def _(default: Any) -> Any:
        return dataclasses.MISSING

except ImportError:
    pass

from typing import cast


class _Partial(_ProtocolMeta, Generic[_C]):
    _target_: _C

    def __getitem__(cls, target: Callable[P, T]) -> type[Callable[P, T]]:
        # return cls(target=target)
        return config_dataclass_for(target)


class Partial(Generic[T], metaclass=_Partial):
    # _target_: Callable[P, T]

    def __call__(self: Partial[T] | Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        constructor_kwargs = dataclasses.asdict(self)
        constructor_kwargs.update(**kwargs)
        self = cast(Partial, self)
        return type(self)._target_(*args, **constructor_kwargs)
