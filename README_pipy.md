[![Build Status](https://travis-ci.org/lebrice/SimpleParsing.svg?branch=master)](https://travis-ci.org/lebrice/SimpleParsing)

# Simple, Elegant Argument Parsing <!-- omit in toc -->


`simple-parsing` extends the capabilities of the builtin `argparse` module by allowing you to group related command-line arguments into neat, reusable [dataclasses](https://docs.python.org/3.7/library/dataclasses.html) and let the ArgumentParser take care of creating the arguments for you.

```python
# examples/demo.py
from dataclasses import dataclass
from simple_parsing import ArgumentParser

@dataclass
class Options:
    """ Set of Options for this script. """
    experiment_name: str        # A required string parameter
    learning_rate: float = 1e-4 # An optional float parameter

parser = ArgumentParser()  
parser.add_arguments(Options, dest="options")
args = parser.parse_args()

options: Options = args.options # retrieve the parsed values
print(options)
```

what you get for free:

```console
$ python examples/demo.py --experiment_name "bob"
Options(experiment_name='bob', learning_rate=0.0001)

$ python examples/demo.py --experiment_name "default" --learning_rate 1.23
Options(experiment_name='default', learning_rate=1.23)

$ python examples/demo.py --help
usage: demo.py [-h] --experiment_name str [--learning_rate float]

optional arguments:
  -h, --help            show this help message and exit

Options ['options']:
  Set of Options for this script.

  --experiment_name str
                        a required string parameter (default: None)
  --learning_rate float
                        An optional float parameter (default: 0.0001)
```

## installation
| python version |                command                  |
|----------------|-----------------------------------------|
|>= 3.7          | `pip install simple-parsing`            |
|== 3.6.X        | `pip install dataclasses simple-parsing`|

## Documentation (Work In Progress): [simple-parsing docs](https://github.com/lebrice/SimpleParsing)

## Features 
- [Automatic "--help" strings](https://github.com/lebrice/SimpleParsing/tree/master/examples/docstrings_example.py)

    As developers, we want to make it easy for people coming into our projects to understand how to run them. However, a user-friendly `--help` message is often hard to write and to maintain, especially as the number of arguments increases.

    With `simple-parsing`, your arguments and their decriptions are defined in the same place, making your code easier to read, write, and maintain.

- Modular, Reusable Arguments *(no more copy-pasting!)*
        
    When you need to add a new group of command-line arguments similar to an existing one, instead of copy-pasting a block of `argparse` code and renaming variables, you can reuse your argument class, and let the `ArgumentParser` take care of adding `relevant` prefixes to the arguments for you:

    ```python
    parser.add_arguments(Options, dest="train")
    parser.add_arguments(Options, dest="valid")
    args = parser.parse_args()
    train_options: Options = args.train
    valid_options: Options = args.valid
    print(train_options)
    print(valid_options)
    ```
    ```console
    $ python examples/demo.py \
        --train.experiment_name "training" \
        --valid.experiment_name "validation"
    Options(experiment_name='training', learning_rate=0.0001)
    Options(experiment_name='validation', learning_rate=0.0001)
    ```
        
    These prefixes can also be set explicitly, or not be used at all. For more info, take a look at the [Prefix Example](https://github.com/lebrice/SimpleParsing/tree/master/examples/prefix_example.py)

- [**Inheritance**!](https://github.com/lebrice/SimpleParsing/tree/master/examples/inheritance_example.py)
You can easily customize an existing argument class by extending it and adding your own attributes, which helps promote code reuse accross projects. For more info, take a look at the [inheritance example](https://github.com/lebrice/SimpleParsing/tree/master/examples/inheritance_example.py)

- [**Nesting**!](https://github.com/lebrice/SimpleParsing/tree/master/examples/nesting_example.py): Dataclasses can be nested within dataclasses, as deep as you need!
- [**Easy serialization**](https://github.com/lebrice/SimpleParsing/tree/master/examples/dataclasses/hyperparameters_example.py): Since dataclasses are just regular classes, its easy to add methods for easy serialization/deserialization to popular formats like `json` or `yaml`. 
- [Easier parsing of lists and tuples](https://github.com/lebrice/SimpleParsing/tree/master/examples/lists_example.py) : This is sometimes tricky to do with regular `argparse`, but `simple-parsing` makes it a lot easier by using the python's builtin type annotations to automatically convert the values to the right type for you.

    As an added feature, by using these type annotations, `simple-parsing` allows you to parse nested lists or tuples, as can be seen in [this example](https://github.com/lebrice/SimpleParsing/tree/master/examples/multiple_lists_example.py)

- [Enums support](https://github.com/lebrice/SimpleParsing/tree/master/examples/enums_example.py)

- (More to come!)


## Example
Specifying command-line arguments in Python is usually done using the `ArgumentParser` class from the  `argparse` package, whereby command-line arguments are added one at a time using the `parser.add_argument(name, **options)` method, like so:
### Before
```python
""" (https://github.com/lebrice/SimpleParsing/tree/master/examples/basic_example_before.py)
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

### After

`simple-parsing` extends the regular `ArgumentParser` by making use of python's amazing new [dataclasses](https://docs.python.org/3/library/dataclasses.html), allowing you to define your arguments in a simple, elegant, easily maintainable, and object-oriented manner:

```python
""" (https://github.com/lebrice/SimpleParsing/tree/master/examples/basic_example_after.py)
An example script with simple_parsing.
"""
from dataclasses import dataclass, asdict
from simple_parsing import ArgumentParser

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
    some_required_int: int      # Some required int parameter
    some_float: float = 1.23    # An optional float parameter
    name: str = "default"       # The name of some important experiment   
    log_dir: str = "/logs"      # an optional string parameter
    flag: bool = False          # Wether or not to do something

parser.add_arguments(Options, dest="options")

args = parser.parse_args()
print(vars(args))

# retrieve the parsed values:
batch_size = args.batch_size
options: Options = args.options
```

