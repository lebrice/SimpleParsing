from __future__ import annotations
import sys
from pathlib import Path

import pytest
from dataclasses import dataclass
from simple_parsing import ArgumentParser, Serializable

from .b import B


@pytest.mark.parametrize(
    'sys_argv, b_value, p_value', [
        (['test.py', '--v', '1'], 1, None),
        (['test.py', '--v', '2', '--p', 'test/'], 2, Path('test/')),
        (['test.py', '--v', '3', '--p', 'test/test1'], 3, Path('test/test1')),
        pytest.param(['test.py'], None, None, marks=pytest.mark.xfail(reason='no default value in the dataclass'))
    ]
)
def test_postponed_annotations_with_baseclass(sys_argv: list[str], b_value: int | None, p_value: Path | None, monkeypatch):
    monkeypatch.setattr(sys, 'argv', sys_argv)
    parser = ArgumentParser()
    parser.add_arguments(B, 'b')
    args = parser.parse_args()
    assert args.b.v == b_value
    assert args.b.p == p_value

@dataclass
class MyArguments(Serializable):
    arg1: str = 'this_argment'
    arg2: str | Path = Path('test_dir')
    
@pytest.mark.parametrize(
    'sys_argv, result', [
        (['test.py'], 'this_argment'),
        (['test.py', '--arg1', 'test2'], 'test2')
    ],
)
def test_postponed_annotations_with_Serializable_base(sys_argv, result):
    parser = ArgumentParser()
    parser.add_arguments(MyArguments, 'myargs')
    args, _ = parser.parse_known_args(sys_argv)
    assert args.myargs.arg1 == result
    assert args.myargs.arg2 == Path('test_dir')