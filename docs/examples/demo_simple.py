# examples/demo_simple.py
from dataclasses import dataclass

import simple_parsing


@dataclass
class Options:
    """Help string for this group of command-line arguments."""

    log_dir: str  # Help string for a required str argument
    learning_rate: float = 1e-4  # Help string for a float argument


options = simple_parsing.parse(Options)
print(options)
