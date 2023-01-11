from dataclasses import dataclass

import pytest

from simple_parsing import helpers
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
        ("--a", '?', True),
        ("--noa", '?', False),
        ("--a true", '?', True),
        ("--a true false", '?', SystemExit('unrecognized arguments')),
        # `nargs=None` is like `nargs='?'`
        ("--a", None, True),
        ("--noa", None, False),
        ("--a true", None, True),
        ("--a true false", None, SystemExit('unrecognized arguments')),
        # 1 argument explicitly required
        ("--a", 1, SystemExit('expected 1 argument')),
        ("--noa", 1, SystemExit('the following arguments are required')),
        ("--a=true", 1, [True]),
        ("--a true false", 1, SystemExit('unrecognized arguments')),
        # 2 argument explicitly required
        ("--a", 2, SystemExit('expected 2 argument')),
        ("--noa", 2, SystemExit('the following arguments are required')),
        ("--a=true", 2, SystemExit('expected 2 argument')),
        ("--a true false", 2, [True, False]),
        # 1+ argument explicitly required
        ("--a", '+', SystemExit('expected at least one argument')),
        ("--noa", '+', SystemExit('the following arguments are required')),
        ("--a=true", '+', [True]),
        ("--a true false", '+', [True, False]),
        # 0 or 1+ argument explicitly required
        ("--a", '*', []),
        ("--noa", '*', SystemExit('unrecognized arguments')),
        ("--a=true", '*', [True]),
        ("--a true false", '*', [True, False]),
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
