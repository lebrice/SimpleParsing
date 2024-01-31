from dataclasses import dataclass

import simple_parsing

# create a parser,
parser = simple_parsing.ArgumentParser()


@dataclass
class MyModelHyperParameters:
    """Hyperparameters of MyModel."""

    # Batch size (per-GPU)
    batch_size: int = 32
    # Learning rate of the Adam optimizer.
    learning_rate: float = 0.05
    # Momentum of the optimizer.
    momentum: float = 0.01


@dataclass
class TrainingConfig:
    """Settings related to Training."""

    data_dir: str = "data"
    log_dir: str = "logs"
    checkpoint_dir: str = "checkpoints"


@dataclass
class EvalConfig:
    """Settings related to evaluation."""

    eval_dir: str = "eval_data"


# automatically add arguments for all the fields of the classes above:
parser.add_arguments(MyModelHyperParameters, "hparams")
parser.add_arguments(TrainingConfig, "train_config")
parser.add_arguments(EvalConfig, "eval_config")

# NOTE: `ArgumentParser` is just a subclass of `argparse.ArgumentParser`,
# so we could add some other arguments as usual:
# parser.add_argument(...)
# parser.add_argument(...)
# (...)
# parser.add_argument(...)
# parser.add_argument(...)

args = parser.parse_args()

# Retrieve the objects from the parsed args!
hparams: MyModelHyperParameters = args.hparams
train_config: TrainingConfig = args.train_config
eval_config: EvalConfig = args.eval_config

print(hparams, train_config, eval_config, sep="\n")
expected = """
MyModelHyperParameters(batch_size=32, learning_rate=0.05, momentum=0.01)
TrainingConfig(data_dir='data', log_dir='logs', checkpoint_dir='checkpoints')
EvalConfig(eval_dir='eval_data')
"""
