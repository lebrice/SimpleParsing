from dataclasses import dataclass
from typing import *

import tensorflow as tf

from simple_parsing import ArgumentParser, choice
from simple_parsing.utils import JsonSerializable, list_field

@dataclass
class ConvBlock(JsonSerializable):
    """A Block of Conv Layers."""
    n_layers: int = 4  # number of layers
    n_filters: List[int] = list_field(16, 32, 64, 64)  # filters per layer
    

@dataclass
class GeneratorHParams(ConvBlock):
    """Settings of the Generator model"""
    optimizer: str = choice("ADAM", "RMSPROP", "SGD", default="ADAM")
    

@dataclass
class DiscriminatorHParams(ConvBlock):
    """Settings of the Discriminator model"""
    optimizer: str = choice("ADAM", "RMSPROP", "SGD", default="ADAM")


@dataclass
class GanHParams(JsonSerializable):
    """ Hyperparameters of the Generator and Discriminator networks. """
    gen: GeneratorHParams
    disc: DiscriminatorHParams
    learning_rate: float = 1e-4
    n_disc_iters_per_g_iter: int = 1  # Number of Discriminator iterations per Generator iteration.


class GAN(tf.keras.Model):
    """ Generative Adversarial Network Model. """   
    def __init__(self, hparams: GanHParams):
        self.hparams = hparams



@dataclass
class WGanHParams(GanHParams):
    """ HParams of the WGAN model """
    e_drift: float = 1e-4
    """Coefficient from the progan authors which penalizes critic outputs for having a large magnitude."""

class WGAN(GAN):
    """ Wasserstein GAN """
    def __init__(self, hparams: WGanHParams):
        self.hparams = hparams



@dataclass
class CriticHParams(DiscriminatorHParams):
    """HyperParameters specific to a Critic. """
    lambda_coefficient: float = 1e-5


@dataclass
class WGanGPHParams(WGanHParams):
    """ Hyperparameters of the WGAN with Gradient Penalty """
    e_drift: float = 1e-4
    """Coefficient from the progan authors which penalizes critic outputs for having a large magnitude."""
    gp_coefficient: float = 10.0
    """Multiplying coefficient for the gradient penalty term of the loss equation. (10.0 is the default value, and was used by the PROGAN authors.)"""
    disc: CriticHParams = CriticHParams() # overwrite the usual 'disc' field of the WGanHParams dataclass.
    """ Parameters of the Critic. """


class WGANGP(WGAN):
    """
    Wasserstein GAN with Gradient Penalty
    """
    
    def __init__(self, hparams: WGanGPHParams):
        self.hparams = hparams

parser = ArgumentParser()
parser.add_arguments(WGanGPHParams, "hparams")
args = parser.parse_args()
print(args.hparams)
