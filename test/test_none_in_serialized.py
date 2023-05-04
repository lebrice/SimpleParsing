from dataclasses import dataclass
from simple_parsing.helpers import Serializable
import tempfile

def test_none_during_decoding_serialized():
    @dataclass
    class A(Serializable):
        a: float = None

    a = A()

    with tempfile.NamedTemporaryFile("w+", suffix=".json") as fp:
        a.save(fp.name)
        b = A.load(fp.name)

    assert a == b