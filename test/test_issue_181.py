from __future__ import annotations
from simple_parsing import Serializable, ArgumentParser
from dataclasses import dataclass
import pytest

@dataclass
class MyArguments(Serializable):
    arg1: str = 'this_argment'
    
@pytest.mark.parametrize(
    'sys_argv, result', [
        (['test.py'], 'this_argment'),
        (['test.py', '--arg1', 'test2'], 'test2')
    ],
)
def test_simple_parsing(sys_argv, result):
    parser = ArgumentParser()
    parser.add_arguments(MyArguments, 'myargs')
    args, _ = parser.parse_known_args(sys_argv)
    assert args.myargs.arg1 == result