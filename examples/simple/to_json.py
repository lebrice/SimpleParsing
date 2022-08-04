import os
from dataclasses import asdict, dataclass

from simple_parsing import ArgumentParser
from simple_parsing.helpers import Serializable


@dataclass
class HParams(Serializable):
    """Set of options for the training of a Model."""

    num_layers: int = 4
    num_units: int = 64
    optimizer: str = "ADAM"
    learning_rate: float = 0.001


parser = ArgumentParser()
parser.add_arguments(HParams, dest="hparams")
args = parser.parse_args()


hparams: HParams = args.hparams


print(asdict(hparams))
expected = """
{'num_layers': 4, 'num_units': 64, 'optimizer': 'ADAM', 'learning_rate': 0.001}
"""


hparams.save_json("config.json")
hparams_ = HParams.load_json("config.json")
assert hparams == hparams_


os.remove("config.json")
