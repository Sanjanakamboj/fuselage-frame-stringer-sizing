import math

import pytest

from frame_stringer.column_buckling import (
    MemberGeometry,
    assess_euler_buckling,
    euler_critical_load,
    euler_critical_stress_from_load,
    euler_critical_stress_from_slenderness,
    global_buckling_margin,
    radius_of_gyration,
    slenderness_ratio,
)
from frame_stringer.loads import SectionLoad
from frame_stringer.material import IsotropicMaterial


@pytest.fixture
def material():
    return IsotropicMaterial(
        name="Illustrative Al-like",
        elastic_modulus=70e9,
        poisson_ratio=0.33,
        density=2700.0,
        yield_strength=300e6,
    )


# ---- member geometry (A-E) ----


def test_valid_member_construction():
    m = MemberGeometry(length=2.0, effective_length_factor=1.0)
    assert m.length == 2.0
    assert m.effective_length_factor == 1.0


def test_invalid_length():
    with pytest.raises(ValueError):
        MemberGeometry(length=0.0, effective_length_factor=1.0)
    with pytest.raises(ValueError):
        MemberGeometry(length=-1.0, effective_length_factor=1.0)


def test_invalid_k():
    with pytest.raises(ValueError):
        MemberGeometry(length=2.0, effective_length_factor=0.0)
    with pytest.raises(ValueError):
        MemberGeometry(length=2.0, effective_length_factor=-0.5)


@pytest.mark.parametrize(
    "field,bad_value", [("length", math.nan), ("effective_length_factor", math.inf)]
)
def test_member_non_finite_rejected(field, bad_value):
    kwargs = dict(length=2.0, effective_length_factor=1.0)
    kwargs[field] = bad_value
    with pytest.raises(ValueError):
        MemberGeometry(**kwargs)


def test_effective_length_hand_calc():
    m = MemberGeometry(length=2.0, effective_length_factor=0.7)
    assert m.effective_length == pytest.approx(1.4)


# ---- radius of gyration / slenderness (F-J) ----


def test_radius_of_gyration_hand_calc():
    r = radius_of_gyration(area=0.002, moment_of_inertia=4e-7)
    assert r == pytest.approx(math.sqrt(4e-7 / 0.002))


def test_slenderness_hand_calc():
    m = MemberGeometry(length=2.0, effective_length_factor=1.0)
    r_g = 0.02
    lam = slenderness_ratio(m, r_g)
    assert lam == pytest.approx(1.0 * 2.0 / 0.02)


def test_slenderness_linear_with_k():
    r_g = 0.02
    m1 = MemberGeometry(length=2.0, effective_length_factor=1.0)
    m2 = MemberGeometry(length=2.0, effective_length_factor=2.0)
    assert slenderness_ratio(m2, r_g) == pytest.approx(2.0 * slenderness_ratio(m1, r_g))


def test_slenderness_linear_with_length():
    r_g = 0.02
    m1 = MemberGeometry(length=1.0, effective_length_factor=1.0)
    m2 = MemberGeometry(length=3.0, effective_length_factor=1.0)
    assert slenderness_ratio(m2, r_g) == pytest.approx(3.0 * slenderness_ratio(m1, r_g))


def test_slenderness_decreases_as_radius_of_gyration_increases():
    m = MemberGeometry(length=2.0, effective_length_factor=1.0)
    lam_small_r = slenderness_ratio(m, 0.01)
    lam_large_r = slenderness_ratio(m, 0.05)
    assert lam_large_r < lam_small_r


def test_radius_of_gyration_invalid_inputs():
    with pytest.raises(ValueError):
        radius_of_gyration(area=0.0, moment_of_inertia=1e-6)
    with pytest.raises(ValueError):
        radius_of_gyration(area=0.002, moment_of_inertia=0.0)


# ---- Euler (K-U) ----


def test_euler_hand_calc():
    E, I, L, K = 70e9, 1.0e-6, 2.0, 1.0
    member = MemberGeometry(length=L, effective_length_factor=K)
    expected = math.pi**2 * E * I / (K * L) ** 2
    assert euler_critical_load(member, E, I) == pytest.approx(expected)


