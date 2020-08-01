import argparse
import textwrap
from dataclasses import dataclass, fields
from simple_parsing import field
from .testutils import *

# @pytest.mark.xfail(
#     "TODO: @lebrice Add something to make it easier to have 'flags'."
# )
def test_flags():
    @dataclass
    class Flags(TestSetup):
        debug: bool = False

        cuda:    bool = field(True)
        no_cuda: bool = field(False, dest="flags.cuda", action="store_true")

    flags = Flags.setup("")
    assert flags == Flags(
        debug=False,
        cuda=True,
        no_cuda=False,
    )
