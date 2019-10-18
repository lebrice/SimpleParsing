"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
import argparse
import collections
import dataclasses
import enum
import inspect
import typing
from collections import namedtuple
from typing import *

# from . import docstring, utils
# from . import simple_parsing

from .parsing import ParseableFromCommandLine, InconsistentArgumentError

__all__ = [
    "ParseableFromCommandLine", "InconsistentArgumentError"
]