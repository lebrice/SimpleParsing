"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
from .utils import Formatter, InconsistentArgumentError
from .parsing import ArgumentParser

__all__ = [
    "ArgumentParser",
    "InconsistentArgumentError",
    "Formatter",
]