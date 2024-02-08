import random


def set_seed(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch
    except ImportError:
        pass
    else:
        try:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except AttributeError:
            pass


def _unused_function():
    ...  # unused function just to check that the PR comments check with codecov works.
