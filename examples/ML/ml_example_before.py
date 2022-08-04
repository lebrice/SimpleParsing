from argparse import ArgumentParser

parser = ArgumentParser()

# hyperparameters
parser.add_argument("--learning_rate", type=float, default=0.05)
parser.add_argument("--momentum", type=float, default=0.01)
# (... other hyperparameters here)

# args for training config
parser.add_argument("--data_dir", type=str, default="/data")
parser.add_argument("--log_dir", type=str, default="/logs")
parser.add_argument("--checkpoint_dir", type=str, default="checkpoints")

args = parser.parse_args()

learning_rate = args.learning_rate
momentum = args.momentum
# (...) dereference all the variables here, without any typing
data_dir = args.data_dir
log_dir = args.log_dir
checkpoint_dir = args.checkpoint_dir


class MyModel:
    def __init__(self, data_dir, log_dir, checkpoint_dir, learning_rate, momentum, *args):
        # config:
        self.data_dir = data_dir
        self.log_dir = log_dir
        self.checkpoint_dir = checkpoint_dir

        # hyperparameters:
        self.learning_rate = learning_rate
        self.momentum = momentum


m = MyModel(data_dir, log_dir, checkpoint_dir, learning_rate, momentum)
# Ok, what if we wanted to add a new hyperparameter?!
