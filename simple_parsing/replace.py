from typing import Any, Dict

from . import ArgumentGenerationMode
from .parsing import parse


def replace(obj: object, changes: Dict[str, Any]):
    """Return a new object replacing specified fields with new values.

    Parameters
    ----------
    - obj: object
    
        If obj is not a dataclass instance, raises TypeError

    - changes: Dict[str, Any]
    """

    _FIELDS = '__dataclass_fields__'

    if not hasattr(type(obj), _FIELDS):
        raise TypeError("replace() should be called on dataclass instances")

    args = []
    for k, v in changes.items():
        args.extend([f'--{k}', str(v)])

    return parse(obj.__class__, args=args, default=obj,
                 argument_generation_mode=ArgumentGenerationMode.NESTED)
