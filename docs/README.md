Welcome to the SimpleParsing wiki!
[![Build Status](https://travis-ci.org/lebrice/SimpleParsing.svg?branch=master)](https://travis-ci.org/lebrice/SimpleParsing)

# Simple, Elegant Argument Parsing

SimpleParsing allows you to group related command-line arguments into dataclasses and let the ArgumentParser take care of creating the arguments for you. 

## Documentation: [SimpleParsing Repo](https://github.com/lebrice/SimpleParsing/tree/master/docs)

## installation
| python version |                command                  |
|----------------|-----------------------------------------|
|>= 3.7          | `pip install simple-parsing`            |
|== 3.6.X        | `pip install dataclasses simple-parsing`|

## Documentation
1. Intro to Python's `@dataclass`:
     - The official [dataclasses module documentation](https://docs.python.org/3.7/library/dataclasses.html)
     - [dataclass_example.py](examples/dataclasses/dataclass_example.py): a simple toy example showing an example of a dataclass
2. Examples:
      - **[Simple Example](examples/simple/simple_example.md)**: Simple use-case example with a before/after comparison.
      - [ML HyperParameter Example](examples/dataclasses/hyperparameters_example.py): With `simple-parsing`, groups of attributes are defined directly in code as dataclasses, each holding a set of related paramters. Methods can also be added to these dataclasses, which helps to promote the "Seperation of Concerns" principle by keeping all the logic related to argument parsing in the same place as the arguments themselves. 
3. Other features and demos scripts:
      - [Automatic "--help" strings creation](examples/docstrings_example.py)
      - [Easy parsing of lists and tuples](examples/lists_example.py)
      - [**Nesting**!!](examples/nesting_example.py): Dataclasses can be nested, allowing easy reuse of similar arguments.
      - [Prefixing](examples/prefix_example.py): Prefixes can be set to easily reuse the same set of arguments multiple times
      - [Multiple instances](examples/multiple_example.py): Multiple instances of the same dataclass can be retrieved from the command-line using either prefixing or merging.
      - [Enums support](examples/enums_example.py)
      - [Parsing Multiple Lists or Tuples](examples/multiple_lists_example.py):
