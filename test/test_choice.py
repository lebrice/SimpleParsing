import pytest

from dataclasses import dataclass
from simple_parsing import ArgumentParser, choice

from .testutils import *

@dataclass
class A(TestSetup):
    color: str = choice("red", "green", "blue", default="red")



def test_choice_default():
    a = A.setup("")
    assert a.color == "red"


def test_value_not_in_choices_throws_error():
    with pytest.raises(SystemExit):
        a = A.setup("--color orange")

def test_passed_value_works_fine():
    a = A.setup("--color red")
    assert a.color == "red"

    a = A.setup("--color green")
    assert a.color == "green"

    a = A.setup("--color blue")
    assert a.color == "blue"
