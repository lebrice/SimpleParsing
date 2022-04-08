import pytest

pytest.register_assert_rewrite("test.testutils")

from . import testutils
from .testutils import *
