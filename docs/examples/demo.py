# examples/demo.py
from dataclasses import dataclass

from simple_parsing import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--foo", type=int, default=123, help="foo help")


@dataclass
class Options:
    """Help string for this group of command-line arguments."""

    log_dir: str  # Help string for a required str argument
    learning_rate: float = 1e-4  # Help string for a float argument


parser.add_arguments(Options, dest="options")

args = parser.parse_args()
print("foo:", args.foo)
print("options:", args.options)
