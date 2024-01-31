## Currently supported features:

- Parsing of attributes of built-in types:
  - `int`, `float`, `str` attributes
  - `bool` attributes (using either the `--<arg-name>` or the `--<arg-name> <value>` syntax)
  - `list` attributes
  - `tuple` attributes
- Parsing of multiple instances of a given dataclass, for the above-mentioned attribute types
- Nested parsing of instances (dataclasses within dataclasses)

## Possible Future Enhancements:

- Parsing two different dataclasses which share a base class (this currently would cause a conflict for the base class arguments.
