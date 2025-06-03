# Parsing Enums

Parsing enums can be done quite simply, like so:

```python
import enum
from dataclasses import dataclass, field

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
    """You can use Enums"""
    color: Color = Color.BLUE # my favorite colour
    temp: Temperature = Temperature.WARM

parser.add_arguments(MyPreferences, "my_preferences")
args = parser.parse_args()
prefs: MyPreferences = args.my_preferences
print(prefs)

```

You parse most datatypes using `simple-parsing`, as the type annotation on an argument is called as a conversion function in case the type of the attribute is not a builtin type or a dataclass.
