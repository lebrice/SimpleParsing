# Simple Example:
## Before:
Specifying command-line arguments in Python is usually done using the `ArgumentParser` class from the  `argparse` package, whereby command-line arguments are added one at a time using the `parser.add_argument(name, **options)` method, like so:

```python
from dataclasses import dataclass, asdict
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

parser.add_argument("--batch_size", default=32, type=int,
                    help="some help string for this argument")

group = parser.add_argument_group(
    title="Options", description="Set of Options for this script")
group.add_argument("--some_required_int", type=int,
                   required=True, help="Some required int parameter")
group.add_argument("--some_float", type=float, default=1.23,
                   help="An optional float parameter")
group.add_argument("--name", type=str, default="default",
                   help="The name of some important experiment")
group.add_argument("--log_dir", type=str, default="/logs",
                   help="An optional string parameter")
group.add_argument("--flag", action="store_true",
                   default=False, help="Wether or not to do something")
group.add_argument("--optimizer", default="ADAM", choices=["ADAM", "SGD", "RMSPROP"], help="Optimizer to use")


args = parser.parse_args()

batch_size = args.batch_size
some_required_int = args.some_required_int
some_float = args.some_float
name = args.name
log_dir = args.log_dir
flag = args.flag
```

While this works great when you only have a few command-line arguments, this become very tedious to read, to use, and to maintain as the number of command-line arguments grows.

## After:

`simple-parsing` extends the regular `ArgumentParser` by making use of python's amazing new [dataclasses](https://docs.python.org/3/library/dataclasses.html) and type annotations, allowing you to define your arguments in a simple, elegant, easily maintainable, and object-oriented manner:

```python
from dataclasses import dataclass, asdict
from simple_parsing import ArgumentParser, choice

parser = ArgumentParser()
# same as before:
parser.add_argument("--batch_size", default=32, type=int, help="some help string for this argument")

# But why do that, when you could instead be doing this!
@dataclass
class Options:
    """ Set of Options for this script.

    (Note: this docstring will be used as the group description,
    while the comments next to the attributes will be used as the
    help text for the arguments.)
    """
    some_required_int: int      # Some required int parameter (this is the help text for the argument)
    some_float: float = 1.23    # An optional float parameter
    name: str = "default"       # The name of some important experiment   
    log_dir: str = "/logs"      # an optional string parameter
    flag: bool = False          # Wether or not to do something
    optimizer: str = choice("ADAM", "SGD", "RMSPROP", default="ADAM") # Which optimizer to use
parser.add_arguments(Options, dest="options")

args = parser.parse_args()

# retrieve the parsed values:
batch_size = args.batch_size
options: Options = args.options
```

# What you get for free:

## - Automatically generates a helpful `--help` message:
```console
$ python examples/simple/simple_example_after.py --help
usage: simple_example_after.py [-h] [--batch_size int] --some_required_int int
                               [--some_float float] [--name str]
                               [--log_dir str] [--flag [str2bool]]
                               [--optimizer {ADAM,SGD,RMSPROP}]

optional arguments:
  -h, --help            show this help message and exit
  --batch_size int      some help string for this argument (default: 32)

Options ['options']:
  Set of Options for this script. (Note: this docstring will be used as the
  group description, while the comments next to the attributes will be used
  as the help text for the arguments.)

  --some_required_int int
                        Some required int parameter (default: None)
  --some_float float    An optional float parameter (default: 1.23)
  --name str            The name of some important experiment (default:
                        default)
  --log_dir str         an optional string parameter (default: /logs)
  --flag [str2bool]     Wether or not to do something (default: False)
  --optimizer {ADAM,SGD,RMSPROP}
                        Which optimizer to use (default: ADAM)
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
    'train': Options(some_required_int=123, some_float=1.23, name='default', log_dir='/logs', flag=False, optimizer="ADAM"),
    'valid': Options(some_required_int=456, some_float=1.23, name='default', log_dir='/logs', flag=False, optimizer="ADAM")
}
```
