from dataclasses import dataclass

from simple_parsing import ArgumentParser, choice
from simple_parsing.helpers import Serializable

# import tensorflow as tf


class GAN:
    @dataclass
    class HyperParameters(Serializable):
        """Hyperparameters of the Generator and Discriminator networks."""

        learning_rate: float = 1e-4
        optimizer: str = choice("ADAM", "RMSPROP", "SGD", default="ADAM")
        n_disc_iters_per_g_iter: int = (
            1  # Number of Discriminator iterations per Generator iteration.
        )

    def __init__(self, hparams: HyperParameters):
        self.hparams = hparams


class WGAN(GAN):
    """Wasserstein GAN."""

    @dataclass
    class HyperParameters(GAN.HyperParameters):
        e_drift: float = 1e-4
        """Coefficient from the progan authors which penalizes critic outputs for having a large
        magnitude."""

    def __init__(self, hparams: HyperParameters):
        self.hparams = hparams


class WGANGP(WGAN):
    """Wasserstein GAN with Gradient Penalty."""

    @dataclass
    class HyperParameters(WGAN.HyperParameters):
        e_drift: float = 1e-4
        """Coefficient from the progan authors which penalizes critic outputs for having a large
        magnitude."""
        gp_coefficient: float = 10.0
        """Multiplying coefficient for the gradient penalty term of the loss equation.

        (10.0 is the default value, and was used by the PROGAN authors.)
        """

    def __init__(self, hparams: HyperParameters):
        self.hparams: WGANGP.HyperParameters = hparams
        print(self.hparams.gp_coefficient)


parser = ArgumentParser()
parser.add_arguments(WGANGP.HyperParameters, "hparams")
args = parser.parse_args()
print(args.hparams)
expected = """
WGANGP.HyperParameters(learning_rate=0.0001, optimizer='ADAM', n_disc_iters_per_g_iter=1, e_drift=0.0001, gp_coefficient=10.0)
"""
