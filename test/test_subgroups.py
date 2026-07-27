from __future__ import annotations

import dataclasses
import functools
import inspect
import shlex
import sys
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Annotated, Callable, TypeVar

import pytest
from pytest_regressions.file_regression import FileRegressionFixture

from simple_parsing import ArgumentParser, parse, subgroups
from simple_parsing.wrappers.field_wrapper import ArgumentGenerationMode, NestedMode

from .test_choice import Color
from .testutils import TestSetup, raises_invalid_choice, raises_missing_required_arg

TestClass = TypeVar("TestClass", bound=TestSetup)


@dataclass
class A:
    a: float = 0.0


@dataclass
class B:
    b: str = "bar"


@dataclass
class AB(TestSetup):
    a_or_b: A | B = subgroups({"a": A, "b": B}, default_factory=A)


@dataclass
class C:
    c: bool = False


@dataclass
class D:
    d: int = 0


@dataclass
class E:
    e: bool = False


@dataclass
class F:
    f: str = "f_default"


@dataclass
class G:
    g: int = 0


@dataclass
class H:
    h: bool = False


@dataclass
class CD:
    c_or_d: C | D = subgroups({"c": C, "d": D}, default_factory=C)
    other_c_arg: str = "bob"


@dataclass
class EF:
    e_or_f: E | F = subgroups({"e": E, "f": F}, default_factory=E)


@dataclass
class GH:
    g_or_h: G | H = subgroups({"g": G, "h": H}, default_factory=G)


@dataclass
class ABCD(TestSetup):
    ab_or_cd: AB | CD = subgroups({"ab": AB, "cd": CD}, default_factory=AB)


@dataclass
class EFGH:
    ef_or_gh: EF | GH = subgroups({"ef": EF, "gh": GH}, default_factory=EF)


@dataclass
class ABCDEFGH(TestSetup):
    """Dataclass with three levels of subgroup nesting."""

    abc_or_efgh: ABCD | EFGH = subgroups({"abcd": ABCD, "efgh": EFGH}, default_factory=ABCD)


@dataclass
class MultipleSubgroupsSameLevel(TestSetup):
    a_or_b: A | B = subgroups({"a": A, "b": B}, default_factory=A)
    c_or_d: C | D = subgroups({"c": C, "d": D}, default_factory=D)


@dataclass
class MultipleSubgroupsDifferentLevel(TestSetup):
    ab_or_cd: AB | CD = subgroups({"ab": AB, "cd": CD}, default_factory=CD)
    ef: EF = field(default_factory=EF)


@dataclass
class EnumsAsKeys(TestSetup):
    """Dataclass where the subgroup choices are keys."""

    a_or_b: A | B = subgroups({Color.red: A, Color.blue: B}, default_factory=A)


@pytest.mark.parametrize(
    "dataclass_type, get_help_text_args, should_contain",
    [
        (AB, {}, ["--a_or_b {a,b}", "--a float"]),
        (AB, {}, ["--a_or_b {a,b}       (default: a)", "--a float"]),
        (EnumsAsKeys, {}, ["--a_or_b {Color.red,Color.blue}", "--a float"]),
        (
            MultipleSubgroupsSameLevel,
            {},
            ["--a_or_b {a,b}", "--a float", "--c_or_d {c,d}", "--d int"],
        ),
        (
            MultipleSubgroupsDifferentLevel,
            {},
            ["--ab_or_cd {ab,cd}", "--c_or_d {c,d}", "--e_or_f {e,f}", "--e bool"],
        ),
    ],
)
def test_help_string(
    dataclass_type: type[TestSetup],
    get_help_text_args: dict,
    should_contain: list[str],
):
    """Test that the arguments for the chosen subgroup are shown in the help string."""
    help_text = dataclass_type.get_help_text(*get_help_text_args)
    for expected in should_contain:
        assert expected in help_text


