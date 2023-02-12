import textwrap
from dataclasses import dataclass
from io import StringIO
from test.testutils import assert_help_output_equals

import pytest

import simple_parsing
from simple_parsing.wrappers.field_wrapper import ArgumentGenerationMode


@dataclass
class JBuildRelease:
    id: int
    url: str
    docker_image: str


def test_issue_46(assert_equals_stdout):
    parser = simple_parsing.ArgumentParser()
    parser.add_argument("--run_id", type=str)
    parser.add_arguments(JBuildRelease, dest="jbuild", prefix="jbuild")

    s = StringIO()
    parser.print_help(s)
    s.seek(0)
    output = str(s.read())

    assert_help_output_equals(
        actual=output,
        expected=textwrap.dedent(
            """\
        usage: pytest [-h] [--run_id str] --jbuildid int --jbuildurl str
                    --jbuilddocker_image str

        optional arguments:
        -h, --help            show this help message and exit
        --run_id str

        JBuildRelease ['jbuild']:
        JBuildRelease(id:int, url:str, docker_image:str)

        --jbuildid int
        --jbuildurl str
        --jbuilddocker_image str
        """
        ),
    )

    # assert_equals_stdout(
    #     textwrap.dedent(
    #         """\
    #         usage: pytest [-h] [--run_id str] --jbuildid int --jbuildurl str
    #                     --jbuilddocker_image str

    #         optional arguments:
    #         -h, --help            show this help message and exit
    #         --run_id str

    #         JBuildRelease ['jbuild']:
    #         JBuildRelease(id:int, url:str, docker_image:str)

    #         --jbuildid int
    #         --jbuildurl str
    #         --jbuilddocker_image str
    #         """
    #     )
    # )
    from .testutils import raises_missing_required_arg

    with raises_missing_required_arg():
        parser.parse_args(
            "--id 123 --jbuild.id 456 --jbuild.url bob --jbuild.docker_image foo".split()
        )


def test_issue_46_solution2(assert_equals_stdout):
    # This (now) works:
    parser = simple_parsing.ArgumentParser(argument_generation_mode=ArgumentGenerationMode.BOTH)
    parser.add_argument("--run_id", type=str)
    parser.add_arguments(JBuildRelease, dest="jbuild", prefix="jbuild.")
    s = StringIO()
    parser.print_help(s)
    s.seek(0)
    output = str(s.read())
    assert_help_output_equals(
        actual=output,
        expected=textwrap.dedent(
            """\
            usage: pytest [-h] [--run_id str] --jbuild.id int --jbuild.url str
                        --jbuild.docker_image str

            optional arguments:
            -h, --help            show this help message and exit
            --run_id str

            JBuildRelease ['jbuild']:
            JBuildRelease(id:int, url:str, docker_image:str)

            --jbuild.id int
            --jbuild.url str
            --jbuild.docker_image str
            """
        ),
    )


@pytest.mark.xfail(reason="TODO: Issue #49")
def test_conflict_with_regular_argparse_arg():
    # This _should_ work, but it doesn't, adding a new issue for this:
    # the problem: SimpleParsing doesn't yet detect
    # conflicts between arguments added the usual way with `add_argument` and those
    # added through `add_arguments`.
    parser = simple_parsing.ArgumentParser()
    parser.add_argument("--id", type=str)
    parser.add_arguments(JBuildRelease, dest="jbuild")
    args = parser.parse_args(
        "--id 123 --jbuild.id 456 --jbuild.url bob --jbuild.docker_image foo".split()
    )
    assert args.id == 123
    assert args.jbuild.id == 456


@pytest.mark.xfail(reason="TODO: Issue #49")
def test_workaround():
    pass

    # This also doesn't work, since the prefix is only added to the 'offending'
    # argument, rather than to all the args in that group.
    @dataclass
    class Main:
        id: int
        jbuild: JBuildRelease

    parser = simple_parsing.ArgumentParser()
    parser.add_arguments(Main, "main")
    args = parser.parse_args(
        "--id 123 --jbuild.id 456 --jbuild.url bob --jbuild.docker_image foo".split()
    )
    args = args.main
    assert args.id == 123
    assert args.jbuild.id == 456
