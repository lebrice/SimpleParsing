# Parsing Container-type Arguments (list, tuple)

In "vanilla" argparse, it is usually difficult to parse lists and tuples.

`simple-parsing` makes it easier, by leveraging the type-annotations of the builtin `typing` module. Simply mark you attributes using the corresponding annotation, and the item types will be automatically converted for you:

<!-- TODO: add an example showing how it can convert a list of date strings to a list of datetime objects! -->

```python

```
