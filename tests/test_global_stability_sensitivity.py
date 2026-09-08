"""Sensitivity of the global beam-column screen to member length, K, and stiffness.

Complements the raw-formula scaling tests in test_column_buckling.py by
verifying the same trends hold end-to-end through assess_beam_column for
a real built-up section.
"""

import pytest

from frame_stringer.beam_column import assess_beam_column
from frame_stringer.column_buckling import MemberGeometry
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


LOAD = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)


def test_length_sensitivity_pcr_decreases_and_amplification_grows(material, section):
    lengths = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
    p_crs = []
    amplifications = []
    for L in lengths:
        member = MemberGeometry(length=L, effective_length_factor=1.0)
        bc = assess_beam_column(member, section, material, LOAD)
        p_crs.append(bc.euler_result.critical_load)
        amplifications.append(bc.amplification_factor)

    # P_cr strictly decreases with length.
    assert p_crs == sorted(p_crs, reverse=True)
    # Amplification factor strictly increases with length (P/Pcr grows).
    assert amplifications == sorted(amplifications)


def test_k_sensitivity_worsens_stability(material, section):
    ks = [0.5, 0.7, 1.0, 1.5, 2.0]
    member_length = 2.0
    p_crs = []
    margins = []
    for K in ks:
        member = MemberGeometry(length=member_length, effective_length_factor=K)
        bc = assess_beam_column(member, section, material, LOAD)
        p_crs.append(bc.euler_result.critical_load)
        margins.append(bc.euler_result.margin)

    # Larger K -> lower P_cr -> lower (worse) Euler margin, monotonically.
    assert p_crs == sorted(p_crs, reverse=True)
    assert margins == sorted(margins, reverse=True)


def test_ei_scaling_linear_in_pcr(material, section):
    from frame_stringer.column_buckling import euler_critical_load

    member = MemberGeometry(length=2.0, effective_length_factor=1.0)
    base_I = section.moment_of_inertia_z
    p_crs = []
    for scale in (0.75, 1.0, 1.25, 1.5):
        P_cr = euler_critical_load(member, material.elastic_modulus, base_I * scale)
        p_crs.append(P_cr)
    # Linear in I (and by the same formula, linear in E).
    assert p_crs[-1] / p_crs[0] == pytest.approx(1.5 / 0.75, rel=1e-9)


def test_bending_efficient_section_also_improves_global_stability(material):
    """More material away from the neutral axis increases both I_z (bending
    efficiency, Milestone 2) and I_z/A (radius of gyration, hence Euler
    P_cr) -- this is a genuinely distinct benefit from Milestone 3's local
    buckling story."""
    from frame_stringer.column_buckling import euler_critical_load, radius_of_gyration
    from frame_stringer.geometry import RectangularSection

    i_sec = i_section(flange_width=0.06, overall_height=0.10, flange_thickness=0.006, web_thickness=0.004)
    # Compact rectangle of the same area.
    target_area = i_sec.area
    h = 0.06
    rect = RectangularSection(width=target_area / h, height=h)

    member = MemberGeometry(length=2.0, effective_length_factor=1.0)
    r_g_i = radius_of_gyration(i_sec.area, i_sec.moment_of_inertia_z)
    r_g_rect = radius_of_gyration(rect.area, rect.moment_of_inertia_z)
    P_cr_i = euler_critical_load(member, material.elastic_modulus, i_sec.moment_of_inertia_z)
    P_cr_rect = euler_critical_load(member, material.elastic_modulus, rect.moment_of_inertia_z)

    assert r_g_i > r_g_rect
    assert P_cr_i > P_cr_rect
