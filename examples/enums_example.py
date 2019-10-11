import argparse
import enum
from dataclasses import dataclass, field

from simple_parsing import ParseableFromCommandLine

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

class Color(enum.Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    BLUE = "BLUE"

class Temperature(enum.Enum):
    HOT = 1
    WARM = 0
    COLD = -1
    MONTREAL = -35

@dataclass
class MyPreferences(ParseableFromCommandLine):
    """You can use Enums"""
    color: Color = Color.BLUE # my favorite colour
    temp: Temperature = Temperature.WARM

MyPreferences.add_arguments(parser)
args = parser.parse_args()
prefs = MyPreferences.from_args(args)
print(prefs)
