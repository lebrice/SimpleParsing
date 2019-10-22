"""A basic example of how to use simple-parse.

The basic workflow goes like this:
  Step 0: Use python 3.7, or install the dataclasses backport for python 3.6 using `pip install dataclasses`
  1- Create an argparse.ArgumentParser(), like usual.
  2- 

"""
import argparse
from dataclasses import dataclass, field
from typing import List, Tuple

from simple_parsing import Formatter, ParseableFromCommandLine

parser = argparse.ArgumentParser(formatter_class=Formatter)

@dataclass()
class Options(ParseableFromCommandLine):
    """ A class which groups related parameters. """
    foo: int # Some required parameter named foo.
    bar: int = 10 # an optional int parameter named bar.
    log_dir: str = "/logs" # an optional string parameter named log_dir.
    """the logging directory to use. (This is an attribute docstring for the log_dir attribute, and shows up when using the "--help" argument!)"""

Options.add_arguments(parser)

args = parser.parse_args()

options = Options.from_args(args)
# Do whatever you want using the Options object here!
# (...)

print(options)
