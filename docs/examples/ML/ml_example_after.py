from dataclasses import dataclass

from simple_parsing import ArgumentParser

# create a parser, as usual
parser = ArgumentParser()


@dataclass
class MyModelHyperParameters:
    """Hyperparameters of MyModel."""

    # Learning rate of the Adam optimizer.
    learning_rate: float = 0.05
    # Momentum of the optimizer.
    momentum: float = 0.01


@dataclass
class TrainingConfig:
    """Training configuration settings."""

    data_dir: str = "/data"
    log_dir: str = "/logs"
    checkpoint_dir: str = "checkpoints"


# automatically add arguments for all the fields of the classes above:
parser.add_arguments(MyModelHyperParameters, dest="hparams")
parser.add_arguments(TrainingConfig, dest="config")

args = parser.parse_args()

# Create an instance of each class and populate its values from the command line arguments:
hyperparameters: MyModelHyperParameters = args.hparams
config: TrainingConfig = args.config


class MyModel:
    def __init__(self, hyperparameters: MyModelHyperParameters, config: TrainingConfig):
        # hyperparameters:
        self.hyperparameters = hyperparameters
        # config:
        self.config = config


m = MyModel(hyperparameters, config)
