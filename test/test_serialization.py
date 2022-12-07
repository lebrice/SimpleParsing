from simple_parsing import Serializable, subgroups
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class MyArguments(Serializable):
    model: str
    dataset: str

def test_serialization_json():
    args = MyArguments(model='ResNet', dataset='ImageNet')
    json_s = args.dumps_json()
    args_from_json = MyArguments.loads_json(json_s)
    assert args.model == args_from_json.model
    assert args.dataset == args_from_json.dataset
    
def test_serialization_yaml():
    args = MyArguments(model='ResNet', dataset='ImageNet')
    yaml_s = args.dumps_yaml()
    args_from_json = MyArguments.loads_yaml(yaml_s)
    assert args.model == args_from_json.model
    assert args.dataset == args_from_json.dataset

def fullname(o):
    klass = o.__class__
    module = klass.__module__
    if module == 'builtins':
        return klass.__qualname__ # avoid outputs like 'builtins.str'
    return module + '.' + klass.__qualname__

@dataclass    
class ModelBase():
    _subgroup: str = field(init=False)
        
    def __post_init__(self):
        pass
    
    @classmethod
    def _type(cls):
        logger.info(cls)
        logger.info(f'{cls.__module__}.{cls.__name__}' )
        choices = {
            'Model_ResNet': 'resnet',
            'Model_VggNet': 'vggnet'
        }
        if cls.__name__ in choices:
            return choices[cls.__name__]
            

class Model_ResNet(ModelBase):
    nclass: int = 1000
    batch_norm: bool = True
    
    def __post_init__(self):
        self._subgroup = self._type()

class Model_VggNet(ModelBase):
    nclass: int = 1000
    batch_norm: bool = False

    def __post_init__(self):
        self._subgroup = self._type()

@dataclass
class MyArgumentsSubgroups(Serializable):
    sub: ModelBase = subgroups(
        {"resnet": Model_ResNet, "vggnet": Model_VggNet},
        default=Model_ResNet()
    )
    sub1: dict = field(default_factory=lambda : {'test': True, 'test1': False})
    
    # def __post_init__(self):
    #     self.sub._subgroup = self.sub
    
def test_serialization_subgroups():
    args = MyArgumentsSubgroups()
    logger.info(args.sub)
    assert args.sub.nclass == 1000
    assert args.sub._subgroup == 'resnet'