@pytest.mark.parametrize(
    "dataclass_type, args, expected",
    [
        (
            AB,
            "--a_or_b a --a 123",
            AB(a_or_b=A(a=123)),
        ),
        (
            AB,
            "--a_or_b b --b foooo",
            AB(a_or_b=B(b="foooo")),
        ),
        (
            MultipleSubgroupsSameLevel,
            "--a_or_b a --a 123 --d 456",
            MultipleSubgroupsSameLevel(a_or_b=A(a=123), c_or_d=D(d=456)),
        ),
        (
            MultipleSubgroupsSameLevel,
            "--a_or_b b --b foooo",
            MultipleSubgroupsSameLevel(a_or_b=B(b="foooo")),
        ),
        (
            ABCD,
            "--ab_or_cd ab --a_or_b a --a 123",
            ABCD(ab_or_cd=AB(a_or_b=A(a=123))),
        ),
        (
            ABCD,
            "--ab_or_cd cd --c_or_d d --d 456",
            ABCD(ab_or_cd=CD(c_or_d=D(d=456))),
        ),
    ],
)
def test_parse(dataclass_type: type[TestClass], args: str, expected: TestClass):
    assert dataclass_type.setup(args) == expected


def test_subgroup_choice_is_saved_on_namespace():
    """Test for https://github.com/lebrice/SimpleParsing/issues/139.

    Need to save the chosen subgroup name somewhere on the args.
    """
    parser = ArgumentParser()
    parser.add_arguments(AB, dest="config")

    args = parser.parse_args(shlex.split("--a_or_b b --b foobar"))
    assert args.config == AB(a_or_b=B(b="foobar"))
    assert args.subgroups == {"config.a_or_b": "b"}


@dataclass
class RequiredSubgroup(TestSetup):
    a_or_b: A | B = subgroups({"a": A, "b": B})


def test_required_subgroup():
    """Test when a subgroup doesn't have a default value, and is required."""

    with raises_missing_required_arg():
        assert RequiredSubgroup.setup("")

    assert RequiredSubgroup.setup("--a_or_b b") == RequiredSubgroup(a_or_b=B())


@dataclass
class TwoSubgroupsWithConflict(TestSetup):
    first: AB | CD = subgroups({"ab": AB, "cd": CD}, default_factory=CD)
    second: AB | GH = subgroups({"ab": AB, "gh": GH}, default_factory=GH)


@pytest.mark.parametrize(
    "args_str, expected",
    [
        (
            (
                "--first ab --first.a_or_b a --first.a_or_b.a 111 "
                "--second ab --second.a_or_b a --second.a_or_b.a 234"
            ),
            TwoSubgroupsWithConflict(first=AB(a_or_b=A(a=111)), second=AB(a_or_b=A(a=234))),
        ),
        (
            # TODO: Unsure about this one. Also have to be careful about the abbrev feature of
            # Argparse.
            "--first ab --first.a_or_b a --a 111 --second ab --second.a_or_b b --b arwg",
            TwoSubgroupsWithConflict(first=AB(a_or_b=A(a=111)), second=AB(a_or_b=B(b="arwg"))),
        ),
    ],
)
def test_two_subgroups_with_conflict(args_str: str, expected: TwoSubgroupsWithConflict):
    assert TwoSubgroupsWithConflict.setup(args_str) == expected


def test_subgroups_with_key_default() -> None:
    with pytest.raises(ValueError):
        subgroups({"a": A, "b": B}, default_factory="a")

    @dataclass
    class Foo(TestSetup):
        a_or_b: A | B = subgroups({"a": A, "b": B}, default="a")

    assert Foo.setup() == Foo(a_or_b=A())
    assert Foo.setup("--a_or_b a --a 445") == Foo(a_or_b=A(a=445))
    assert Foo.setup("--a_or_b b") == Foo(a_or_b=B())
    assert Foo.setup("--a_or_b b --b zodiak") == Foo(a_or_b=B(b="zodiak"))


