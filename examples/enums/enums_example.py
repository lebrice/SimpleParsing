import enum
from dataclasses import dataclass

from simple_parsing import ArgumentParser

parser = ArgumentParser()


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
class MyPreferences:
    """You can use Enums."""

    color: Color = Color.BLUE  # my favorite colour
    temp: Temperature = Temperature.WARM


parser.add_arguments(MyPreferences, "my_preferences")
args = parser.parse_args()
prefs: MyPreferences = args.my_preferences
print(prefs)
expected = """
MyPreferences(color=<Color.BLUE: 'BLUE'>, temp=<Temperature.WARM: 0>)
"""
