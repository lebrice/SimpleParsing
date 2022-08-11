import textwrap
from dataclasses import dataclass
from io import StringIO
from test.testutils import assert_help_output_equals

from simple_parsing import ArgumentParser, field


@dataclass
class InputArgs:
    # Start date from which to collect data about base users. Input in iso format (YYYY-MM-DD).
    # The date is included in the data
    start_date: str = field(alias="s", metadata={"a": "b"})

    # End date for collecting base users. Input in iso format (YYYY-MM-DD). The date is included in the data.
    # Should not be before `start_date`
    end_date: str = field(alias="e")


def test_issue_48():
    parser = ArgumentParser("Prepare input data for training")
    parser.add_arguments(InputArgs, dest="args")
    s = StringIO()
    parser.print_help(file=s)
    s.seek(0)
    output = str(s.read())
    assert_help_output_equals(
        actual=output,
        expected=textwrap.dedent(
            """\
            usage: Prepare input data for training [-h] -s str -e str

            optional arguments:
            -h, --help            show this help message and exit

            InputArgs ['args']:
            InputArgs(start_date:str, end_date:str)

            -s str, --start_date str
                                    Start date from which to collect data about base
                                    users. Input in iso format (YYYY-MM-DD). The date is
                                    included in the data (default: None)
            -e str, --end_date str
                                    End date for collecting base users. Input in iso
                                    format (YYYY-MM-DD). The date is included in the data.
                                    Should not be before `start_date` (default: None)
            """
        ),
    )

    # args = parser.parse_args()
