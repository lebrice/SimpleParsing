from dataclasses import dataclass, field
from typing import List, Tuple

from simple_parsing import ArgumentParser, MutableField

parser = ArgumentParser()

@dataclass()
class Example():
    # As well as lists using dataclasses.field (see the dataclasses package):
    some_list_of_ints: List[int] = MutableField([])
    """This list is empty, by default. when passed some parameters, they are
    automatically converted to integers, since we annotated the attribute with
    a type (typing.List[<some_type>]).
    """

    # MutableField(value) is just a shortcut for field(default_factory=lambda: value)
    some_list_of_strings: List[str] = MutableField(["default_1", "default_2"])
    """This list has a default value of ["default_1", "default_2"]."""


parser.add_arguments(Example, "example")
args = parser.parse_args()

example: Example = args.example

print(example)