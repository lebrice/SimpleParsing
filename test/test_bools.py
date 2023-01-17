import textwrap
from dataclasses import dataclass

import pytest

from simple_parsing import helpers
from simple_parsing.helpers.fields import field, flag

from .testutils import TestSetup


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
    assert Flags.get_help_text() == textwrap.dedent(
        """\
        usage: pytest [-h] -a bool [-b bool] [-c bool]

        optional arguments:
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


@pytest.mark.parametrize(
    "flag, nargs, a",
    [
        # By default, support both --noflag and --flag=false
        ("--a", "?", True),
        ("--noa", "?", False),
        ("--a true", "?", True),
        ("--a true false", "?", SystemExit("unrecognized arguments")),
        # `nargs=None` is like `nargs='?'`
        ("--a", None, True),
        ("--noa", None, False),
        ("--a true", None, True),
        ("--a true false", None, SystemExit("unrecognized arguments")),
        # 1 argument explicitly required
        ("--a", 1, SystemExit("expected 1 argument")),
        ("--noa", 1, SystemExit("the following arguments are required")),
        ("--a=true", 1, [True]),
        ("--a true false", 1, SystemExit("unrecognized arguments")),
        # 2 argument explicitly required
        ("--a", 2, SystemExit("expected 2 argument")),
        ("--noa", 2, SystemExit("the following arguments are required")),
        ("--a=true", 2, SystemExit("expected 2 argument")),
        ("--a true false", 2, [True, False]),
        # 1+ argument explicitly required
        ("--a", "+", SystemExit("expected at least one argument")),
        ("--noa", "+", SystemExit("the following arguments are required")),
        ("--a=true", "+", [True]),
        ("--a true false", "+", [True, False]),
        # 0 or 1+ argument explicitly required
        ("--a", "*", []),
        ("--noa", "*", SystemExit("unrecognized arguments")),
        ("--a=true", "*", [True]),
        ("--a true false", "*", [True, False]),
    ],
)
def test_bool_nargs(flag, nargs, a, capsys: pytest.CaptureFixture):
    @dataclass
    class MyClass(TestSetup):
        """Some test class"""

        a: bool = helpers.field(nargs=nargs)

    if isinstance(a, SystemExit):
        with pytest.raises(SystemExit):
            MyClass.setup(flag)
        assert str(a) in capsys.readouterr().err
    else:
        flags = MyClass.setup(flag)
        assert flags.a == a


@pytest.mark.parametrize("field", [field, flag])
def test_using_custom_negative_prefix(field):
    """Check that we can customize the negative prefix for a boolean field, either with the
    `field` function or with the `flag` function.
    """

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
def test_using_custom_negative_alias(field):
    from simple_parsing.helpers.fields import flag

    @dataclass
    class Config(TestSetup):
        debug: bool = field(default=False, negative_alias="--release")

    help_text = Config.get_help_text()
    assert "--nodebug" not in help_text
    assert "--release" in help_text
    assert Config.setup("--release").debug is False

    @dataclass
    class OtherConfig(TestSetup):
        """Same as above but the default is `True` for `debug`."""

        debug: bool = flag(default=True, negative_alias="--no-debug")

    help_text = OtherConfig.get_help_text()
    assert "--nodebug" not in help_text
    assert "--no-debug" in help_text
    assert OtherConfig.setup("--no-debug").debug is False