def test_stress_load_identity():
    E, I, A = 70e9, 1.0e-6, 0.002
    member = MemberGeometry(length=2.0, effective_length_factor=1.0)
    P_cr = euler_critical_load(member, E, I)
    r_g = radius_of_gyration(A, I)
    lam = slenderness_ratio(member, r_g)
    sigma_from_load = euler_critical_stress_from_load(P_cr, A)
    sigma_from_slenderness = euler_critical_stress_from_slenderness(E, lam)
    assert sigma_from_load == pytest.approx(sigma_from_slenderness, rel=1e-9)


def test_length_inverse_squared_scaling():
    E, I = 70e9, 1.0e-6
    m1 = MemberGeometry(length=2.0, effective_length_factor=1.0)
    m2 = MemberGeometry(length=4.0, effective_length_factor=1.0)  # doubled
    P1 = euler_critical_load(m1, E, I)
    P2 = euler_critical_load(m2, E, I)
    assert P2 == pytest.approx(P1 / 4.0)


def test_k_inverse_squared_scaling():
    E, I = 70e9, 1.0e-6
    m1 = MemberGeometry(length=2.0, effective_length_factor=1.0)
    m2 = MemberGeometry(length=2.0, effective_length_factor=2.0)  # doubled
    P1 = euler_critical_load(m1, E, I)
    P2 = euler_critical_load(m2, E, I)
    assert P2 == pytest.approx(P1 / 4.0)


def test_elastic_modulus_linear_scaling():
    I = 1.0e-6
    m = MemberGeometry(length=2.0, effective_length_factor=1.0)
    P1 = euler_critical_load(m, 70e9, I)
    P2 = euler_critical_load(m, 140e9, I)
    assert P2 == pytest.approx(2.0 * P1)


def test_moment_of_inertia_linear_scaling():
    E = 70e9
    m = MemberGeometry(length=2.0, effective_length_factor=1.0)
    P1 = euler_critical_load(m, E, 1.0e-6)
    P2 = euler_critical_load(m, E, 2.0e-6)
    assert P2 == pytest.approx(2.0 * P1)


def test_zero_compression_not_applicable(material):
    member = MemberGeometry(length=2.0, effective_length_factor=1.0)
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_euler_buckling(member, 0.002, 4e-7, material, load)
    assert result.applicable is False
    assert result.margin is None
    assert result.passes is True


def test_tension_not_applicable(material):
    member = MemberGeometry(length=2.0, effective_length_factor=1.0)
    load = SectionLoad(axial_force=50e3, shear_force_y=0.0, bending_moment_z=0.0)  # tension
    result = assess_euler_buckling(member, 0.002, 4e-7, material, load)
    assert result.applicable is False
    assert result.margin is None
    assert result.passes is True


def test_exact_euler_boundary_passes(material):
    member = MemberGeometry(length=2.0, effective_length_factor=1.0)
    A, I = 0.002, 4e-7
    P_cr = euler_critical_load(member, material.elastic_modulus, I)
    load = SectionLoad(axial_force=-P_cr, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_euler_buckling(member, A, I, material, load)
    assert result.margin == pytest.approx(0.0, abs=1e-9)
    assert result.passes is True


def test_slightly_below_pcr_passes(material):
    member = MemberGeometry(length=2.0, effective_length_factor=1.0)
    A, I = 0.002, 4e-7
    P_cr = euler_critical_load(member, material.elastic_modulus, I)
    load = SectionLoad(axial_force=-0.9 * P_cr, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_euler_buckling(member, A, I, material, load)
    assert result.passes is True
    assert result.margin > 0


def test_slightly_above_pcr_fails(material):
    member = MemberGeometry(length=2.0, effective_length_factor=1.0)
    A, I = 0.002, 4e-7
    P_cr = euler_critical_load(member, material.elastic_modulus, I)
    load = SectionLoad(axial_force=-1.1 * P_cr, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_euler_buckling(member, A, I, material, load)
    assert result.passes is False
    assert result.margin < 0


def test_global_buckling_margin_zero_demand():
    assert global_buckling_margin(critical_load=100e3, compressive_load_demand=0.0) is None
