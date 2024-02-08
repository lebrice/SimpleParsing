from dataclasses import dataclass
from pathlib import Path

from simple_parsing.helpers.serialization.yaml_schema import save_yaml_with_schema


@dataclass
class Bob:
    """Some docstring."""

    foo: int = 123
    """A very important field."""


@dataclass
class Nested:
    """Some docstring of the 'Nested' class."""

    bob: Bob  # inline comment for field `bob` of class `Nested`
    """bobobobo."""

    other_field: str  # inline comment for `other_field` of class `Nested`
    """This is a docstring for the other field."""


if __name__ == "__main__":
    save_yaml_with_schema(
        Bob(foo=222),
        Path(__file__).parent / "bob_with_schema.yaml",
    )

    save_yaml_with_schema(
        Nested(bob=Bob(foo=222), other_field="babab"),
        Path(__file__).parent / "nested_with_schema.yaml",
    )
