from dataclasses import dataclass
from typing import List

from typing_extensions import assert_type

from simple_parsing import flag

from .testutils import TestSetup

assert_type(flag(), bool)
assert_type(flag(nargs=None), bool)
assert_type(flag(nargs="?"), bool)
assert_type(flag(nargs=0), bool)
assert_type(flag(nargs=1), List[bool])
assert_type(flag(nargs="*"), List[bool])
assert_type(flag(nargs="+"), List[bool])


def test_flags():
    @dataclass
    class Flags(TestSetup):
        debug: bool = flag(False)

        cuda: bool = flag(True, negative_prefix="--no-")

    assert Flags.setup("--no-cuda") == Flags(debug=False, cuda=False)
