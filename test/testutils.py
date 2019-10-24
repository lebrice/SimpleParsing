import argparse
from typing import *
import shlex
import pytest
import simple_parsing
from simple_parsing import InconsistentArgumentError, ArgumentParser, Formatter


from simple_parsing.utils import camel_case

T = TypeVar("T", bound="TestSetup")

class TestSetup():
    @classmethod
    def setup(cls: Type[T], arguments: Optional[str] = "", dest: Optional[str] = None) -> T:
        """Basic setup for a test.
        
        Keyword Arguments:
            arguments {Optional[str]} -- The arguments to pass to the parser (default: {""})
            dest {Optional[str]} -- the attribute where the argument should be stored. (default: {None})
        
        Returns:
            {cls}} -- the class's type.
        """
        parser = simple_parsing.ArgumentParser()
        if dest is None:
            dest = camel_case(cls.__name__)
        
        parser.add_arguments(cls, dest=dest)

        if arguments is None:
            args = parser.parse_args()
        else:
            splits = shlex.split(arguments)
            args = parser.parse_args(splits)
        instance: cls = getattr(parser, dest) #type: ignore
        return instance
    
    @classmethod
    def setup_multiple(cls: Type[T], num_to_parse: int, arguments: Optional[str] = "") -> Tuple[T, ...]:
        parser = simple_parsing.ArgumentParser()
        class_name = camel_case(cls.__name__)
        for i in range(num_to_parse):
            parser.add_arguments(cls, f"{class_name}_{i}")

        if arguments is None:
            args = parser.parse_args()
        else:
            splits = shlex.split(arguments)
            args = parser.parse_args(splits)

        return tuple(getattr(args, f"{class_name}_{i}") for i in range(num_to_parse))
        

    @classmethod
    def get_help_text(cls, multiple=False):
        import contextlib
        from io import StringIO
        f = StringIO()
        with contextlib.suppress(SystemExit), contextlib.redirect_stdout(f):
            _ = cls.setup("--help")
        s = f.getvalue()
        return s
