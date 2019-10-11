import argparse
from dataclasses import dataclass, field
from typing import List, Tuple

from simple_parsing import ParseableFromCommandLine

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

@dataclass
class Example(ParseableFromCommandLine):
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


Example.add_arguments(parser)
args = parser.parse_args()
example = Example.from_args(args)
print(example)