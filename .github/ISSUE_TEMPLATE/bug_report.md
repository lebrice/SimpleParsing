---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
```python
from simple_parsing import ArgumentParser
from dataclasses import dataclass

@dataclass
class Foo:
   bar: int = 123

if __name__ == "__main__":
   parser = ArgumentParser()
   parser.add_arguments(Foo, "foo")
   args = parser.parse_args()
   foo: Foo = args.foo
   print(foo)
```

**Expected behavior**
A clear and concise description of what you expected to happen.

```console
$ python issue.py
Foo(bar=123)
$ python issue.py --bar 456
Foo(bar=456)
```

**Actual behavior**
A clear and concise description of what is happening.

```console
$ python issue.py
Foo(bar=123)
$ python issue.py --bar 456
Foo(bar=456)
```

**Desktop (please complete the following information):**
 - Version [e.g. 22]
 - Python version: ?

**Additional context**
Add any other context about the problem here.
