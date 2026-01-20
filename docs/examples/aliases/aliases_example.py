from dataclasses import dataclass

from simple_parsing import ArgumentParser, field


@dataclass
class RunSettings:
    """Parameters for a run."""

    # whether or not to execute in debug mode.
    debug: bool = field(alias=["-d"], default=False)
    # whether or not to add a lot of logging information.
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

parser.print_help()
expected += """\
usage: aliases_example.py [-h] [-train.d bool] [-train.v] [-valid.d bool]
                          [-valid.v]

optional arguments:
  -h, --help            show this help message and exit

RunSettings ['train']:
  Parameters for a run.

  -train.d bool, --train.debug bool, --train.nod bool, --train.nodebug bool
                        whether or not to execute in debug mode. (default:
                        False)
  -train.v, --train.verbose
                        whether or not to add a lot of logging information.
                        (default: False)

RunSettings ['valid']:
  Parameters for a run.

  -valid.d bool, --valid.debug bool, --valid.nod bool, --valid.nodebug bool
                        whether or not to execute in debug mode. (default:
                        False)
  -valid.v, --valid.verbose
                        whether or not to add a lot of logging information.
                        (default: False)
"""
