"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
from .utils import Formatter
from .parsing import ArgumentParser, InconsistentArgumentError

__all__ = [
    "ArgumentParser",
    "InconsistentArgumentError",
    "Formatter",
]