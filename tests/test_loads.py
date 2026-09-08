import math

import pytest

from frame_stringer.loads import SectionLoad


def test_valid_construction_all_zero():
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0)
    assert load.axial_force == 0.0
    assert load.shear_force_y == 0.0
    assert load.bending_moment_z == 0.0


def test_positive_and_negative_values_allowed():
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=-4e3)
    assert load.axial_force == -80e3
    assert load.shear_force_y == 25e3
    assert load.bending_moment_z == -4e3


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("axial_force", math.nan),
        ("axial_force", math.inf),
        ("shear_force_y", math.nan),
        ("shear_force_y", -math.inf),
        ("bending_moment_z", math.nan),
        ("bending_moment_z", math.inf),
    ],
)
def test_non_finite_rejected(field, bad_value):
    kwargs = dict(axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0)
    kwargs[field] = bad_value
    with pytest.raises(ValueError):
        SectionLoad(**kwargs)
