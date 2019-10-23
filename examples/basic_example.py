"""A basic example of how to use simple-parsing."""
import argparse
from dataclasses import dataclass, field
from typing import List, Tuple

from simple_parsing import Formatter, ParseableFromCommandLine

parser = argparse.ArgumentParser(formatter_class=Formatter)

@dataclass()
class Options(ParseableFromCommandLine):
	""" A class which groups related parameters. """

	some_int: int              	# Some required int parameter
	some_float: float = 1.23    # An optional float parameter

	name: str = "default"   	# The name of some important experiment

	log_dir: str = "/logs" 		# an optional string parameter
	flag: bool = False 			# Wether or not we do something

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

# convert the dataclass to a dict
options_dict = options.asdict()

# create an instance from a dict
options_ = Options(**options_dict)
assert options == options_


# save to a file using whichever framework you like (json, yaml, etc.)
import json
with open(options.name + ".json", "w") as f:
	json.dump(options_dict, f, indent=1)
""" >>> cat default.json
{
 "some_int": 123,
 "some_float": 1.23,
 "name": "default",
 "log_dir": "/logs",
 "flag": false,
 "some_integers": [],
 "some_floats": []
}
"""

with open("default.json") as f:
	params = json.load(f)
	default_options = Options(**params)
	assert options == default_options
	print(default_options)




""" >>> python ./basic_example.py --help
usage: basic_example.py [-h] --some_int int [--some_float float] [--name str]
												[--log_dir str] [--flag [str2bool]]
												[--some_integers [int [int ...]]]
												[--some_floats [float [float ...]]]

optional arguments:
	-h, --help            show this help message and exit

Options:
	A class which groups related parameters.

	--some_int int        Some required parameter int parameter (default: None)
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
"""