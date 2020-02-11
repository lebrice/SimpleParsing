from dataclasses import dataclass
from simple_parsing import ArgumentParser, field


@dataclass
class RunSettings:
    ''' Parameters for a run. '''
    # wether or not to execute in debug mode.
    debug: bool = field(alias=["-d"], default=False)
    some_value: int = field(alias=["-v"], default=123)


if __name__ == "__main__":
    parser = ArgumentParser(add_option_string_dash_variants=True)
    parser.add_arguments(RunSettings, dest="train")
    parser.add_arguments(RunSettings, dest="valid")
    parser.print_help()

# This prints:
'''
usage: test.py [-h] [--train.debug [bool]] [--train.some_value int]
               [--valid.debug [bool]] [--valid.some_value int]

optional arguments:
  -h, --help            show this help message and exit

RunSettings ['train']:
  Parameters for a run.

  --train.debug [bool], --train.d [bool]
                        wether or not to execute in debug mode. (default:
                        False)
  --train.some_value int, --train.v int, ---train.some-value int

RunSettings ['valid']:
  Parameters for a run.

  --valid.debug [bool], --valid.d [bool]
                        wether or not to execute in debug mode. (default:
                        False)
  --valid.some_value int, --valid.v int, ---valid.some-value int
'''
