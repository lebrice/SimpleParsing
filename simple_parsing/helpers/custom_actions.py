from __future__ import annotations

import argparse
from typing import Any, Callable, Iterable, Sequence

from typing_extensions import Literal

from .. import utils

DEFAULT_NEGATIVE_PREFIX = "--no"


class BooleanOptionalAction(argparse.Action):
    """Similar to `argparse.BooleanOptionalAction`.

    * Support using a custom negative prefix (makes this compatible with `absl.flags`)
    * Accept `--flag=true` value
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
        nargs: Literal["?"] | None = "?",
        negative_prefix: str = DEFAULT_NEGATIVE_PREFIX,
        negative_option: str | None = None,
        _conflict_prefix: str | None = "",
    ):
        option_strings = list(option_strings)
        if nargs is None:
            nargs = "?"

        if nargs != "?":
            more_info = ""
            if nargs in {0, 1}:
                more_info = (
                    "In argparse, nargs=0 parses an empty list, and nargs=1 is list of bools "
                    "with one item, not a required single boolean."
                )
            elif nargs in {"+", "*"} or isinstance(nargs, int):
                more_info = (
                    "To parse a field with a list of booleans, use a sequence of booleans as a "
                    "field annotation (e.g. list[bool] or tuple[bool, ...])."
                )

            field = {option.lstrip("-") for option in option_strings}
            raise ValueError(
                f"Invalid nargs for bool field '{'/'.join(field)}': {nargs!r}\n"
                f"Fields with a `bool` annotation only accepts nargs of `'?'` or `None`, since it "
                "parses single-boolean fields. " + "\n" + more_info
            )

        self.negative_prefix = negative_prefix
        self.negative_option = negative_option

        self.negative_option_strings: list[str] = []
        if negative_option is not None:
            # Use the negative option.
            # _conflict_prefix is passed down from the FieldWrapper, and is used to also add a
            # prefix to the generated negative options. This is used to avoid conflicts between
            # the negative options of different fields!
            # For example if both a `train: Config` and `valid: Config` have a `--verbose` flag,
            # with a `--silent` negative option, then we have to add a prefix to the negative flags
            # also!
            after_dashes = ""
            if _conflict_prefix:
                assert _conflict_prefix.endswith(".")
                after_dashes = _conflict_prefix

            if negative_option.startswith("-"):
                negative_option_without_leading_dashes = negative_option.lstrip("-")
                num_leading_dashes = len(negative_option) - len(
                    negative_option_without_leading_dashes
                )

            else:
                negative_option_without_leading_dashes = negative_option
                # NOTE: Pre-emptively changing this here so we don't use a single leading dash when
                # there's prefix.
                # Use a single leading dash only when there isn't a prefix and if the negative
                # option is a single character.
                num_leading_dashes = 2 if len(after_dashes + negative_option) > 1 else 1
            negative_option = (
                "-" * num_leading_dashes + after_dashes + negative_option_without_leading_dashes
            )
            self.negative_option_strings = [negative_option]
        else:
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

                elif option_string.startswith("-"):
                    without_leading_dashes = option_string.lstrip("-")
                    negative_option_string = self.negative_prefix + without_leading_dashes
                    if negative_option_string not in self.negative_option_strings:
                        # NOTE: don't want -a and --a to both add a --noa negative option.
                        self.negative_option_strings.append(negative_option_string)
                else:
                    raise NotImplementedError(
                        f"Invalid option string {option_string!r} for boolean field. "
                        f"This action doesn't support positional arguments. "
                        f"Option strings should start with one or more dashes ('-'). "
                    )
        if help is not None and default is not None and default is not argparse.SUPPRESS:
            help += " (default: %(default)s)"

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
        self.type: Callable[[str], bool]
        assert self.type is not None

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: str | None = None,
    ):
        # NOTE: `option_string` is only None when using a positional argument.
        if option_string is None:
            raise NotImplementedError("This action doesn't support positional arguments yet.")
        assert option_string in self.option_strings

        used_negative_flag = option_string in self.negative_option_strings

        bool_value: bool
        if values is None:  # --my_flag / --nomy_flag
            bool_value = not used_negative_flag
        elif used_negative_flag:  # Cannot set `--nomy_flag=True/False`
            parser.exit(
                message=f"Negative flags cannot be passed a value (Got: {option_string}={values})"
            )
        elif isinstance(values, bool):
            bool_value = values
        elif isinstance(values, str):  # --my_flag true
            bool_value = self.type(values)
        else:
            raise ValueError(f"Unsupported value for {option_string}: {values!r}")

        setattr(namespace, self.dest, bool_value)

    def format_usage(self):
        return " | ".join(self.option_strings)
