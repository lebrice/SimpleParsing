from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from functools import partial
from test.testutils import TestSetup
from typing import Callable

import pytest


@dataclass
class Value:
    """A simple dataclass with a single int field."""

    v: int = 123


@dataclass
class Wrapped:
    """A dataclass with a single field, which is a Value."""

    value: Value = field(default_factory=partial(Value, v=456))


@pytest.mark.parametrize(
    "default_factory, expected_default_in_help_str",
    [
        (partial(Wrapped, value=Value(v=789)), 789),
        (Wrapped, 456),
        # Should fetch the default from the field type.
        (dataclasses.MISSING, 456),
        # NOTE: We actually invoke the default factory lambda here, which isn't ideal.
        (lambda: Wrapped(value=Value(789)), 789),
    ],
)
def test_defaults_from_field_default_factory_show_in_help(
    default_factory: Callable[[], Wrapped] | dataclasses._MISSING_TYPE,
    expected_default_in_help_str: int,
):
    """When using a functools.partial as the default factory for a field, we want to be able to
    show the right default values in the help string: those from the factory, not those from the
    dataclass field.

    This isn't *that* big a deal, but it would be nice.
    """

    @dataclass
    class Config(TestSetup):
        """A dataclass with a single field, which is a Wrapped object."""

        wrapped: Wrapped = field(default_factory=default_factory)  # type: ignore

    help_text = Config.get_help_text()

    assert f"--v int  (default: {expected_default_in_help_str})" in help_text
