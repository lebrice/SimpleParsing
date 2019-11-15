from dataclasses import field, dataclass, asdict
from simple_parsing import ArgumentParser
from typing import List, ClassVar
from pprint import pprint

@dataclass
class HParams:
    """
    Model Hyper-parameters
    """
    # Number of examples per batch
    batch_size: int = 32
    # fixed learning rate passed to the optimizer.
    learning_rate: float = 0.005 
    # name of the optimizer class to use
    optimizer: str = "ADAM"
    
    
    default_num_layers: ClassVar[int] = 10
    
    # number of layers.
    num_layers: int = default_num_layers
    # the number of neurons at each layer
    neurons_per_layer: List[int] = field(default_factory=lambda: [128] * HParams.default_num_layers)
@dataclass
class RunConfig:
    """
    Group of settings used during a training or validation run.
    """
    # the set of hyperparameters for this run.
    hparams: HParams = HParams()
    log_dir: str = "logs" # The logging directory where
    checkpoint_dir: str = field(init=False)
    
    def __post_init__(self):
        """Post-Init to set the fields that shouldn't be constructor arguments."""
        import os
        self.checkpoint_dir = os.path.join(self.log_dir, "checkpoints")

@dataclass
class TrainConfig:
    """
    Top-level settings for multiple runs.
    """
    # run config to be used during training
    train: RunConfig = RunConfig(log_dir="train")
    # run config to be used during validation.
    valid: RunConfig = RunConfig(log_dir="valid")

parser = ArgumentParser()

parser.add_arguments(TrainConfig, "train_config")

args = parser.parse_args()

train_config: TrainConfig = args.train_config

pprint(asdict(train_config), compact=True)