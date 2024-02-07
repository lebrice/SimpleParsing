from dataclasses import dataclass
from pathlib import Path

from pytest_regressions.file_regression import FileRegressionFixture

from simple_parsing.helpers.serialization.serializable import load_yaml
from simple_parsing.helpers.serialization.yaml_schema import save_yaml_with_schema


@dataclass
class Bob:
    """Some docstring."""

    foo: int = 123
    """A very important field."""


@dataclass
class Nested:
    bob: Bob  # inline comment for field `bob` of class `Nested`
    other_field: str  # inline comment for `other_field` of class `Nested`


def test_save_with_yaml_schema(tmp_path: Path, file_regression: FileRegressionFixture):
    dc = Nested(bob=Bob(foo=222), other_field="babab")
    savepath = tmp_path / "nested.yaml"
    schemas_dir = tmp_path / ".schemas"
    schemas_dir.mkdir()

    schema_file = save_yaml_with_schema(dc, savepath, generated_schemas_dir=schemas_dir)
    assert schema_file.exists()
    loaded_dc = load_yaml(type(dc), savepath)
    assert loaded_dc == dc
    # todo: Unsure how I could test that the schema is generated correctly except manually:
    file_regression.check(schema_file.read_text() + "\n", extension=".json")
