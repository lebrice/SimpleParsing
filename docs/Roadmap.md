## Currently supported features:
* Parsing of attributes of built-in types: 
    * `int`, `float`, `str` attributes
    * `bool` attributes (using either the `--<arg-name>` or the `--<arg-name> <value>` syntax)
    * `list` attributes
    * `tuple` attributes
* Parsing of multiple instances of a given dataclass, for the above-mentioned attribute types

## Possible Future Enhancements: 
* Nested parsing of instances (dataclasses within dataclasses)
* Parsing two different dataclasses which share a base class (this currently would cause a conflict for the base class arguments.