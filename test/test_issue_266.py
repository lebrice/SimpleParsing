import dataclasses
import tempfile

import simple_parsing
from simple_parsing.helpers.serialization import register_decoding_fn, get_decoding_fn


@dataclasses.dataclass
class Id:
    value: str

    def __post_init__(self):
        assert isinstance(self.value, str)


class NonDCId:
    def __init__(self, value: str):
        assert isinstance(value, str)
        self.value = value

    def __eq__(self, other):
        return self.value == other.value


register_decoding_fn(Id, (lambda x, drop_extra_fields: Id(value=x)))
register_decoding_fn(NonDCId, (lambda x: NonDCId(value=x)))


@dataclasses.dataclass
class Person:
    name: str
    other_id: NonDCId
    id: Id


def test_parse_helper_uses_custom_decoding_fn():
    config_str = """
    name: bob
    id: hi
    other_id: hello
    """

    # ok
    assert get_decoding_fn(Person)({"name": "bob", "id": "hi", "other_id": "hello"}) == Person(
        "bob", NonDCId("hello"), Id("hi")
    )  # type: ignore

    with tempfile.NamedTemporaryFile("w", suffix=".yaml") as f:
        f.write(config_str)
        f.flush()

        parsed = simple_parsing.parse(Person, f.name, args=[])
        assert parsed == Person("bob", NonDCId("hello"), Id("hi"))  # type: ignore
