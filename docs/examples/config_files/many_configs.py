import shlex
from dataclasses import dataclass

import simple_parsing


@dataclass
class TrainConfig:
    """Training config for Machine Learning."""

    workers: int = 8  # The number of workers for training
    exp_name: str = "default_exp"  # The experiment name


@dataclass
class EvalConfig:
    """Evaluation config."""

    n_batches: int = 8  # The number of batches for evaluation
    checkpoint: str = "best.pth"  # The checkpoint to use


def main(args=None) -> None:
    parser = simple_parsing.ArgumentParser(add_config_path_arg=True)

    parser.add_arguments(TrainConfig, dest="train")
    parser.add_arguments(EvalConfig, dest="eval")

    if isinstance(args, str):
        args = shlex.split(args)
    args = parser.parse_args(args)

    train_config: TrainConfig = args.train
    eval_config: EvalConfig = args.eval
    print(f"Training {train_config.exp_name} with {train_config.workers} workers...")
    print(f"Evaluating '{eval_config.checkpoint}' with {eval_config.n_batches} batches...")


main()
expected = """
Training default_exp with 8 workers...
Evaluating 'best.pth' with 8 batches...
"""


main("")
expected += """\
Training default_exp with 8 workers...
Evaluating 'best.pth' with 8 batches...
"""

main("--config_path many_configs.yaml --exp_name my_first_exp")
expected += """\
Training my_first_exp with 42 workers...
Evaluating 'best.pth' with 100 batches...
"""
