# Prefixing Mechanics

Before starting to use multiple dataclasses or nesting them, it is good to first understand the prefixing mechanism used by `simple-parsing`.

What's important to consider is that in `argparse`, arguments can only be provided as a "flat" list.

In order to be able to "reuse" arguments and parse multiple instances of the same class from the command-line, we therefore have to choose between these options:

1. Give each individual argument a differentiating prefix; (default)
2. Disallow the reuse of arguments;
3. Parse a List of values instead of a single value, and later redistribute the value to the instances.

You can control which of these three behaviours the parser is to use by setting the `conflict_resolution` argument of `simple_parsing.ArgumentParser`'s `__init__` method.

- For option 1, use either the `ConflictResolution.AUTO` or `ConflictResolution.EXPLICIT` options
- For option 2, use the `ConflictResolution.NONE` option.
- For option 3, use the `ConflictResolution.ALWAYS_MERGE` option.
