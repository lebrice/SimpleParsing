"""Tests for compatibility with the postponed evaluation of annotations."""
from __future__ import annotations

import dataclasses
import sys
import typing
from dataclasses import InitVar, dataclass
from typing import Any, Callable, Generic, TypeVar

import pytest

from simple_parsing import field
from simple_parsing.annotation_utils.get_field_annotations import (
    get_field_type_from_annotations,
)
from simple_parsing.helpers import Serializable
from simple_parsing.utils import is_list, is_tuple

from .testutils import YAML_INSTALLED, TestSetup


@dataclass
class Foo(TestSetup):
    a: int = 123

    b: str = "fooobar"
    c: tuple[int, float] = (123, 4.56)

    d: list[bool] = field(default_factory=list)

    e: InitVar[int] = 5
    d: int = field(init=False)

    def __post_init__(self, e: int) -> None:
        self.d = e + 2


@dataclass
class Bar(TestSetup):
    barry: Foo = field(default_factory=Foo)
    joe: Foo = field(default_factory=lambda: Foo(b="rrrrr"))
    z: float = 123.456
    some_list: list[float] = field(default_factory=[1.0, 2.0].copy)


def test_future_annotations():
    foo = Foo.setup()
    assert foo == Foo()

    foo = Foo.setup("--a 2 --b heyo --c 1 7.89")
    assert foo == Foo(a=2, b="heyo", c=(1, 7.89))


@pytest.mark.skipif(
    sys.version_info[:2] < (3, 8),
    reason="Before 3.8 `InitVar[tp] is InitVar` so it's impossible to retrieve field type",
)
def test_future_annotations_initvar():
    foo = Foo.setup("--e 6")
    assert foo.d == 8


def test_future_annotations_nested():
    bar = Bar.setup()
    assert bar == Bar()
    assert bar.barry == Foo()
    bar = Bar.setup("--barry.a 2 --barry.b heyo --barry.c 1 7.89")
    assert bar.barry == Foo(a=2, b="heyo", c=(1, 7.89))
    assert isinstance(bar.joe, Foo)


@dataclass
class ClassWithNewUnionSyntax(TestSetup):
    v: int | float = 123


@dataclass
class OtherClassWithNewUnionSyntax(ClassWithNewUnionSyntax):
    """Create a child class without annotations, just to check that they are picked up from the
    base class."""


@pytest.mark.parametrize(
    "ClassWithNewUnionSyntax", [ClassWithNewUnionSyntax, OtherClassWithNewUnionSyntax]
)
def test_new_union_syntax(ClassWithNewUnionSyntax: type[ClassWithNewUnionSyntax]):
    assert ClassWithNewUnionSyntax.setup() == ClassWithNewUnionSyntax()
    assert ClassWithNewUnionSyntax.setup("--v 456") == ClassWithNewUnionSyntax(v=456)
    assert ClassWithNewUnionSyntax.setup("--v 4.56") == ClassWithNewUnionSyntax(v=4.56)

    field_annotations = {f.name: f.type for f in dataclasses.fields(ClassWithNewUnionSyntax)}
    from simple_parsing.utils import is_union

    assert is_union(field_annotations["v"])

    # with pytest.raises(Exception):
    #     assert ClassWithNewUnionSyntax.setup("--v bob")


