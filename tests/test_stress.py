import pytest

from frame_stringer.geometry import RectangularSection
from frame_stringer.loads import SectionLoad
from frame_stringer.stress import (
    axial_stress,
    bending_stress,
    evaluate_combined_stress,
    evaluate_normal_stress,
    max_shear_stress,
    normal_stress,
    shear_stress,
)


@pytest.fixture
def section():
    return RectangularSection(width=0.04, height=0.08)


# ---- axial / bending ----


def test_pure_tension_hand_calc(section):
    load = SectionLoad(axial_force=32000.0, shear_force_y=0.0, bending_moment_z=0.0)
    expected = 32000.0 / section.area
    assert axial_stress(load, section) == pytest.approx(expected)
    assert expected > 0


def test_pure_compression_hand_calc(section):
    load = SectionLoad(axial_force=-32000.0, shear_force_y=0.0, bending_moment_z=0.0)
    expected = -32000.0 / section.area
    assert axial_stress(load, section) == pytest.approx(expected)
    assert expected < 0


def test_zero_axial_force_gives_zero_stress(section):
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0)
    assert axial_stress(load, section) == 0.0


def test_pure_positive_bending_gives_opposite_signed_extremes(section):
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=1000.0)
    top = normal_stress(section.y_top, load, section)
    bottom = normal_stress(section.y_bottom, load, section)
    assert top < 0  # sigma = -M*y/I ; positive M, +y -> compression
    assert bottom > 0
    assert top == pytest.approx(-bottom)


def test_reversing_moment_reverses_extreme_stress_signs(section):
    load_pos = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=1000.0)
    load_neg = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=-1000.0)
    top_pos = normal_stress(section.y_top, load_pos, section)
    top_neg = normal_stress(section.y_top, load_neg, section)
    assert top_pos == pytest.approx(-top_neg)


def test_axial_bending_superposition_hand_calc(section):
    N = -80e3
    M = 4e3
    load = SectionLoad(axial_force=N, shear_force_y=0.0, bending_moment_z=M)
    y = section.y_top
    expected = N / section.area - M * y / section.moment_of_inertia_z
    assert normal_stress(y, load, section) == pytest.approx(expected)


def test_zero_load_case_gives_zero_everywhere(section):
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0)
    assert normal_stress(section.y_top, load, section) == 0.0
    assert normal_stress(section.y_bottom, load, section) == 0.0
    assert normal_stress(0.0, load, section) == 0.0


def test_stress_scales_linearly_with_axial_force(section):
    load1 = SectionLoad(axial_force=1000.0, shear_force_y=0.0, bending_moment_z=0.0)
    load2 = SectionLoad(axial_force=3000.0, shear_force_y=0.0, bending_moment_z=0.0)
    s1 = axial_stress(load1, section)
    s2 = axial_stress(load2, section)
    assert s2 == pytest.approx(3.0 * s1)


def test_stress_scales_linearly_with_moment(section):
    load1 = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=500.0)
    load2 = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=1500.0)
    s1 = bending_stress(section.y_top, load1, section)
    s2 = bending_stress(section.y_top, load2, section)
    assert s2 == pytest.approx(3.0 * s1)


def test_normal_stress_result_structure(section):
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    result = evaluate_normal_stress(load, section)
    assert result.top_stress == pytest.approx(
        normal_stress(section.y_top, load, section)
    )
    assert result.bottom_stress == pytest.approx(
        normal_stress(section.y_bottom, load, section)
    )
    assert result.max_tensile_stress == max(
        result.top_stress, result.bottom_stress, 0.0
    )
    assert result.max_compressive_stress == min(
        result.top_stress, result.bottom_stress, 0.0
    )


def test_normal_stress_result_all_compression_has_no_tension_location(section):
    # Large compression, small bending -> both fibers in compression.
    load = SectionLoad(axial_force=-1e6, shear_force_y=0.0, bending_moment_z=1.0)
    result = evaluate_normal_stress(load, section)
    assert result.max_tensile_stress == 0.0
    assert result.governing_tension_location == "none"


# ---- shear ----


def test_neutral_axis_shear_equals_1_5_V_over_A(section):
    load = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=0.0)
    expected = 1.5 * load.shear_force_y / section.area
    assert shear_stress(0.0, load, section) == pytest.approx(expected)
    assert max_shear_stress(load, section) == pytest.approx(expected)


def test_top_and_bottom_shear_is_zero(section):
    load = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=0.0)
    assert shear_stress(section.y_top, load, section) == pytest.approx(0.0, abs=1e-9)
    assert shear_stress(section.y_bottom, load, section) == pytest.approx(
        0.0, abs=1e-9
    )


def test_shear_distribution_symmetric(section):
    load = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=0.0)
    for y in (0.01, 0.02, 0.03):
        assert shear_stress(y, load, section) == pytest.approx(
            shear_stress(-y, load, section)
        )


def test_reversing_shear_reverses_tau_sign(section):
    load_pos = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=0.0)
    load_neg = SectionLoad(axial_force=0.0, shear_force_y=-25e3, bending_moment_z=0.0)
    assert shear_stress(0.0, load_pos, section) == pytest.approx(
        -shear_stress(0.0, load_neg, section)
    )


def test_shear_scales_linearly_with_V(section):
    load1 = SectionLoad(axial_force=0.0, shear_force_y=10e3, bending_moment_z=0.0)
    load2 = SectionLoad(axial_force=0.0, shear_force_y=30e3, bending_moment_z=0.0)
    tau1 = shear_stress(0.0, load1, section)
    tau2 = shear_stress(0.0, load2, section)
    assert tau2 == pytest.approx(3.0 * tau1)


def test_shear_rejects_point_outside_section(section):
    load = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=0.0)
    with pytest.raises(ValueError):
        shear_stress(section.y_top + 0.001, load, section)
    with pytest.raises(ValueError):
        shear_stress(section.y_bottom - 0.001, load, section)


def test_combined_stress_state_point(section):
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    state = evaluate_combined_stress(0.0, load, section)
    assert state.y == 0.0
    assert state.sigma_x == pytest.approx(normal_stress(0.0, load, section))
    assert state.tau_xy == pytest.approx(shear_stress(0.0, load, section))
