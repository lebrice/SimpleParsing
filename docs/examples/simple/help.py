from dataclasses import dataclass

from simple_parsing import ArgumentParser


@dataclass
class HParams:
    """Set of options for the training of a ML Model.

    Some more detailed description can be placed here, and will show-up in
    the auto-generated "--help" text.

    Some other **cool** uses for this space:
    - Provide links to previous works: (easy to click on from the command-line)
      - MAML: https://arxiv.org/abs/1703.03400
      - google: https://www.google.com
    - This can also interact nicely with documentation tools like Sphinx!
      For instance, you could add links to other parts of your documentation.

    The default HelpFormatter used by `simple_parsing` will keep the formatting
    of this section intact, will add an indicator of the default values, and
    will use the name of the attribute's type as the metavar in the help string.
    For more info, check out the `SimpleFormatter` class found in
    ./simple_parsing/utils.py
    """

    num_layers: int = 4  # Number of layers in the model.
    num_units: int = 64  # Number of units (neurons) per layer.
    optimizer: str = "ADAM"  # Which optimizer to use.
    learning_rate: float = 0.001  # Learning_rate used by the optimizer.

    alpha: float = 0.05  # TODO: Tune this. (This doesn't appear in '--help')
    """A detailed description of this new 'alpha' parameter, which can potentially span multiple
    lines."""


parser = ArgumentParser()
parser.add_arguments(HParams, dest="hparams")
args = parser.parse_args()

print(args.hparams)
expected = """
HParams(num_layers=4, num_units=64, optimizer='ADAM', learning_rate=0.001, alpha=0.05)
"""

parser.print_help()
expected += """
usage: help.py [-h] [--num_layers int] [--num_units int] [--optimizer str]
               [--learning_rate float] [--alpha float]

optional arguments:
  -h, --help            show this help message and exit

HParams ['hparams']:
   Set of options for the training of a ML Model.

      Some more detailed description can be placed here, and will show-up in
      the auto-generated "--help" text.

      Some other **cool** uses for this space:
      - Provide links to previous works: (easy to click on from the command-line)
        - MAML: https://arxiv.org/abs/1703.03400
        - google: https://www.google.com
      - This can also interact nicely with documentation tools like Sphinx!
        For instance, you could add links to other parts of your documentation.

      The default HelpFormatter used by `simple_parsing` will keep the formatting
      of this section intact, will add an indicator of the default values, and
      will use the name of the attribute's type as the metavar in the help string.
      For more info, check out the `SimpleFormatter` class found in
      ./simple_parsing/utils.py


  --num_layers int      Number of layers in the model. (default: 4)
  --num_units int       Number of units (neurons) per layer. (default: 64)
  --optimizer str       Which optimizer to use. (default: ADAM)
  --learning_rate float
                        Learning_rate used by the optimizer. (default: 0.001)
  --alpha float         A detailed description of this new 'alpha' parameter,
                        which can potentially span multiple lines. (default:
                        0.05)
"""
