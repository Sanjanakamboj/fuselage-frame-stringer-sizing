import math

import pytest

from frame_stringer.column_buckling import MemberGeometry
from frame_stringer.crippling import CripplingCorrelation
from frame_stringer.load_cases import CANONICAL_LOAD_CASES, FrameStringerLoadCase
from frame_stringer.material import IsotropicMaterial
from frame_stringer.sizing import (
    FAMILIES,
    HAT_CROWN_WIDTH,
    HAT_FLANGE_WIDTH,
    HAT_OVERALL_HEIGHT,
    I_FLANGE_WIDTH,
    I_OVERALL_HEIGHT,
    Z_FLANGE_WIDTH,
    Z_WEB_HEIGHT,
    assess_load_case,
    assess_multi_load_case,
    build_uniform_hat_plate_model,
    build_uniform_hat_section,
    build_uniform_i_plate_model,
    build_uniform_i_section,
    build_uniform_z_plate_model,
    build_uniform_z_section,
    size_section_family,
)


@pytest.fixture
def material():
    return IsotropicMaterial(
        name="Illustrative Al-like", elastic_modulus=70e9, poisson_ratio=0.33, density=2700.0, yield_strength=300e6
    )


@pytest.fixture
def member():
    return MemberGeometry(length=1.2, effective_length_factor=1.0)


@pytest.fixture
def correlation():
    return CripplingCorrelation(alpha=1.2, exponent=0.6, label="Illustrative", source_note="illustrative")


PANEL_LENGTH = 0.30


# ---- factories (G-K) ----


def test_uniform_i_section_thickness_propagated():
    t = 0.004
    section = build_uniform_i_section(t)
    web = next(c for c in section.components if c.label == "web")
    top = next(c for c in section.components if c.label == "top_flange")
    assert web.width == pytest.approx(t)
    assert top.height == pytest.approx(t)


def test_uniform_z_section_thickness_propagated():
    t = 0.004
    section = build_uniform_z_section(t)
    web = next(c for c in section.components if c.label == "web")
    top = next(c for c in section.components if c.label == "top_flange")
    assert web.width == pytest.approx(t)
    assert top.height == pytest.approx(t)


def test_uniform_hat_section_thickness_propagated():
    t = 0.004
    section = build_uniform_hat_section(t)
    web_pair = next(c for c in section.components if c.label == "web_pair")
    crown = next(c for c in section.components if c.label == "crown")
    assert web_pair.width == pytest.approx(2 * t)
    assert crown.height == pytest.approx(t)


def test_fixed_outer_geometry_preserved_while_t_changes():
    t1, t2 = 0.002, 0.005
    s1 = build_uniform_i_section(t1)
    s2 = build_uniform_i_section(t2)
    # Overall height (top_y - bottom_y) and flange width are held fixed
    # regardless of t; only the clear web height (which depends on flange
    # thickness = t by construction) changes with t.
    assert s1.y_top - s1.y_bottom == pytest.approx(I_OVERALL_HEIGHT)
    assert s2.y_top - s2.y_bottom == pytest.approx(I_OVERALL_HEIGHT)
    top1 = next(c for c in s1.components if c.label == "top_flange")
    top2 = next(c for c in s2.components if c.label == "top_flange")
    assert top1.width == pytest.approx(I_FLANGE_WIDTH)
    assert top2.width == pytest.approx(I_FLANGE_WIDTH)
    web1 = next(c for c in s1.components if c.label == "web")
    web2 = next(c for c in s2.components if c.label == "web")
    expected_h1 = I_OVERALL_HEIGHT - 2 * t1
    expected_h2 = I_OVERALL_HEIGHT - 2 * t2
    assert web1.height == pytest.approx(expected_h1)
    assert web2.height == pytest.approx(expected_h2)


def test_invalid_thickness_rejected():
    with pytest.raises(ValueError):
        build_uniform_i_section(0.0)
    with pytest.raises(ValueError):
        build_uniform_i_section(-0.001)
    with pytest.raises(ValueError):
        build_uniform_i_section(I_OVERALL_HEIGHT)  # way too thick: h_web <= 0


# ---- single-case assessment (L-U) ----


def test_assessment_returns_all_five_constraints(material, member, correlation):
    section = build_uniform_i_section(0.005)
    model = build_uniform_i_plate_model(0.005, PANEL_LENGTH)
    lc = FrameStringerLoadCase(name="x", axial_force=-40e3, shear_force_y=10e3, bending_moment_z=2e3)
    result = assess_load_case(section, model, material, member, lc, correlation)
    assert result.yield_result is not None
    assert result.local_buckling_result is not None
    assert result.euler_result is not None
    assert result.amplified_yield_result is not None
    assert result.crippling_result is not None


