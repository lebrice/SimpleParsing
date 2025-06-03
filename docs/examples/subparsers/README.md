### [(Examples Home)](../README.md)

# Creating Commands with Subparsers

Subparsers are one of the more advanced features of `argparse`. They allow the creation of subcommands, each having their own set of arguments. The `git` command, for instance, takes different arguments than the `pull` subcommand in `git pull`.

For some more info on subparsers, check out the [argparse documentation](https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers).

With `simple-parsing`, subparsers can easily be created by using a `Union` type annotation on a dataclass attribute. By annotating a variable with a Union type, for example `x: Union[T1, T2]`, we simply state that `x` can either be of type `T1` or `T2`. When the arguments to the `Union` type **are all dataclasses**, `simple-parsing` creates subparsers for each dataclass type, using the lowercased class name as the command name by default.

If you want to extend or change this behaviour (to have "t" and "train" map to the same training subcommand, for example), use the `subparsers` function, passing in a dictionary mapping command names to the appropriate type.

<!-- TODO: if the string name in the dict has an uppercase letter, the command might not be executable? -->

## Example:

```python
from dataclasses import dataclass
from typing import *
from pathlib import Path
from simple_parsing import ArgumentParser, subparsers

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
    """Some top-level command"""
    command: Union[Train, Test]
    verbose: bool = False   # log additional messages in the console.

    def execute(self):
        print(f"Executing Program (verbose: {self.verbose})")
        return self.command.execute()


parser = ArgumentParser()
parser.add_arguments(Program, dest="prog")
args = parser.parse_args()
prog: Program = args.prog

print("prog:", prog)
prog.execute()
```

Here are some usage examples:

- Executing the training command:

  ```console
  $ python examples/subparsers/subparsers_example.py train
  prog: Program(command=Train(train_dir=PosixPath('~/train')), verbose=False)
  Executing Program (verbose: False)
  Training in directory ~/train
  ```

- Passing a custom training directory:

  ```console
  $ python examples/subparsers/subparsers_example.py train --train_dir ~/train
  prog: Program(command=Train(train_dir=PosixPath('/home/fabrice/train')), verbose=False)
  Executing Program (verbose: False)
  Training in directory /home/fabrice/train
  ```

- Getting help for a subcommand:

  ```console
  $ python examples/subparsers/subparsers_example.py train --help
  usage: subparsers_example.py train [-h] [--train_dir Path]

  optional arguments:
  -h, --help        show this help message and exit

  Train ['prog.command']:
  Example of a command to start a Training run.

  --train_dir Path  the training directory (default: ~/train)
  ```

- Getting Help for the parent command:

  ```console
  $ python examples/subparsers/subparsers_example.py --help
  usage: subparsers_example.py [-h] [--verbose [str2bool]] {train,test} ...

  optional arguments:
  -h, --help            show this help message and exit

  Program ['prog']:
  Some top-level command

  --verbose [str2bool]  log additional messages in the console. (default:
                          False)

  command:
  {train,test}
  ```
