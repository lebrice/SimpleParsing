# Using Aliases

## Notes about `option_strings`:

Additional names for the same argument can be added via the `alias` argument
of the `field` function (see [the custom_args Example](/examples/custom_args/README.md) for more info).

The `simple_parsing.ArgumentParser` accepts an argument (currently called `add_option_string_dash_variants`, which defaults to False) which adds additional variants to allow using either dashes or underscores to refer to an argument:

- Whenever the name of an attribute includes underscores ("\_"), the same
  argument can be passed by using dashes ("-") instead. This also includes
  aliases.
- If an alias contained leading dashes, either single or double, the
  same number of dashes will be used, even in the case where a prefix is
  added.
  For instance, consider the following example.
  Here we have two prefixes: `"train"` and `"valid"`.
  The corresponding option_strings for each argument will be
  `["--train.debug", "-train.d"]` and `["--valid.debug", "-valid.d"]`,
  respectively, as shown here:

```python
from dataclasses import dataclass
from simple_parsing import ArgumentParser, field

@dataclass
class RunSettings:
    ''' Parameters for a run. '''
    # whether or not to execute in debug mode.
    debug: bool = field(alias=["-d"], default=False)
    some_value: int = field(alias=["-v"], default=123)

parser = ArgumentParser(add_option_string_dash_variants=True)
parser.add_arguments(RunSettings, dest="train")
parser.add_arguments(RunSettings, dest="valid")
parser.print_help()

# This prints:
'''
usage: test.py [-h] [--train.debug [bool]] [--train.some_value int]
               [--valid.debug [bool]] [--valid.some_value int]

optional arguments:
  -h, --help            show this help message and exit

RunSettings ['train']:
  Parameters for a run.

  --train.debug [bool], --train.d [bool]
                        whether or not to execute in debug mode. (default:
                        False)
  --train.some_value int, --train.v int, ---train.some-value int

RunSettings ['valid']:
  Parameters for a run.

  --valid.debug [bool], --valid.d [bool]
                        whether or not to execute in debug mode. (default:
                        False)
  --valid.some_value int, --valid.v int, ---valid.some-value int
'''
```
