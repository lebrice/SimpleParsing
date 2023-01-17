from __future__ import annotations
from simple_parsing.helpers.serialization import to_dict, from_dict
from simple_parsing import subgroups, Serializable
from .testutils import TestSetup
from dataclasses import dataclass, field


@dataclass
class A(TestSetup):
    a: float = 0.0


@dataclass
class B(TestSetup):
    b: str = "bar"
    b_post_init: str = field(init=False)
    
    def __post_init__(self):
        self.b_post_init = self.b + '_post'


@dataclass
class AB(TestSetup, Serializable):
    integer_only_by_post_init: int = field(init=False)
    integer_in_string: str = "1"
    a_or_b: A | B = subgroups({"a": A, "b": B}, default="a")

    def __post_init__(self):
        self.integer_only_by_post_init = int(self.integer_in_string)

def test_to_dict_from_dict():
    config = AB.setup("--a_or_b b --b foo --integer_in_string 2")
    config_dict = to_dict(config)
    print(config_dict)
    new_config = from_dict(AB, config_dict,drop_extra_fields=True)
    print(new_config)
    assert config == new_config
    
def test_serialization_yaml():
    config = AB.setup("--a_or_b b --b foo --integer_in_string 2")
    dump_str = config.dumps_yaml()
    new_config = AB.loads_yaml(dump_str)
    assert config == new_config
    
def test_serialization_json():
    config = AB.setup("--a_or_b b --b foo --integer_in_string 2")
    dump_str = config.dumps_json()
    new_config = AB.loads_json(dump_str)
    assert config == new_config
    