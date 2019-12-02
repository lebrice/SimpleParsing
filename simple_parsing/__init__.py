"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
from .utils import Formatter, InconsistentArgumentError, MutableField
from .parsing import ArgumentParser, ConflictResolution

__all__ = [
    "ArgumentParser",
    "InconsistentArgumentError",
    "Formatter",
    "ConflictResolution",
    "MutableField"
]