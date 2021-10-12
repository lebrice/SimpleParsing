from dataclasses import dataclass
import itertools

import pytest

from .testutils import TestSetup, parametrize, assert_help_output_equals


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


def test_bool_attributes_work():
    ext = Base.setup("--a 5 --f")
    assert ext.f == True

    ext = Base.setup("--a 5")
    assert ext.f == False

    true_strings = ["True", "true"]
    for s in true_strings:
        ext = Base.setup(f"--a 5 --f {s}")
        assert ext.f == True

    false_strings = ["False", "false"]
    for s in false_strings:
        ext = Base.setup(f"--a 5 --f {s}")
        assert ext.f == False


def test_bool_flags_work():
    flags = Flags.setup("--a true --b --c")
    assert flags.a == True
    assert flags.b == True
    assert flags.c == True

@parametrize(
    "default_value, flag_used, passed_value",
    list(itertools.product(
        (True, False, None),  # default values
        ('--a', '--no_a', '-a'),  # Flag passed at cmd line. No such thing as -na.
        (True, False, '')  # Value passed at cmd-line
    )),
)
def test_all_bool_combos(default_value, flag_used, passed_value):
    @dataclass
    class SomeClass(TestSetup):
        a: bool = default_value  # type: ignore
    flags = SomeClass.setup(f'{flag_used} {passed_value}')
    bool_implication_of_flag = False if 'no' in flag_used else True
    # --any-flag True and --any-flag mean same.
    passed_value_bool = passed_value if isinstance(passed_value, bool) else True
    expected_value = passed_value_bool if bool_implication_of_flag else not passed_value_bool
    assert flags.a == expected_value

def test_bool_help_text():
    @dataclass
    class MyFlags(TestSetup):
        a: bool
        b: bool = True
        c: bool = False

    assert_help_output_equals(
        MyFlags.get_help_text(),
        f"""
        usage: pytest [-h] -a [bool] [-b [bool]] [-c [bool]]

        optional arguments:
        -h, --help            show this help message and exit

        test_bool_help_text.<locals>.MyFlags ['my_flags']:
          MyFlags(a: bool, b: bool = True, c: bool = False)

          -a [bool], --a [bool], --no_a [bool]
          -b [bool], --b [bool], --no_b [bool]
                                (default: True)
          -c [bool], --c [bool], --no_c [bool]
                                (default: False)
        """,
    )
