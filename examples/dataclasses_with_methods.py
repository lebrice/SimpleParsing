
## - Argument dataclasses can also have methods!
import json
from dataclasses import dataclass, asdict

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
        with open(path, "r") as f:
            config_dict = json.load(f)
            return cls(**config_dict)


parser.add_arguments(HyperParameters, dest="hparams")

args = parser.parse_args()

hparams: HyperParameters = args.hparams
print(hparams)

# save and load from a json file: 
hparams.save("hyperparameters.json")
_hparams = HyperParameters.load("hyperparameters.json")
assert hparams == _hparams