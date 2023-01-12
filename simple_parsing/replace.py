from collections.abc import MutableMapping
from typing import Any, Dict

from . import ArgumentGenerationMode
from .parsing import Dataclass, parse


def flatten(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def replace(obj: object, changes: Dict[str, Any]) -> Dataclass:
    """Return a new object replacing specified fields with new values.

    Parameters
    ----------
    - obj: object

        If obj is not a dataclass instance, raises TypeError

    - changes: Dict[str, Any]

        The dictionary can be nested or flatten structure which is especially useful for frozen classes. Example usage::

        @dataclass
        class InnerClass:
            arg1: int = 0
            arg2: str = "foo"

        @dataclass(frozen=True)
        class OuterClass:
            outarg: int = 1
            nested: InnerClass = InnerClass()

        changes_1 = {"outarg": 2, "nested.arg1": 1, "nested.arg2": "bar"}
        changes_2 = {"outarg": 2, "nested": {"arg1": 1, "arg2": "bar"}}
        c = OuterClass()
        c1 = replace(c, changes_1)
        c2 = replace(c, changes_2)
        assert c1 == c2
    """

    _FIELDS = "__dataclass_fields__"

    if not hasattr(type(obj), _FIELDS):
        raise TypeError("replace() should be called on dataclass instances")

    flatten_changes = flatten(changes)
    print(flatten_changes)
    args = []
    for k, v in flatten_changes.items():
        args.extend([f"--{k}", str(v)])

    return parse(
        obj.__class__,
        args=args,
        default=obj,
        argument_generation_mode=ArgumentGenerationMode.NESTED,
    )
