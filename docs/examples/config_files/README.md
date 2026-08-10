# Using config files

Simple-Parsing can use default values from one or more configuration files.

The `config_path` argument can be passed to the ArgumentParser constructor. The values read from
that file will overwrite the default values from the dataclass definitions.

Additionally, when the `add_config_path_arg` argument of the `ArgumentParser` constructor is set,
a `--config_path` argument will be added to the parser. This argument accepts one or more paths to configuration
files, whose contents will be read, and used to update the defaults, in the same manner as with the
`config_path` argument above.

When using both options (the `config_path` parameter of `ArgumentParser.__init__`, as well as the `--config_path` command-line argument), the defaults are first updated using `ArgumentParser.config_path`, and then
updated with the contents of the `--config_path` file(s).

In other words, the default values are set like so, in increasing priority:

1. normal defaults (e.g. from the dataclass definitions)
2. updated with the contents of the `config_path` file(s) of `ArgumentParser.__init__`
3. updated with the contents of the `--config_path` file(s) from the command-line.

## [Single Config example](one_config.py)

When using a single config dataclass, the `simple_parsing.parse` function can then be used to simplify the argument parsing setup a bit.

## [Multiple Configs](many_configs.py)

Config files can also be used when defining multiple config dataclasses with the same parser.

## [Composition (WIP)](composition.py)

(Coming soon): Multiple config files can be composed together à-la Hydra!
