[![Build Status](https://travis-ci.org/lebrice/SimpleParsing.svg?branch=master)](https://travis-ci.org/lebrice/SimpleParsing)

# Simple, Elegant Argument Parsing

SimpleParsing allows you to group related command-line arguments into dataclasses and let the ArgumentParser take care of creating the arguments for you. 

## Documentation (Work In Progress): [simple-parsing docs](https://github.com/lebrice/SimpleParsing/tree/master/docs)

## installation
| python version |                command                  |
|----------------|-----------------------------------------|
|>= 3.7          | `pip install simple-parsing`            |
|== 3.6.X        | `pip install dataclasses simple-parsing`|


# Before:
Specifying command-line arguments in Python is usually done using the `ArgumentParser` class from the  `argparse` package, whereby command-line arguments are added one at a time using the `parser.add_argument(name, **options)` method, like so:

```python
""" (examples/basic_example_before.py)
An example script without simple_parsing.
"""
from dataclasses import dataclass, asdict
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

parser.add_argument("--batch_size", default=32, type=int, help="some help string for this argument")

group  = parser.add_argument_group(title="Options", description="Set of Options for this script")
group.add_argument("--some_required_int", type=int, required=True, help="Some required int parameter")
group.add_argument("--some_float", type=float, default=1.23, help="An optional float parameter")
group.add_argument("--name", type=str, default="default", help="The name of some important experiment")
group.add_argument("--log_dir", type=str, default="/logs", help="An optional string parameter")
group.add_argument("--flag", action="store_true", default=False, help="Wether or not to do something")

args = parser.parse_args()
print(vars(args))

# retrieve the parsed values:
batch_size = args.batch_size
some_required_int = args.some_required_int
some_float = args.some_float
name = args.name
log_dir = args.log_dir
flag = args.flag
```

While this works great when you only have a few command-line arguments, this become very tedious to read, to use, and to maintain as the number of command-line arguments grows.

# After:

`simple-parsing` extends the regular `ArgumentParser` by making use of python's amazing new [dataclasses](https://docs.python.org/3/library/dataclasses.html), allowing you to define your arguments in a simple, elegant, easily maintainable, and object-oriented manner:

```python
""" (examples/basic_example_after.py)
An example script with simple_parsing.
"""
from dataclasses import dataclass, asdict
from simple_parsing import ArgumentParser

parser = ArgumentParser()
# `ArgumentParser` is a subclass of `argparse.ArgumentParser`,
# hence we can add arguments in exactly the same way as before if we want to:
parser.add_argument("--batch_size", default=32, type=int, help="some help string for this argument")

# But why do that, when you could instead be doing this!
@dataclass
class Options:
    """ Set of Options for this script.
    (Note: this docstring will be used as the group description)
    """
    # Some required int parameter
    # (NOTE: this comment will be used as the help text for the argument)
    some_required_int: int
    # An optional float parameter
    some_float: float = 1.23
    # The name of some important experiment
    name: str = "default"
    # an optional string parameter   
    log_dir: str = "/logs"
    # Wether or not to do something
    flag: bool = False

parser.add_arguments(Options, dest="options")

args = parser.parse_args()
print(vars(args))

# retrieve the parsed values:
batch_size = args.batch_size
options: Options = args.options
```

# What you get for free:

## - Automatically generates a helpful `--help` message:
```console
$ python ./examples/basic_example_after.py --help
usage: basic_example_after.py [-h] [--batch_size int] --some_required_int int
                              [--some_float float] [--name str]
                              [--log_dir str] [--flag [str2bool]]

optional arguments:
  -h, --help            show this help message and exit
  --batch_size int      some help string for this argument (default: 32)

Options ['options']:
  Set of Options for this script. (Note: this docstring will be used as the
  group description)

  --some_required_int int
                        Some required int parameter (NOTE: this comment will
                        be used as the help text for the argument) (default:
                        None)
  --some_float float    An optional float parameter (default: 1.23)
  --name str            The name of some important experiment (default:
                        default)
  --log_dir str         an optional string parameter (default: /logs)
  --flag [str2bool]     Wether or not to do something (default: False)
```

## - Modular and Reusable:
With SimpleParsing, you can easily add similar groups of command-line arguments by simply reusing the dataclasses you define! There is no longer need for any copy-pasting of blocks, or adding prefixes everywhere by hand.

Instead, SimpleParsing's ArgumentParser detects when more than one instance of the same `@dataclass` needs to be parsed, and automatically adds the relevant prefix to each argument automatically for you:
```python
    parser.add_arguments(Options, dest="train") # prefix = "train."
    parser.add_arguments(Options, dest="valid") # prefix = "valid."
    args = parser.parse_args()
    train_options: Options = args.train
    valid_options: Options = args.valid
```
```console
$ python examples/basic_example_after.py \
    --train.some_required_int 123 \
    --valid.some_required_int 456
{
    'batch_size': 128,
    'train': Options(some_required_int=123, some_float=1.23, name='default', log_dir='/logs', flag=False),
    'valid': Options(some_required_int=456, some_float=1.23, name='default', log_dir='/logs', flag=False)
}
```

Prefixes can also be set explicitly, or not be used at all. For more info, take a look at the [Prefix Example](examples/prefix_example.py)

## - Inheritance!
You can easily add new, specialized arguments by extending an existing dataclass and adding your own custom arguments!

## - __Nesting__!
You can even put dataclasses within dataclasses! The sky is the limit!
For more info, take a look at the [Nesting Example](examples/nesting_example.py)

## - Argument dataclasses can also have methods!
Using Dataclasses, you can add methods in your argument dataclasses, further promoting the "Seperation of Concerns" principle, by keeping all the logic related to argument parsing in the same place!

```python

## - Argument dataclasses can also have methods!
import json
from dataclasses import dataclass, asdict

from simple_parsing import ArgumentParser
parser = ArgumentParser()

@dataclass
class HyperParameters:
    batch_size: int = 32
    optimizer: str = "ADAM"
    learning_rate: float = 1e-4
    max_epochs: int = 100
    l1_reg: float = 1e-5
    l2_reg: float = 1e-5

    def save(self, path: str):
        with open(path, "w") as f:
            config_dict = asdict(self)
            json.dump(config_dict, f, indent=1)
    
    @classmethod
    def load(cls, path: str):
        with open(path, "r") as f:
            config_dict = json.load(f)
            return cls(**config_dict)


parser.add_arguments(HyperParameters, dest="hparams")

args = parser.parse_args()

hparams: HyperParameters = args.hparams
print(hparams)

# save and load from a json file: 
hparams.save("hyperparameters.json")
_hparams = HyperParameters.load("hyperparameters.json")
assert hparams == _hparams
```
