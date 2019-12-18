from simple_parsing import ArgumentParser

from dataclasses import dataclass

@dataclass
class GANHyperParameters:
    batch_size: int = 32    # batch size
    d_steps: int = 1        # number of generator updates
    g_steps: int = 1        # number of discriminator updates
    learning_rate: float = 1e-4
    optimizer: str = "ADAM"   

@dataclass
class WGANHyperParameters(GANHyperParameters):
    lambda_coeff: float = 10 # the lambda penalty coefficient.


@dataclass
class WGANGPHyperParameters(WGANHyperParameters):
    gp_penalty: float = 1e-6 # Gradient penalty coefficient


parser = ArgumentParser()
parser.add_arguments(WGANGPHyperParameters, dest="hparams")
args = parser.parse_args()
hparams: WGANGPHyperParameters = args.hparams
print(hparams)
