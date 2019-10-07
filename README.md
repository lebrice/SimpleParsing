# Simple, Elegant Argument Parsing

Do you ever find youself stuck with an endless list of command-line arguments, say, when specifying all the hyper-parameters of your ML model? Well, say no more, here's something to make your life just a little bit easier!

`simple-parsing` uses python 3.7's amazing [dataclasses](https://docs.python.org/3/library/dataclasses.html) to allow you to define your arguments in a simple, elegant, and object-oriented way.

When applied to a dataclass, this enables creating an instance of that class and populating the attributes automatically from the command-line arguments.

## Basic Example: Parsing arguments

```python

parser = argparse.ArgumentParser()

@dataclass
class Options(ParseableFromCommandLine):
    a: int
    b: int = 10


Options.add_arguments(parser)

args = parser.parse_args("--a 5")

options = Options.from_args(args)
print(options)
>>>Options(a=5, b=10)
```




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
import argparse

from simple_parsing import ParseableFromCommandLine

# create a parser, as usual
parser = argparse.ArgumentParser()

@dataclass
class MyModelHyperParameters(ParseableFromCommandLine):
    """Hyperparameters of MyModel"""
    learning_rate: float = 0.05
    momentum: float = 0.01

@dataclass
class TrainingConfig(ParseableFromCommandLine):
    """Training configuration settings"""
    data_dir: str = "/data"
    log_dir: str = "/logs"
    checkpoint_dir: str = "checkpoints"


# automatically add arguments for all the fields of the classes above:
MyModelHyperParameters.add_arguments(parser)
TrainingConfig.add_arguments(parser)

args = parser.parse_args()

# Create an instance of each class and populate its values from the command line arguments:
hyperparameters = MyModelHyperParameters.from_args(args)
config = TrainingConfig.from_args(args)

class MyModel():
    def __init__(self, hyperparameters: MyModelHyperParameters, config: TrainingConfig):
        # hyperparameters:
        self.hyperparameters = hyperparameters
        # config:
        self.config = config

m = MyModel(hyperparameters, config)
```

## Parsing multiple instances at once:
It is also possible to use `from_args_multiple` to create multiple instances of a class from the command line arguments. For example, suppose you had a class `BlockConfig` for each block in a ML model.

```python
@dataclass
class BlockConfig(ParseableFromCommandLine):
    num_layers: int
    kernel_size: int = 3
    num_filters: int = 64

parser = argparse.ArgumentParser()

BlockConfig.add_arguments(parser)

args = parser.parse_args("--num_layers 15 20 25 --kernel_size 5".split())

# get the settings for all three blocks.
block_configs = BlockConfig.from_args_multiple(args, 3)
print(block_configs)
## >>> prints:
# [
#     BlockConfig(num_layers=15, kernel_size=5, num_filters=64),
#     BlockConfig(num_layers=20, kernel_size=5, num_filters=64),
#     BlockConfig(num_layers=25, kernel_size=5, num_filters=64)
# ]
```
As can be seen in the example above, a value can be specified either for each instance, or a single value for all instances, or none, in which case the default value is used.