def test_safe_case_passes(material, member, correlation):
    section = build_uniform_i_section(0.006)
    model = build_uniform_i_plate_model(0.006, PANEL_LENGTH)
    lc = FrameStringerLoadCase(name="x", axial_force=-10e3, shear_force_y=2e3, bending_moment_z=200.0)
    result = assess_load_case(section, model, material, member, lc, correlation)
    assert result.overall_pass is True


def test_yield_failure_construction(material, member, correlation):
    section = build_uniform_i_section(0.006)
    model = build_uniform_i_plate_model(0.006, PANEL_LENGTH)
    lc = FrameStringerLoadCase(name="x", axial_force=0.0, shear_force_y=0.0, bending_moment_z=20_000.0)
    result = assess_load_case(section, model, material, member, lc, correlation)
    assert result.yield_result.passes is False
    assert result.overall_pass is False


def test_local_buckling_failure_construction(material, correlation):
    thin_member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    section = build_uniform_i_section(0.0009)
    model = build_uniform_i_plate_model(0.0009, PANEL_LENGTH)
    lc = FrameStringerLoadCase(name="x", axial_force=-30e3, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_load_case(section, model, material, thin_member, lc, correlation)
    assert result.local_buckling_result.passes is False
    assert result.overall_pass is False


def test_euler_failure_construction(material, correlation):
    slender_member = MemberGeometry(length=6.0, effective_length_factor=2.0)
    section = build_uniform_i_section(0.006)
    model = build_uniform_i_plate_model(0.006, PANEL_LENGTH)
    lc = FrameStringerLoadCase(name="x", axial_force=-50e3, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_load_case(section, model, material, slender_member, lc, correlation)
    assert result.euler_result.passes is False
    assert result.overall_pass is False


def test_amplified_yield_failure_construction(material, correlation):
    section = build_uniform_i_section(0.004)
    model = build_uniform_i_plate_model(0.004, PANEL_LENGTH)
    member = MemberGeometry(length=3.0, effective_length_factor=1.0)
    lc = FrameStringerLoadCase(name="x", axial_force=-80e3, shear_force_y=0.0, bending_moment_z=4e3)
    result = assess_load_case(section, model, material, member, lc, correlation)
    assert result.amplified_yield_result.passes is False
    assert result.overall_pass is False


def test_crippling_failure_construction(material, member):
    section = build_uniform_i_section(0.006)
    model = build_uniform_i_plate_model(0.006, PANEL_LENGTH)
    weak_corr = CripplingCorrelation(alpha=0.05, exponent=0.6, label="weak", source_note="illustrative-weak")
    lc = FrameStringerLoadCase(name="x", axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    result = assess_load_case(section, model, material, member, lc, weak_corr)
    assert result.crippling_result.passes is False
    assert result.overall_pass is False


def test_governing_constraint_is_minimum_margin(material, member, correlation):
    section = build_uniform_i_section(0.0038)
    model = build_uniform_i_plate_model(0.0038, PANEL_LENGTH)
    lc = FrameStringerLoadCase(name="x", axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    result = assess_load_case(section, model, material, member, lc, correlation)
    margins = {
        "yield": result.yield_result.min_margin,
        "local_buckling": result.local_buckling_result.min_margin,
        "euler": result.euler_result.margin,
        "amplified_yield": result.amplified_yield_result.min_margin if result.amplified_yield_result else None,
        "crippling": result.crippling_result.governing_margin,
    }
    applicable = {k: v for k, v in margins.items() if v is not None}
    expected = min(applicable, key=lambda k: applicable[k])
    assert result.governing_constraint == expected


def test_deterministic_exact_tie_break(material, member, correlation):
    section = build_uniform_i_section(0.006)
    model = build_uniform_i_plate_model(0.006, PANEL_LENGTH)
    lc = FrameStringerLoadCase(name="x", axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0)
    r1 = assess_load_case(section, model, material, member, lc, correlation)
    r2 = assess_load_case(section, model, material, member, lc, correlation)
    assert r1.governing_constraint == r2.governing_constraint


def test_repeated_result_deterministic(material, member, correlation):
    section = build_uniform_i_section(0.004)
    model = build_uniform_i_plate_model(0.004, PANEL_LENGTH)
    lc = FrameStringerLoadCase(name="x", axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    r1 = assess_load_case(section, model, material, member, lc, correlation)
    r2 = assess_load_case(section, model, material, member, lc, correlation)
    assert r1.governing_margin == pytest.approx(r2.governing_margin)


# ---- multi-case (V-AA) ----


def test_all_safe_gives_pass(material, member, correlation):
    section = build_uniform_i_section(0.006)
    model = build_uniform_i_plate_model(0.006, PANEL_LENGTH)
    cases = (
        FrameStringerLoadCase(name="a", axial_force=-10e3, shear_force_y=2e3, bending_moment_z=200.0),
        FrameStringerLoadCase(name="b", axial_force=-5e3, shear_force_y=1e3, bending_moment_z=100.0),
    )
    result = assess_multi_load_case(section, model, material, member, cases, correlation)
    assert result.all_cases_pass is True


def test_one_failing_case_gives_fail(material, member, correlation):
    section = build_uniform_i_section(0.006)
    model = build_uniform_i_plate_model(0.006, PANEL_LENGTH)
    cases = (
        FrameStringerLoadCase(name="safe", axial_force=-10e3, shear_force_y=2e3, bending_moment_z=200.0),
        FrameStringerLoadCase(name="huge_moment", axial_force=0.0, shear_force_y=0.0, bending_moment_z=20_000.0),
    )
    result = assess_multi_load_case(section, model, material, member, cases, correlation)
    assert result.all_cases_pass is False


def test_governing_load_case_selected_by_minimum_margin(material, member, correlation):
    section = build_uniform_i_section(0.004)
    model = build_uniform_i_plate_model(0.004, PANEL_LENGTH)
    result = assess_multi_load_case(section, model, material, member, CANONICAL_LOAD_CASES, correlation)
    expected = min(result.per_case, key=lambda c: c.governing_margin if c.governing_margin is not None else math.inf)
    assert result.governing_load_case == expected.load_case.name


def test_load_case_order_preserved(material, member, correlation):
    section = build_uniform_i_section(0.004)
    model = build_uniform_i_plate_model(0.004, PANEL_LENGTH)
    result = assess_multi_load_case(section, model, material, member, CANONICAL_LOAD_CASES, correlation)
    assert [c.load_case.name for c in result.per_case] == [lc.name for lc in CANONICAL_LOAD_CASES]


def test_deterministic_tie_behavior(material, member, correlation):
    section = build_uniform_i_section(0.004)
    model = build_uniform_i_plate_model(0.004, PANEL_LENGTH)
    cases = (
        FrameStringerLoadCase(name="first", axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3),
        FrameStringerLoadCase(name="second", axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3),
    )
    result = assess_multi_load_case(section, model, material, member, cases, correlation)
    assert result.governing_load_case == "first"


def test_identical_duplicate_cases_use_first_occurrence(material, member, correlation):
    lc = FrameStringerLoadCase(name="dup", axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    section = build_uniform_i_section(0.004)
    model = build_uniform_i_plate_model(0.004, PANEL_LENGTH)
    result = assess_multi_load_case(section, model, material, member, (lc, lc), correlation)
    assert result.governing_load_case == "dup"
    assert len(result.per_case) == 2


# ---- monotonicity (AB-AG) ----


def test_area_increases_with_thickness():
    areas = [build_uniform_i_section(t).area for t in (0.001, 0.002, 0.004, 0.006)]
    assert areas == sorted(areas)


def test_mass_increases_with_thickness(material):
    from frame_stringer.mass import linear_mass

    masses = [linear_mass(build_uniform_i_section(t), material) for t in (0.001, 0.002, 0.004, 0.006)]
    assert masses == sorted(masses)


@pytest.mark.parametrize(
    "build_section,build_model",
    [
        (build_uniform_i_section, build_uniform_i_plate_model),
        (build_uniform_z_section, build_uniform_z_plate_model),
        (build_uniform_hat_section, build_uniform_hat_plate_model),
    ],
)
def test_canonical_feasibility_non_decreasing_with_thickness(material, member, correlation, build_section, build_model):
    thicknesses = [t / 1000 for t in (0.75, 1.5, 2.5, 3.5, 4.5, 5.5, 6.0)]
    passes = []
    for t in thicknesses:
        section = build_section(t)
        model = build_model(t, PANEL_LENGTH)
        result = assess_multi_load_case(section, model, material, member, CANONICAL_LOAD_CASES, correlation)
        passes.append(result.all_cases_pass)
    # Once True, must remain True for all larger t (no oscillation).
    seen_pass = False
    for p in passes:
        if seen_pass:
            assert p is True
        if p:
            seen_pass = True


# ---- sizing (AH-AR) ----


def test_lower_bound_already_passes(material, member, correlation):
    result = size_section_family(
        FAMILIES[0], material, member, CANONICAL_LOAD_CASES, correlation, PANEL_LENGTH, t_min_gauge=5.0e-3
    )
    assert result.status in ("minimum_gauge_governs", "converged")
    assert result.iterations == 0


def test_minimum_gauge_governs(material, member, correlation):
    # A large minimum gauge that comfortably passes on its own.
    result = size_section_family(
        FAMILIES[0], material, member, CANONICAL_LOAD_CASES, correlation, PANEL_LENGTH, t_min_gauge=5.0e-3
    )
    assert result.status == "minimum_gauge_governs"
    assert result.required_thickness == pytest.approx(5.0e-3)


def test_lower_fails_upper_passes_converges(material, member, correlation):
    result = size_section_family(
        FAMILIES[0], material, member, CANONICAL_LOAD_CASES, correlation, PANEL_LENGTH, t_min_gauge=1.5e-3
    )
    assert result.status == "converged"
    assert result.iterations > 0


def test_returned_thickness_passes(material, member, correlation):
    result = size_section_family(
        FAMILIES[0], material, member, CANONICAL_LOAD_CASES, correlation, PANEL_LENGTH, t_min_gauge=1.5e-3
    )
    section = build_uniform_i_section(result.required_thickness)
    model = build_uniform_i_plate_model(result.required_thickness, PANEL_LENGTH)
    check = assess_multi_load_case(section, model, material, member, CANONICAL_LOAD_CASES, correlation)
    assert check.all_cases_pass is True


def test_slightly_thinner_point_fails_when_structurally_controlled(material, member, correlation):
    result = size_section_family(
        FAMILIES[0], material, member, CANONICAL_LOAD_CASES, correlation, PANEL_LENGTH, t_min_gauge=1.5e-3
    )
    assert result.status == "converged"
    t_thinner = result.required_thickness - 0.05e-3
    section = build_uniform_i_section(t_thinner)
    model = build_uniform_i_plate_model(t_thinner, PANEL_LENGTH)
    check = assess_multi_load_case(section, model, material, member, CANONICAL_LOAD_CASES, correlation)
    assert check.all_cases_pass is False


def test_upper_bound_infeasible_handling(material, member, correlation):
    result = size_section_family(
        FAMILIES[0],
        material,
        member,
        CANONICAL_LOAD_CASES,
        correlation,
        PANEL_LENGTH,
        t_min_gauge=1.5e-3,
        t_max_search=1.0e-3,  # far too small to ever pass
    )
    assert result.status == "upper_bound_infeasible"
    assert result.required_thickness is None
    assert result.section is None
    assert result.mass_per_length is None
    assert result.final_assessment is not None  # diagnostics still available


def test_repeated_sizing_deterministic(material, member, correlation):
    r1 = size_section_family(FAMILIES[0], material, member, CANONICAL_LOAD_CASES, correlation, PANEL_LENGTH, 1.5e-3)
    r2 = size_section_family(FAMILIES[0], material, member, CANONICAL_LOAD_CASES, correlation, PANEL_LENGTH, 1.5e-3)
    assert r1.required_thickness == pytest.approx(r2.required_thickness)
    assert r1.status == r2.status


def test_thickness_within_bounds(material, member, correlation):
    result = size_section_family(
        FAMILIES[0], material, member, CANONICAL_LOAD_CASES, correlation, PANEL_LENGTH, t_min_gauge=1.5e-3
    )
    assert 0.75e-3 <= result.required_thickness <= 6.0e-3


def test_tolerance_respected(material, member, correlation):
    tol = 1e-5
    result = size_section_family(
        FAMILIES[0], material, member, CANONICAL_LOAD_CASES, correlation, PANEL_LENGTH, t_min_gauge=1.5e-3,
        tolerance=tol,
    )
    # The converged result should be within `tol` of the true feasibility
    # boundary -- check the neighboring failing point is at most `tol` away.
    t_thinner = result.required_thickness - tol
    section = build_uniform_i_section(t_thinner)
    model = build_uniform_i_plate_model(t_thinner, PANEL_LENGTH)
    check = assess_multi_load_case(section, model, material, member, CANONICAL_LOAD_CASES, correlation)
    assert check.all_cases_pass is False


def test_mass_matches_existing_mass_helper(material, member, correlation):
    from frame_stringer.mass import linear_mass

    result = size_section_family(
        FAMILIES[0], material, member, CANONICAL_LOAD_CASES, correlation, PANEL_LENGTH, t_min_gauge=1.5e-3
    )
    assert result.mass_per_length == pytest.approx(linear_mass(result.section, material))


def test_governing_case_matches_final_assessment(material, member, correlation):
    result = size_section_family(
        FAMILIES[0], material, member, CANONICAL_LOAD_CASES, correlation, PANEL_LENGTH, t_min_gauge=1.5e-3
    )
    assert result.governing_load_case == result.final_assessment.governing_load_case
    assert result.governing_constraint == result.final_assessment.governing_constraint
    assert result.governing_margin == pytest.approx(result.final_assessment.governing_margin)
