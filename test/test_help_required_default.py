from dataclasses import dataclass

from simple_parsing import ArgumentParser


@dataclass
class Options:
    list_items: list[str]  # SOMETHING


def test_required_field_without_default_does_not_show_default_none(capsys):
    parser = ArgumentParser(add_option_string_dash_variants=True)
    parser.add_arguments(Options, dest="options")

    parser.print_help()
    help_text = capsys.readouterr().out

    assert "SOMETHING" in help_text
    assert "(default: None)" not in help_text
