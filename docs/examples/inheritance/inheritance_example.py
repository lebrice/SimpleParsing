from dataclasses import dataclass

from simple_parsing import ArgumentParser
from simple_parsing.helpers import Serializable


@dataclass
class GANHyperParameters(Serializable):
    batch_size: int = 32  # batch size
    d_steps: int = 1  # number of generator updates
    g_steps: int = 1  # number of discriminator updates
    learning_rate: float = 1e-4
    optimizer: str = "ADAM"


@dataclass
class WGANHyperParameters(GANHyperParameters):
    lambda_coeff: float = 10  # the lambda penalty coefficient.


@dataclass
class WGANGPHyperParameters(WGANHyperParameters):
    gp_penalty: float = 1e-6  # Gradient penalty coefficient


parser = ArgumentParser()
parser.add_argument(
    "--load_path",
    type=str,
    default=None,
    help="If given, the HyperParameters are read from the given file instead of from the command-line.",
)
parser.add_arguments(WGANGPHyperParameters, dest="hparams")

args = parser.parse_args()

load_path: str = args.load_path
if load_path is None:
    hparams: WGANGPHyperParameters = args.hparams
else:
    hparams = WGANGPHyperParameters.load_json(load_path)

assert hparams == WGANGPHyperParameters(
    batch_size=32,
    d_steps=1,
    g_steps=1,
    learning_rate=0.0001,
    optimizer="ADAM",
    lambda_coeff=10,
    gp_penalty=1e-06,
)