def test_more_complicated_unions():
    """Test that simple-parsing can properly convert the 'new-style' type annotations.

    These are converted to the 'old-style' annotations using the `typing` module, e.g.
    A | B -> Union[A, B]
    tuple[A, B, C] -> Tuple[A,B,C]

    These values are then used to modify the `type` attribute of the `dataclasses.Field` objects
    on the class, *in-place*, so that simple-parsing can work just like before.
    """

    # T = TypeVarTuple("T")  # TODO: Use this eventually (when it becomes possible).
    T = TypeVar("T")
    U = TypeVar("U")

    class Try(Generic[T, U]):
        """Returns a callable that attempts to use the given functions, and returns the first
        result that is obtained without raising an exception.

        If all the functions fail, calls `none_worked` if it's a callable, or returns it as a value
        if it isn't a callable.
        """

        def __init__(
            self,
            *functions: Callable[..., T] | Callable[..., U],
        ) -> None:
            self.functions = functions

        def __str__(self) -> str:
            return (
                f"{type(self).__qualname__}("
                + ", otherwise ".join(f.__qualname__ for f in self.functions)
                + ")"
            )

        def __call__(self, *args: Any, **kwargs: Any) -> T | U:
            exceptions: list[Exception] = []
            for function in self.functions:
                try:
                    return function(*args, **kwargs)
                except Exception as exc:
                    exceptions.append(exc)
            return self.none_worked(exceptions)

        def none_worked(self, exceptions: list[Exception]) -> typing.NoReturn:
            raise RuntimeError(
                "None of the functions worked!\n"
                + "\n".join(
                    "- Function {func} raised: {exc}\n"
                    for func, exc in zip(self.functions, exceptions)
                )
            )

    int_or_float: Try[int, float] = Try(int, float)

    @dataclass
    class MoreComplex(TestSetup):
        vals_list: list[int | float] = field(default_factory=list, type=int_or_float)
        vals_tuple: tuple[int | float, bool] = field(default=(1, False))

    assert (
        get_field_type_from_annotations(MoreComplex, "vals_list") == list[typing.Union[int, float]]
    )
    assert MoreComplex.__annotations__["vals_list"] == "list[int | float]"
    assert MoreComplex.__annotations__["vals_tuple"] == "tuple[int | float, bool]"
    assert (
        get_field_type_from_annotations(MoreComplex, "vals_tuple")
        == tuple[typing.Union[int, float], bool]
    )
    # NOTE: Before we do anything related to simple-parsing, the value in Field.type should still be
    # equivalent to their annotations.
    field_annotations = {f.name: f.type for f in dataclasses.fields(MoreComplex)}
    assert field_annotations["vals_list"] == "list[int | float]"

    # Now, once we add arguments for it, we expect these fields here to have a different `type`,
    # if python < 3.9
    from simple_parsing import ArgumentParser

    ArgumentParser().add_arguments(MoreComplex, dest="unused")
    field_annotations = {f.name: f.type for f in dataclasses.fields(MoreComplex)}
    assert field_annotations["vals_list"] == list[typing.Union[int, float]]
    assert field_annotations["vals_tuple"] == tuple[typing.Union[int, float], bool]

    assert is_list(field_annotations["vals_list"])
    assert is_tuple(field_annotations["vals_tuple"])

    assert MoreComplex.setup("--vals_list 456 123") == MoreComplex(vals_list=[456, 123])
    assert MoreComplex.setup("--vals_list 4.56 1.23") == MoreComplex(vals_list=[4.56, 1.23])
    # NOTE: Something funky is happening: Seems like the `float` type here is being registered as
    # the handler also in the second case, for the tuple!
    assert MoreComplex.setup("--vals_tuple 456 False") == MoreComplex(vals_tuple=(456, False))
    assert MoreComplex.setup("--vals_tuple 4.56 True") == MoreComplex(vals_tuple=(4.56, True))


@pytest.mark.xfail(reason="TODO: Properly support containers of union types.")
def test_parsing_containers_of_unions():
    @dataclass
    class MoreComplex(TestSetup):
        vals_list: list[int | float] = field(default_factory=list)
        vals_tuple: tuple[int | float, bool] = field(default=(1, False))

    assert MoreComplex.setup("--vals_list 456 123") == MoreComplex(vals_list=[456, 123])
    assert MoreComplex.setup("--vals_list 4.56 1.23") == MoreComplex(vals_list=[4.56, 1.23])
    assert MoreComplex.setup("--vals_tuple 456 False") == MoreComplex(vals_tuple=(456, False))
    assert MoreComplex.setup("--vals_tuple 4.56 True") == MoreComplex(vals_tuple=(4.56, True))


@dataclass
class Opts1(Serializable):
    a: int = 64
    b: float = 1.0


@dataclass
class Opts2(Serializable):
    a: int = 32
    b: float = 0.0


@dataclass
class Wrapper(Serializable):
    opts1: Opts1 = field(default_factory=Opts1)
    opts2: Opts2 = field(default_factory=Opts2)


def test_serialization_deserialization():
    # Show that it's not possible to deserialize nested dataclasses
    opts = Wrapper()
    assert Wrapper in Serializable.subclasses
    assert Opts1 in Serializable.subclasses
    assert Opts2 in Serializable.subclasses
    assert Wrapper.from_dict(opts.to_dict()) == opts
    assert Wrapper.loads_json(opts.dumps_json()) == opts

    if YAML_INSTALLED:
        assert Wrapper.loads_yaml(opts.dumps_yaml()) == opts


@dataclass
class OptimizerConfig(TestSetup):
    lr_scheduler: str = "cosine"
    """LR scheduler to use."""


@dataclass
class SubclassOfOptimizerConfig(OptimizerConfig):
    bar: int | float = 123
    """Some dummy arg bar."""


def test_missing_annotation_on_subclass():
    """Test that the annotation are correctly fetched from the base class."""

    assert SubclassOfOptimizerConfig.setup("--lr_scheduler cosine") == SubclassOfOptimizerConfig(
        lr_scheduler="cosine"
    )
