## Use-Case Example: ML Scripts

Let's look at a great use-case for `simple-parsing`: ugly ML code:

### Before:

```python
import argparse

parser = argparse.ArgumentParser()

# hyperparameters
parser.add_argument("--learning_rate", type=float, default=0.05)
parser.add_argument("--momentum", type=float, default=0.01)
# (... other hyperparameters here)

# args for training config
parser.add_argument("--data_dir", type=str, default="/data")
parser.add_argument("--log_dir", type=str, default="/logs")
parser.add_argument("--checkpoint_dir", type=str, default="checkpoints")

args = parser.parse_args()

learning_rate = args.learning_rate
momentum = args.momentum
# (...) dereference all the variables here, without any typing
data_dir = args.data_dir
log_dir = args.log_dir
checkpoint_dir = args.checkpoint_dir

class MyModel():
    def __init__(self, data_dir, log_dir, checkpoint_dir, learning_rate, momentum, *args):
        # config:
        self.data_dir = data_dir
        self.log_dir = log_dir
        self.checkpoint_dir = checkpoint_dir

        # hyperparameters:
        self.learning_rate = learning_rate
        self.momentum = momentum

m = MyModel(data_dir, log_dir, checkpoint_dir, learning_rate, momentum)
# Ok, what if we wanted to add a new hyperparameter?!
```

### After:

```python
from dataclasses import dataclass
from simple_parsing import ArgumentParser

# create a parser, as usual
parser = ArgumentParser()

@dataclass
class MyModelHyperParameters:
    """Hyperparameters of MyModel"""
    # Learning rate of the Adam optimizer.
    learning_rate: float = 0.05
    # Momentum of the optimizer.
    momentum: float = 0.01

@dataclass
class TrainingConfig:
    """Training configuration settings"""
    data_dir: str = "/data"
    log_dir: str = "/logs"
    checkpoint_dir: str = "checkpoints"


# automatically add arguments for all the fields of the classes above:
parser.add_arguments(MyModelHyperParameters, dest="hparams")
parser.add_arguments(TrainingConfig, dest="config")

args = parser.parse_args()

# Create an instance of each class and populate its values from the command line arguments:
hyperparameters: MyModelHyperParameters = args.hparams
config: TrainingConfig = args.config

class MyModel():
    def __init__(self, hyperparameters: MyModelHyperParameters, config: TrainingConfig):
        # hyperparameters:
        self.hyperparameters = hyperparameters
        # config:
        self.config = config

m = MyModel(hyperparameters, config)

```
