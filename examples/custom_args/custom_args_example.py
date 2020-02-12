"""Example of overwriting auto-generated argparse options with custom ones. 
"""

from dataclasses import dataclass
from simple_parsing import ArgumentParser, field
from simple_parsing.helpers import list_field
from typing import List, TypeVar, Type
import pytest


def parse(cls, args: str=""):
    """Removes some boilerplate code from the examples. """
    parser = ArgumentParser()  # Create an argument parser
    parser.add_arguments(cls, "example")  # add arguments for the dataclass
    namespace = parser.parse_args(args.split())  # parse the given `args`
    return namespace.example  # return the dataclass instance


### Example 1: List of Choices:
 

@dataclass
class Example1:
    # A list of animals to take on a walk. (can only be passed 'cat' or 'dog')
    pets_to_walk: List[str] = list_field(default=["dog"], choices=["cat", "dog"])


# passing no arguments uses the default values:
assert parse(Example1, "") == Example1(pets_to_walk=['dog'])
assert parse(Example1, "--pets_to_walk") == Example1(pets_to_walk=[])
assert parse(Example1, "--pets_to_walk cat") == Example1(pets_to_walk=['cat'])
assert parse(Example1, "--pets_to_walk dog dog cat") == Example1(pets_to_walk=['dog', 'dog', 'cat'])


# Passing a value not in 'choices' produces an error:
with pytest.raises(SystemExit):
    example = parse(Example1, "--pets_to_walk racoon")
    expected = """
    usage: custom_args_example.py [-h] [--pets_to_walk [{cat,dog,horse} [{cat,dog} ...]]]
    custom_args_example.py: error: argument --pets_to_walk: invalid choice: 'racoon' (choose from 'cat', 'dog')
    """


### Example 2: Additional Option Strings


@dataclass
class Example2:
    # This argument can be passed using any of "-o", "--out", or "--output_dir")
    output_dir: str = field("./out", alias=["-o", "--out"])

assert parse(Example2, "-o tmp/data")  == Example2(output_dir='tmp/data')
assert parse(Example2, "--out louise") == Example2(output_dir='louise')
assert parse(Example2, "--output_dir joe/annie") == Example2(output_dir='joe/annie')
