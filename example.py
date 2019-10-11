import argparse
from dataclasses import dataclass
from simple_parsing import ParseableFromCommandLine

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

@dataclass
class Options(ParseableFromCommandLine):
    """ A class which groups related parameters. """
    foo: int # Some required parameter named foo.
    bar: int = 10 # Some parameter named bar
    log_dir: str = "/logs"
    """the logging directory to use. (This is an attribute docstring)"""

@dataclass
class OtherOptions(ParseableFromCommandLine):
    """Some other options, cleanly separated from the `Options` class
    """
    #This parameter is very different.
    different_param: float = 0.05 # NOTE: this  



Options.add_arguments(parser)
OtherOptions.add_arguments(parser)

args = parser.parse_args()

options = Options.from_args(args)
other_options = OtherOptions.from_args(args)

# Do whatever you want using the Options object here!
# (...)
print(options)
print(other_options)

""">>> python example.py --help
usage: example.py [-h] --foo FOO [--bar BAR] [--log_dir LOG_DIR]
                  [--different_param DIFFERENT_PARAM]

optional arguments:
  -h, --help            show this help message and exit

Options:
  A class which groups related parameters.

  --foo FOO             Some required parameter named foo. (default: None)
  --bar BAR             Some parameter named bar (default: 10)
  --log_dir LOG_DIR     the logging directory to use. (This is an attribute
                        docstring) (default: /logs)

OtherOptions:
  Some other options, cleanly separated from the `Options` class

  --different_param DIFFERENT_PARAM
                        This parameter is very different. (default: 0.05)
"""

""">>> python example.py --foo 123 --bar 2 --different_param 0.24
Options(foo=123, bar=2, log_dir='/logs')
OtherOptions(different_param=0.24)
"""

""">>> python example.py --bar 1234
usage: example.py [-h] --foo FOO [--bar BAR] [--log_dir LOG_DIR]
                  [--different_param DIFFERENT_PARAM]
example.py: error: the following arguments are required: --foo
"""