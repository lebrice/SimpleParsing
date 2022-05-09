from dataclasses import dataclass

from simple_parsing import ArgumentParser
from simple_parsing.helpers.partial import config_dataclass_for

parser = ArgumentParser()


# Suppose we import the Adam and SGD optimizers from PyTorch:


class Adam:
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


# Dynamically create a dataclass that will be used for the above type:

AdamConfig = config_dataclass_for(Adam, ignore_args="params")


@dataclass
class Config:

    # Which optimizer to use.
    optimizer: AdamConfig = AdamConfig(lr=3e-4)


parser.add_arguments(Config, "config")
args = parser.parse_args()


config: Config = args.config
print(config)

my_model_parameters = []  # nn.Sequential(...)

optimizer: Adam = config.optimizer(parameters=my_model_parameters)
print(optimizer)
