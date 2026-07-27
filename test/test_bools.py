import sys
import textwrap
from contextlib import AbstractContextManager as ContextManager
from dataclasses import dataclass
from typing import Callable, Union

import pytest

from simple_parsing import helpers
from simple_parsing.helpers.fields import field, flag

from .testutils import (
    TestSetup,
    exits_and_writes_to_stderr,
    raises_expected_n_args,
    raises_missing_required_arg,
    raises_unrecognized_args,
)


@dataclass
class Base(TestSetup):
    """Some extension of base-class `Base`"""

    a: int = 5
    f: bool = False


@dataclass
class Flags(TestSetup):
    a: bool  # an example required flag (defaults to False)
    b: bool = True  # optional flag 'b'.
    c: bool = False  # optional flag 'c'.


@pytest.mark.parametrize(
    "flag,expected_f",
    [
        ("--a 5", False),
        ("--a 5 --f", True),
        ("--a 5 --nof", False),
        ("--a 5 --f=true", True),
        ("--a 5 --f true", True),
        ("--a 5 --f True", True),
        ("--a 5 --f=false", False),
        ("--a 5 --f false", False),
        ("--a 5 --f False", False),
        ("--a 5 --f --f false", False),
    ],
)
def test_bool_base_work(flag: str, expected_f: bool):
    assert Base.setup(flag).f is expected_f


def test_bool_args_in_help():
    prog = sys.argv[0].split("/")[-1]
    options = "options" if sys.version_info >= (3, 10) else "optional arguments"
    assert Flags.get_help_text() == textwrap.dedent(
        f"""\
        usage: {prog} [-h] -a bool [-b bool] [-c bool]

        {options}:
          -h, --help            show this help message and exit

        Flags ['flags']:
          Flags(a: bool, b: bool = True, c: bool = False)

          -a bool, --a bool, --noa bool
                                an example required flag (defaults to False) (default:
                                None)
          -b bool, --b bool, --nob bool
                                optional flag 'b'. (default: True)
          -c bool, --c bool, --noc bool
                                optional flag 'c'. (default: False)
        """
    )


def test_bool_attributes_work():
    ext = Base.setup("--a 5 --f")
    assert ext.f is True

    ext = Base.setup("--a 5")
    assert ext.f is False


@pytest.mark.parametrize(
    "flag,a,b,c",
    [
        ("--a", True, True, False),
        ("--a true --b --c", True, True, True),
        ("--a true --noc --b --c --noc", True, True, False),
        ("--noa --b false --noc", False, False, False),
    ],
)
def test_bool_flags_work(flag: str, a: bool, b: bool, c: bool):
    flags = Flags.setup(flag)
    assert flags.a is a
    assert flags.b is b
    assert flags.c is c


@pytest.mark.parametrize("invalid_nargs", [0, 1, "*", "+"])
def test_bool_field_doesnt_accept_invalid_nargs(invalid_nargs: Union[int, str]):
    """When using a `bool` annotation on a field, it doesn't accept `nargs` other than ? or None.

    This is because in argparse, `nargs=0` means a list with no values, and `nargs=1` is a list
    with one value (not just a required bool value).
    """

    @dataclass
    class Options(TestSetup):
        val: bool = field(default=True, nargs=invalid_nargs)

    with pytest.raises(ValueError, match="Invalid nargs for bool field"):
        Options.setup("")


@pytest.mark.parametrize(
    "flag, nargs, a_or_failure",
    [
        # By default, support both --noflag and --flag=false
        ("--a", "?", True),
        ("--noa", "?", False),
        ("--a true", "?", True),
        ("--a true false", "?", lambda: raises_unrecognized_args("false")),
        # `nargs=None` is like `nargs='?'`
        ("--a", None, True),
        ("--noa", None, False),
        ("--a true", None, True),
        ("--a true false", None, lambda: raises_unrecognized_args("false")),
    ],
)
def test_bool_nargs(
    flag,
    nargs,
    a_or_failure: Union[bool, Callable[[], ContextManager]],
):
    @dataclass
    class MyClass(TestSetup):
        """Some test class."""

        a: bool = helpers.field(nargs=nargs)

    if isinstance(a_or_failure, (bool, list, tuple)):
        a = a_or_failure
        flags = MyClass.setup(flag)
        assert flags.a == a
    else:
        expect_failure_context_manager = a_or_failure
        with expect_failure_context_manager():
            MyClass.setup(flag)


@pytest.mark.parametrize(
    "flag, nargs, a_or_failure",
    [
        # 1 argument explicitly required
        ("--a", 1, lambda: raises_expected_n_args(1)),
        ("--noa", 1, lambda: raises_missing_required_arg("-a/--a")),
        ("--a=true", 1, [True]),
        ("--a true false", 1, lambda: raises_unrecognized_args("false")),
        # 2 argument explicitly required
        ("--a", 2, lambda: raises_expected_n_args(2)),
        ("--noa", 2, lambda: raises_missing_required_arg("-a/--a")),
        ("--a=true", 2, lambda: raises_expected_n_args(2)),
        ("--a true false", 2, [True, False]),
        # 1+ argument explicitly required
        ("--a", "+", lambda: exits_and_writes_to_stderr("expected at least one argument")),
        ("--noa", "+", lambda: exits_and_writes_to_stderr("the following arguments are required")),
        ("--a=true", "+", [True]),
        ("--a true false", "+", [True, False]),
        # 0 or 1+ argument explicitly required
        ("--a", "*", []),
        ("--noa", "*", lambda: raises_unrecognized_args("--noa")),
        ("--a=true", "*", [True]),
        ("--a true false", "*", [True, False]),
    ],
)
def test_list_of_bools_nargs(
    flag,
    nargs,
    a_or_failure: Union[list[bool], Callable[[], ContextManager]],
):
    @dataclass
    class MyClass(TestSetup):
        """Some test class."""

        a: list[bool] = helpers.field(nargs=nargs)

    if isinstance(a_or_failure, (list, tuple)):
        a = a_or_failure
        flags = MyClass.setup(flag)
        assert flags.a == a
    else:
        expect_failure_context_manager = a_or_failure
        with expect_failure_context_manager():
            MyClass.setup(flag)


