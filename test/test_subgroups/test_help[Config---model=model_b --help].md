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

and command: '--model=model_b --help'

We expect to get:

```console
usage: pytest [-h] [--model {model_a,model_b}] [--lr float] [--optimizer str]
              [--momentum float]

options:
  -h, --help            show this help message and exit

Config ['config']:
  Config(model: 'ModelConfig' = <factory>)

  --model {model_a,model_b}
                        Which model to use (default: model_a)

ModelBConfig ['config.model']:
  ModelBConfig(lr: 'float' = 0.001, optimizer: 'str' = 'SGD', momentum: 'float' = 1.234)

  --lr float            (default: 0.001)
  --optimizer str       (default: SGD)
  --momentum float      (default: 1.234)

```