# IDEA: Make it possible to use a default factory that is a partial for a function, if that
# function has a return annotation.
# def some_a_factory(a: int = -1) -> A:
#     return A(a=a)


def test_subgroup_default_needs_to_be_key_in_dict():
    with pytest.raises(ValueError, match="default must be a key in the subgroups dict"):
        _ = subgroups({"a": B, "aa": A}, default="b")


def test_subgroup_default_factory_needs_to_be_value_in_dict():
    with pytest.raises(
        ValueError, match="`default_factory` must be a value in the subgroups dict"
    ):
        _ = subgroups({"a": B, "aa": A}, default_factory=C)


def test_lambdas_dont_return_same_instance():
    """Slightly unrelated, but I just want to check if lambda expressions return the same object
    instance when a default factory looks like `lambda: A()`.

    If so, then I won't encourage this.
    """

    @dataclass
    class A:
        a: int = 123

    @dataclass
    class Config(TestSetup):
        a_config: A = dataclasses.field(default_factory=lambda: A())

    assert Config().a_config is not Config().a_config


def test_partials_new_args_overwrite_set_values():
    """Double-check that functools.partial overwrites the keywords that are stored when it is
    created with the ones that are passed when calling it."""
    # just to avoid the test passing if I were to hard-code the same value as the default by
    # accident.
    default_a = A().a
    CustomA = functools.partial(A, a=default_a + 1)
    assert CustomA() == A(a=default_a + 1)
    assert CustomA(a=default_a * 34) == A(a=default_a * 34)


def test_defaults_from_partial():
    @dataclass
    class Foo(TestSetup):
        a_or_b: A | B = subgroups(
            {
                "a": A,
                "a_1.23": functools.partial(A, a=1.23),
                "a_4.56": functools.partial(A, a=4.56),
                "b": B,
                "b_bob": functools.partial(B, b="bob"),
            },
            default="a",
        )

    # TODO: The issue is that the default value from the field is being set in the dict of
    # constructor arguments, and even if the dataclass_fn is a partial(A, a=1.23), since it's being
    # called like `dataclass_fn(**{"a": 0.0})` (from the field default), then the value of `a` is
    # overwritten with the default value from the field. I think the solution is either:
    # 1. Not populate the constructor arguments with the value for this field;
    # 2. Change the default value to be the one from the partial, instead of the one from the
    #    field. The partial would then be called with the same value.
    # I think 1. makes more sense. For fields that aren't required (have a default value), then the
    # constructor_arguments dict doesn't need to contain the default values. Calling the
    # dataclass_fn (which is almost always just the dataclass type itself) will use the default
    # values from the fields.

    # NOTE: Now I've changed my mind. Option 2 might be easiest for now, since I still don't have a
    # complete grasp of how argparse works internally, and I feel like I could easily make it work
    # quickly.
    assert Foo.setup("--a_or_b a_4.56") == Foo(a_or_b=A(a=4.56))


def test_subgroups_with_partials():
    @dataclass
    class Foo(TestSetup):
        a_or_b: A | B = subgroups(
            {
                "a": A,
                "a_1.23": functools.partial(A, a=1.23),
                "a_4.56": functools.partial(A, a=4.56),
                "b": B,
                "b_bob": functools.partial(B, b="bob"),
            },
            default="a",
        )

    assert Foo.setup() == Foo() == Foo(a_or_b=A())
    assert Foo.setup("--a_or_b a") == Foo(a_or_b=A())
    assert Foo.setup("--a_or_b a --a=6.66") == Foo(a_or_b=A(a=6.66))
    assert Foo.setup("--a_or_b a_1.23") == Foo(a_or_b=A(a=1.23))
    assert Foo.setup("--a_or_b a_4.56") == Foo(a_or_b=A(a=4.56))
    assert Foo.setup("--a_or_b b") == Foo(a_or_b=B())
    assert Foo.setup("--a_or_b b --b fooo") == Foo(a_or_b=B(b="fooo"))
    assert Foo.setup("--a_or_b b_bob") == Foo(a_or_b=B(b="bob"))

    with raises_invalid_choice():
        Foo.setup("--a_or_b c")


