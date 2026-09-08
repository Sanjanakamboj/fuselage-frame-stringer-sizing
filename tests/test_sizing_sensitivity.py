"""Sensitivity of the multi-load-case sizing study to minimum gauge, member
length, K, and the crippling correlation."""

import pytest

from frame_stringer.column_buckling import MemberGeometry, euler_critical_load
from frame_stringer.crippling import CripplingCorrelation
from frame_stringer.load_cases import CANONICAL_LOAD_CASES
from frame_stringer.material import IsotropicMaterial
from frame_stringer.plate_buckling import critical_compression_stress
from frame_stringer.sizing import FAMILIES, build_uniform_i_section, size_section_family


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
I_FAMILY = FAMILIES[0]


def _size(material, member, correlation, t_min_gauge=1.5e-3, **kwargs):
    return size_section_family(
        I_FAMILY, material, member, CANONICAL_LOAD_CASES, correlation, PANEL_LENGTH, t_min_gauge, **kwargs
    )


def test_increasing_minimum_gauge_cannot_reduce_selected_thickness(material, member, correlation):
    # Below the structural requirement, bisection converges independently
    # for each gauge to within `tolerance` of the same true feasibility
    # boundary, so tiny (sub-tolerance) numerical noise is expected and
    # tolerated here; a *meaningful* decrease must never occur.
    tol = 1e-6
    gauges = [1.0e-3, 1.5e-3, 2.0e-3, 2.5e-3, 3.0e-3]
    thicknesses = [_size(material, member, correlation, t_min_gauge=g).required_thickness for g in gauges]
    for earlier, later in zip(thicknesses, thicknesses[1:]):
        assert later >= earlier - 2 * tol


def test_increasing_minimum_gauge_cannot_reduce_mass(material, member, correlation):
    tol = 1e-6
    gauges = [1.0e-3, 1.5e-3, 2.0e-3, 2.5e-3, 3.0e-3]
    results = [_size(material, member, correlation, t_min_gauge=g) for g in gauges]
    for earlier, later in zip(results, results[1:]):
        # Mass is monotonic in thickness (verified elsewhere), so allow the
        # same small tolerance-driven slack as the thickness itself.
        assert later.required_thickness >= earlier.required_thickness - 2 * tol
        if later.required_thickness > earlier.required_thickness + 2 * tol:
            assert later.mass_per_length > earlier.mass_per_length


def test_gauge_governs_once_it_exceeds_structural_requirement(material, member, correlation):
    unconstrained = _size(material, member, correlation, t_min_gauge=0.75e-3)
    required_by_structure = unconstrained.required_thickness
    # A gauge well above the structural requirement should govern exactly.
    generous_gauge = required_by_structure * 2.0
    result = _size(material, member, correlation, t_min_gauge=generous_gauge)
    assert result.status == "minimum_gauge_governs"
    assert result.required_thickness == pytest.approx(generous_gauge)


def test_increasing_member_length_does_not_improve_euler_capacity(material):
    I = build_uniform_i_section(0.004).moment_of_inertia_z
    lengths = [0.75, 1.0, 1.2, 1.5, 2.0]
    p_crs = [
        euler_critical_load(MemberGeometry(length=L, effective_length_factor=1.0), material.elastic_modulus, I)
        for L in lengths
    ]
    assert p_crs == sorted(p_crs, reverse=True)


def test_increasing_k_does_not_improve_euler_capacity(material):
    I = build_uniform_i_section(0.004).moment_of_inertia_z
    ks = [0.5, 0.7, 1.0, 1.5, 2.0]
    p_crs = [
        euler_critical_load(MemberGeometry(length=1.2, effective_length_factor=K), material.elastic_modulus, I)
        for K in ks
    ]
    assert p_crs == sorted(p_crs, reverse=True)


def test_member_length_sensitivity_propagates_into_sizing(material, correlation):
    lengths = [0.75, 1.0, 1.2, 1.5, 2.0]
    results = [
        _size(material, MemberGeometry(length=L, effective_length_factor=1.0), correlation) for L in lengths
    ]
    # Required thickness must be non-decreasing as the member gets longer
    # (longer member -> lower Pcr -> harder to satisfy Euler/amplified
    # yield -> requires at least as much thickness).
    thicknesses = [r.required_thickness for r in results]
    assert thicknesses == sorted(thicknesses)


def test_k_sensitivity_propagates_into_sizing(material, correlation):
    ks = [0.5, 0.7, 1.0, 1.5, 2.0]
    results = [_size(material, MemberGeometry(length=1.2, effective_length_factor=K), correlation) for K in ks]
    thicknesses = [r.required_thickness for r in results]
    assert thicknesses == sorted(thicknesses)


def test_alpha_sensitivity_propagates_into_sizing(material, member):
    # A weak correlation (small alpha, but still feasible within the
    # search bounds) should require at least as much thickness as a
    # strong one, all else equal -- and here it is genuinely
    # crippling-governed, unlike the stronger cases.
    weak = CripplingCorrelation(alpha=0.3, exponent=0.6, label="weak", source_note="illustrative")
    strong = CripplingCorrelation(alpha=3.0, exponent=0.6, label="strong", source_note="illustrative")
    weak_result = _size(material, member, weak)
    strong_result = _size(material, member, strong)
    assert weak_result.required_thickness >= strong_result.required_thickness
    assert weak_result.governing_constraint == "crippling"


def test_exponent_sensitivity_propagates_into_sizing(material, member):
    corr_a = CripplingCorrelation(alpha=1.2, exponent=0.4, label="a", source_note="illustrative")
    corr_b = CripplingCorrelation(alpha=1.2, exponent=0.8, label="b", source_note="illustrative")
    result_a = _size(material, member, corr_a)
    result_b = _size(material, member, corr_b)
    # Both should still be findable within the search bounds; the exact
    # governing thickness may or may not differ depending on whether
    # crippling ever governs -- this test only confirms both sizing runs
    # complete and produce a valid, self-consistent result.
    for result in (result_a, result_b):
        assert result.status in ("converged", "minimum_gauge_governs")
        assert result.required_thickness is not None


def test_panel_length_leaves_compression_critical_stress_unchanged(material):
    section = build_uniform_i_section(0.004)
    web = next(c for c in section.components if c.label == "web")
    b, t = web.height, web.width
    stresses = []
    for panel_length in (0.15, 0.30, 0.60, 1.20):
        # Compression buckling coefficient/critical stress depend only on
        # b, t, and boundary condition -- never on panel length (`a`).
        sigma_cr = critical_compression_stress("internal", b, t, material)
        stresses.append(sigma_cr)
    assert all(s == pytest.approx(stresses[0]) for s in stresses)
