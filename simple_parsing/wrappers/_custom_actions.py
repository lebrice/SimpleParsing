from __future__ import annotations

import argparse
import typing
from typing import Any, Callable, Iterable, Sequence

from typing_extensions import Literal

from .. import utils

if typing.TYPE_CHECKING:
    from simple_parsing import ArgumentParser


DEFAULT_NEGATIVE_PREFIX = "--no"


class BooleanOptionalAction(argparse.Action):
    """Similar to `argparse.BooleanOptionalAction`.

    * Support custom prefix (for `absl.flags` compatibility)
    * Accept `--flag=true` value
    * Support `nargs`
    * Support Python 3.8

    """

    def __init__(
        self,
        option_strings: Sequence[str],
        dest: str,
        default: bool | None = None,
        type: Callable[[str], bool] = utils.str2bool,
        choices: Iterable[Any] | None = None,
        required: bool = False,
        help: str | None = None,
        metavar: str | tuple[str, ...] | None = "bool",
        nargs: int | Literal["?", "*", "+"] | None = "?",
        negative_prefix: str = DEFAULT_NEGATIVE_PREFIX,
        negative_alias: str | None = None,
    ):
        option_strings = list(option_strings)
        if nargs is None:
            nargs = "?"
        if not (isinstance(nargs, int) or nargs in {"?", "*", "+"}):
            raise ValueError(f"nargs={nargs!r} not supported for bools")
        self.negative_prefix = negative_prefix

        if negative_alias is not None and not negative_alias.startswith("-"):
            raise ValueError(
                f"The negative alias for a field must start with at least one dash. "
                f"Got {negative_alias!r}"
            )
        self.negative_alias = negative_alias

        self.negative_option_strings: list[str] = []
        # Do not add the negative prefix to the option strings when `nargs >= 1`
        if nargs in {"+", "*"} or (isinstance(nargs, int) and nargs >= 1):
            self.negative_option_strings = []
        elif self.negative_alias is not None:
            assert nargs in ("?", 0)
            self.negative_option_strings = [self.negative_alias]
        else:
            assert nargs in ("?", 0)
            self.negative_option_strings = []
            for option_string in option_strings:
                if "." in option_string:
                    parts = option_string.split(".")
                    # NOTE: Need to be careful here.
                    first, *middle, last = parts

                    negative_prefix_without_leading_dashes = negative_prefix.lstrip("-")
                    num_leading_dashes = len(negative_prefix) - len(
                        negative_prefix_without_leading_dashes
                    )
                    first_without_leading_dashes = first.lstrip("-")

                    first = "-" * num_leading_dashes + first_without_leading_dashes
                    last = negative_prefix_without_leading_dashes + last

                    negative_option_string = ".".join([first] + middle + [last])
                    self.negative_option_strings.append(negative_option_string)

                elif option_string.startswith("--"):
                    negative_option_string = self.negative_prefix + option_string[2:]
                    self.negative_option_strings.append(negative_option_string)

        super().__init__(
            option_strings=option_strings + self.negative_option_strings,
            dest=dest,
            nargs=nargs,
            default=default,
            type=type,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar,
        )
        assert self.type is not None

    def __call__(
        self,
        parser: ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str | None = None,
    ):
        if option_string not in self.option_strings:
            return

        if self.negative_alias:
            is_neg = option_string == self.negative_alias
        else:
            assert option_string is not None
            is_neg = option_string in self.negative_option_strings

        if values is None:  # --my_flag / --nomy_flag
            bool_value = not is_neg
        elif is_neg:  # Cannot set `--nomy_flag=True/False`
            parser.exit(
                message=f"{self.negative_prefix} cannot be used with value (Got: {option_string}={values})"
            )
        elif isinstance(values, bool):
            bool_value = values
        elif isinstance(values, str):  # --my_flag true
            assert self.type is not None
            bool_value = self.type(values)
        elif isinstance(values, list):  # --my_flag true true false
            assert self.type is not None
            bool_value = [self.type(v) for v in values]
        else:
            raise ValueError(f"Unsupported value for {option_string}: {values!r}")

        setattr(namespace, self.dest, bool_value)

    def format_usage(self):
        return " | ".join(self.option_strings)
