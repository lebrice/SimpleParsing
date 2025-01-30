"""Adds typed dataclasses for the "config" yaml files."""
import functools
from dataclasses import dataclass, field
from test.testutils import pytest, raises
from typing import Any, Optional

from simple_parsing import mutable_field
from simple_parsing.helpers import FlattenedAccess


@dataclass()
class LabelOffset:
    """Offset of the label within a dataset."""

    mnist: Optional[int] = None
    cifar10: Optional[int] = None
    ciraf100: Optional[int] = None


@dataclass
class DatasetConfig:
    """Dataset Config."""

    data_root: str = "./data"
    batch_size: int = 10
    num_workers: int = 16
    sleep_batch_size: int = 50
    sleep_num_workers: int = 4
    eval_batch_size: int = 256
    eval_num_workers: int = 4

    label_offset: LabelOffset = field(default_factory=functools.partial(LabelOffset, mnist=0))


@dataclass
class ModelConfig:
    """Model configuration."""

    x_c: int = 1
    x_h: int = 28
    x_w: int = 28
    y_c: int = 10

    device: str = "cpu"

    model_name: str = "ndpm_model"
    g: str = "mlp_sharing_vae"
    d: Optional[str] = None
    disable_d: bool = True
    vae_nf_base: int = 64
    vae_nf_ext: int = 16
    z_dim: int = 16
    z_samples: int = 1

    precursor_conditioned_decoder: bool = False
    recon_loss: str = "bernoulli"
    classifier_chill: float = 1


@dataclass
class DPMoEConfig:
    """Configuration of the Dirichlet Process Mixture of Experts Model."""

    log_alpha: int = 410
    stm_capacity: int = 1000
    sleep_val_size: int = 0
    stm_erase_period: int = 0

    sleep_step_g: int = 12000
    sleep_step_d: int = 700
    sleep_summary_step: int = 500
    update_min_usage: float = 0.1


@dataclass(init=False)
class ObjectConfig:
    """Configuration for a generic Object with a type and some kwargs."""

    type: str = ""
    options: dict[str, Any] = field(default_factory=dict)

    def __init__(self, type: str, **kwargs):
        self.type = type
        self.options = kwargs


@dataclass
class TrainConfig:
    """Training Configuration."""

    weight_decay: float = 0.00001
    implicit_lr_decay: bool = False
    optimizer_g: ObjectConfig = field(
        default_factory=functools.partial(ObjectConfig, type="Adam", lr=0.0003)
    )
    lr_scheduler_g: ObjectConfig = field(
        default_factory=functools.partial(
            ObjectConfig, type="MultiStepLR", milestones=[1], gamma=0.003
        )
    )
    clip_grad: ObjectConfig = field(
        default_factory=functools.partial(ObjectConfig, type="value", clip_value=0.5)
    )


@dataclass
class EvalConfig:
    """Eval configuration."""

    eval_d: bool = False
    eval_g: bool = True


@dataclass
class SummaryConfig:
    """Settings related to the summaries generated during training."""

    summary_step: int = 250
    eval_step: int = 250
    ckpt_step: int = 1000000000
    summarize_samples: bool = True
    sample_grid: tuple[int, int] = (10, 10)


@dataclass
class Config(FlattenedAccess):
    """Overall Configuration."""

    dataset: DatasetConfig = mutable_field(DatasetConfig)
    model: ModelConfig = mutable_field(ModelConfig)
    dpmmoe: DPMoEConfig = mutable_field(DPMoEConfig)
    train: TrainConfig = mutable_field(TrainConfig)
    eval: EvalConfig = mutable_field(EvalConfig)
    summary: SummaryConfig = mutable_field(SummaryConfig)
    et: float = 1.23


def test_getattr():
    c = Config()
    assert c.batch_size is c.dataset.batch_size
    assert c.dataset == getattr(c, "dataset")


def test_attr_similar_name():
    c = Config()
    c.et = 4.56
    assert c.et == 4.56


def test_setattr_existing():
    c = Config()
    assert c.summary.sample_grid == (10, 10)
    c.sample_grid = (12, 12)
    assert c.summary.sample_grid == (12, 12)


def test_setattr_new(caplog):
    c = Config()
    with pytest.warns(UserWarning):
        c.blablabob = "123"
        assert c.blablabob == "123"


def test_getattr_ambiguous():
    c = Config()
    with raises(AttributeError, match="Ambiguous"):
        _ = c.type


def test_setattr_ambiguous():
    c = Config()
    with raises(AttributeError, match="Ambiguous"):
        c.type = "value"


def test_getitem():
    c = Config()
    sample_grid = c["sample_grid"]
    assert sample_grid == c.summary.sample_grid


def test_getitem_nested():
    c = Config()
    sample_grid = c["summary.sample_grid"]
    assert sample_grid == c.summary.sample_grid


def test_setitem():
    c = Config()
    assert c.summary.sample_grid == (10, 10)
    c["sample_grid"] = (7, 7)
    assert c.summary.sample_grid == (7, 7)


def test_setitem_nested():
    c = Config()
    assert c.summary.sample_grid == (10, 10)
    c["summary.sample_grid"] = (7, 7)
    assert c.summary.sample_grid == (7, 7)


def test_setitem_new(caplog):
    c = Config()
    with pytest.warns(UserWarning):
        c["blablabob"] = "123"
        assert c["blablabob"] == "123"


def test_getitem_ambiguous():
    c = Config()
    with raises(AttributeError, match="Ambiguous"):
        _ = c["type"]


def test_setitem_ambiguous():
    c = Config()
    with raises(AttributeError, match="Ambiguous"):
        c["type"] = "value"