@pytest.mark.xfail(strict=True, reason="I'm not sure this is a good idea anymore.")
def test_subgroups_with_functions():
    def make_b(b: str = "default from make_b") -> B:
        return B(b=b)

    @dataclass
    class Foo(TestSetup):
        a_or_b: A | B = subgroups(
            {
                "a": A,
                "b": B,
                "make_b": make_b,
            },
            default="a",
        )

    # TODO: decide if this is correct. In this case here, since the default value for `b` is the
    # same as passed (i.e. arg isn't used), then the constructor args dict doesn't have an entry
    # for `b`, and the default value from the function definition is used.
    # This also means that `b` can't be a required argument in this function, since it won't be
    # passed if it isn't different from the default value..
    # TODO: Now that I think about it, it might make more sense to have the default values in the
    # dictionary of constructor arguments, right? Not 100% sure.

    assert Foo.setup("--a_or_b make_b") == Foo(a_or_b=B(b="default from make_b"))
    assert Foo.setup("--a_or_b make_b") == Foo(a_or_b=B(b="default from make_b"))
    assert Foo.setup("--a_or_b make_b --b foo") == Foo(a_or_b=B(b="foo"))


def test_subgroup_functions_receive_all_fields():
    """TODO: Decide how we want to go about this.
    Either the functions receive all the fields (the default values), or only the ones that are set
    (harder to implement).
    """

    @dataclass
    class Obj:
        a: float = 0.0
        b: str = "default from field"

    def make_obj(**kwargs) -> Obj:
        assert kwargs == {"a": 0.0, "b": "foo"}  # first case (current): receives all fields
        # assert kwargs == {"b": "foo"}  # second case: receive only set fields.
        return Obj(**kwargs)

    @dataclass
    class Foo(TestSetup):
        a_or_b: Obj = subgroups(
            {
                "make_obj": make_obj,
            },
            default_factory=make_obj,
        )

    Foo.setup("--a_or_b make_obj --b foo")


lambdas_arent_supported_yet = functools.partial(
    pytest.param,
    marks=pytest.mark.xfail(
        strict=True,
        raises=NotImplementedError,
        reason="Lambda expressions aren't allowed in the subgroup dict or default_factory at the moment.",
    ),
)


@pytest.mark.parametrize(
    "a_factory, b_factory",
    [
        (partial(A), partial(B)),
        (partial(A, a=321), partial(B, b="foobar")),
        lambdas_arent_supported_yet(lambda: A(), lambda: B()),
        lambdas_arent_supported_yet(lambda: A(a=123), lambda: B(b="foooo")),
    ],
)
def test_other_default_factories(a_factory: Callable[[], A], b_factory: Callable[[], B]):
    """Test using other kinds of default factories (i.e. functools.partial or lambda
    expressions)"""

    @dataclass
    class Foo(TestSetup):
        a_or_b: A | B = subgroups({"a": a_factory, "b": b_factory}, default="a")

    assert Foo.setup() == Foo(a_or_b=a_factory())
    assert Foo.setup("--a_or_b a --a 445") == Foo(a_or_b=A(a=445))
    assert Foo.setup("--a_or_b b") == Foo(a_or_b=b_factory())


