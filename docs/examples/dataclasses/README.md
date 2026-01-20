# Dataclasses

These are simple examples showing how to use `@dataclass` to create argument classes.

First, take a look at the official [dataclasses module documentation](https://docs.python.org/3.7/library/dataclasses.html).

With `simple-parsing`, groups of attributes are defined directly in code as dataclasses, each holding a set of related parameters. Methods can also be added to these dataclasses, which helps to promote the "Separation of Concerns" principle by keeping all the logic related to argument parsing in the same place as the arguments themselves.

## Examples:

- [dataclass_example.py](dataclass_example.py): a simple toy example showing an example of a dataclass

- [hyperparameters_example.py](hyperparameters_example.py): Shows an example of an argument dataclass which also defines serialization methods.

<!-- TODO: add an example for mutable fields. -->

NOTE: For attributes of a mutable type (a type besides `int`, `float`, `bool` or `str`, such as `list`, `tuple`, or `object` or any of their subclasses), it is highly recommended (and often required) to use the `field` function of the dataclasses module, and to specify either a default value or a default factory function.

To simplify this, `simple-parsing` provides `MutableField`, a convenience function, which directly sets the passed argument as the return value of an anonymous factory function.
