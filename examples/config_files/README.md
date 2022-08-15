# Using config files

Simple-Parsing can use default values from a configuration file.

The `config_path` argument can be passed to the ArgumentParser constructor. The default values for
all arguments will be set from that file.

Additionally, when the `add_config_path_arg` argument of the `ArgumentParser` constructor is set,
a `--config_path` argument will be added. This argument will overwrite the defaults.
If the `config_path` argument to the `ArgumentParser` constructor is also set, then the values in
the config file passed as `--config_path` are applied on top of those from the `ArgumentParser.config_file`.

Therefore, the default values are set like so, in increasing priority:
1. normal defaults (e.g. from the dataclass definitions)
2. from the `config_path` argument of `ArgumentParser.__init__`
3. from the `--config_path` argument on the command-line.


## Examples:

1. [train_model.py]()



Note: Pyrallis is a "fork" of Simple-Parsing. It has some nice features. Check it out if you want.
