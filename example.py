import argparse
from dataclasses import dataclass, field
from typing import List, Tuple

from simple_parsing import ParseableFromCommandLine

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

@dataclass
class Options(ParseableFromCommandLine):
    """ A class which groups related parameters. """
    foo: int # Some required parameter named foo.
    bar: int = 10 # Some parameter named bar.
    log_dir: str = "/logs"
    """the logging directory to use. (This is an attribute docstring)"""


import enum
class Color(enum.Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    BLUE = "BLUE"


@dataclass
class OtherOptions(ParseableFromCommandLine):
    """Some other options, cleanly separated from the `Options` class
    """
    #This parameter is very different. it has a comment above it, which acts as a docstring.
    different_param: float = 0.05
    
    # This flag, when present, changes everything.
    some_flag: bool = False
    
    # You can use Enums:
    some_enum: Color = Color.BLUE # this 



@dataclass
class ListsExample(ParseableFromCommandLine):
    # As well as lists using dataclasses.field (see the dataclasses package):
    some_list_of_ints: List[int] = field(default_factory=list)
    """This list is empty, by default. when passed some parameters, they are
    automatically converted to integers, since we annotated the attribute with
    a type (typing.List[<some_type>]).
    """
    
    some_list_of_strings: List[str] = field(default_factory=lambda: ["default_1", "default_2"])
    """This list has a default value of ["default_1", "default_2"]."""


    some_list_of_strings: List[str] = field(default_factory=lambda: ["default_1", "default_2"])
    """This list has a default value of ["default_1", "default_2"]."""


@dataclass
class DocStringsExample(ParseableFromCommandLine):
    """
    A simple example to demonstrate the order of importance of docstrings,
    to be able to understand which one ends up in the help text for each attribute.
    
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

    NOTE: This block of text is the class docstring, and it will show up under
    the name of the class in the --help group for this set of parameters.    
    """

    attribute1: float = 1.0
    """docstring below, When used, this always shows up in the --help text for this attribute"""

    # Comment above only: this shows up in the help text, since there is no docstring below.
    attribute3: float = 1.0

    attribute2: float = 1.0 # inline comment only (this shows up in the help text, since none of the two other options are present.)

    # comment above
    attribute4: float = 1.0 # inline comment
    """docstring below (this appears in --help)"""

    # comment above (this appears in --help)
    attribute5: float = 1.0 # inline comment
    
    attribute6: float = 1.0 # inline comment (this appears in --help)

    attribute7: float = 1.0 # inline comment
    """docstring below (this appears in --help)"""




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
