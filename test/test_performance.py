import functools
import importlib
import sys
from typing import Callable, TypeVar
import pytest
from pytest_benchmark.fixture import BenchmarkFixture

C = TypeVar("C", bound=Callable)


def import_sp():
    assert "simple_parsing" not in sys.modules
    __import__("simple_parsing")


def unimport_sp():
    if "simple_parsing" in sys.modules:
        import simple_parsing  # noqa

        del simple_parsing
        importlib.invalidate_caches()
        sys.modules.pop("simple_parsing")
    assert "simple_parsing" not in sys.modules


def clear_lru_caches():
    from simple_parsing.docstring import dp_parse, inspect_getdoc, inspect_getsource

    dp_parse.cache_clear()
    inspect_getdoc.cache_clear()
    inspect_getsource.cache_clear()


def call_before(before: Callable[[], None], fn: C) -> C:
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        before()
        return fn(*args, **kwargs)

    return wrapped  # type: ignore


@pytest.mark.benchmark(
    group="import",
)
def test_import_performance(benchmark: BenchmarkFixture):
    # NOTE: Issue is that the `conftest.py` actually already imports simple-parsing!
    benchmark(call_before(unimport_sp, import_sp))


def test_parse_performance(benchmark: BenchmarkFixture):
    import simple_parsing as sp
    from test.nesting.example_use_cases import HyperParameters

    benchmark(
        call_before(clear_lru_caches, sp.parse),
        HyperParameters,
        args="--age_group.num_layers 5 --age_group.num_units 65 ",
    )