@pytest.mark.parametrize(
    "a_factory, b_factory",
    [
        (partial(A, a=321), partial(B, b="foobar")),
        (partial(partial(A, a=111), a=321), partial(partial(B), b="foobar")),
        (partial(partial(A, a=111)), partial(partial(B, b="foobar"))),
        lambdas_arent_supported_yet(lambda: A(a=123), lambda: B(b="foooo")),
    ],
)
def test_help_string_displays_default_factory_arguments(
    a_factory: Callable[[], A], b_factory: Callable[[], B]
):
    """The help string should be basically the same when using a `partial` or a lambda that returns
    a dataclass, as using just the class itself.

    When using `functools.partial` or lambda expressions, we'd ideally also like the help text to
    show the field values from inside the `partial` or lambda, if possible.
    """

    # NOTE: Here we need to return just A() and B() with these default factories, so the defaults
    # for the fields are the same
    @dataclass
    class Foo(TestSetup):
        a_or_b: A | B = subgroups({"a": a_factory, "b": b_factory}, default="a")

    a_default_from_factory = a_factory().a
    b_default_from_factory = b_factory().b
    a_default_from_field = A().a
    b_default_from_field = B().b

    # Just to make sure that we're using a different value for the default.
    assert a_default_from_field != a_default_from_factory
    assert b_default_from_field != b_default_from_factory

    # Check that it doesn't use the default value from the field in the help text.
    assert f"--a float (default: {a_default_from_field})" not in Foo.get_help_text("")
    assert f"--a float (default: {a_default_from_field})" not in Foo.get_help_text("--a_or_b a")
    assert f"--b str (default: {b_default_from_field})" not in Foo.get_help_text("--a_or_b b")

    # Check that it uses the default value from the factory in the help text.
    assert f"--a float  (default: {a_default_from_factory})" in Foo.get_help_text("")
    assert f"--a float  (default: {a_default_from_factory})" in Foo.get_help_text("--a_or_b a")
    assert f"--b str  (default: {b_default_from_factory})" in Foo.get_help_text("--a_or_b b")


def test_factory_is_only_called_once():
    class_constructor_calls = 0
    partial_calls = 0

    class _partial(partial):
        def __call__(self, *args, **kwargs):
            nonlocal partial_calls
            partial_calls += 1
            return super().__call__(*args, **kwargs)

    @dataclass
    class SomeObj:
        a: int = 0

        def __post_init__(self):
            nonlocal class_constructor_calls
            class_constructor_calls += 1

    @dataclass
    class Config(TestSetup):
        obj: SomeObj = subgroups(
            {
                "a": SomeObj,
                "b": _partial(SomeObj, a=123),
            },
            default_factory=SomeObj,
        )

    assert class_constructor_calls == 0
    Config()
    assert class_constructor_calls == 1

    config = Config.setup("")
    assert class_constructor_calls == 2
    assert config.obj.a == 0

    config = Config.setup("--obj a --a 321")
    assert class_constructor_calls == 3
    assert config == Config(obj=SomeObj(a=321))
    assert class_constructor_calls == 4

    assert partial_calls == 0
    config = Config.setup("--obj b")
    assert partial_calls == 1
    assert class_constructor_calls == 5
    assert config.obj.a == 123


@pytest.mark.xfail(strict=True, reason="Not implemented yet. Remove this once it is.")
def test_all_subgroups_are_in_help_string():
    @dataclass
    class Foo(TestSetup):
        a_or_b: A | B = subgroups({"a": A, "b": B}, default_factory=B)

    help_text = Foo.get_help_text()

    assert "-a float, --a float  (default: 0.0)" in help_text
    assert "-b str, --b str  (default: bar)" in help_text


def test_typing_of_subgroups_function() -> None:
    """TODO: There should be a typing errors here. Could we check for it programmatically?"""
    # note: This should raise an error with the type checker:
    bob: A = subgroups({"a": A, "b": B})  # noqa: F841
    # reveal_type(bob)

    with pytest.raises(ValueError):
        other: A | B = subgroups({"a": A, "b": B}, default_factory=C)  # noqa: F841
    # reveal_type(other)


@dataclass
class ModelConfig:
    ...


@dataclass
class ModelAConfig(ModelConfig):
    lr: float = 3e-4
    optimizer: str = "Adam"
    betas: tuple[float, float] = (0.9, 0.999)


