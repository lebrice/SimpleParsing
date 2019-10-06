# Simple, Elegant Argument Parsing

When applied to a dataclass, this enables creating an instance of that class and populating the attributes from the command-line.
    
A simple example:
```
@dataclass
class Options(ParseableFromCommandLine):
    a: int
    b: int = 10

parser = argparse.ArgumentParser()
Options.add_cmd_args(parser)

args = parser.parse_args("--a 5")
options = Options.from_args(args)
print(options) # gives "Options(a=5, b=10)"

args = parser.parse_args("--a 1 2 --b 9")
options_list = Options.from_args_multiple(args, 2)
print(options_list) # gives "[Options(a=1, b=9), Options(a=2, b=9)]"

```