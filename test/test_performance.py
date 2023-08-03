import functools
import importlib
import sys
from typing import Callable, TypeVar
import pytest
from pytest_benchmark.fixture import BenchmarkFixture


def _import_sp():
    assert "simple_parsing" not in sys.modules
    __import__("simple_parsing")


def _unimport_sp():
    if "simple_parsing" in sys.modules:
        import simple_parsing  # noqa

        del simple_parsing
        importlib.invalidate_caches()
        sys.modules.pop("simple_parsing")
    assert "simple_parsing" not in sys.modules


@pytest.mark.benchmark(
    group="import",
)
def test_import_performance(benchmark: BenchmarkFixture):
    # NOTE: Issue is that the `conftest.py` actually already imports simple-parsing!
    benchmark.pedantic(_import_sp, setup=_unimport_sp, rounds=10)


def _clear_lru_caches():
    from simple_parsing.docstring import dp_parse, inspect_getdoc, inspect_getsource

    dp_parse.cache_clear()
    inspect_getdoc.cache_clear()
    inspect_getsource.cache_clear()


C = TypeVar("C", bound=Callable)


def clear_caches_before(fn: C) -> C:
    @functools.wraps(fn)
    def _inner(*args, **kwargs):
        _clear_lru_caches()
        return fn(*args, **kwargs)

    return _inner  # type: ignore


def test_parse_performance(benchmark: BenchmarkFixture):
    import simple_parsing as sp
    from test.nesting.example_use_cases import HyperParameters

    benchmark(
        clear_caches_before(sp.parse),
        HyperParameters,
        args="--age_group.num_layers 5 --age_group.num_units 65 ",
    )