@dataclass
class ModelBConfig(ModelConfig):
    lr: float = 1e-3
    optimizer: str = "SGD"
    momentum: float = 1.234


@dataclass
class Config(TestSetup):
    # Which model to use
    model: ModelConfig = subgroups(
        {"model_a": ModelAConfig, "model_b": ModelBConfig},
        default_factory=ModelAConfig,
    )


def test_destination_substring_of_other_destination_issue191():
    """Test for https://github.com/lebrice/SimpleParsing/issues/191."""

    parser = ArgumentParser()
    parser.add_arguments(Config, dest="config")
    parser.add_arguments(Config, dest="config2")  # this produces and exception
    # parser.add_arguments(Config, dest="something") # this works as expected
    args = parser.parse_args("")

    config: Config = args.config
    assert config.model == ModelAConfig()


def test_subgroup_partial_with_nested_field():
    """Test the case where a subgroup has a nested dataclass field, and that nested field is an
    argument to the partial."""

    @dataclass
    class Obj:
        a: int = 0

    @dataclass
    class Foo:
        obj: Obj = field(default_factory=Obj)

    @dataclass
    class Config(TestSetup):
        foo: Foo = subgroups(
            {
                "simple": Foo,
                "default": partial(Foo, obj=Obj(a=123)),  # bad idea!
            },
            default="default",
        )

    first_config = Config()
    first_object = first_config.foo.obj
    second_config = Config()
    # Bad idea! This is reusing the dataclass instance!
    # TODO: Do we want to explicitly disallow this?
    assert second_config.foo.obj is first_object

    assert Config.setup("").foo.obj.a == 123
    assert Config.setup("--foo=default").foo.obj.a == 123
    assert Config.setup("--foo=simple").foo.obj.a == 0
    assert "--a int       (default: 123)" in Config.get_help_text()


class Model:
    def __init__(self, num_layers: int = 3, hidden_dim: int = 64):
        self.num_layers = num_layers
        self.hidden_dim = hidden_dim


@dataclass
class CustomAnnotation:
    default_factory: Callable[[], Model]


SmallModel = Annotated[
    Model, CustomAnnotation(default_factory=partial(Model, num_layers=1, hidden_dim=32))
]
BigModel = Annotated[
    Model, CustomAnnotation(default_factory=partial(Model, num_layers=12, hidden_dim=128))
]


@pytest.mark.xfail(strict=True, reason="Annotated isn't supported as an option yet.")
def test_annotated_as_subgroups():
    """Test using the new Annotated type to create variants of the same dataclass."""

    @dataclasses.dataclass
    class Config(TestSetup):
        model: Model = subgroups(
            {"small": SmallModel, "big": BigModel}, default_factory=SmallModel
        )

    assert Config.setup().model == SmallModel()
    # Hopefully this illustrates why Annotated aren't exactly great:
    # At runtime, they are basically the same as the original dataclass when called.
    assert SmallModel() == Model()
    assert BigModel() == Model()

    assert Config.setup("--model small").model == Model(num_layers=1, hidden_dim=32)
    assert Config.setup("--model big").model == Model(num_layers=12, hidden_dim=128)
    assert Config.setup("--num_layers 123").model == Model(num_layers=123, hidden_dim=32)


@dataclasses.dataclass(frozen=True)
class FrozenConfig:
    a: int = 1
    b: str = "bob"


def test_subgroups_doesnt_support_nonfrozen_instances():
    with pytest.raises(
        ValueError,
        match="'default' can either be a key of the subgroups dict or a hashable",
    ):
        _ = subgroups({"a": A, "b": B}, default=A(a=1.0))

    with pytest.raises(
        ValueError,
        match="'default' can either be a key of the subgroups dict or a hashable",
    ):
        _ = subgroups({"a": A(a=1.0), "b": B}, default=A(a=1.0))


