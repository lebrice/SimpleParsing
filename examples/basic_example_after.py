""" (basic_example.py)
An example script with simple_parsing.
"""
from dataclasses import dataclass, asdict
from simple_parsing import ArgumentParser

parser = ArgumentParser()
# `ArgumentParser` is a subclass of `argparse.ArgumentParser`,
# hence we can add arguments in exactly the same way as before if we want to:
parser.add_argument("--batch_size", default=32, type=int, help="some help string for this argument")

# But why do that, when you could instead be doing this!
@dataclass
class Options:
    """ Set of Options for this script. (Note: this docstring will be used as the group description) """
    # Some required int parameter
    # (NOTE: this comment will be used as the help text for the argument)
    some_required_int: int
    # An optional float parameter
    some_float: float = 1.23
    # The name of some important experiment
    name: str = "default"
    # an optional string parameter   
    log_dir: str = "/logs"
    # Wether or not to do something
    flag: bool = False

parser.add_arguments(Options, dest="options")

args = parser.parse_args()
print(vars(args))
# retrieve the parsed values:
batch_size = args.batch_size
options: Options = args.options

"""$ python ./examples/basic_example_after.py --help
usage: basic_example_after.py [-h] [--batch_size int] --some_required_int int
                              [--some_float float] [--name str]
                              [--log_dir str] [--flag [str2bool]]

optional arguments:
  -h, --help            show this help message and exit
  --batch_size int      some help string for this argument (default: 32)

Options ['options']:
  Set of Options for this script. (Note: this docstring will be used as the
  group description)

  --some_required_int int
                        Some required int parameter (NOTE: this comment will
                        be used as the help text for the argument) (default:
                        None)
  --some_float float    An optional float parameter (default: 1.23)
  --name str            The name of some important experiment (default:
                        default)
  --log_dir str         an optional string parameter (default: /logs)
  --flag [str2bool]     Wether or not to do something (default: False)
"""

"""$ python examples/basic_example_after.py --some_required_int 123
{'batch_size': 32, 'options': Options(some_required_int=123, some_float=1.23, name='default', log_dir='/logs', flag=False)}
"""