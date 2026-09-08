import math

import pytest

from frame_stringer.built_up_strength import (
    assess_builtup_strength,
    bending_yield_capacity,
)
from frame_stringer.loads import SectionLoad
from frame_stringer.material import IsotropicMaterial
from frame_stringer.sections import i_section
from frame_stringer.strength import von_mises_stress


@pytest.fixture
def section():
    return i_section(
        flange_width=0.05, overall_height=0.10, flange_thickness=0.005, web_thickness=0.004
    )


@pytest.fixture
def material():
    return IsotropicMaterial(
        name="Illustrative Al-like",
        elastic_modulus=70e9,
        poisson_ratio=0.33,
        density=2700.0,
        yield_strength=300e6,
    )


def test_pure_axial_von_mises(section, material):
    N = 0.3 * material.yield_strength * section.area
    load = SectionLoad(axial_force=N, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_builtup_strength(load, section, material)
    top_point = next(p for p in result.points if p.label == "top_extreme")
    assert top_point.sigma_vm == pytest.approx(abs(top_point.sigma_x))


def test_pure_bending_governed_by_extreme_fiber(section, material):
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=6000.0)
    result = assess_builtup_strength(load, section, material)
    assert result.governing_location in ("top_extreme", "bottom_extreme")


def test_pure_shear_governed_in_web_region(section, material):
    load = SectionLoad(axial_force=0.0, shear_force_y=60e3, bending_moment_z=0.0)
    result = assess_builtup_strength(load, section, material)
    assert "boundary" in result.governing_location or result.governing_location == "neutral_axis"


def test_exact_yield_boundary_passes(section, material):
    N = material.yield_strength * section.area
    load = SectionLoad(axial_force=N, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_builtup_strength(load, section, material)
    assert result.passes is True
    assert result.min_margin == pytest.approx(0.0, abs=1e-9)


def test_combined_load_hand_calc_at_neutral_axis(section, material):
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    result = assess_builtup_strength(load, section, material)
    na_point = next(p for p in result.points if p.label == "neutral_axis")
    expected_sigma_x = -80e3 / section.area  # M contributes 0 at y_bar for symmetric I
    expected_sigma_vm = von_mises_stress(na_point.sigma_x, na_point.tau_xy)
    assert na_point.sigma_x == pytest.approx(expected_sigma_x)
    assert na_point.sigma_vm == pytest.approx(expected_sigma_vm)


def test_governing_point_is_computed_not_assumed(section, material):
    load = SectionLoad(axial_force=-80e3, shear_force_y=60e3, bending_moment_z=4e3)
    result = assess_builtup_strength(load, section, material)
    candidates = {p.label: p.sigma_vm for p in result.points}
    expected_label = max(candidates, key=lambda k: candidates[k])
    assert result.governing_location == expected_label
    assert result.governing_sigma_vm == pytest.approx(candidates[expected_label])


def test_deterministic_tie_break_for_zero_load(section, material):
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0)
    result1 = assess_builtup_strength(load, section, material)
    result2 = assess_builtup_strength(load, section, material)
    assert result1.governing_location == result2.governing_location


def test_strength_result_invariant_to_component_order(section, material):
    from frame_stringer.built_up_geometry import BuiltUpSection

    reordered = BuiltUpSection(tuple(reversed(section.components)))
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    result_a = assess_builtup_strength(load, section, material)
    result_b = assess_builtup_strength(load, reordered, material)
    assert result_a.governing_location == result_b.governing_location
    assert result_a.governing_sigma_vm == pytest.approx(result_b.governing_sigma_vm)
    assert result_a.min_margin == pytest.approx(result_b.min_margin)


def test_bending_yield_capacity_symmetric_section(section, material):
    result = bending_yield_capacity(section, material)
    assert result.moment_yield_top == pytest.approx(result.moment_yield_bottom)
    assert result.moment_yield == pytest.approx(result.moment_yield_top)


def test_bending_yield_capacity_asymmetric_section(material):
    from frame_stringer.sections import hat_section

    section = hat_section(crown_width=0.05, overall_height=0.06, wall_thickness=0.002, flange_width=0.02)
    result = bending_yield_capacity(section, material)
    assert result.moment_yield_top != pytest.approx(result.moment_yield_bottom)
    assert result.moment_yield == pytest.approx(
        min(result.moment_yield_top, result.moment_yield_bottom)
    )
