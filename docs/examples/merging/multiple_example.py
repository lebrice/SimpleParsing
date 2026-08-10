"""Example of how to create multiple instances of a class from the command-line.

# NOTE: If your dataclass has a list attribute, and you wish to parse multiple instances of that class from the command line,
# simply enclose each list with single or double quotes.
# For this example, something like:
>>> python examples/multiple_instances_example.py --num_instances 2 --foo 1 2 --list_of_ints "3 5 7" "4 6 10"
"""
from dataclasses import dataclass

from simple_parsing import ArgumentParser, ConflictResolution

parser = ArgumentParser(conflict_resolution=ConflictResolution.ALWAYS_MERGE)


@dataclass
class Config:
    """A class which groups related parameters."""

    run_name: str = "train"  # Some parameter for the run name.
    some_int: int = 10  # an optional int parameter.
    log_dir: str = "logs"  # an optional string parameter.
    """The logging directory to use.

    (This is an attribute docstring for the log_dir attribute, and shows up when using the "--help"
    argument!)
    """


parser.add_arguments(Config, "train_config")
parser.add_arguments(Config, "valid_config")

args = parser.parse_args()

train_config: Config = args.train_config
valid_config: Config = args.valid_config

print(train_config, valid_config, sep="\n")

expected = """
Config(run_name='train', some_int=10, log_dir='logs')
Config(run_name='train', some_int=10, log_dir='logs')
"""
