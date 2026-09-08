import math

import pytest

from frame_stringer.load_cases import CANONICAL_LOAD_CASES, FrameStringerLoadCase


def test_valid_load_case():
    lc = FrameStringerLoadCase(name="maneuver bending", axial_force=-40e3, shear_force_y=25e3, bending_moment_z=5e3)
    assert lc.name == "maneuver bending"
    assert lc.load_factor == pytest.approx(1.0)


def test_invalid_name():
    with pytest.raises(ValueError):
        FrameStringerLoadCase(name="", axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0)
    with pytest.raises(ValueError):
        FrameStringerLoadCase(name="   ", axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("axial_force", math.nan),
        ("shear_force_y", math.inf),
        ("bending_moment_z", -math.inf),
        ("load_factor", math.nan),
    ],
)
def test_non_finite_loads_rejected(field, bad_value):
    kwargs = dict(name="x", axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0, load_factor=1.0)
    kwargs[field] = bad_value
    with pytest.raises(ValueError):
        FrameStringerLoadCase(**kwargs)


def test_invalid_load_factor():
    with pytest.raises(ValueError):
        FrameStringerLoadCase(name="x", axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0, load_factor=0.0)
    with pytest.raises(ValueError):
        FrameStringerLoadCase(name="x", axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0, load_factor=-1.0)


def test_design_load_scaling():
    lc = FrameStringerLoadCase(
        name="x", axial_force=-40e3, shear_force_y=10e3, bending_moment_z=2e3, load_factor=1.5
    )
    load = lc.design_load
    assert load.axial_force == pytest.approx(-60e3)
    assert load.shear_force_y == pytest.approx(15e3)
    assert load.bending_moment_z == pytest.approx(3e3)


def test_signed_loads_preserved():
    lc = FrameStringerLoadCase(name="x", axial_force=-100e3, shear_force_y=-20e3, bending_moment_z=-4e3)
    load = lc.design_load
    assert load.axial_force < 0
    assert load.shear_force_y < 0
    assert load.bending_moment_z < 0


def test_design_load_default_factor_is_identity():
    lc = FrameStringerLoadCase(name="x", axial_force=-40e3, shear_force_y=10e3, bending_moment_z=2e3)
    load = lc.design_load
    assert load.axial_force == pytest.approx(-40e3)
    assert load.shear_force_y == pytest.approx(10e3)
    assert load.bending_moment_z == pytest.approx(2e3)


def test_canonical_load_cases_are_distinct_and_valid():
    names = [lc.name for lc in CANONICAL_LOAD_CASES]
    assert len(names) == len(set(names))
    assert len(CANONICAL_LOAD_CASES) == 4
    for lc in CANONICAL_LOAD_CASES:
        assert lc.load_factor == pytest.approx(1.0)
