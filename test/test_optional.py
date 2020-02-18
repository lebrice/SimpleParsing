from dataclasses import dataclass
from typing import Optional
from simple_parsing import ArgumentParser



@dataclass
class Config:
    seed: Optional[int] = None

def test_optional_seed():
    """Test that a value marked as Optional works fine.
    
    (Reproduces https://github.com/lebrice/SimpleParsing/issues/14#issue-562538623)
    """
    parser = ArgumentParser()
    parser.add_arguments(Config, dest="config")

    args = parser.parse_args("".split())
    config: Config = args.config
    assert config == Config()

    args = parser.parse_args("--seed 123".split())
    config: Config = args.config
    assert config == Config(123)