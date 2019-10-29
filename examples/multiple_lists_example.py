from dataclasses import dataclass, field
from typing import List

from simple_parsing import ArgumentParser

@dataclass()
class CNNStack():
    name: str = "stack"
    num_layers: int = 3
    kernel_sizes: List[int] = field(default_factory=lambda: [7, 5, 5])
    num_filters: List[int] = field(default_factory=lambda: [32,64,64])

#Parsing a single instance of this class can be done like so, using the usual command-line list syntax:
parser = ArgumentParser()
num_stacks = 3
for i in range(num_stacks):
    parser.add_arguments(CNNStack, f"stack_{i}")

args = parser.parse_args()

stack_0 = args.stack_0
stack_1 = args.stack_1
stack_2 = args.stack_2

# BUG: TODO: Fix the multiple + list attributes bug.
print(stack_0, stack_1, stack_2, sep="\n")