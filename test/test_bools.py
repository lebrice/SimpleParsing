from dataclasses import dataclass

import pytest

from .testutils import TestSetup

@dataclass
class Base(TestSetup):
    """ Some extension of base-class `Base` """
    a: int = 5
    f: bool = False


@dataclass
class Flags(TestSetup):
    a: bool # an example required flag (defaults to False)
    b: bool = True # optional flag 'b'.
    c: bool = False # optional flag 'c'.

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
    assert flags.b == False
    assert flags.c == True
