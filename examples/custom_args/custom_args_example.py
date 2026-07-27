"""Example of overwriting auto-generated argparse options with custom ones."""

from dataclasses import dataclass

from simple_parsing import ArgumentParser, field
from simple_parsing.helpers import list_field


def parse(cls, args: str = ""):
    """Removes some boilerplate code from the examples."""
    parser = ArgumentParser()  # Create an argument parser
    parser.add_arguments(cls, "example")  # add arguments for the dataclass
    ns = parser.parse_args(args.split())  # parse the given `args`
    return ns.example  # return the dataclass instance


# Example 1: List of Choices:


@dataclass
class Example1:
    # A list of animals to take on a walk. (can only be passed 'cat' or 'dog')
    pets_to_walk: list[str] = list_field(default=["dog"], choices=["cat", "dog"])


# passing no arguments uses the default values:
assert parse(Example1, "") == Example1(pets_to_walk=["dog"])
assert parse(Example1, "--pets_to_walk") == Example1(pets_to_walk=[])
assert parse(Example1, "--pets_to_walk cat") == Example1(pets_to_walk=["cat"])
assert parse(Example1, "--pets_to_walk dog dog cat") == Example1(
    pets_to_walk=["dog", "dog", "cat"]
)


# # Passing a value not in 'choices' produces an error:
# with pytest.raises(SystemExit):
#     example = parse(Example1, "--pets_to_walk racoon")
#     expected = """
#     usage: custom_args_example.py [-h] [--pets_to_walk [{cat,dog,horse} [{cat,dog} ...]]]
#     custom_args_example.py: error: argument --pets_to_walk: invalid choice: 'racoon' (choose from 'cat', 'dog')
#     """


# Example 2: Additional Option Strings


@dataclass
class Example2:
    # (This argument can be passed either as "-i" or "--input_dir")
    input_dir: str = field("./in", alias="-i")
    # (This argument can be passed either as "-o", "--out", or "--output_dir")
    output_dir: str = field("./out", alias=["-o", "--out"])


assert parse(Example2, "-i tmp/data") == Example2(input_dir="tmp/data")
assert parse(Example2, "-o tmp/data") == Example2(output_dir="tmp/data")
assert parse(Example2, "--out louise") == Example2(output_dir="louise")
assert parse(Example2, "--input_dir louise") == Example2(input_dir="louise")
assert parse(Example2, "--output_dir joe/annie") == Example2(output_dir="joe/annie")
assert parse(Example2, "-i input -o output") == Example2(input_dir="input", output_dir="output")


# Example 3: Using other actions (store_true, store_false, store_const, etc.)


@dataclass
class Example3:
    """Examples with other actions."""

    b: bool = False
    debug: bool = field(alias="-d", action="store_true")
    verbose: bool = field(alias="-v", action="store_true")

    cache: bool = False
    # cache:    bool = field(default=True, "--no_cache", "store_false")
    # no_cache: bool = field(dest=cache, action="store_false")


parser = ArgumentParser()
parser.add_arguments(Example3, "example")
args = parser.parse_args()
example = args.example
print(example)
delattr(args, "example")
assert not vars(args)
