import pytest
from examples.ugly.ugly_example_after import Parameters
from simple_parsing import utils

class DatasetParams:
    pass

class OptimizerParams:
    pass

class GanParams:
    pass

class CameraParams:
    pass

class RenderingParams:
    def __init__(self, render_type):
        self.render_type = render_type
        self.render_img_nc = 0

class OtherParams:
    out_dir = "output"

@pytest.fixture
def params_img():
    return Parameters(
        rendering=RenderingParams(render_type="img")
    )

@pytest.fixture
def params_depth():
    return Parameters(
        rendering=RenderingParams(render_type="depth")
    )

@pytest.fixture
def params_unknown():
    return Parameters(
        rendering=RenderingParams(render_type="unknown")
    )

def test_post_init_img(params_img):
    params_img.__post_init__()
    assert params_img.rendering.render_img_nc == 3
    assert utils.branch_coverage["ugly_example_post_init_1"] == True

def test_post_init_depth(params_depth):
    params_depth.__post_init__()
    assert params_depth.rendering.render_img_nc == 1
    assert utils.branch_coverage["ugly_example_post_init_2"] == True

def test_post_init_unknown(params_unknown):
    with pytest.raises(ValueError, match="Unknown rendering type"):
        params_unknown.__post_init__()
    assert utils.branch_coverage["ugly_example_post_init_3"] == True