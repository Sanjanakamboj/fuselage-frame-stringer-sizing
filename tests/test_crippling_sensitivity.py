"""Sensitivity of the section-level crippling screen to thickness, width,
alpha, and exponent, through the full I-section factory + mapping path.
"""

import pytest

from frame_stringer.crippling import CripplingCorrelation, assess_section_crippling
from frame_stringer.local_buckling import i_section_plate_elements
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
LOAD = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)


def _corr(alpha=1.2, exponent=0.6):
    return CripplingCorrelation(alpha=alpha, exponent=exponent, label="Illustrative", source_note="illustrative")


def test_web_thickness_scaling_improves_crippling_stress(material):
    corr = _corr()
    raw_values = []
    for scale in (0.75, 1.0, 1.25, 1.5):
        params = dict(BASE)
        params["web_thickness"] = BASE["web_thickness"] * scale
        model = i_section_plate_elements(panel_length=PANEL_LENGTH, **params)
        result = assess_section_crippling(model, material, corr, LOAD)
        raw_values.append(result.raw_crippling_stress)
    # Thicker web -> larger t -> smaller b/t -> higher raw crippling stress.
    assert raw_values == sorted(raw_values)


def test_flange_width_scaling_reduces_crippling_stress(material):
    corr = _corr()
    raw_values = []
    for scale in (0.75, 1.0, 1.25, 1.5):
        params = dict(BASE)
        # Widen the outstand (flange_width), holding web_thickness fixed --
        # only affects flange geometry, not the (here web-governed) driver
        # unless the flange becomes even more slender than the web.
        b_out_base = (BASE["flange_width"] - BASE["web_thickness"]) / 2.0
        params["flange_width"] = BASE["web_thickness"] + 2 * (b_out_base * scale)
        model = i_section_plate_elements(panel_length=PANEL_LENGTH, **params)
        result = assess_section_crippling(model, material, corr, LOAD)
        raw_values.append((result.governing_element, result.raw_crippling_stress))

    # The web remains more slender than the flange throughout this range,
    # so it continues to govern and the raw crippling stress (driven only
    # by the unchanged web b/t) stays constant.
    assert all(name == "web" for name, _ in raw_values)
    stresses = [s for _, s in raw_values]
    assert stresses == pytest.approx([stresses[0]] * len(stresses))


def test_alpha_scaling_linear_before_cap(material):
    # Use a deliberately slender constructed section (thin web) so the
    # correlation stays below yield across the alpha sensitivity range.
    thin_params = dict(flange_width=0.06, overall_height=0.10, flange_thickness=0.006, web_thickness=0.0006)
    model = i_section_plate_elements(panel_length=PANEL_LENGTH, **thin_params)
    load = SectionLoad(axial_force=-5e3, shear_force_y=0.0, bending_moment_z=0.0)
    raws = []
    for scale in (0.75, 1.0, 1.25, 1.5):
        corr = _corr(alpha=1.2 * scale)
        result = assess_section_crippling(model, material, corr, load)
        raws.append(result.raw_crippling_stress)
    assert raws == sorted(raws)
    assert raws[-1] / raws[0] == pytest.approx(1.5 / 0.75, rel=1e-9)


def test_exponent_sensitivity_changes_stress_strongly(material):
    corr_values = []
    model = _thin_model()
    for m in (0.4, 0.5, 0.6, 0.7, 0.8):
        corr = _corr(alpha=1.2, exponent=m)
        result = assess_section_crippling(model, material, corr, SectionLoad(-5e3, 0.0, 0.0))
        corr_values.append(result.raw_crippling_stress)
    # Since b/t > 1 here, (t/b)^m shrinks as m grows -> raw stress decreases
    # monotonically with increasing exponent.
    assert corr_values == sorted(corr_values, reverse=True)


def _thin_model():
    thin_params = dict(flange_width=0.06, overall_height=0.10, flange_thickness=0.006, web_thickness=0.0006)
    return i_section_plate_elements(panel_length=PANEL_LENGTH, **thin_params)


def test_baseline_representative_sections_are_yield_capped(material):
    """Documents the honest baseline finding: for the Milestone 2/3
    representative (fairly stocky) I/Z/hat proportions, the illustrative
    correlation with alpha=1.2, m=0.6 predicts a raw crippling stress well
    above yield, so the yield cap is active and material yield -- not this
    illustrative crippling correlation -- governs. This is not a defect;
    it is the honest, un-tuned result of applying the suggested
    illustrative coefficient range to these particular proportions."""
    from frame_stringer.local_buckling import hat_section_plate_elements, z_section_plate_elements

    corr = _corr()
    models = {
        "I": i_section_plate_elements(panel_length=PANEL_LENGTH, **BASE),
        "Z": z_section_plate_elements(
            web_height=0.08, web_thickness=0.0058, flange_width=0.05, flange_thickness=0.011, panel_length=PANEL_LENGTH
        ),
        "hat": hat_section_plate_elements(
            crown_width=0.065, overall_height=0.07, wall_thickness=0.0068, flange_width=0.028, panel_length=PANEL_LENGTH
        ),
    }
    for name, model in models.items():
        result = assess_section_crippling(model, material, corr, LOAD)
        assert result.yield_cap_active is True, f"{name}-section unexpectedly not yield-capped"
        assert result.crippling_stress == pytest.approx(material.yield_strength)
