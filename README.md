Welcome to the SimpleParsing wiki!

# Simple, Elegant Argument Parsing

Do you ever find youself stuck with an endless list of command-line arguments, say, when specifying all the hyper-parameters of your ML model? Well, say no more, here's something to make your life just a little bit easier!

`simple-parsing` uses python 3.7's amazing [dataclasses](https://docs.python.org/3/library/dataclasses.html) to allow you to define your arguments in a simple, elegant, and object-oriented way.

When applied to a dataclass, this enables creating an instance of that class and populating the attributes automatically from the command-line arguments.

Documentation: See the [SimpleParse GitHub Wiki](https://github.com/lebrice/SimpleParsing/wiki)

# Table of Contents
1. [Basic Usage](#basic-usage)
1. [Examples](https://github.com/lebrice/SimpleParsing/wiki/Basic-Examples)
2. [Use-Case Example: ML Training Script](https://github.com/lebrice/SimpleParsing/wiki/Example-Use-Case:-ML-Training-Script)
3. [Roadmap](https://github.com/lebrice/SimpleParsing/wiki/Roadmap)

## Basic Usage: <a name="basic-usage"></a>
```python
import argparse
from dataclasses import dataclass
from simple_parsing import ParseableFromCommandLine

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

@dataclass()
class Options(ParseableFromCommandLine):
    """ A class which groups related parameters. """
    # Some required parameter named foo.
    foo: int
    # Some parameter named bar
    bar: int = 10 
    # The logging directory to use
    # (this is an attribute docstring)
    log_dir: str = "/logs"

@dataclass()
class OtherOptions(ParseableFromCommandLine):
    """ Some other options, cleanly separated from the `Options` class """
    # This parameter is very different.
    different_param: float = 0.05 # TODO: tune this parameter

# add command-line arguments for each class
Options.add_arguments(parser)
OtherOptions.add_arguments(parser)

# parse the provided command-line arguments as usual
args = parser.parse_args()

# Create instances of the classes above from the parsed arguments:
options = Options.from_args(args)
other_options = OtherOptions.from_args(args)

# Do whatever you want using the Options object here!
# (...)
print(options)
print(other_options)

```

This script is called just like any other argparse script, and the values are stored inside the objects:
```console
>>> python example.py --foo 123 --bar 2 --different_param 0.24
Options(foo=123, bar=2, log_dir='/logs')
OtherOptions(different_param=0.24)
```

However, we get a lot of nice information for free! For instance, passing the "--help" option displays relevant information for each argument:

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


