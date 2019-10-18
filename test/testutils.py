import argparse
from typing import *

import pytest
import simple_parsing
from simple_parsing import InconsistentArgumentError, ParseableFromCommandLine


class Setup():
    @classmethod
    def setup(cls: ParseableFromCommandLine, arguments = "", multiple = False) -> str:
        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        cls.add_arguments(parser, multiple=multiple)
        args = parser.parse_args(arguments.split())
        return args
    
    @classmethod
    def get_help_text(cls: ParseableFromCommandLine, multiple=False):
        import contextlib
        from io import StringIO
        f = StringIO()
        with contextlib.suppress(SystemExit), contextlib.redirect_stdout(f):
            _ = cls.setup("--help")
        s = f.getvalue()
        return s
