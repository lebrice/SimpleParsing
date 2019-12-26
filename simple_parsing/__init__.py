"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
from .utils import Formatter, InconsistentArgumentError, MutableField, choice
from .parsing import ArgumentParser, ConflictResolution

__version__ = "0.0.3.post6"

__all__ = [
    "ArgumentParser",
    "InconsistentArgumentError",
    "Formatter",
    "ConflictResolution",
    "MutableField",
    "choice",
]