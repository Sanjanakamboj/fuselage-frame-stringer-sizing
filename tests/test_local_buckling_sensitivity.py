"""Section-level sensitivity tests: thickness, width, panel length, boundary condition.

These complement the plate-level scaling tests in test_plate_buckling.py
(which verify the raw t^2 / b^-2 / E-linear / boundary-ratio formulas) by
checking that the same trends hold end-to-end through the I-section
factory mapping and section-level assessment.
"""

import pytest

from frame_stringer.local_buckling import assess_section_local_buckling, i_section_plate_elements
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


BASE = dict(flange_width=0.06, overall_height=0.10, flange_thickness=0.0095, web_thickness=0.006)
PANEL_LENGTH = 0.30


def _flange_outstand_result(model, load, material, side="top_flange_outstand"):
    from frame_stringer.local_buckling import assess_section_local_buckling

    result = assess_section_local_buckling(model, load, material)
    return next(p for p in result.plates if p.plate_name == side)


def test_flange_thickness_scaling_improves_flange_margin(material):
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=6000.0)
    margins = []
    for scale in (0.75, 1.0, 1.25, 1.5):
        params = dict(BASE)
        params["flange_thickness"] = BASE["flange_thickness"] * scale
        model = i_section_plate_elements(panel_length=PANEL_LENGTH, **params)
        result = _flange_outstand_result(model, load, material, "bottom_flange_outstand")
        margins.append(result.sigma_cr)
    # sigma_cr ~ t^2, monotonically increasing with thickness scale.
    assert margins == sorted(margins)
    assert margins[-1] / margins[0] == pytest.approx((1.5 / 0.75) ** 2, rel=1e-9)


def test_web_thickness_scaling_improves_web_critical_stresses(material):
    load = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=4e3)
    sigma_crs = []
    tau_crs = []
    for scale in (0.75, 1.0, 1.25, 1.5):
        params = dict(BASE)
        params["web_thickness"] = BASE["web_thickness"] * scale
        model = i_section_plate_elements(panel_length=PANEL_LENGTH, **params)
        result = assess_section_local_buckling(model, load, material)
        web = next(p for p in result.plates if p.plate_name == "web")
        sigma_crs.append(web.sigma_cr)
        tau_crs.append(web.tau_cr)
    assert sigma_crs == sorted(sigma_crs)
    assert tau_crs == sorted(tau_crs)


def test_panel_length_affects_shear_but_not_compression_critical_stress(material):
    load = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=4e3)
    sigma_crs = []
    tau_crs = []
    for panel_length in (0.15, 0.30, 0.60, 1.20):
        model = i_section_plate_elements(panel_length=panel_length, **BASE)
        result = assess_section_local_buckling(model, load, material)
        web = next(p for p in result.plates if p.plate_name == "web")
        sigma_crs.append(web.sigma_cr)
        tau_crs.append(web.tau_cr)

    # Compression critical stress is independent of panel length (b, t, k_c
    # don't depend on `a`).
    assert all(s == pytest.approx(sigma_crs[0]) for s in sigma_crs)

    # Shear critical stress changes with aspect ratio and, for a web that is
    # already several times longer than it is wide, decreases monotonically
    # towards the long-plate asymptote (k_s -> 5.34) as panel length grows.
    assert tau_crs == sorted(tau_crs, reverse=True)


def test_flange_outstand_width_scaling_reduces_margin(material):
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=6000.0)
    margins = []
    for scale in (0.75, 1.0, 1.25, 1.5):
        params = dict(BASE)
        # Widen the flange (and hence the outstand) while holding the web
        # thickness fixed, so only b_out changes.
        params["flange_width"] = BASE["web_thickness"] + 2 * (
            (BASE["flange_width"] - BASE["web_thickness"]) / 2.0 * scale
        )
        model = i_section_plate_elements(panel_length=PANEL_LENGTH, **params)
        result = _flange_outstand_result(model, load, material, "top_flange_outstand")
        margins.append(result.sigma_cr)
    # Wider outstand -> lower sigma_cr (b^-2), monotonically decreasing.
    assert margins == sorted(margins, reverse=True)


def test_bending_efficient_section_is_not_automatically_locally_stable(material):
    """Milestone 2 vs Milestone 3 lesson, expressed as a regression test.

    A thin-walled section can have an excellent (high-margin) yield check
    while still failing local buckling in its thin flange -- the two
    checks are independent and neither implies the other.
    """
    from frame_stringer.built_up_strength import assess_builtup_strength

    thin_model = i_section_plate_elements(
        flange_width=0.20, overall_height=0.10, flange_thickness=0.001, web_thickness=0.003,
        panel_length=1.0,
    )
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=800.0)
    yield_result = assess_builtup_strength(load, thin_model.section, material)
    buckling_result = assess_section_local_buckling(thin_model, load, material)

    assert yield_result.passes is True
    assert yield_result.min_margin > 1.0  # comfortable yield margin
    assert buckling_result.passes is False  # yet locally unstable
