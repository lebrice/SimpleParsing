from dataclasses import dataclass
from simple_parsing import ArgumentParser, field


@dataclass
class RunSettings:
    """Parameters for a run."""

    # wether or not to execute in debug mode.
    debug: bool = field(alias=["-d"], default=False)
    # wether or not to add a lot of logging information.
    verbose: bool = field(alias=["-v"], action="store_true")


parser = ArgumentParser(add_option_string_dash_variants=True)
parser.add_arguments(RunSettings, dest="train")
parser.add_arguments(RunSettings, dest="valid")
args = parser.parse_args()
print(args)
# This prints:
expected = """
Namespace(train=RunSettings(debug=False, verbose=False), valid=RunSettings(debug=False, verbose=False))
"""
