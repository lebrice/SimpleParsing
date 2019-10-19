"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
from .parsing import ParseableFromCommandLine, InconsistentArgumentError

__all__ = [
    "ParseableFromCommandLine", "InconsistentArgumentError"
]