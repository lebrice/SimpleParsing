"""
A simple example to demonstrate the 'attribute docstrings' mechanism of simpleparse.
    
A docstring can either be: 
    - An inline comment after the attribute definition
    - A single or multi-line comment on the preceding line(s)
    - A single or multi-line docstring on the following line(s), starting
    with either <\"\"\"> or <'''> and ending with the same token.

When more than one docstring options are present, one of them is chosen to
be used as the '--help' text of the attribute, according to the following ordering:
    1- docstring below the attribute
    2- comment above the attribute
    3- inline comment

NOTE: It is recommended to add blank lines between cosecutive attribute
assignments when using either the 'comment above' or 'docstring below'
style, just for clarity. This doesn't change anything about the output of
the "--help" command.
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
