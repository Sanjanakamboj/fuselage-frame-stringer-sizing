import math

import pytest

from frame_stringer.geometry import RectangularSection
from frame_stringer.loads import SectionLoad
from frame_stringer.material import IsotropicMaterial
from frame_stringer.strength import (
    assess_section_strength,
    axial_yield_load,
    bending_yield_moment,
    shear_yield_load,
    shear_yield_stress,
    von_mises_stress,
    yield_margin,
)


@pytest.fixture
def section():
    return RectangularSection(width=0.04, height=0.08)


@pytest.fixture
def material():
    return IsotropicMaterial(
        name="Illustrative Al-like",
        elastic_modulus=70e9,
        poisson_ratio=0.33,
        density=2700.0,
        yield_strength=300e6,
    )


# ---- von Mises basics ----


def test_von_mises_pure_axial_reduces_to_abs_sigma():
    assert von_mises_stress(150e6, 0.0) == pytest.approx(150e6)
    assert von_mises_stress(-150e6, 0.0) == pytest.approx(150e6)


def test_von_mises_pure_shear_gives_sqrt3_times_tau():
    tau = 50e6
    assert von_mises_stress(0.0, tau) == pytest.approx(math.sqrt(3.0) * tau)


def test_von_mises_combined_hand_calculation():
    sigma = 100e6
    tau = 40e6
    expected = math.sqrt(sigma**2 + 3.0 * tau**2)
    assert von_mises_stress(sigma, tau) == pytest.approx(expected)


# ---- margin ----


def test_yield_margin_exact_boundary_is_zero():
    assert yield_margin(300e6, 300e6) == pytest.approx(0.0)


def test_yield_margin_below_yield_is_positive():
    assert yield_margin(150e6, 300e6) == pytest.approx(1.0)


def test_yield_margin_above_yield_is_negative():
    assert yield_margin(400e6, 300e6) < 0


def test_yield_margin_zero_stress_is_none():
    assert yield_margin(0.0, 300e6) is None


# ---- section strength assessment ----


def test_exact_yield_boundary_passes(section, material):
    # Choose N such that sigma_x at top exactly equals yield_strength.
    N = material.yield_strength * section.area
    load = SectionLoad(axial_force=N, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_section_strength(load, section, material)
    assert result.passes is True
    assert result.min_margin == pytest.approx(0.0, abs=1e-9)


def test_below_yield_passes(section, material):
    N = 0.5 * material.yield_strength * section.area
    load = SectionLoad(axial_force=N, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_section_strength(load, section, material)
    assert result.passes is True
    assert result.min_margin > 0


def test_above_yield_fails(section, material):
    N = 2.0 * material.yield_strength * section.area
    load = SectionLoad(axial_force=N, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_section_strength(load, section, material)
    assert result.passes is False


def test_governing_point_is_deterministic_for_zero_load(section, material):
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_section_strength(load, section, material)
    # all three points tie at zero stress -> first in fixed order (top) wins
    assert result.governing_location == "top"


def test_pure_bending_governed_by_extreme_fiber(section, material):
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=4e3)
    result = assess_section_strength(load, section, material)
    assert result.governing_location in ("top", "bottom")
    assert result.governing_sigma_vm == pytest.approx(
        max(abs(result.top.sigma_x), abs(result.bottom.sigma_x))
    )


def test_pure_shear_governed_by_neutral_axis(section, material):
    load = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=0.0)
    result = assess_section_strength(load, section, material)
    assert result.governing_location == "neutral_axis"


def test_mixed_load_case_computes_all_points_rather_than_assuming(section, material):
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    result = assess_section_strength(load, section, material)
    # governing point must be the actual max of the three computed sigma_vm
    candidates = {
        "top": result.top.sigma_vm,
        "neutral_axis": result.neutral_axis.sigma_vm,
        "bottom": result.bottom.sigma_vm,
    }
    expected_governing = max(candidates, key=lambda k: candidates[k])
    assert result.governing_location == expected_governing
    assert result.governing_sigma_vm == pytest.approx(candidates[expected_governing])


# ---- closed-form reference capacities ----


def test_axial_yield_load_gives_zero_margin(section, material):
    N_y = axial_yield_load(section, material)
    load = SectionLoad(axial_force=N_y, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_section_strength(load, section, material)
    assert result.min_margin == pytest.approx(0.0, abs=1e-9)


def test_bending_yield_moment_gives_zero_margin(section, material):
    M_y = bending_yield_moment(section, material)
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=M_y)
    result = assess_section_strength(load, section, material)
    assert result.min_margin == pytest.approx(0.0, abs=1e-9)


def test_shear_yield_load_gives_zero_margin(section, material):
    V_yield = shear_yield_load(section, material)
    load = SectionLoad(axial_force=0.0, shear_force_y=V_yield, bending_moment_z=0.0)
    result = assess_section_strength(load, section, material)
    assert result.min_margin == pytest.approx(0.0, abs=1e-9)


def test_reference_capacities_scale_linearly_with_yield_strength(section, material):
    material2 = IsotropicMaterial(
        name=material.name,
        elastic_modulus=material.elastic_modulus,
        poisson_ratio=material.poisson_ratio,
        density=material.density,
        yield_strength=2.0 * material.yield_strength,
    )
    assert axial_yield_load(section, material2) == pytest.approx(
        2.0 * axial_yield_load(section, material)
    )
    assert bending_yield_moment(section, material2) == pytest.approx(
        2.0 * bending_yield_moment(section, material)
    )
    assert shear_yield_load(section, material2) == pytest.approx(
        2.0 * shear_yield_load(section, material)
    )
    assert shear_yield_stress(material2) == pytest.approx(
        2.0 * shear_yield_stress(material)
    )
