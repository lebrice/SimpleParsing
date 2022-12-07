import sys
from pathlib import Path

import pytest

from simple_parsing import ArgumentParser

from .b import B


@pytest.mark.parametrize(
    'sys_argv, b_value, p_value', [
        (['test.py', '--v', '1'], 1, None),
        (['test.py', '--v', '2', '--p', 'test/'], 2, Path('test/')),
        (['test.py', '--v', '3', '--p', 'test/test1'], 3, Path('test/test1')),
        # pytest.param(['test.py'], None, None, marks=pytest.mark.xfail(reason='no default value in the dataclass'))
    ]
)
def test_postponed_annotation_with_baseclass(sys_argv, b_value, p_value, monkeypatch):
    monkeypatch.setattr(sys, 'argv', sys_argv)
    parser = ArgumentParser()
    parser.add_arguments(B, 'b')
    args = parser.parse_args()
    assert args.b.v == b_value
    assert args.b.p == p_value