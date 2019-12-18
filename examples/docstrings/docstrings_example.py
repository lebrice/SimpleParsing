"""
A simple example to demonstrate the 'attribute docstrings' mechanism of simple-parsing.

"""
from dataclasses import dataclass, field
from typing import List, Tuple

from simple_parsing import ArgumentParser

parser = ArgumentParser()

@dataclass
class DocStringsExample():
    """NOTE: This block of text is the class docstring, and it will show up under
    the name of the class in the --help group for this set of parameters.    
    """

    attribute1: float = 1.0
    """docstring below, When used, this always shows up in the --help text for this attribute"""

    # Comment above only: this shows up in the help text, since there is no docstring below.
    attribute2: float = 1.0

    attribute3: float = 1.0 # inline comment only (this shows up in the help text, since none of the two other options are present.)

    # comment above 42
    attribute4: float = 1.0 # inline comment
    """docstring below (this appears in --help)"""

    # comment above (this appears in --help) 46
    attribute5: float = 1.0 # inline comment
    
    attribute6: float = 1.0 # inline comment (this appears in --help)

    attribute7: float = 1.0 # inline comment
    """docstring below (this appears in --help)"""


parser.add_arguments(DocStringsExample, "example")
args = parser.parse_args()
ex = args.example
print(ex)
