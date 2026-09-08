import math

import pytest

from frame_stringer.beam_column import (
    amplification_factor,
    amplified_moment,
    assess_beam_column,
    eccentricity,
    section_stability_summary,
)
from frame_stringer.built_up_strength import assess_builtup_strength
from frame_stringer.column_buckling import MemberGeometry
from frame_stringer.local_buckling import assess_section_local_buckling, i_section_plate_elements
from frame_stringer.loads import SectionLoad
from frame_stringer.material import IsotropicMaterial
from frame_stringer.sections import i_section


@pytest.fixture
def material():
    return IsotropicMaterial(
        name="Illustrative Al-like",
        elastic_modulus=70e9,
        poisson_ratio=0.33,
        density=2700.0,
        yield_strength=300e6,
    )


@pytest.fixture
def section():
    return i_section(flange_width=0.06, overall_height=0.10, flange_thickness=0.0095, web_thickness=0.006)


@pytest.fixture
def plate_model():
    return i_section_plate_elements(
        flange_width=0.06, overall_height=0.10, flange_thickness=0.0095, web_thickness=0.006, panel_length=0.30
    )


# ---- amplification (V-AC) ----


def test_amplification_zero_compression_gives_one():
    assert amplification_factor(0.0, 100e3) == pytest.approx(1.0)


def test_amplification_hand_calc_half_pcr():
    assert amplification_factor(50e3, 100e3) == pytest.approx(2.0)


def test_amplification_monotonic_increase():
    P_cr = 100e3
    values = [amplification_factor(p, P_cr) for p in (0, 20e3, 40e3, 60e3, 80e3, 95e3)]
    assert values == sorted(values)


def test_amplification_grows_strongly_near_pcr():
    P_cr = 100e3
    B_far = amplification_factor(50e3, P_cr)
    B_near = amplification_factor(99e3, P_cr)
    assert B_near > 10 * B_far


def test_amplification_at_or_above_pcr_is_none():
    assert amplification_factor(100e3, 100e3) is None
    assert amplification_factor(150e3, 100e3) is None


def test_amplified_moment_zero_applied_moment():
    assert amplified_moment(0.0, 50e3, 100e3) == pytest.approx(0.0)


def test_amplified_moment_linear_scaling_at_fixed_ratio():
    P_comp, P_cr = 50e3, 100e3
    m1 = amplified_moment(1000.0, P_comp, P_cr)
    m2 = amplified_moment(3000.0, P_comp, P_cr)
    assert m2 == pytest.approx(3.0 * m1)


def test_amplified_moment_reversal_reverses_sign_only():
    P_comp, P_cr = 50e3, 100e3
    m_pos = amplified_moment(2000.0, P_comp, P_cr)
    m_neg = amplified_moment(-2000.0, P_comp, P_cr)
    assert m_neg == pytest.approx(-m_pos)


def test_eccentricity_zero_compression_is_none():
    assert eccentricity(applied_moment=1000.0, compressive_load_demand=0.0) is None


def test_eccentricity_hand_calc():
    assert eccentricity(applied_moment=4000.0, compressive_load_demand=80e3) == pytest.approx(4000.0 / 80e3)


# ---- amplified stress / assess_beam_column (AD-AI) ----


def test_zero_compression_reproduces_ordinary_strength_exactly(material, section):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=4e3)
    bc = assess_beam_column(member, section, material, load)
    ordinary = assess_builtup_strength(load, section, material)
    assert bc.amplified_moment == pytest.approx(load.bending_moment_z)
    assert bc.amplified_yield_result.min_margin == pytest.approx(ordinary.min_margin)
    assert bc.amplified_yield_result.governing_location == ordinary.governing_location


def test_compressive_load_increases_bending_magnitude(material, section):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    bc = assess_beam_column(member, section, material, load)
    assert abs(bc.amplified_moment) > abs(load.bending_moment_z)


def test_amplified_top_bottom_stress_hand_calc(material, section):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    bc = assess_beam_column(member, section, material, load)

    from frame_stringer.built_up_stress import normal_stress

    amplified_load = SectionLoad(
        axial_force=load.axial_force, shear_force_y=load.shear_force_y, bending_moment_z=bc.amplified_moment
    )
    expected_top = normal_stress(section.y_top, amplified_load, section)
    top_point = next(p for p in bc.amplified_yield_result.points if p.label == "top_extreme")
    assert top_point.sigma_x == pytest.approx(expected_top)


