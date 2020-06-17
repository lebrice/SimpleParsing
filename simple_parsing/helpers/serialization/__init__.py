from .serializable import Serializable
JsonSerializable = Serializable
try:
    from .yaml_serialization import YamlSerializable
except ImportError:
    pass
from .decoding import *
from .encoding import *
