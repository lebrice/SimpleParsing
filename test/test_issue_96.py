from dataclasses import dataclass

from simple_parsing import ArgumentParser

from .testutils import TestSetup, exits_and_writes_to_stderr


def test_repro_issue_96():
    @dataclass
    class Options(TestSetup):
        list_items: list[str]  # SOMETHING

    parser = ArgumentParser(add_option_string_dash_variants=True)
    parser.add_arguments(Options, dest="options")

    with exits_and_writes_to_stderr(match="the following arguments are required: --list_items"):
        assert Options.setup("")

    assert Options.setup("--list_items foo") == Options(list_items=["foo"])
    assert Options.setup("--list_items") == Options(list_items=[])
