from simple_parsing import ArgumentParser, field
from dataclasses import dataclass

@dataclass
class InputArgs:
    # Start date from which to collect data about base users. Input in iso format (YYYY-MM-DD).
    # The date is included in the data
    start_date: str = field(alias="s", metadata={'a':'b'})

    # End date for collecting base users. Input in iso format (YYYY-MM-DD). The date is included in the data.
    # Should not be before `start_date`
    end_date: str = field(alias="e")


from io import StringIO
import textwrap


def test_issue_48():
    parser = ArgumentParser("Prepare input data for training")
    parser.add_arguments(InputArgs, dest="args")
    s = StringIO()
    parser.print_help(file=s)
    s.seek(0)
    assert s.read().replace(" ", "") == textwrap.dedent("""\
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
        """).replace(" ", "")
    
    
    # args = parser.parse_args()