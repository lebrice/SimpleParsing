import numpy as np
import random

def set_seed(seed: int):
    np.random.seed(seed)
    random.seed(seed)
    try:
        import torch
    except ImportError:
        pass
    else:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)