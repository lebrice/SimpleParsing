"""Example of overwriting auto-generated argparse options with custom ones. 
"""

from dataclasses import dataclass
from simple_parsing import ArgumentParser, field
from typing import List

@dataclass
class Foo:
    """ Some class Foo """

    # A sequence of tasks.
    task_sequence: List[str] = field(choices=["train", "test", "ood"])

parser = ArgumentParser()
parser.add_arguments(Foo, "foo")

args = parser.parse_args("--task_sequence train train ood".split())
foo: Foo = args.foo
print(foo)
assert foo.task_sequence == ["train", "train", "ood"]

# This would produce an error:
# parser.parse_args("--task_sequence train bob test".split())


