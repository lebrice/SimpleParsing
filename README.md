[![Build Status](https://travis-ci.org/lebrice/SimpleParsing.svg?branch=master)](https://travis-ci.org/lebrice/SimpleParsing)

# Simple, Elegant Argument Parsing

Do you ever find youself stuck with an endless list of command-line arguments, say, when specifying all the hyper-parameters of your ML model? Well, say no more, here's something to make your life just a little bit easier!

`simple-parsing` uses python 3.7's amazing [dataclasses](https://docs.python.org/3/library/dataclasses.html) to allow you to define your arguments in a simple, elegant, and object-oriented way. When applied to a dataclass, the `ParseableFromCommandLine` base-class enables creating instances of that class automatically from the provided command-line arguments.

## Documentation: [SimpleParse Wiki](https://github.com/lebrice/SimpleParsing/wiki)

## installation

python version >= 3.7:
```console
pip install simple-parsing
```
python version == 3.6.X:
```console
pip install dataclasses simple-parsing
```

## Basic Usage: <a name="basic-usage"></a>

Instead of adding your command-line arguments with `parser.add_argument(...)`, you can instead define your arguments directly in code!
Simply create a `dataclass` to hold your arguments, adding `ParseableFromCommandLine` as a base class:

```python
"""A basic example of how to use simple-parsing."""
import argparse
from dataclasses import dataclass, field
from typing import List

from simple_parsing import Formatter, ParseableFromCommandLine

parser = argparse.ArgumentParser(formatter_class=Formatter)

@dataclass()
class Options(ParseableFromCommandLine):
	""" A class which groups related parameters. """

	some_int: int			# Some required int parameter
	some_float: float = 1.23	# An optional float parameter

	name: str = "default"   	# The name of some important experiment

	log_dir: str = "/logs" 		# an optional string parameter
	flag: bool = False 		# Wether or not we do something

	# This is a list of integers (empty by default)
	some_integers: List[int] = field(default_factory=list)

	# Converting the list items to the right type will be taken care of for you!
	some_floats: List[float] = field(default_factory=list)

# add the arguments
Options.add_arguments(parser)

# parse the arguments from stdin
args = parser.parse_args()

# create an instance of Options with the arguments
options = Options.from_args(args)

# Do whatever you want using the Options object here!
print(options)
```
## Executing the script:
This script is called just like any other argparse script, and the values are stored inside the object:
```console
$ python ./examples/basic_example.py --some_int 123 --flag true --some_integers 23 45 67
Options(some_int=123, some_float=1.23, name='default', log_dir='/logs', flag=True, some_integers=[23, 45, 67], some_floats=[])
```

**However, we get a lot of nice information for free!**
For instance, passing the "--help" option displays relevant information for each argument:
```console
$ python ./basic_example.py --help
usage: basic_example.py [-h] --some_int int [--some_float float] [--name str]
                        [--log_dir str] [--flag [str2bool]]
                        [--some_integers [int [int ...]]]
                        [--some_floats [float [float ...]]]

optional arguments:
  -h, --help            show this help message and exit

Options:
  A class which groups related parameters.

  --some_int int        Some required int parameter (default: None)
  --some_float float    An optional float parameter (default: 1.23)
  --name str            The name of some important experiment (default:
                        default)
  --log_dir str         an optional string parameter (default: /logs)
  --flag [str2bool]     Wether or not we do something (default: False)
  --some_integers [int [int ...]]
                        This is a list of integers (empty by default)
                        (default: [])
  --some_floats [float [float ...]]
                        Converting the list items to the right type will be
                        taken care of for you! (default: [])
```

### Easily convert to/from a dictionary:
```python
# convert the dataclass to a dict
options_dict = options.asdict()

# create an instance from a dict
options_ = Options(**options_dict)
assert options == options_

```
You can then use whichever library you like (`yaml`, `json`, etc.) and save the dict to a file: 
```python
import json
with open(options.name + ".json", "w") as f:
	json.dump(options_dict, f, indent=1)
```
```console
$ cat default.json
{
 "some_int": 123,
 "some_float": 1.23,
 "name": "default",
 "log_dir": "/logs",
 "flag": true,
 "some_integers": [
  23,
  45,
  67
 ],
 "some_floats": []
}
```
Loading from a dictionary or JSON file:
```python
with open("default.json") as f:
	params = json.load(f)
	default_options = Options(**params)
	assert options == default_options
	print(default_options)
```
