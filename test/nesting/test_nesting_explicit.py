from simple_parsing import ConflictResolution

from .example_use_cases import HyperParameters, TaskHyperParameters


def test_real_use_case(silent):
    hparams = HyperParameters.setup(
        "--hyper_parameters.age_group.num_layers 5",
        conflict_resolution_mode=ConflictResolution.EXPLICIT,
    )
    assert isinstance(hparams, HyperParameters)
    # print(hparams.get_help_text())
    assert hparams.age_group.num_layers == 5
    assert hparams.gender.num_layers == 1
    assert hparams.gender.num_units == 32
    assert isinstance(hparams.age_group, TaskHyperParameters)
    assert hparams.age_group.use_likes is True
