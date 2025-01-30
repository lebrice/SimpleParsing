from dataclasses import dataclass, field

from simple_parsing import ArgumentParser, choice
from simple_parsing.helpers import Serializable, list_field

# import tensorflow as tf


@dataclass
class ConvBlock(Serializable):
    """A Block of Conv Layers."""

    n_layers: int = 4  # number of layers
    n_filters: list[int] = list_field(16, 32, 64, 64)  # filters per layer


@dataclass
class GeneratorHParams(ConvBlock):
    """Settings of the Generator model."""

    optimizer: str = choice("ADAM", "RMSPROP", "SGD", default="ADAM")


@dataclass
class DiscriminatorHParams(ConvBlock):
    """Settings of the Discriminator model."""

    optimizer: str = choice("ADAM", "RMSPROP", "SGD", default="ADAM")


@dataclass
class GanHParams(Serializable):
    """Hyperparameters of the Generator and Discriminator networks."""

    gen: GeneratorHParams
    disc: DiscriminatorHParams
    learning_rate: float = 1e-4
    n_disc_iters_per_g_iter: int = 1  # Number of Discriminator iterations per Generator iteration.


class GAN:
    """Generative Adversarial Network Model."""

    def __init__(self, hparams: GanHParams):
        self.hparams = hparams


@dataclass
class WGanHParams(GanHParams):
    """HParams of the WGAN model."""

    e_drift: float = 1e-4
    """Coefficient from the progan authors which penalizes critic outputs for having a large
    magnitude."""


class WGAN(GAN):
    """Wasserstein GAN."""

    def __init__(self, hparams: WGanHParams):
        self.hparams = hparams


@dataclass
class CriticHParams(DiscriminatorHParams):
    """HyperParameters specific to a Critic."""

    lambda_coefficient: float = 1e-5


@dataclass
class WGanGPHParams(WGanHParams):
    """Hyperparameters of the WGAN with Gradient Penalty."""

    e_drift: float = 1e-4
    """Coefficient from the progan authors which penalizes critic outputs for having a large
    magnitude."""
    gp_coefficient: float = 10.0
    """Multiplying coefficient for the gradient penalty term of the loss equation.

    (10.0 is the default value, and was used by the PROGAN authors.)
    """
    disc: CriticHParams = field(default_factory=CriticHParams)
    # overwrite the usual 'disc' field of the WGanHParams dataclass.
    """ Parameters of the Critic. """


class WGANGP(WGAN):
    """Wasserstein GAN with Gradient Penalty."""

    def __init__(self, hparams: WGanGPHParams):
        self.hparams = hparams


parser = ArgumentParser()
parser.add_arguments(WGanGPHParams, "hparams")
args = parser.parse_args()

print(args.hparams)

expected = """
WGanGPHParams(gen=GeneratorHParams(n_layers=4, n_filters=[16, 32, 64, 64], \
optimizer='ADAM'), disc=CriticHParams(n_layers=4, n_filters=[16, 32, 64, 64], \
optimizer='ADAM', lambda_coefficient=1e-05), learning_rate=0.0001, \
n_disc_iters_per_g_iter=1, e_drift=0.0001, gp_coefficient=10.0)
"""
