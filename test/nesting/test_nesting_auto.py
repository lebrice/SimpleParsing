from __future__ import annotations

from simple_parsing import ConflictResolution

from .example_use_cases import HyperParameters


def test_real_use_case(silent):
    hparams = HyperParameters.setup(
        "--age_group.num_layers 5 " "--age_group.num_units 65 ",
        conflict_resolution_mode=ConflictResolution.AUTO,
    )
    assert isinstance(hparams, HyperParameters)
    # print(hparams.get_help_text())
    assert hparams.gender.num_layers == 1
    assert hparams.gender.num_units == 32
    assert hparams.age_group.num_layers == 5
    assert hparams.age_group.num_units == 65
    assert hparams.age_group.use_likes is True
