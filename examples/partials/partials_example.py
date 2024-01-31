from __future__ import annotations

from dataclasses import dataclass

from simple_parsing import ArgumentParser
from simple_parsing.helpers import subgroups
from simple_parsing.helpers.partial import Partial, config_for


# Suppose we want to choose between the Adam and SGD optimizers from PyTorch:
# (NOTE: We don't import pytorch here, so we just create the types to illustrate)
class Optimizer:
    def __init__(self, params):
        ...


class Adam(Optimizer):
    def __init__(
        self,
        params,
        lr: float = 3e-4,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eps: float = 1e-08,
    ):
        self.params = params
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps


class SGD(Optimizer):
    def __init__(
        self,
        params,
        lr: float = 3e-4,
        weight_decay: float | None = None,
        momentum: float = 0.9,
        eps: float = 1e-08,
    ):
        self.params = params
        self.lr = lr
        self.weight_decay = weight_decay
        self.momentum = momentum
        self.eps = eps


# Dynamically create a dataclass that will be used for the above type:
# NOTE: We could use Partial[Adam] or Partial[Optimizer], however this would treat `params` as a
# required argument.
# AdamConfig = Partial[Adam]  # would treat 'params' as a required argument.
# SGDConfig = Partial[SGD]    # same here
AdamConfig: type[Partial[Adam]] = config_for(Adam, ignore_args="params")
SGDConfig: type[Partial[SGD]] = config_for(SGD, ignore_args="params")


@dataclass
class Config:
    # Which optimizer to use.
    optimizer: Partial[Optimizer] = subgroups(
        {
            "sgd": SGDConfig,
            "adam": AdamConfig,
        },
        default_factory=AdamConfig,
    )


parser = ArgumentParser()
parser.add_arguments(Config, "config")
args = parser.parse_args()


config: Config = args.config
print(config)
expected = "Config(optimizer=AdamConfig(lr=0.0003, beta1=0.9, beta2=0.999, eps=1e-08))"

my_model_parameters = [123]  # nn.Sequential(...).parameters()

optimizer = config.optimizer(params=my_model_parameters)
print(vars(optimizer))
expected += """
{'params': [123], 'lr': 0.0003, 'beta1': 0.9, 'beta2': 0.999, 'eps': 1e-08}
"""
