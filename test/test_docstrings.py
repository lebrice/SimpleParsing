from dataclasses import dataclass

from simple_parsing import field
from simple_parsing.docstring import AttributeDocString, get_attribute_docstring

from .testutils import TestSetup


@dataclass
class Base:
    """A simple base-class example."""

    a: int  # TODO: finetune this

    """docstring for attribute 'a'"""

    b: float = 5.0  # inline comment on attribute 'b'

    c: str = ""
    """Multi
    Line
    Docstring for 'c'
    """


@dataclass
class Extended(Base):
    """Some extension of base-class `Base`"""

    # Comment above d)
    # its multiline, does it still work?
    d: int = 5
    """ docstring for 'd' in Extended. """

    # Comment above e, but with a line skipped

    e: float = -1  # *# comment on the side of e


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
    assert docstring.comment_above == "Comment above d)\nits multiline, does it still work?"
    assert docstring.comment_inline == ""
    assert docstring.docstring_below == "docstring for 'd' in Extended."

    docstring = get_attribute_docstring(Extended, "e")
    assert docstring.comment_above == "Comment above e, but with a line skipped"
    assert docstring.comment_inline == "*# comment on the side of e"
    assert docstring.docstring_below == ""


def test_docstring_works_with_field_function():
    @dataclass
    class UniqueFoo(TestSetup):
        """Some class Foo"""

        # A sequence of tasks.
        task_sequence: list[str] = field(choices=["train", "test", "ood"])  # side
        """Below"""

    docstring = get_attribute_docstring(UniqueFoo, "task_sequence")
    assert docstring.comment_above == "A sequence of tasks."
    assert docstring.comment_inline == "side"
    assert docstring.docstring_below == "Below"


def test_docstrings_with_multiple_inheritance():
    """Test to reproduce issue 162: https://github.com/lebrice/SimpleParsing/issues/162."""

    @dataclass
    class Fooz:
        bar: int = 123  #: The bar property

    @dataclass
    class Baz:
        bat: int = 123  #: The bat property

    @dataclass
    class FooBaz(Fooz, Baz):
        foobaz: int = 123  #: The foobaz property

    assert get_attribute_docstring(FooBaz, "bar") == AttributeDocString(
        comment_inline=": The bar property"
    )
    assert get_attribute_docstring(FooBaz, "bat") == AttributeDocString(
        comment_inline=": The bat property"
    )
    assert get_attribute_docstring(FooBaz, "foobaz") == AttributeDocString(
        comment_inline=": The foobaz property"
    )


def test_weird_docstring_with_field_like():
    @dataclass
    class FooA:
        """
        @dataclass
        class weird:
            bar: int = 123  # WRONG DOCSTRING
        """

        bar: int = 123  # The bar property

    assert get_attribute_docstring(FooA, "bar") == AttributeDocString(
        comment_inline="The bar property"
    )


def test_docstring_builds_upon_bases():
    @dataclass
    class Base2(TestSetup):
        """
        # WRONG ABOVE
        bar: int = 333 # WRONG INLINE
        '''WRONG DOCSTRING'''
        """

        bar: int = 123  # inline
        """Field docstring from base class."""

    @dataclass
    class FooB(Base2):
        # Above
        bar: int = 123  # The bar property

    assert get_attribute_docstring(FooB, "bar") == AttributeDocString(
        comment_inline="The bar property",
        comment_above="Above",
        docstring_below="Field docstring from base class.",
    )

    assert "Field docstring from base class." in FooB.get_help_text()


def test_getdocstring_bug():
    @dataclass
    class HParams:
        batch_size: int = 32

    @dataclass
    class Parent(TestSetup):
        batch_size: int = 48
        child: HParams = field(default_factory=lambda: HParams())

    assert get_attribute_docstring(Parent, "child") == AttributeDocString()


def test_desc_from_cls_docstring():
    @dataclass
    class SomeClass:
        """Creates a new object.

        Parameters
        ----------
        batch_size : int, optional
            _description_, by default 32
        """

        # above
        batch_size: int = 32  # side
        """Below."""

    assert get_attribute_docstring(SomeClass, "batch_size") == AttributeDocString(
        desc_from_cls_docstring="_description_, by default 32",
        comment_above="above",
        comment_inline="side",
        docstring_below="Below.",
    )


def test_help_takes_value_from_docstring():
    @dataclass
    class Args:
        """args.

        Attributes:
            user: Username
            verbose: Display logs
        """

        user: str
        verbose: bool = False

    assert get_attribute_docstring(Args, "verbose") == AttributeDocString(
        desc_from_cls_docstring="Display logs",
    )
