import pytest

pytest.register_assert_rewrite("test.testutils")

from . import testutils  # noqa: E402

__all__ = ["testutils"]
