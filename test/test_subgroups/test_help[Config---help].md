# Regression file for test_subgroups.py::test_help

Given Source code:

```python
@dataclass
class Config(TestSetup):
    # Which model to use
    model: ModelConfig = subgroups(
        {"model_a": ModelAConfig, "model_b": ModelBConfig},
        default_factory=ModelAConfig,
    )

```

and command: '--help'

We expect to get:

```console
usage: pytest [-h] [--model {model_a,model_b}] [--lr float] [--optimizer str]
              [--betas float float]

options:
  -h, --help            show this help message and exit

Config ['config']:
  Config(model: 'ModelConfig' = <factory>)

  --model {model_a,model_b}
                        Which model to use (default: model_a)

ModelAConfig ['config.model']:
  ModelAConfig(lr: 'float' = 0.0003, optimizer: 'str' = 'Adam', betas: 'tuple[float, float]' = (0.9, 0.999))

  --lr float            (default: 0.0003)
  --optimizer str       (default: Adam)
  --betas float float   (default: (0.9, 0.999))

```
