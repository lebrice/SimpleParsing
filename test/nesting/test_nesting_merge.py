from simple_parsing import ArgumentParser, ConflictResolution

from .example_use_cases import HyperParameters


def test_parser_preprocessing_steps():
    parser = ArgumentParser(conflict_resolution=ConflictResolution.ALWAYS_MERGE)
    parser.add_arguments(HyperParameters, "hparams")

    wrappers = parser._wrappers
    # Fix the potential conflicts between dataclass fields with the same names.
    merged_wrappers = parser._conflict_resolver.resolve_and_flatten(wrappers)
    from simple_parsing.parsing import _unflatten_wrappers

    assert merged_wrappers[1].parent is merged_wrappers[0]
    assert merged_wrappers[1] in merged_wrappers[0]._children

    assert _unflatten_wrappers(merged_wrappers) == [merged_wrappers[0]]

    wrappers = merged_wrappers

    assert len(wrappers) == 2
    hparams_dc_wrapper = wrappers[0]
    assert hparams_dc_wrapper.destinations == ["hparams"]
    merged_dcs_wrapper = wrappers[1]
    assert merged_dcs_wrapper.destinations == [
        "hparams.gender",
        "hparams.age_group",
        "hparams.personality",
    ]
    num_layers_field_wrapper = next(f for f in merged_dcs_wrapper.fields if f.name == "num_layers")
    assert num_layers_field_wrapper.destinations == [
        "hparams.gender.num_layers",
        "hparams.age_group.num_layers",
        "hparams.personality.num_layers",
    ]
    assert num_layers_field_wrapper.option_strings == ["--num_layers"]
    assert num_layers_field_wrapper.arg_options == {
        "default": [1, 2, 1],
        "type": int,
        "required": False,
        "help": "number of dense layers",
        "nargs": "*",
        # NOTE: This `dest` is where all the merged values are stored.
        "dest": "hparams.gender.num_layers",
    }

    parser._wrappers = wrappers
    parser._preprocessing_done = True
    # Create one argument group per dataclass
    for wrapped_dataclass in wrappers:
        print(
            f"Parser {id(parser)} is Adding arguments for dataclass: {wrapped_dataclass.dataclass} "
            f"at destinations {wrapped_dataclass.destinations}"
        )
        wrapped_dataclass.add_arguments(parser=parser)
    assert "--num_layers" in parser._option_string_actions


def test_hparam_use_case(silent):
    hparams = HyperParameters.setup(
        "--num_layers 5 6 7", conflict_resolution_mode=ConflictResolution.ALWAYS_MERGE
    )
    assert isinstance(hparams, HyperParameters)
    # print(hparams.get_help_text())
    assert hparams.gender.num_layers == 5
    assert hparams.age_group.num_layers == 6
    assert hparams.personality.num_layers == 7

    assert hparams.gender.num_units == 32
    assert hparams.age_group.num_units == 64
    assert hparams.personality.num_units == 8

    assert hparams.gender.use_likes is True
    assert hparams.age_group.use_likes is True
    assert hparams.personality.use_likes is False