@pytest.mark.parametrize("field", [field, flag])
def test_using_custom_negative_prefix(field):
    """Check that we can customize the negative prefix for a boolean field, either with the `field`
    function or with the `flag` function."""

    @dataclass
    class Config(TestSetup):
        debug: bool = field(default=False, negative_prefix="--no-")

    help_text = Config.get_help_text()
    assert "--nodebug" not in help_text
    assert "--no-debug" in help_text
    assert Config.setup("--no-debug").debug is False

    @dataclass
    class OtherConfig(TestSetup):
        """Same as above but the default is `True` for `debug`."""

        debug: bool = field(default=True, negative_prefix="--no-debug")

    help_text = OtherConfig.get_help_text()
    assert "--nodebug" not in help_text
    assert "--no-debug" in help_text
    assert OtherConfig.setup("--no-debug").debug is False


a = flag(default=True, negative_prefix="--no-")


@pytest.mark.parametrize("field", [field, flag])
def test_using_custom_negative_option(field):
    from simple_parsing.helpers.fields import flag

    @dataclass
    class Config(TestSetup):
        debug: bool = field(default=False, negative_option="--release")

    help_text = Config.get_help_text()
    assert "--nodebug" not in help_text
    assert "--release" in help_text
    assert Config.setup("--release").debug is False

    @dataclass
    class OtherConfig(TestSetup):
        """Same as above but the default is `True` for `debug`."""

        debug: bool = flag(default=True, negative_option="--no-debug")

    help_text = OtherConfig.get_help_text()
    assert "--nodebug" not in help_text
    assert "--no-debug" in help_text
    assert OtherConfig.setup("--no-debug").debug is False


@pytest.mark.parametrize("default_value", [True, False])
def test_nested_bool_field_negative_args(default_value: bool):
    """Test that we get --train.nodebug instead of --notrain.debug."""

    @dataclass
    class Options:
        debug: bool = default_value

    @dataclass
    class Config(TestSetup):
        train: Options = field(default_factory=Options)
        valid: Options = field(default_factory=Options)

    assert Config.setup("") == Config()
    assert Config.setup("--train.debug") == Config(train=Options(debug=True))
    assert Config.setup("--train.nodebug") == Config(train=Options(debug=False))

    help_text = Config.get_help_text()
    assert "--notrain.debug" not in help_text
    assert "--novalid.debug" not in help_text
    assert "--valid.nodebug" in help_text
    assert "--train.nodebug" in help_text


@pytest.mark.parametrize("default_value", [True, False])
def test_using_abbrev_feature(default_value: bool):
    @dataclass
    class Options(TestSetup):
        verbose: bool = field(default=default_value, negative_option="silent")

    assert Options.setup("--verbose") == Options(verbose=True)
    assert Options.setup("--verb") == Options(verbose=True)
    assert Options.setup("--silent") == Options(verbose=False)
    assert Options.setup("--sil") == Options(verbose=False)


@pytest.mark.parametrize("default_value", [True, False])
def test_nested_bool_field_negative_option_conflict(default_value: bool):
    """Check that the negative option strings also get a prefix when there's a conflict."""

    @dataclass
    class Options:
        verbose: bool = field(default=default_value, negative_option="silent")

    @dataclass
    class Config(TestSetup):
        train: Options = field(default_factory=Options)
        valid: Options = field(default_factory=Options)

    help_text = Config.get_help_text()
    assert "--train.silent" in help_text
    assert "--valid.silent" in help_text
    assert "--silent" not in help_text


@pytest.mark.xfail(
    reason=(
        "TODO: When a field has a single letter name, we usually add `-{name}` and `--{name}`. "
        "However, if a prefix gets added when there's a conflict, then we'd like to only generate "
        "`--{prefix}.{name}`, and *not* `-{prefix}.{name}`."
    ),
    strict=True,
    raises=AssertionError,
)
@pytest.mark.parametrize("bool_field", [field, flag])
@pytest.mark.parametrize("default_value", [True, False])
def test_bool_nested_field_when_conflict_has_two_dashes(
    bool_field: Callable[..., bool], default_value: bool
):
    """TODO:"""

    # Check that there isn't a "-train.d bool" argument generated here, only "--train.d bool"
    @dataclass
    class Options:
        # whether or not to execute in debug mode.
        d: bool = bool_field(default=default_value)

    @dataclass
    class Config(TestSetup):
        train: Options = field(default_factory=Options)
        valid: Options = field(default_factory=Options)

    help_text = Config.get_help_text()
    assert "--train.d bool" in help_text
    assert " -train.d bool" not in help_text
