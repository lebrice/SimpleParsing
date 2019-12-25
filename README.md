[![Build Status](https://travis-ci.org/lebrice/SimpleParsing.svg?branch=master)](https://travis-ci.org/lebrice/SimpleParsing)

# Simple, Elegant Argument Parsing <!-- omit in toc -->

`simple-parsing` helps you parse arguments easier. Using the power of Python [dataclasses](https://docs.python.org/3.7/library/dataclasses.html), you can now define groups of `argparse` arguments in a way that is easier for people to read, write, and maintain, while using fewer lines of code. Argument groups are reusable and extendable, and can even be nested!

```python
# examples/demo.py
from dataclasses import dataclass
import simple_parsing

parser = simple_parsing.ArgumentParser()
parser.add_argument("--foo", type=int, default=123, help="foo help string")

@dataclass
class Options:
    """ Help string for this group of command-line arguments """
    log_dir: str                # Help string for a required str argument
    learning_rate: float = 1e-4 # Help string for a float argument

parser.add_arguments(Options, dest="options")

args = parser.parse_args("--log_dir logs --foo 123".split())
print(args.foo)     # 123
print(args.options) # Options(log_dir='logs', learning_rate=0.0001)
```

Additionally, `simple-parsing` makes it easier to document your arguments by generating `"--help"` strings directly from your source code!

```console
$ python examples/demo.py --help
usage: demo.py [-h] [--foo int] --log_dir str [--learning_rate float]

optional arguments:
  -h, --help            show this help message and exit
  --foo int             foo help string (default: 123)

Options ['options']:
  Help string for this group of command-line arguments

  --log_dir str         Help string for a required str argument (default:
                        None)
  --learning_rate float
                        Help string for a float argument (default: 0.0001)
```

## installation

`pip install simple-parsing`

## [Examples](examples/README.md)

## [API Documentation](docs/README.md) (Under construction)

## Features 
- [Automatic "--help" strings](examples/docstrings/README.md)

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
        
    These prefixes can also be set explicitly, or not be used at all. For more info, take a look at the [Prefixing Guide](examples/prefixing/README.md)

- [**Inheritance**!](examples/inheritance/README.md)
You can easily customize an existing argument class by extending it and adding your own attributes, which helps promote code reuse accross projects. For more info, take a look at the [inheritance example](examples/inheritance_example.py)

- [**Nesting**!](examples/nesting/README.md): Dataclasses can be nested within dataclasses, as deep as you need!
- [**Easy serialization**](examples/dataclasses/hyperparameters_example.py): Since dataclasses are just regular classes, its easy to add methods for easy serialization/deserialization to popular formats like `json` or `yaml`. 
- [Easier parsing of lists and tuples](examples/container_types/README.md) : This is sometimes tricky to do with regular `argparse`, but `simple-parsing` makes it a lot easier by using the python's builtin type annotations to automatically convert the values to the right type for you.

    As an added feature, by using these type annotations, `simple-parsing` allows you to parse nested lists or tuples, as can be seen in [this example](examples/merging/README.md)

- [Enums support](examples/enums/README.md)

- (More to come!)


## Examples:
Additional examples for all the features mentioned above can be found in the [examples folder](examples/README.md)
