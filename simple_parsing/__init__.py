"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
from .utils import Formatter, InconsistentArgumentError
from .parsing import ArgumentParser, PrefixingMode

__all__ = [
    "ArgumentParser",
    "InconsistentArgumentError",
    "Formatter",
    "PrefixingMode",
]