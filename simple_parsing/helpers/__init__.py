""" Collection of helper classes and functions to reduce boilerplate code. """
from .fields import *
from .flatten import FlattenedAccess
from .serialization import Serializable, SimpleJsonEncoder, encode

try:
    from .serialization import YamlSerializable
except ImportError:
    pass

# For backward compatibility purposes
JsonSerializable = Serializable
SimpleEncoder = SimpleJsonEncoder
