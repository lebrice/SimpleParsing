import argparse
from typing import *
import shlex
import pytest
import simple_parsing
from simple_parsing import InconsistentArgumentError, ParseableFromCommandLine, Formatter


class TestSetup():
    @classmethod
    def setup(cls, arguments: Optional[str] = "", multiple = False) -> argparse.Namespace:
        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        # parser = argparse.ArgumentParser(formatter_class=Formatter)
        cls.add_arguments(parser, multiple=multiple)
        # BUG: the arguments might have quotes in them, hence we shouldn't necessarily just split() with whitespace..
        if arguments is None:
            return parser.parse_args()
        else:
            splits = shlex.split(arguments)
            return parser.parse_args(splits)
    
    @classmethod
    def get_help_text(cls, multiple=False):
        import contextlib
        from io import StringIO
        f = StringIO()
        with contextlib.suppress(SystemExit), contextlib.redirect_stdout(f):
            _ = cls.setup("--help")
        s = f.getvalue()
        return s