def test_reversing_moment_swaps_top_bottom(material, section):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load_pos = SectionLoad(axial_force=-80e3, shear_force_y=0.0, bending_moment_z=4e3)
    load_neg = SectionLoad(axial_force=-80e3, shear_force_y=0.0, bending_moment_z=-4e3)
    bc_pos = assess_beam_column(member, section, material, load_pos)
    bc_neg = assess_beam_column(member, section, material, load_neg)

    top_pos = next(p for p in bc_pos.amplified_yield_result.points if p.label == "top_extreme").sigma_x
    top_neg = next(p for p in bc_neg.amplified_yield_result.points if p.label == "top_extreme").sigma_x
    # Reversing M reverses the bending contribution -> different (not equal) top stress.
    assert top_pos != pytest.approx(top_neg)
    # But P/Pcr, B are unchanged since axial load and Euler load are unchanged.
    assert bc_pos.p_over_pcr == pytest.approx(bc_neg.p_over_pcr)
    assert bc_pos.amplification_factor == pytest.approx(bc_neg.amplification_factor)


def test_shear_unchanged_by_amplification(material, section):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    bc = assess_beam_column(member, section, material, load)
    top_point = next(p for p in bc.amplified_yield_result.points if p.label == "neutral_axis")
    ordinary_top_point = next(
        p for p in bc.unamplified_yield_result.points if p.label == "neutral_axis"
    )
    # Shear at the neutral axis is unaffected by moment amplification (M
    # contributes zero shear directly; V_y is passed through unchanged).
    assert top_point.tau_xy == pytest.approx(ordinary_top_point.tau_xy)


def test_amplified_yield_may_fail_while_unamplified_passes(material):
    # A slender, short-panel member near its Euler load, with enough bending
    # that amplification pushes the yield screen over the edge while the
    # unamplified (first-order, no-amplification) screen still passes.
    section = i_section(flange_width=0.06, overall_height=0.10, flange_thickness=0.006, web_thickness=0.004)
    member = MemberGeometry(length=3.0, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=0.0, bending_moment_z=4e3)
    bc = assess_beam_column(member, section, material, load)
    assert bc.unamplified_yield_result.passes is True
    assert bc.amplified_yield_result.passes is False


# ---- global assessment (AJ-AP) ----


def test_safe_construction_passes(material, section):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    bc = assess_beam_column(member, section, material, load)
    assert bc.overall_pass is True


def test_euler_governed_failure(material, section):
    member = MemberGeometry(length=6.0, effective_length_factor=2.0)  # very slender
    load = SectionLoad(axial_force=-50e3, shear_force_y=0.0, bending_moment_z=0.0)
    bc = assess_beam_column(member, section, material, load)
    assert bc.overall_pass is False
    assert bc.euler_passes is False


def test_amplified_yield_governed_failure(material):
    section = i_section(flange_width=0.06, overall_height=0.10, flange_thickness=0.006, web_thickness=0.004)
    member = MemberGeometry(length=3.0, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=0.0, bending_moment_z=4e3)
    bc = assess_beam_column(member, section, material, load)
    assert bc.euler_passes is True
    assert bc.amplified_yield_passes is False
    assert bc.overall_pass is False


def test_deterministic_governing_mode_selection(material, section):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    bc1 = assess_beam_column(member, section, material, load)
    bc2 = assess_beam_column(member, section, material, load)
    assert bc1.governing_mode == bc2.governing_mode
    assert bc1.governing_margin == pytest.approx(bc2.governing_margin)


def test_component_order_invariance(material, section):
    from frame_stringer.built_up_geometry import BuiltUpSection

    reordered = BuiltUpSection(tuple(reversed(section.components)))
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    bc_a = assess_beam_column(member, section, material, load)
    bc_b = assess_beam_column(member, reordered, material, load)
    assert bc_a.governing_mode == bc_b.governing_mode
    assert bc_a.governing_margin == pytest.approx(bc_b.governing_margin)


def test_repeated_deterministic_result(material, section):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    bc1 = assess_beam_column(member, section, material, load)
    bc2 = assess_beam_column(member, section, material, load)
    assert bc1.overall_pass == bc2.overall_pass
    assert bc1.amplification_factor == pytest.approx(bc2.amplification_factor)


def test_overall_status_requires_euler_and_amplified_yield(material, section):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    bc = assess_beam_column(member, section, material, load)
    assert bc.overall_pass == (bc.euler_passes and bc.amplified_yield_passes)


# ---- section stability summary ----


def test_section_stability_summary_combines_without_blending(material, plate_model):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    bc = assess_beam_column(member, plate_model.section, material, load)
    lb = assess_section_local_buckling(plate_model, load, material)
    summary = section_stability_summary(bc.unamplified_yield_result, lb, bc)

    assert summary.yield_pass == bc.unamplified_yield_result.passes
    assert summary.local_buckling_pass == lb.passes
    assert summary.global_euler_pass == bc.euler_passes
    assert summary.amplified_yield_pass == bc.amplified_yield_passes
    assert summary.overall_preliminary_pass == (
        summary.yield_pass and summary.local_buckling_pass and summary.global_euler_pass and summary.amplified_yield_pass
    )
