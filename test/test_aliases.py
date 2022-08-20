from dataclasses import dataclass

from simple_parsing import field, Alias
from test.testutils import TestSetup, raises_unrecognized_args, raises_ambiguous_option


def test_aliases_with_given_dashes():
    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(default="/out", alias=["-o", "--out"])

    foo = Foo.setup("--output_dir /bob")
    assert foo.output_dir == "/bob"

    foo = Foo.setup("-o /cat")
    assert foo.output_dir == "/cat"

    with raises_ambiguous_option():
        Foo.setup("--o /cake")

    foo = Foo.setup("--out /john")
    assert foo.output_dir == "/john"

    with raises_unrecognized_args():
        Foo.setup("-out /joe")


def test_aliases_without_dashes():
    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(default="/out", alias=["o", "out"])

    foo = Foo.setup("--output_dir /bob")
    assert foo.output_dir == "/bob"

    foo = Foo.setup("-o /cat")
    assert foo.output_dir == "/cat"

    with raises_ambiguous_option():
        Foo.setup("--o /cat")

    with raises_unrecognized_args():
        Foo.setup("-out /john")

    foo = Foo.setup("--out /john")
    assert foo.output_dir == "/john"


def test_aliases_with_unsuppressed_prefix():
    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(default="/out", alias=[Alias("-o"), Alias("--out")])

    foo = Foo.setup("--prefix_output_dir /bob", prefix="prefix_")
    assert foo.output_dir == "/bob"

    with raises_unrecognized_args():
        Foo.setup("--output_dir /bob", prefix="prefix_")

    foo = Foo.setup("-prefix_o /cat", prefix="prefix_")
    assert foo.output_dir == "/cat"

    with raises_unrecognized_args():
        Foo.setup("-o /cat", prefix="prefix_")

    foo = Foo.setup("--prefix_out /john", prefix="prefix_")
    assert foo.output_dir == "/john"

    with raises_unrecognized_args():
        Foo.setup("--out /john", prefix="prefix_")


def test_aliases_with_suppressed_prefix():
    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(default="/out",
                                alias=[Alias("-o", suppress_prefix=True),
                                       Alias("--out", suppress_prefix=True)])

    foo = Foo.setup("--prefix_output_dir /bob", prefix="prefix_")
    assert foo.output_dir == "/bob"

    with raises_unrecognized_args():
        Foo.setup("--output_dir /bob", prefix="prefix_")

    foo = Foo.setup("-o /cat", prefix="prefix_")
    assert foo.output_dir == "/cat"

    foo = Foo.setup("--o /cake", prefix="prefix_")
    assert foo.output_dir == "/cake"

    with raises_unrecognized_args():
        Foo.setup("-prefix_o /bob", prefix="prefix_")

    foo = Foo.setup("--prefix_o /bob", prefix="prefix_")
    assert foo.output_dir == "/bob"

    foo = Foo.setup("--out /john", prefix="prefix_")
    assert foo.output_dir == "/john"
