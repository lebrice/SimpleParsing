import argparse
import textwrap
from dataclasses import dataclass, fields
from simple_parsing import field, flag
from .testutils import *

@xfail(reason="TODO: @lebrice Add something to make it easier to have 'flags'.")
def test_flags():
    @dataclass
    class Flags(TestSetup):
        debug: bool = flag(False)

        cuda:    bool = flag(True, opposite_prefix="no-")

    assert Flags.setup("--no-cuda") == Flags(debug=False, cuda=False)
