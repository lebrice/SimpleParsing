from dataclasses import dataclass
from pathlib import Path
from typing import Union

from simple_parsing import ArgumentParser


@dataclass
class Train:
    """Example of a command to start a Training run."""

    # the training directory
    train_dir: Path = Path("~/train")

    def execute(self):
        print(f"Training in directory {self.train_dir}")


@dataclass
class Test:
    """Example of a command to start a Test run."""

    # the testing directory
    test_dir: Path = Path("~/train")

    def execute(self):
        print(f"Testing in directory {self.test_dir}")


@dataclass
class Program:
    """Some top-level command."""

    command: Union[Train, Test]
    verbose: bool = False  # log additional messages in the console.

    def execute(self):
        print(f"Program (verbose: {self.verbose})")
        return self.command.execute()


parser = ArgumentParser()
parser.add_arguments(Program, dest="prog")
args = parser.parse_args()
prog: Program = args.prog

print("prog:", prog)
prog.execute()
