"""Here, we demonstrate parsing multiple classes each of which has a list attribute. There are a
few options for doing this. For example, if we want to let each instance have a distinct prefix for
its arguments, we could use the ConflictResolution.AUTO option.

Here, we want to create a few instances of `CNNStack` from the command line,
but don't want to have a different prefix for each instance.
To do this, we pass the `ConflictResolution.ALWAYS_MERGE` option to the argument parser constructor.
This creates a single argument for each attribute, that will be set as multiple
(i.e., if the attribute is a `str`, the argument becomes a list of `str`, one for each class instance).

For more info, check out the docstring of the `ConflictResolution` enum.
"""

from dataclasses import dataclass, field

from simple_parsing import ArgumentParser, ConflictResolution


@dataclass
class CNNStack:
    name: str = "stack"
    num_layers: int = 3
    kernel_sizes: tuple[int, int, int] = (7, 5, 5)
    num_filters: list[int] = field(default_factory=[32, 64, 64].copy)


parser = ArgumentParser(conflict_resolution=ConflictResolution.ALWAYS_MERGE)

num_stacks = 3
for i in range(num_stacks):
    parser.add_arguments(CNNStack, dest=f"stack_{i}", default=CNNStack())

args = parser.parse_args()
stack_0 = args.stack_0
stack_1 = args.stack_1
stack_2 = args.stack_2

# BUG: When the list length and the number of instances to parse is the same,
# AND there is no default value passed to `add_arguments`, it gets parsed as
# multiple lists each with only one element, rather than duplicating the field's
# default value correctly.

print(stack_0, stack_1, stack_2, sep="\n")
expected = """\
CNNStack(name='stack', num_layers=3, kernel_sizes=(7, 5, 5), num_filters=[32, 64, 64])
CNNStack(name='stack', num_layers=3, kernel_sizes=(7, 5, 5), num_filters=[32, 64, 64])
CNNStack(name='stack', num_layers=3, kernel_sizes=(7, 5, 5), num_filters=[32, 64, 64])
"""

# Example of how to pass different lists for each instance:

args = parser.parse_args("--num_filters [1,2,3] [4,5,6] [7,8,9] ".split())
stack_0 = args.stack_0
stack_1 = args.stack_1
stack_2 = args.stack_2

# BUG: TODO: Fix the multiple + list attributes bug.
print(stack_0, stack_1, stack_2, sep="\n")
expected += """\
CNNStack(name='stack', num_layers=3, kernel_sizes=(7, 5, 5), num_filters=[1, 2, 3])
CNNStack(name='stack', num_layers=3, kernel_sizes=(7, 5, 5), num_filters=[4, 5, 6])
CNNStack(name='stack', num_layers=3, kernel_sizes=(7, 5, 5), num_filters=[7, 8, 9])
"""
