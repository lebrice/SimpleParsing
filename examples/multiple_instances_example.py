"""Example of how to create multiple instances of a class from the command-line.

# NOTE: If your dataclass has a list attribute, and you wish to parse multiple instances of that class from the command line, 
# simply enclose each list with single or double quotes.
# For this example, something like:
>>> python examples/multiple_instances_example.py --num_instances 2 --foo 1 2 --list_of_ints "3 5 7" "4 6 10"
"""
import argparse
from dataclasses import dataclass, field
from simple_parsing import ArgumentParser
from typing import List

parser = ArgumentParser()

@dataclass()
class Example():
    """ A class which groups related parameters. """
    foo: int # Some required parameter named foo.
    bar: int = 10 # an optional int parameter named bar.
    log_dir: str = "/logs" # an optional string parameter named log_dir.
    """the logging directory to use. (This is an attribute docstring for the log_dir attribute, and shows up when using the "--help" argument!)"""
    


num_instances = 2
for i in range(num_instances):
    parser.add_arguments(Example, f"example_{i}")

args = parser.parse_args()

example1 = args.example_0
example2 = args.example_1
print(example1, example2, sep="\n")