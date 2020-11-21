[![Build Status](https://travis-ci.com/lebrice/SimpleParsing.svg?branch=master)](https://travis-ci.com/lebrice/SimpleParsing) [![PyPI version](https://badge.fury.io/py/simple-parsing.svg)](https://badge.fury.io/py/simple-parsing)


# Simple, Elegant, Typed Argument Parsing <!-- omit in toc -->

`simple-parsing` allows you to transform your ugly `argparse` scripts into beautifully structured, strongly typed little works of art. This isn't a fancy, complicated new command-line tool either, ***this simply adds new features to plain-old argparse!***
Using [dataclasses](https://docs.python.org/3.7/library/dataclasses.html), `simple-parsing` makes it easier to share and reuse command-line arguments - ***no more copy pasting!***

Supports inheritance, **nesting**, easy serialization to json/yaml, automatic help strings from comments, and much more!

```python
# examples/demo.py
from dataclasses import dataclass
from simple_parsing import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--foo", type=int, default=123, help="foo help")

@dataclass
class Options:
    """ Help string for this group of command-line arguments """
    log_dir: str                # Help string for a required str argument    
    learning_rate: float = 1e-4 # Help string for a float argument

parser.add_arguments(Options, dest="options")

args = parser.parse_args()
print("foo:", args.foo)
print("options:", args.options)
```
```console
$ python examples/demo.py --log_dir logs --foo 123
foo: 123
options: Options(log_dir='logs', learning_rate=0.0001)
```
```console
$ python examples/demo.py --help
usage: demo.py [-h] [--foo int] --log_dir str [--learning_rate float]

optional arguments:
  -h, --help            show this help message and exit
  --foo int             foo help (default: 123)

Options ['options']:
   Help string for this group of command-line arguments 

  --log_dir str         Help string for a required str argument (default:
                        None)
  --learning_rate float
                        Help string for a float argument (default: 0.0001)
```


## installation

`pip install simple-parsing`

## [Examples](https://github.com/lebrice/SimpleParsing/tree/master/examples/README.md)

## [API Documentation](https://github.com/lebrice/SimpleParsing/tree/master/docs/README.md) (Under construction)

## Features 
- ### [Automatic "--help" strings](https://github.com/lebrice/SimpleParsing/tree/master/examples/docstrings/README.md)

    As developers, we want to make it easy for people coming into our projects to understand how to run them. However, a user-friendly `--help` message is often hard to write and to maintain, especially as the number of arguments increases.

    With `simple-parsing`, your arguments and their decriptions are defined in the same place, making your code easier to read, write, and maintain.

- ### Modular, Reusable, Cleanly Grouped Arguments
    
    *(no more copy-pasting)*
        
    When you need to add a new group of command-line arguments similar to an existing one, instead of copy-pasting a block of `argparse` code and renaming variables, you can reuse your argument class, and let the `ArgumentParser` take care of adding relevant prefixes to the arguments for you:

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
        --train.log_dir "training" \
        --valid.log_dir "validation"
    Options(log_dir='training', learning_rate=0.0001)
    Options(log_dir='validation', learning_rate=0.0001)
    ```
        
    These prefixes can also be set explicitly, or not be used at all. For more info, take a look at the [Prefixing Guide](https://github.com/lebrice/SimpleParsing/tree/master/examples/prefixing/README.md)

- ### [**Easy serialization**](https://github.com/lebrice/SimpleParsing/tree/master/examples/serialization/README.md):
    
    Easily save/load configs to `json` or `yaml`!. 

- ### [**Inheritance**!](https://github.com/lebrice/SimpleParsing/tree/master/examples/inheritance/README.md)
    
    You can easily customize an existing argument class by extending it and adding your own attributes, which helps promote code reuse accross projects. For more info, take a look at the [inheritance example](https://github.com/lebrice/SimpleParsing/tree/master/examples/inheritance_example.py)

- ### [**Nesting**!](https://github.com/lebrice/SimpleParsing/tree/master/examples/nesting/README.md):
    
    Dataclasses can be nested within dataclasses, as deep as you need!

- ### [Easier parsing of lists and tuples](https://github.com/lebrice/SimpleParsing/tree/master/examples/container_types/README.md) :
    This is sometimes tricky to do with regular `argparse`, but `simple-parsing` makes it a lot easier by using the python's builtin type annotations to automatically convert the values to the right type for you.
    As an added feature, by using these type annotations, `simple-parsing` allows you to parse nested lists or tuples, as can be seen in [this example](https://github.com/lebrice/SimpleParsing/tree/master/examples/merging/README.md)

- ### [Enums support](https://github.com/lebrice/SimpleParsing/tree/master/examples/enums/README.md)

- (More to come!)


## Examples:
Additional examples for all the features mentioned above can be found in the [examples folder](https://github.com/lebrice/SimpleParsing/tree/master/examples/README.md)
