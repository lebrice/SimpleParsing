

from dataclasses import dataclass

from test.testutils import TestSetup

from simple_parsing import ArgumentParser, field, ConflictResolution


def test_cmd_false_doesnt_create_conflicts():
    @dataclass
    class A:
        batch_size: int = field(default=10, cmd=False)
        
    @dataclass
    class B:
        batch_size: int = 20
    
    # @dataclass
    # class Foo(TestSetup):
    #     a: A = mutable_field(A)
    #     b: B = mutable_field(B)
    
    parser = ArgumentParser(conflict_resolution=ConflictResolution.NONE)
    parser.add_arguments(A, "a")
    parser.add_arguments(B, "b")
    args = parser.parse_args("--batch_size 32".split())
    a: A = args.a
    b: B = args.b
    assert a == A()
    assert b == B(batch_size=32)
    
    