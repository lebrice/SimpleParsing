from dataclasses import dataclass

import pytest

import simple_parsing
from simple_parsing.docstring import get_attribute_docstring
from simple_parsing import field
from typing import List
from test.testutils import TestSetup
from .testutils import TestSetup

@dataclass
class Base():
    """A simple base-class example"""
    a: int # TODO: finetune this


    """docstring for attribute 'a'"""



    b: float = 5.0 # inline comment on attribute 'b'
    
    
    c: str = ""
    """Multi
    Line
    Docstring for 'c'
    """

@dataclass
class Extended(Base):
    """ Some extension of base-class `Base` """
    ## Comment above d)
    # its multiline, does it still work?
    d: int = 5
    """ docstring for 'd' in Extended. """
    
    # Comment above e, but with a line skipped

    e: float = -1               #*# comment on the side of e


def test_docstring_parsing_work_on_base():
    docstring = get_attribute_docstring(Base, "a")
    assert docstring.comment_above == ""
    assert docstring.comment_inline == "TODO: finetune this"
    assert docstring.docstring_below == "docstring for attribute 'a'"

    docstring = get_attribute_docstring(Base, "b")
    assert docstring.comment_above == ""
    assert docstring.comment_inline == "inline comment on attribute 'b'"
    assert docstring.docstring_below == ""

    docstring = get_attribute_docstring(Base, "c")
    assert docstring.comment_above == ""
    assert docstring.comment_inline == ""
    assert docstring.docstring_below == "Multi\nLine\nDocstring for 'c'\n"


def test_docstring_parsing_works_on_extended():
    docstring = get_attribute_docstring(Extended, "a")
    assert docstring.comment_above == ""
    assert docstring.comment_inline == "TODO: finetune this"
    assert docstring.docstring_below == "docstring for attribute 'a'"

    docstring = get_attribute_docstring(Extended, "b")
    assert docstring.comment_above == ""
    assert docstring.comment_inline == "inline comment on attribute 'b'"
    assert docstring.docstring_below == ""

    docstring = get_attribute_docstring(Extended, "c")
    assert docstring.comment_above == ""
    assert docstring.comment_inline == ""
    assert docstring.docstring_below == "Multi\nLine\nDocstring for 'c'\n"

    docstring = get_attribute_docstring(Extended, "d")
    assert docstring.comment_above == "# Comment above d)\nits multiline, does it still work?"
    assert docstring.comment_inline == ""
    assert docstring.docstring_below == "docstring for 'd' in Extended."

    docstring = get_attribute_docstring(Extended, "e")
    assert docstring.comment_above == "Comment above e, but with a line skipped"
    assert docstring.comment_inline == "*# comment on the side of e"
    assert docstring.docstring_below == ""

def test_docstring_works_with_field_function():
    @dataclass
    class Foo(TestSetup):
        """ Some class Foo """

        # A sequence of tasks.
        task_sequence: List[str] = field(choices=["train", "test", "ood"]) # side
        """Below"""


    docstring = get_attribute_docstring(Foo, "task_sequence")
    assert docstring.comment_above == "A sequence of tasks."
    assert docstring.comment_inline == "side"
    assert docstring.docstring_below == "Below"
