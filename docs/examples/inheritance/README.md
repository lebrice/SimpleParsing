# Inheritance

Say you are working on a new research project, building on top of some previous work.

Let's suppose that the previous authors were smart enough to use `simple-parsing` to define their `HyperParameters` as a dataclass, potentially saving you and others a lot of work. All the model hyperparameters can therefore be provided directly as command-line arguments.

You have a set of new hyperparameters or command-line arguments you want to add to your model. Rather than redefining the same HyperParameters over and over, wouldn't it be nice to be able to just add a few new arguments to an existing arguments dataclass?

Behold, inheritance:

```python
from simple_parsing import ArgumentParser
from simple_parsing.helpers import JsonSerializable


from dataclasses import dataclass
from typing import Optional

@dataclass
class GANHyperParameters(JsonSerializable):
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
parser.add_argument(
    "--load_path",
    type=str,
    default=None,
    help="If given, the HyperParameters are read from the given file instead of from the command-line."
)
parser.add_arguments(WGANGPHyperParameters, dest="hparams")

args = parser.parse_args()

load_path: str = args.load_path
if load_path is None:
    hparams: WGANGPHyperParameters = args.hparams
else:
    hparams = WGANGPHyperParameters.load_json(load_path)
print(hparams)
```