odd = FrozenConfig(a=1, b="odd")
even = FrozenConfig(a=2, b="even")


@dataclasses.dataclass
class ConfigWithFrozen(TestSetup):
    conf: FrozenConfig = subgroups({"odd": odd, "even": even}, default=odd)


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("", ConfigWithFrozen(odd)),
        ("--conf=odd", ConfigWithFrozen(odd)),
        ("--conf=even", ConfigWithFrozen(even)),
        ("--conf=odd --a 123", ConfigWithFrozen(dataclasses.replace(odd, a=123))),
        ("--conf=even --a 100", ConfigWithFrozen(dataclasses.replace(even, a=100))),
    ],
)
def test_subgroups_supports_frozen_instances(command: str, expected: ConfigWithFrozen):
    assert ConfigWithFrozen.setup(command) == expected


@pytest.mark.parametrize(
    ("dataclass_type", "command"),
    [
        (Config, "--help"),
        (Config, "--model=model_a --help"),
        (Config, "--model=model_b --help"),
        (ConfigWithFrozen, "--help"),
        (ConfigWithFrozen, "--conf=odd --help"),
        (ConfigWithFrozen, "--conf=even --help"),
        (ConfigWithFrozen, "--conf=odd --a 123 --help"),
        (ConfigWithFrozen, "--conf=even --a 100 --help"),
    ],
)
def test_help(
    dataclass_type: type[TestSetup],
    command: str,
    file_regression: FileRegressionFixture,
    request: pytest.FixtureRequest,
):
    if sys.version_info[:2] != (3, 11):
        pytest.skip("The regression check is only ran with Python 3.11")

    here = Path(__file__).relative_to(Path.cwd())
    file_regression.check(
        f"""\
# Regression file for {Path(__file__).name:}::{test_help.__name__}

Given Source code:

```python
{"".join(inspect.getsourcelines(dataclass_type)[0])}
```

and command: {command!r}

We expect to get:

```console
{dataclass_type.get_help_text(command, prog="pytest")}
```
""",
        basename=request.node.name,
        extension=".md",
    )


# def test_subgroups_with_partials():
#     class Model:
#         def __init__(self, num_layers: int = 3, hidden_dim: int = 64):
#             self.num_layers = num_layers
#             self.hidden_dim = hidden_dim

#     _ModelConfig: type[Partial[Model]] = config_dataclass_for(Model)

#     ModelConfig = _ModelConfig()
#     SmallModel = _ModelConfig(num_layers=1, hidden_dim=32)
#     BigModel = _ModelConfig(num_layers=32, hidden_dim=128)

#     @dataclasses.dataclass
#     class Config(TestSetup):
#         model: Model = subgroups({"small": SmallModel, "big": BigModel}, default_factory=SmallModel)

#     assert Config.setup().model == SmallModel()
#     # Hopefully this illustrates why Annotated aren't exactly great:
#     # At runtime, they are basically the same as the original dataclass when called.
#     assert SmallModel() != Model()
#     assert SmallModel() == Model(num_layers=1, hidden_dim=32)
#     assert BigModel() != Model()
#     assert BigModel() == Model(num_layers=32, hidden_dim=128)

#     assert Config.setup("--model small").model == SmallModel()
#     assert Config.setup("--model big").model == BigModel()
#     assert Config.setup("--num_layers 123").model == Model(num_layers=123, hidden_dim=32)


