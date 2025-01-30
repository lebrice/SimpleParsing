import sys
from dataclasses import InitVar, dataclass
from typing import Any

import pytest
from typing_extensions import Literal

from .testutils import TestSetup


@pytest.mark.skipif(
    sys.version_info[:2] < (3, 8),
    reason="Before 3.8 `InitVar[tp] is InitVar` so it's impossible to retrieve field type",
)
@pytest.mark.parametrize(
    "tp, passed_value, expected",
    [
        (int, "1", 1),
        (float, "1.4", 1.4),
        (tuple[int, float], "2 -1.2", (2, -1.2)),
        (list[str], "12 abc", ["12", "abc"]),
        (Literal[1, 2, 3, "4"], "1", 1),
        (Literal[1, 2, 3, "4"], "4", "4"),
    ],
)
def test_initvar(tp: type[Any], passed_value: str, expected: Any) -> None:
    @dataclass
    class Foo(TestSetup):
        init_var: InitVar[tp]

        def __post_init__(self, init_var: tp) -> None:
            assert init_var == expected

    Foo.setup(f"--init_var {passed_value}")
