"""
Here, we demonstrate parsing multiple classes each of which has a list attribute.
There are a few options for doing this. For example, if we want to let each instance
have a distinct prefix for its arguments, we could use the ConflictResolution.AUTO option.

Here, we want to create a few instances of `CNNStack` from the command line,
but don't want to have a different prefix for each instance.
To do this, we pass the `ConflictResolution.ALWAYS_MERGE` option to the argument parser constructor.
This creates a single argument for each attribute, that will be set as multiple
(i.e., if the attribute is a `str`, the argument becomes a list of `str`, one for each class instance). 

For more info, check out the docstring of the `ConflictResolution` enum.
"""

from dataclasses import dataclass, field, fields
from typing import List, Tuple

from simple_parsing import ArgumentParser, MutableField, ConflictResolution
from simple_parsing.utils import list_field
@dataclass
class CNNStack():
    name: str = "stack"
    num_layers: int = 3
    kernel_sizes: Tuple[int,int,int] = (7, 5, 5)
    num_filters: List[int] = list_field(32,64,64)

if __name__ == "__main__":
    parser = ArgumentParser(conflict_resolution=ConflictResolution.ALWAYS_MERGE)
    num_stacks = 3
    for i in range(num_stacks):
        parser.add_arguments(CNNStack, f"stack_{i}")

    args = parser.parse_args()

    stack_0 = args.stack_0
    stack_1 = args.stack_1
    stack_2 = args.stack_2

    # BUG: TODO: Fix the multiple + list attributes bug.
    print(stack_0, stack_1, stack_2, sep="\n")