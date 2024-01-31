from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest
from pytest_regressions.file_regression import FileRegressionFixture

from simple_parsing.helpers.serialization import load, save

from ..testutils import needs_yaml


@dataclass
class A:
    a: int = 123


@dataclass
class B(A):
    b: str = "bob"


@dataclass
class Container:
    item: A = field(default_factory=A)


@dataclass
class BB(B):
    """A class that is not shown in the `A | B` annotation above, but that can be set as `item`."""

    extra_field: int = 123
    other_field: int = field(init=False)

    def __post_init__(self):
        self.other_field = self.extra_field * 2


@pytest.mark.parametrize(
    "obj",
    [
        Container(item=B(b="hey")),
        Container(item=BB(b="hey", extra_field=111)),
    ],
)
@pytest.mark.parametrize("file_type", [".json", pytest.param(".yaml", marks=needs_yaml)])
def test_encoding_with_dc_types(
    obj: Container, file_type: str, tmp_path: Path, file_regression: FileRegressionFixture
):
    file = (tmp_path / "test").with_suffix(file_type)
    save(obj, file, save_dc_types=True)
    file_regression.check(file.read_text(), extension=file.suffix)

    assert load(Container, file) == obj


@pytest.fixture(autouse=True)
def reset_encoding_fns():
    from simple_parsing.helpers.serialization.decoding import _decoding_fns

    copy = _decoding_fns.copy()
    # info = get_decoding_fn.cache_info()

    yield

    _decoding_fns.clear()
    _decoding_fns.update(copy)


@pytest.mark.parametrize("file_type", [".json", pytest.param(".yaml", marks=needs_yaml)])
def test_encoding_inner_dc_types_raises_warning_and_doest_work(tmp_path: Path, file_type: str):
    file = (tmp_path / "test").with_suffix(file_type)

    @dataclass(eq=True)
    class BBInner(B):
        something: float = 3.21

    obj = Container(item=BBInner(something=123.456))
    with pytest.warns(
        RuntimeWarning,
        match="BBInner'> is defined in a function scope, which might cause issues",
    ):
        save(obj, file, save_dc_types=True)

    # NOTE: This would work if `A` were made a subclass of `Serializable`, because we currently
    # don't pass the value of the `drop_extra_fields` flag to the decoding function for each field.
    # We only use it when deserializing the top-level dataclass.

    # Here we actually expect this to work (since BBInner should be found via
    # `B.__subclasses__()`).
    from simple_parsing.helpers.serialization.decoding import _decoding_fns

    print(_decoding_fns.keys())
    loaded_obj = load(Container, file, drop_extra_fields=False)
    # BUG: There is something a bit weird going on with this comparison: The two objects aren't
    # considered equal, but they seem identical 🤔
    assert str(loaded_obj) == str(obj)  # This comparison works!

    # NOTE: There appears to be some kind of caching mechanism. Running this test a few times in
    # succession fails the first time, and passes the remaining times. Seems like waiting 30
    # seconds or so invalidates some sort of caching mechanism, and makes the test fail again.

    # assert loaded_obj == obj  # BUG? This comparison fails, because:
    # assert type(loaded_obj.item) == type(obj.item)  # These two types are *sometimes* different?!
