from dataclasses import dataclass, field

from simple_parsing import ArgumentParser
from simple_parsing.helpers import list_field


@dataclass
class Example:
    some_integers: list[int] = field(
        default_factory=list
    )  # This is a list of integers (empty by default)
    """This list is empty, by default.

    when passed some parameters, they are automatically converted to integers, since we annotated
    the attribute with a type (typing.List[<some_type>]).
    """

    # When using a list attribute, the dataclasses module requires us to use `dataclass.field()`,
    # so each instance of this class has a different list, rather than them sharing the same list.
    # To simplify this, you can use `MutableField(value)` which is just a shortcut for `field(default_factory=lambda: value)`.
    some_floats: list[float] = list_field(3.14, 2.56)

    some_list_of_strings: list[str] = list_field("default_1", "default_2")
    """This list has a default value of ["default_1", "default_2"]."""


parser = ArgumentParser()
parser.add_arguments(Example, "example")
args = parser.parse_args()

example: Example = args.example
print(example)
expected = "Example(some_integers=[], some_floats=[3.14, 2.56], some_list_of_strings=['default_1', 'default_2'])"
