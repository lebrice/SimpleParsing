""" A Partial helper that can be used to add arguments for an arbitrary class or callable. """
import dataclasses
import inspect
import typing
from dataclasses import make_dataclass
from functools import lru_cache, singledispatch, wraps
from logging import getLogger as get_logger
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Hashable,
    Sequence,
    Type,
    TypeVar,
    Union,
    _ProtocolMeta,
    cast,
    get_type_hints,
    overload,
)

from typing_extensions import ParamSpec

import simple_parsing

__all__ = ["Partial", "config_dataclass_for", "infer_type_annotation_from_default"]

C = TypeVar("C", bound=Callable)
P = ParamSpec("P")
T = TypeVar("T", bound="Any")
_C = TypeVar("_C", bound=Callable[..., Any])

logger = get_logger(__name__)


@singledispatch
def infer_type_annotation_from_default(default: Any) -> Union[Any, type]:
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
def cache_when_possible(fn: _C) -> _C:
    ...


@overload
def cache_when_possible(*, cache_fn=lru_cache) -> Callable[[_C], _C]:
    ...


@overload
def cache_when_possible(fn: _C, *, cache_fn: Callable = lru_cache) -> _C:
    ...


default_cache_fn = lambda fn: lru_cache(maxsize=None)(fn)


def cache_when_possible(
    fn: Union[_C, None] = None, *, cache_fn: Callable = default_cache_fn
) -> Union[_C, Callable[[_C], _C]]:

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


@cache_when_possible()
def config_dataclass_for(
    cls: Callable[P, T],
    ignore_args: Union[str, Sequence[str]] = (),
    *_: P.args,
    **defaults: P.kwargs,
) -> Type["Partial[T]"]:
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

    cls_name = _get_generated_config_class_name(cls)
    config_class = make_dataclass(cls_name=cls_name, bases=(Partial,), fields=fields)
    config_class._target_ = cls

    config_class.__doc__ = (
        f"Auto-Generated configuration dataclass for {cls.__module__}.{cls.__qualname__}\n"
        + (cls.__doc__ or "")
    )

    return config_class


def _parse_args_from_docstring(docstring: str) -> Dict[str, str]:
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


def _get_generated_config_class_name(target: Union[Type, Callable]) -> str:
    if inspect.isclass(target):
        return target.__name__ + "Config"
    elif inspect.isfunction(target):
        return target.__name__ + "_config"
    raise NotImplementedError(target)


class _Partial(_ProtocolMeta):
    _target_: _C

    def __getitem__(cls, target: Callable[P, T]) -> Type[Callable[P, T]]:
        full_path = target.__module__ + "." + target.__qualname__
        if full_path in _autogenerated_config_classes:
            return _autogenerated_config_classes[full_path]

        # # if generated_class_name in caller_globals:
        # #     return caller_globals[generated_class_name]
        # caller_module_name: Optional[str] = None
        # # caller_globals: Optional[Dict[str, Any]] = None
        # call_stack = inspect.stack()
        # assert call_stack, "No call stack?!"

        # Create the config class.
        config_class = config_dataclass_for(target)
        # Set it's module to be the one calling this, and set that class name in the globals of
        # the calling module? --> No, too hacky.

        # OR: Set the module to be simple_parsing.helpers.partial ?
        # TODO: What if we had the name of the class directly encode how to recreate the class?
        config_class.__module__ = __name__
        _autogenerated_config_classes[config_class.__qualname__] = config_class
        return config_class


_autogenerated_config_classes: dict[str, type] = {}


def __getattr__(name: str):
    """
    Getting an attribute on this module here will check for the autogenerated config class with that name.
    """
    if name in globals():
        return globals()[name]
    if name.startswith("__") and name.endswith("__"):
        return  # use default getattr

    if name in _autogenerated_config_classes:
        return _autogenerated_config_classes[name]

    raise AttributeError(f"Module {__name__} has no attribute {name}")


import functools
from typing import Optional, Type


class Partial(functools.partial, Generic[T], metaclass=_Partial):
    def __new__(cls, __func: Optional[Callable[P, T]] = None, *args: P.args, **kwargs: P.kwargs):
        __func = __func or cls._target_
        return super().__new__(cls, __func, *args, **kwargs)

    def __call__(self: Union["Partial[T]", Callable[P, T]], *args: P.args, **kwargs: P.kwargs) -> T:
        constructor_kwargs = dataclasses.asdict(self)
        constructor_kwargs.update(**kwargs)
        self = cast(Partial, self)
        return type(self)._target_(*args, **constructor_kwargs)
