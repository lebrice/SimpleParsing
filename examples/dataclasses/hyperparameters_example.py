""" - Argument dataclasses can also have methods! """
import json
import os
from dataclasses import asdict, dataclass

from simple_parsing import ArgumentParser

parser = ArgumentParser()


@dataclass
class HyperParameters:
    batch_size: int = 32
    optimizer: str = "ADAM"
    learning_rate: float = 1e-4
    max_epochs: int = 100
    l1_reg: float = 1e-5
    l2_reg: float = 1e-5

    def save(self, path: str):
        with open(path, "w") as f:
            config_dict = asdict(self)
            json.dump(config_dict, f, indent=1)

    @classmethod
    def load(cls, path: str):
        with open(path) as f:
            config_dict = json.load(f)
            return cls(**config_dict)


parser.add_arguments(HyperParameters, dest="hparams")

args = parser.parse_args()

hparams: HyperParameters = args.hparams
print(hparams)
expected = """
HyperParameters(batch_size=32, optimizer='ADAM', learning_rate=0.0001, max_epochs=100, l1_reg=1e-05, l2_reg=1e-05)
"""

# save and load from a json file:
hparams.save("hyperparameters.json")
_hparams = HyperParameters.load("hyperparameters.json")
assert hparams == _hparams


os.remove("hyperparameters.json")
