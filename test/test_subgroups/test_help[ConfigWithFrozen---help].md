# Regression file for test_subgroups.py::test_help

Given Source code:

```python
@dataclasses.dataclass
class ConfigWithFrozen(TestSetup):
    conf: FrozenConfig = subgroups({"odd": odd, "even": even}, default=odd)

```

and command: '--help'

We expect to get:

```console
usage: pytest [-h] [--conf {odd,even}] [-a int] [-b str]

options:
  -h, --help         show this help message and exit

ConfigWithFrozen ['config_with_frozen']:
  ConfigWithFrozen(conf: 'FrozenConfig' = 'odd')

  --conf {odd,even}  (default: odd)

FrozenConfig ['config_with_frozen.conf']:
  FrozenConfig(a: 'int' = 1, b: 'str' = 'bob')

  -a int, --a int    (default: 1)
  -b str, --b str    (default: odd)

```
