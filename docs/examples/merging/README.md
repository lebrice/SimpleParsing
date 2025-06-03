# Parsing Multiple Dataclasses with Merging

Here, we demonstrate parsing multiple classes each of which has a list attribute.
There are a few options for doing this. For example, if we want to let each instance have a distinct prefix for its arguments, we could use the ConflictResolution.AUTO option.

In the following examples, we instead want to create a multiple instances of the argument dataclasses from the command line, but we don't want to have a different prefix for each instance.

To do this, we pass the `ConflictResolution.ALWAYS_MERGE` option to the argument parser constructor. This creates a single argument for each attribute that will be set as multiple (i.e., if the attribute was of type `str`, the argument becomes a list of `str`, one for each class instance).

For more info, check out the docstring of the `ConflictResolution` enum.

## Examples:

- [multiple_example.py](multiple_example.py)
- [multiple_lists_example.py](multiple_lists_example.py)
