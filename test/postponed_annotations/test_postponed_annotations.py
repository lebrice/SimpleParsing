from __future__ import annotations
from pathlib import Path

import pytest
from dataclasses import dataclass
from simple_parsing import Serializable

from .b import B
from .multi_inherits import P4, C
from ..test_utils import TestSetup


@pytest.mark.parametrize(
    'argv, v, p', [
        ('--v 1', 1, None),
        ("--v 2 --p test/", 2, Path('test/')),
        ("--v 3 --p test/test1", 3, Path('test/test1')),
        pytest.param("", None, None, marks=pytest.mark.xfail(reason='no default value in the dataclass'))
    ]
)
def test_postponed_annotations_with_baseclass(argv: str, v: int | None, p: Path | None):
    assert B.setup(argv) == B(v=v,p=p)


@dataclass
class MyArguments(Serializable, TestSetup):
    arg1: str = 'this_argument'
    arg2: str | Path = Path('test_dir')
    
@pytest.mark.parametrize(
    'argv, arg1, arg2', [
        ('', 'this_argument', 'test_dir'),
        ('--arg1 test1', 'test1', Path('test_dir')),
        ('--arg2 test_path_dir', 'this_argument', Path('test_path_dir')),
    ],
)
def test_postponed_annotations_with_Serializable_base(argv: str, arg1: str, arg2: str | Path):
    actual_args = MyArguments.setup(argv)
    target_args = MyArguments(arg1=arg1, arg2=arg2)
    assert actual_args.arg1 == target_args.arg1
    assert str(actual_args.arg2) == str(target_args.arg2)
    

def test_postponed_annotations_with_multi_depth_inherits_1():
    assert P4.setup('--a1 4 --a2 3 --a3 2 --a4 1') == P4(4,3,2,1)
    
def test_postponed_annotations_with_multi_depth_inherits_2():
    assert C.setup('--p test/test1 --v 1 --m string') == C(Path('test/test1'), 1, 'string')