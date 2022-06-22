from dataclasses import dataclass
from simple_parsing import flag
from .testutils import TestSetup, xfail


@xfail(reason="TODO: @lebrice Add something to make it easier to have 'flags'.")
def test_flags():
    @dataclass
    class Flags(TestSetup):
        debug: bool = flag(False)

        cuda: bool = flag(True, opposite_prefix="no-")

    assert Flags.setup("--no-cuda") == Flags(debug=False, cuda=False)
