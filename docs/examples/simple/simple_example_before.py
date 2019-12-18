""" (examples/basic_example.py)
An example script without simple_parsing.
"""
from dataclasses import dataclass, asdict
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

parser.add_argument("--batch_size", default=32, type=int,
                    help="some help string for this argument")

group = parser.add_argument_group(
    title="Options", description="Set of Options for this script")
group.add_argument("--some_required_int", type=int,
                   required=True, help="Some required int parameter")
group.add_argument("--some_float", type=float, default=1.23,
                   help="An optional float parameter")
group.add_argument("--name", type=str, default="default",
                   help="The name of some important experiment")
group.add_argument("--log_dir", type=str, default="/logs",
                   help="An optional string parameter")
group.add_argument("--flag", action="store_true",
                   default=False, help="Wether or not to do something")

if __name__ == "__main__":  
    args = parser.parse_args()
    print(vars(args))

    batch_size = args.batch_size
    some_required_int = args.some_required_int
    some_float = args.some_float
    name = args.name
    log_dir = args.log_dir
    flag = args.flag

"""$ python examples/basic_example_before.py --help
usage: basic_example_before.py [-h] [--batch_size BATCH_SIZE]
                               --some_required_int SOME_REQUIRED_INT
                               [--some_float SOME_FLOAT] [--name NAME]
                               [--log_dir LOG_DIR] [--flag]

optional arguments:
  -h, --help            show this help message and exit
  --batch_size BATCH_SIZE
                        some help string for this argument (default: 32)

Options:
  Set of Options for this script

  --some_required_int SOME_REQUIRED_INT
                        Some required int parameter (default: None)
  --some_float SOME_FLOAT
                        An optional float parameter (default: 1.23)
  --name NAME           The name of some important experiment (default:
                        default)
  --log_dir LOG_DIR     An optional string parameter (default: /logs)
  --flag                Wether or not to do something (default: False)
"""

"""$ python examples/basic_example_before.py --some_required_int 123
{'batch_size': 32, 'some_required_int': 123, 'some_float': 1.23, 'name': 'default', 'log_dir': '/logs', 'flag': False}
"""