@pytest.mark.parametrize("frozen", [True, False])
def test_nested_subgroups(frozen: bool):
    """Assert that #160 is fixed: https://github.com/lebrice/SimpleParsing/issues/160."""

    @dataclass(frozen=frozen)
    class FooConfig:
        ...

    @dataclass(frozen=frozen)
    class BarConfig:
        foo: FooConfig

    @dataclass(frozen=frozen)
    class FooAConfig(FooConfig):
        foo_param_a: float = 0.0

    @dataclass(frozen=frozen)
    class FooBConfig(FooConfig):
        foo_param_b: str = "foo_b"

    @dataclass(frozen=frozen)
    class Bar1Config(BarConfig):
        foo: FooConfig = subgroups(
            {"foo_a": FooAConfig, "foo_b": FooBConfig},
            default_factory=FooAConfig,
        )

    @dataclass(frozen=frozen)
    class Bar2Config(BarConfig):
        foo: FooConfig = subgroups(
            {"foo_a": FooAConfig, "foo_b": FooBConfig},
            default_factory=FooBConfig,
        )

    @dataclass(frozen=frozen)
    class Config(TestSetup):
        bar: Bar1Config | Bar2Config = subgroups(
            {"bar_1": Bar1Config, "bar_2": Bar2Config},
            default_factory=Bar2Config,
        )

    assert Config.setup("") == Config(bar=Bar2Config(foo=FooBConfig()))
    assert Config.setup("--bar=bar_1 --foo=foo_a") == Config(bar=Bar1Config(foo=FooAConfig()))


@dataclass
class ModelConfig:
    ...


@dataclass
class DatasetConfig:
    ...


@dataclass
class ModelAConfig(ModelConfig):
    lr: float = 3e-4
    optimizer: str = "Adam"
    betas: tuple[float, float] = (0.9, 0.999)


@dataclass
class ModelBConfig(ModelConfig):
    lr: float = 1e-3
    optimizer: str = "SGD"
    momentum: float = 1.234


@dataclass
class Dataset1Config(DatasetConfig):
    data_dir: str | Path = "data/foo"
    foo: bool = False


@dataclass
class Dataset2Config(DatasetConfig):
    data_dir: str | Path = "data/bar"
    bar: float = 1.2


@dataclass
class Config(TestSetup):
    # Which model to use
    model: ModelConfig = subgroups(
        {"model_a": ModelAConfig, "model_b": ModelBConfig},
        default_factory=ModelAConfig,
    )

    # Which dataset to use
    dataset: DatasetConfig = subgroups(
        {"dataset_1": Dataset1Config, "dataset_2": Dataset2Config},
        default_factory=Dataset2Config,
    )


def _parse_config(args: str) -> Config:
    return parse(
        Config,
        args=args,
        argument_generation_mode=ArgumentGenerationMode.NESTED,
        nested_mode=NestedMode.WITHOUT_ROOT,
    )


def test_ordering_of_args_doesnt_matter():
    """Test to confirm that #160 is fixed:"""

    # $ python issue.py --model model_a --model.lr 1e-2
    assert _parse_config(args="--model model_a --model.lr 1e-2") == Config(
        model=ModelAConfig(lr=0.01, optimizer="Adam", betas=(0.9, 0.999)),
        dataset=Dataset2Config(data_dir="data/bar", bar=1.2),
    )

    # I was expecting this to work given that both model configs have `lr` attribute
    # $ python issue.py --model.lr 1e-2.
    assert _parse_config(args="--model.lr 1e-2") == Config(
        model=ModelAConfig(lr=1e-2, optimizer="Adam", betas=(0.9, 0.999)),
        dataset=Dataset2Config(data_dir="data/bar", bar=1.2),
    )

    # $ python issue.py --model model_a --model.betas 0. 1.
    assert _parse_config(args="--model model_a --model.betas 0. 1.") == Config(
        model=ModelAConfig(lr=0.0003, optimizer="Adam", betas=(0.0, 1.0)),
        dataset=Dataset2Config(data_dir="data/bar", bar=1.2),
    )

    # % ModelA being the default, I was expecting this two work
    # $ python issue.py --model.betas 0. 1.
    assert _parse_config(args="--model.betas 0. 1.") == Config(
        model=ModelAConfig(lr=0.0003, optimizer="Adam", betas=(0.0, 1.0)),
        dataset=Dataset2Config(data_dir="data/bar", bar=1.2),
    )
