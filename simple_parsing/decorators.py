from __future__ import annotations

import collections
import dataclasses
import functools
import inspect
import typing
from typing import Any, Callable, NamedTuple

import docstring_parser as dp

from simple_parsing.docstring import dp_parse, inspect_getdoc

from . import helpers, parsing


class _Field(NamedTuple):
    name: str
    annotation: type
    field: dataclasses.Field


def _description_from_docstring(docstring: dp.Docstring) -> str:
    """Construct a description from the short and long description of a docstring."""
    description = ""
    if docstring.short_description:
        description += f"{docstring.short_description}\n"
        if docstring.blank_after_short_description:
            description += "\n"
    if docstring.long_description:
        description += f"{docstring.long_description}\n"
        if docstring.blank_after_long_description:
            description += "\n"
    return description


@typing.overload
def main(original_function: None = None, **sp_kwargs) -> Callable[..., Callable[..., Any]]:
    ...


@typing.overload
def main(original_function: Callable[..., Any], **sp_kwargs) -> Callable[..., Any]:
    ...


def main(original_function=None, **sp_kwargs):
    """Parse a function's arguments using simple-parsing from type annotations."""

    def _decorate_with_cli_args(function: Callable[..., Any]) -> Callable[..., Any]:
        """Decorate `function` by binding its arguments obtained from simple-parsing."""

        @functools.wraps(function)
        def _wrapper(*other_args, **other_kwargs) -> Any:
            # Parse signature and parameters
            signature = inspect.signature(function, follow_wrapped=True)
            parameters = signature.parameters

            # Parse docstring to use as help strings
            docstring = dp_parse(inspect_getdoc(function) or "")
            docstring_param_description = {
                param.arg_name: param.description for param in docstring.params
            }

            # Parse all arguments from the function
            fields = []
            for name, parameter in parameters.items():
                # Replace empty annotation with Any
                if parameter.annotation == inspect.Parameter.empty:
                    parameter = parameter.replace(annotation=Any)

                # Parse default or default_factory if the default is callable.
                default, default_factory = dataclasses.MISSING, dataclasses.MISSING
                if parameter.default != inspect.Parameter.empty:
                    if inspect.isfunction(parameter.default):
                        default_factory = parameter.default
                    else:
                        default = parameter.default

                field = _Field(
                    name,
                    parameter.annotation,
                    helpers.field(
                        name=name,
                        default=default,
                        default_factory=default_factory,
                        help=docstring_param_description.get(name, ""),
                        positional=parameter.kind == inspect.Parameter.POSITIONAL_ONLY,
                    ),
                )
                fields.append(field)

            # We can have positional arguments with no defaults that come out of order
            # when parsing the function signature. Therefore, before we construct
            # the dataclass we have to sort fields according to their default value.
            # We query fields by name so there's no need to worry about the order.
            def _field_has_default(field: _Field) -> bool:
                return (
                    field.field.default is not dataclasses.MISSING
                    or field.field.default_factory is not dataclasses.MISSING
                )

            fields = sorted(fields, key=_field_has_default)

            # Create the dataclass using the fields derived from the function's signature
            FunctionArgs = dataclasses.make_dataclass(function.__qualname__, fields)
            FunctionArgs.__doc__ = _description_from_docstring(docstring) or None
            function_args = parsing.parse(
                FunctionArgs,
                dest="args",
                add_config_path_arg=False,
                **sp_kwargs,
            )

            # Construct both positional and keyword arguments.
            args, kwargs = [], {}
            for field in dataclasses.fields(function_args):
                value = getattr(function_args, field.name)
                if field.metadata.get("positional", False):
                    args.append(value)
                else:
                    # TODO: py39: use union operator (|=)
                    kwargs.update({field.name: value})

            # Construct positional arguments with CLI and runtime args
            positionals = (*args, *other_args)
            # Construct keyword arguments so it can override arguments
            # so we don't receive multiple value errors.
            keywords = collections.ChainMap(kwargs, other_kwargs)

            # Call the function
            return function(*positionals, **keywords)

        return _wrapper

    if original_function:
        return _decorate_with_cli_args(original_function)

    return _decorate_with_cli_args
