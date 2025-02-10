from typing import Union
import dataclasses
import simple_parsing
import yaml
from pathlib import Path

@dataclasses.dataclass
class ModelTypeA:
    model_a_param: str = "default_a"

@dataclasses.dataclass
class ModelTypeB:
    model_b_param: str = "default_b"

@dataclasses.dataclass
class TrainConfig:
    model_type: Union[ModelTypeA, ModelTypeB] = simple_parsing.subgroups(
        {"type_a": ModelTypeA, "type_b": ModelTypeB},
        default_factory=ModelTypeA,
        positional=False,
    )

def main():
    # Create a config file
    config_path = Path("repro_subgroup_minimal.yaml")
    config = {
        "model_a_param": "test"  # This should work but fails
    }
    with config_path.open('w') as f:
        yaml.dump(config, f)

    print("\nTrying with config file:")
    try:
        # This fails with:
        # RuntimeError: ['model_a_param'] are not fields of <class '__main__.TrainConfig'> at path 'config'!
        args = simple_parsing.parse(TrainConfig, add_config_path_arg=True, args=['--config_path', 'repro_subgroup_minimal.yaml'])
        print(f"Config from file: {args}")
    except RuntimeError as e:
        print(f"Failed with config file as expected: {e}")

    print("\nTrying with CLI args:")
    # This works fine
    args = simple_parsing.parse(TrainConfig, args=['--model_a_param', 'test'])
    print(f"Config from CLI: {args}")

if __name__ == "__main__":
    main() 