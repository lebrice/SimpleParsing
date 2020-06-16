
import dataclasses
import json
import yaml
import logging
from collections import OrderedDict, defaultdict
from functools import singledispatch
from dataclasses import dataclass, is_dataclass, fields, Field
from pathlib import Path
from typing import *
from typing import IO
import warnings
import typing_inspect
from typing_inspect import is_generic_type, is_optional_type, get_args
from textwrap import shorten
import os
logger = logging.getLogger(__file__)

from .decoding import register_decoding_fn
from .encoding import encode, SimpleJsonEncoder
from .serializable import Serializable, from_dict

Dataclass = TypeVar("Dataclass")

JsonSerializable = Serializable

@encode.register
def encode_json(obj: JsonSerializable) -> Dict:
    return json.loads(json.dumps(obj, cls=SimpleJsonEncoder))
