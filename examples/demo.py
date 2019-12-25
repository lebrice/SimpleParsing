# examples/demo.py
from dataclasses import dataclass
import simple_parsing

parser = simple_parsing.ArgumentParser()
parser.add_argument("--foo", type=int, default=123, help="foo help string")

@dataclass
class Options:
    """ Help string for this group of command-line arguments """
    log_dir: str                # Help string for a required str argument    
    learning_rate: float = 1e-4 # Help string for a float argument

parser.add_arguments(Options, dest="options")

args = parser.parse_args("--help ".split())
print(args.foo)     # 123
print(args.options) # Options(log_dir='logs', learning_rate=0.0001)


# args = parser.parse_args("--help".split())