from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

group = parser.add_argument_group(
    title="Options", description="Set of options for the training of a Model."
)
group.add_argument("--num_layers", default=4, help="Number of layers to use")
group.add_argument("--num_units", default=64, help="Number of units per layer")
group.add_argument("--learning_rate", default=0.001, help="Learning rate to use")
group.add_argument(
    "--optimizer",
    default="ADAM",
    choices=["ADAM", "SGD", "RMSPROP"],
    help="Which optimizer to use",
)

args = parser.parse_args()
print(args)
expected = """
Namespace(learning_rate=0.001, num_layers=4, num_units=64, optimizer='ADAM')
"""

parser.print_help()
expected += """
usage: _before.py [-h] [--num_layers NUM_LAYERS] [--num_units NUM_UNITS]
                  [--learning_rate LEARNING_RATE]
                  [--optimizer {ADAM,SGD,RMSPROP}]

optional arguments:
  -h, --help            show this help message and exit

Options:
  Set of options for the training of a Model.

  --num_layers NUM_LAYERS
                        Number of layers to use (default: 4)
  --num_units NUM_UNITS
                        Number of units per layer (default: 64)
  --learning_rate LEARNING_RATE
                        Learning rate to use (default: 0.001)
  --optimizer {ADAM,SGD,RMSPROP}
                        Which optimizer to use (default: ADAM)
"""
