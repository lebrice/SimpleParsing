from __future__ import annotations
from simple_parsing import Serializable
from simple_parsing.helpers.serialization import from_dict, to_dict
from dataclasses import dataclass, field
import functools
import pytest

@dataclass
class InnerConfig:
    arg1: int = 1
    arg2: str = 'foo'
    arg1_post_init: str = field(init=False)
    
    def __post_init__(self):
        self.arg1_post_init = str(self.arg1)
    
    
@dataclass
class OuterConfig1(Serializable):
    out_arg: int = 0
    inner: InnerConfig = field(default_factory=InnerConfig)

@dataclass
class OuterConfig2(Serializable):
    out_arg: int = 0
    inner: InnerConfig = field(default_factory=functools.partial(InnerConfig, arg2='bar'))
    
@dataclass
class Level1:
    arg: int = 1
    
@dataclass
class Level2:
    arg: int = 1
    prev: Level1 = field(default_factory=Level1)
    

@dataclass
class Level3:
    arg: int = 1
    prev: Level2 = field(default_factory=Level2)
    

@pytest.mark.parametrize(
    ('config'),
    [
        (OuterConfig1()),
        (OuterConfig2()),
        (Level2()),
        (Level3()),
    ]
)
def test_nested_dataclasses_serialization(config: object):
    config_dict = to_dict(config)
    print(config_dict)
    new_config = from_dict(
        config.__class__,
        config_dict,
        drop_extra_fields=True,
    )
    assert config == new_config