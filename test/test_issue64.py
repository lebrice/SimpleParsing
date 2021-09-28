from dataclasses import dataclass

from simple_parsing import ArgumentParser
from io import StringIO
import textwrap
import pytest


@dataclass
class Options:
    """These are the options"""

    foo: str = "aaa"  # Description
    bar: str = "bbb"


@pytest.mark.xfail(reason="Issue64 is solved below.")
def test_reproduce_issue64():

    parser = ArgumentParser("issue64")

    parser.add_arguments(Options, dest="options")

    # args = parser.parse_args(["--help"])

    s = StringIO()
    parser.print_help(file=s)
    s.seek(0)

    assert s.read() == textwrap.dedent(
        """\
    usage: issue64 [-h] [--foo str] [--bar str]

    optional arguments:
      -h, --help  show this help message and exit

    Options ['options']:
      These are the options

      --foo str   Description (default: aaa)
      --bar str
    """
    )


def test_vanilla_argparse_issue64():
    """This test shows that the ArgumentDefaultsHelpFormatter of argparse doesn't add
    the "(default: xyz)" if the 'help' argument isn't already passed!

    This begs the question: Should simple-parsing add a 'help' argument always, so that
    the formatter can then add the default string after?
    """
    import argparse

    parser = ArgumentParser(
        "issue64", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    group = parser.add_argument_group(
        "Options ['options']", description="These are the options"
    )
    group.add_argument(
        "--foo", type=str, metavar="str", default="aaa", help="Description"
    )
    group.add_argument("--bar", type=str, metavar="str", default="bbb")

    from io import StringIO

    s = StringIO()
    parser.print_help(file=s)
    s.seek(0)

    assert s.read() == textwrap.dedent(
        """\
    usage: issue64 [-h] [--foo str] [--bar str]

    optional arguments:
      -h, --help  show this help message and exit

    Options ['options']:
      These are the options

      --foo str   Description (default: aaa)
      --bar str
    """
    )


def test_solved_issue64():
    """test that shows that Issue 64 is solved now, by adding a single space as the
    'help' argument, the help formatter can then add the "(default: bbb)" after the
    argument.
    """
    parser = ArgumentParser("issue64")
    parser.add_arguments(Options, dest="options")

    s = StringIO()
    parser.print_help(file=s)
    s.seek(0)

    assert s.read() == textwrap.dedent(
        """\
    usage: issue64 [-h] [--foo str] [--bar str]

    optional arguments:
      -h, --help  show this help message and exit

    Options ['options']:
      These are the options

      --foo str   Description (default: aaa)
      --bar str   (default: bbb)
    """
    )
