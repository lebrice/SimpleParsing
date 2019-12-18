""" (examples/simple/simple_example_after.py)
An example script with simple_parsing.
"""
from dataclasses import dataclass, asdict
from simple_parsing import ArgumentParser

parser = ArgumentParser()
# same as before:
parser.add_argument("--batch_size", default=32, type=int, help="some help string for this argument")

# But why do that, when you could instead be doing this!
@dataclass
class Options:
    """ Set of Options for this script.

    (Note: this docstring will be used as the group description,
    while the comments next to the attributes will be used as the
    help text for the arguments.)
    """
    some_required_int: int      # Some required int parameter
    some_float: float = 1.23    # An optional float parameter
    name: str = "default"       # The name of some important experiment   
    log_dir: str = "/logs"      # an optional string parameter
    flag: bool = False          # Wether or not to do something

parser.add_arguments(Options, dest="options")

args = parser.parse_args()
print(vars(args))

# retrieve the parsed values:
batch_size = args.batch_size
options: Options = args.options