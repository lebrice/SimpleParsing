import simple_parsing
from simple_parsing import ParseableFromCommandLine, InconsistentArgumentError

import argparse
import dataclasses
from dataclasses import dataclass, Field

import pytest
import inspect
import textwrap

@dataclass
class Base(ParseableFromCommandLine):
    """A simple base-class example"""
    a: int # TODO: finetune this


    """docstring for attribute 'a'"""



    b: float = 5.0 # inline comment on attribute 'b'
    
    
    c: str = ""
    """Multi
    Line
    Docstring for 'c'
    """


def test_docstring_parsing_works():
    from simple_parsing.utils import find_docstring_of_field, AttributeDocString
    docstring = find_docstring_of_field(Base, "a")
    assert docstring.comment_above == ""
    assert docstring.comment_inline == "TODO: finetune this"
    assert docstring.docstring_below == "docstring for attribute 'a'"

    docstring = find_docstring_of_field(Base, "b")
    assert docstring.comment_above == ""
    assert docstring.comment_inline == "inline comment on attribute 'b'"
    assert docstring.docstring_below == ""

    docstring = find_docstring_of_field(Base, "c")
    assert docstring.comment_above == ""
    assert docstring.comment_inline == ""
    assert docstring.docstring_below == "Multi\nLine\nDocstring for 'c'\n"