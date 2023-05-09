from pathlib import Path

from ..nesting.example_use_cases import HyperParameters


def test_save_yaml(tmpdir: Path):
    hparams = HyperParameters.setup("")
    tmp_path = Path(tmpdir / "temp.yml")
    hparams.save_yaml(tmp_path)

    _hparams = HyperParameters.load_yaml(tmp_path)
    assert hparams == _hparams


def test_save_json(tmpdir: Path):
    hparams = HyperParameters.setup("")
    tmp_path = Path(tmpdir / "temp.json")
    hparams.save_yaml(tmp_path)
    _hparams = HyperParameters.load_yaml(tmp_path)
    assert hparams == _hparams


def test_save_yml(tmpdir: Path):
    hparams = HyperParameters.setup("")
    tmp_path = Path(tmpdir / "temp.yml")
    hparams.save(tmp_path)

    _hparams = HyperParameters.load(tmp_path)
    assert hparams == _hparams


def test_save_pickle(tmpdir: Path):
    hparams = HyperParameters.setup("")
    tmp_path = Path(tmpdir / "temp.pkl")
    hparams.save(tmp_path)

    _hparams = HyperParameters.load(tmp_path)
    assert hparams == _hparams


def test_save_numpy(tmpdir: Path):
    hparams = HyperParameters.setup("")
    tmp_path = Path(tmpdir / "temp.npy")
    hparams.save(tmp_path)

    _hparams = HyperParameters.load(tmp_path)
    assert hparams == _hparams


def test_save_torch(tmpdir: Path):
    hparams = HyperParameters.setup("")
    tmp_path = Path(tmpdir / "temp.pth")
    hparams.save(tmp_path)

    _hparams = HyperParameters.load(tmp_path)
    assert hparams == _hparams
