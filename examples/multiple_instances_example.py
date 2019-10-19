"""Example of how to create multiple instances of a class from the command-line.

# NOTE: If your dataclass has a list attribute, and you wish to parse multiple instances of that class from the command line, 
# simply enclose each list with single or double quotes.
# For this example, something like:
>>> python examples/multiple_instances_example.py --num_instances 2 --foo 1 2 --list_of_ints "3 5 7" "4 6 10"
"""
import argparse
from dataclasses import dataclass, field
from simple_parsing import ParseableFromCommandLine
from typing import List
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)


@dataclass()
class Example(ParseableFromCommandLine):
    """ A class which groups related parameters. """
    foo: int # Some required parameter named foo.
    bar: int = 10 # an optional int parameter named bar.
    log_dir: str = "/logs" # an optional string parameter named log_dir.
    """the logging directory to use. (This is an attribute docstring for the log_dir attribute, and shows up when using the "--help" argument!)"""
    
    
    list_of_ints: List[int] = field(default_factory=list) 
    list_of_strings: List[str] = field(default_factory=list)


parser.add_argument("--num_instances", default=2, type=int, help="Number of instances of `Example` to create from the command line values.")
Example.add_arguments(parser, multiple=True)

args = parser.parse_args()
num_instances = args.num_instances

examples = Example.from_args_multiple(args, num_instances)

assert len(examples) == num_instances
for example in examples:
    print(example)