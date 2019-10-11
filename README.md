# Simple, Elegant Argument Parsing

Do you ever find youself stuck with an endless list of command-line arguments, say, when specifying all the hyper-parameters of your ML model? Well, say no more, here's something to make your life just a little bit easier!

`simple-parsing` uses python 3.7's amazing [dataclasses](https://docs.python.org/3/library/dataclasses.html) to allow you to define your arguments in a simple, elegant, and object-oriented way.

When applied to a dataclass, this enables creating an instance of that class and populating the attributes automatically from the command-line arguments.

## Basic Example: Parsing arguments
Suppose you have the following script "example.py"
```python
import argparse
from dataclasses import dataclass
from simple_parsing import ParseableFromCommandLine

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

@dataclass
class Options(ParseableFromCommandLine):
    """ A class which groups related parameters. """
    foo: int # Some required parameter named foo.
    bar: int = 10 # Some parameter named bar
    log_dir: str = "/logs"
    """the logging directory to use. (This is an attribute docstring)"""

@dataclass
class OtherOptions(ParseableFromCommandLine):
    """Some other options, cleanly separated from the `Options` class
    """
    #This parameter is very different.
    different_param: float = 0.05 # TODO: tune this parameter

Options.add_arguments(parser)
OtherOptions.add_arguments(parser)

args = parser.parse_args()

options = Options.from_args(args)
other_options = OtherOptions.from_args(args)

# Do whatever you want using the Options object here!
# (...)
print(options)
print(other_options)

```

This script is called just like any other argparse script, but adds a lot of nice information that would otherwise have been tedious to write out by hand:
```console
>>> python example.py --help
usage: example.py [-h] --foo FOO [--bar BAR] [--log_dir LOG_DIR]
                  [--different_param DIFFERENT_PARAM]

optional arguments:
  -h, --help            show this help message and exit

Options:
  A class which groups related parameters.

  --foo FOO             Some required parameter named foo. (default: None)
  --bar BAR             Some parameter named bar (default: 10)
  --log_dir LOG_DIR     the logging directory to use. (This is an attribute
                        docstring) (default: /logs)

OtherOptions:
  Some other options, cleanly separated from the `Options` class

  --different_param DIFFERENT_PARAM
                        This parameter is very different. (default: 0.05)
```

Required arguments are enforced:
```console
>>> python example.py --bar 1234
usage: example.py [-h] --foo FOO [--bar BAR] [--log_dir LOG_DIR]
                  [--different_param DIFFERENT_PARAM]
example.py: error: the following arguments are required: --foo
```
Passing values works as expected:
```console
>>> python example.py --foo 123 --bar 2 --different_param 0.24
Options(foo=123, bar=2, log_dir='/logs')
OtherOptions(different_param=0.24)
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

## Parsing multiple instances of the same class:
It is also possible to create multiple instances of a class from the command line arguments.
To do this, use `add_arguments(parser, multiple=True)` when registering the arguments, and use the `from_args_multiple` function to create the instances.

For example, suppose you had a class `BlockConfig` for each block in a ML model.

```python
@dataclass
class BlockConfig(ParseableFromCommandLine):
    num_layers: int
    kernel_size: int = 3
    num_filters: int = 64

parser = argparse.ArgumentParser()

BlockConfig.add_arguments(parser, multiple=True)

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