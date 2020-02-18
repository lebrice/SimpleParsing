
from dataclasses import dataclass

from test.testutils import TestSetup

from simple_parsing import ArgumentParser, field


def test_aliases_with_given_dashes():
    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(default="/out", alias=["-o", "--out"])

    foo = Foo.setup("--output_dir /bob")
    assert foo.output_dir == "/bob"

    foo = Foo.setup("-o /cat")
    assert foo.output_dir == "/cat"

    foo = Foo.setup("--out /john")
    assert foo.output_dir == "/john"


def test_aliases_without_dashes():
    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(default="/out", alias=["o", "out"])

    foo = Foo.setup("--output_dir /bob")
    assert foo.output_dir == "/bob"

    foo = Foo.setup("-o /cat")
    assert foo.output_dir == "/cat"

    foo = Foo.setup("--out /john")
    assert foo.output_dir == "/john"
