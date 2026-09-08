import math

import pytest

from frame_stringer.built_up_geometry import BuiltUpSection
from frame_stringer.built_up_stress import evaluate_normal_stress
from frame_stringer.crippling import (
    CripplingCorrelation,
    assess_section_crippling,
    section_geometry_driver,
)
from frame_stringer.local_buckling import (
    hat_section_plate_elements,
    i_section_plate_elements,
    z_section_plate_elements,
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


@pytest.fixture
def correlation():
    return CripplingCorrelation(
        alpha=1.2, exponent=0.6, label="Illustrative baseline", source_note="illustrative, not sourced"
    )


PANEL_LENGTH = 0.30


def _i_model():
    return i_section_plate_elements(
        flange_width=0.06, overall_height=0.10, flange_thickness=0.0095, web_thickness=0.006, panel_length=PANEL_LENGTH
    )


def _z_model():
    return z_section_plate_elements(
        web_height=0.08, web_thickness=0.0058, flange_width=0.05, flange_thickness=0.011, panel_length=PANEL_LENGTH
    )


def _hat_model():
    return hat_section_plate_elements(
        crown_width=0.065, overall_height=0.07, wall_thickness=0.0068, flange_width=0.028, panel_length=PANEL_LENGTH
    )


# ---- geometry driver (M-R) ----


def test_i_section_governing_bt():
    model = _i_model()
    name, b, t, bt = section_geometry_driver(model)
    web = next(m for m in model.mappings if m.plate.name == "web")
    top = next(m for m in model.mappings if m.plate.name == "top_flange_outstand")
    assert bt == pytest.approx(max(web.plate.width / web.plate.thickness, top.plate.width / top.plate.thickness))
    assert name == "web"  # web is the more slender element here


def test_z_section_governing_bt():
    model = _z_model()
    name, b, t, bt = section_geometry_driver(model)
    expected_bt = max(m.plate.width / m.plate.thickness for m in model.mappings)
    assert bt == pytest.approx(expected_bt)
    assert name == "web"


def test_hat_section_governing_bt():
    model = _hat_model()
    name, b, t, bt = section_geometry_driver(model)
    expected_bt = max(m.plate.width / m.plate.thickness for m in model.mappings)
    assert bt == pytest.approx(expected_bt)
    # One of the two identical, most-slender webs governs.
    assert name in ("web_left", "web_right")


def test_deterministic_tie_break_for_equal_bt_elements():
    # Hat's two webs are geometrically identical (same b/t) -- the fixed
    # mapping order must deterministically pick the first one.
    model = _hat_model()
    name, _, _, _ = section_geometry_driver(model)
    assert name == "web_left"  # web_left precedes web_right in mapping order


def test_geometry_driver_component_order_independence():
    model_i = _i_model()
    reordered_section = BuiltUpSection(tuple(reversed(model_i.section.components)))
    # section_geometry_driver only depends on model.mappings, which are
    # unaffected by section component order (they were built directly by
    # the factory from explicit parameters) -- confirm invariance.
    from frame_stringer.local_buckling import SectionPlateModel

    reordered_model = SectionPlateModel(reordered_section, model_i.mappings)
    name_a, b_a, t_a, bt_a = section_geometry_driver(model_i)
    name_b, b_b, t_b, bt_b = section_geometry_driver(reordered_model)
    assert (name_a, b_a, t_a, bt_a) == (name_b, b_b, t_b, bt_b)


def test_panel_length_does_not_affect_geometry_driver():
    model_short = i_section_plate_elements(
        flange_width=0.06, overall_height=0.10, flange_thickness=0.0095, web_thickness=0.006, panel_length=0.10
    )
    model_long = i_section_plate_elements(
        flange_width=0.06, overall_height=0.10, flange_thickness=0.0095, web_thickness=0.006, panel_length=1.50
    )
    assert section_geometry_driver(model_short) == section_geometry_driver(model_long)


# ---- axial capacity (S-X) ----


def test_axial_capacity_equals_stress_times_area(material, correlation):
    model = _i_model()
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    result = assess_section_crippling(model, material, correlation, load)
    assert result.equivalent_crippling_load == pytest.approx(result.crippling_stress * result.area)


def test_zero_compression_axial_margin_none(material, correlation):
    model = _i_model()
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_section_crippling(model, material, correlation, load)
    assert result.axial_average_margin is None
    assert result.peak_compression_margin is None
    assert result.passes is True


def test_tension_axial_margin_none(material, correlation):
    model = _i_model()
    load = SectionLoad(axial_force=50e3, shear_force_y=0.0, bending_moment_z=0.0)  # tension
    result = assess_section_crippling(model, material, correlation, load)
    assert result.axial_average_margin is None
    assert result.compressive_load_demand == 0.0


def test_exact_axial_boundary_passes(material, correlation):
    model = _i_model()
    # First find equivalent_crippling_load with a nominal load, then apply
    # exactly that as the compressive demand.
    probe = assess_section_crippling(model, material, correlation, SectionLoad(0.0, 0.0, 0.0))
    P_crip = probe.equivalent_crippling_load
    load = SectionLoad(axial_force=-P_crip, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_section_crippling(model, material, correlation, load)
    assert result.axial_average_margin == pytest.approx(0.0, abs=1e-9)
    assert result.passes is True


def test_below_axial_capacity_passes(material, correlation):
    model = _i_model()
    probe = assess_section_crippling(model, material, correlation, SectionLoad(0.0, 0.0, 0.0))
    P_crip = probe.equivalent_crippling_load
    load = SectionLoad(axial_force=-0.5 * P_crip, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_section_crippling(model, material, correlation, load)
    assert result.passes is True
    assert result.axial_average_margin > 0


def test_above_axial_capacity_fails(material, correlation):
    model = _i_model()
    probe = assess_section_crippling(model, material, correlation, SectionLoad(0.0, 0.0, 0.0))
    P_crip = probe.equivalent_crippling_load
    load = SectionLoad(axial_force=-1.5 * P_crip, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_section_crippling(model, material, correlation, load)
    assert result.passes is False
    assert result.axial_average_margin < 0


# ---- peak compression (Y-AE) ----


def test_pure_axial_peak_stress_equals_P_over_A(material, correlation):
    model = _i_model()
    load = SectionLoad(axial_force=-40e3, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_section_crippling(model, material, correlation, load)
    assert result.peak_compressive_stress == pytest.approx(40e3 / model.section.area)


def test_pure_bending_peak_compression_hand_calc(material, correlation):
    model = _i_model()
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=6000.0)
    result = assess_section_crippling(model, material, correlation, load)
    normal = evaluate_normal_stress(load, model.section)
    assert result.peak_compressive_stress == pytest.approx(abs(normal.max_compressive_stress))


def test_axial_bending_peak_compression_hand_calc(material, correlation):
    model = _i_model()
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    result = assess_section_crippling(model, material, correlation, load)
    normal = evaluate_normal_stress(load, model.section)
    assert result.peak_compressive_stress == pytest.approx(abs(normal.max_compressive_stress))
    assert result.peak_compression_location == normal.governing_compression_location


def test_reversing_moment_swaps_compression_side(material, correlation):
    model = _i_model()
    load_pos = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=6000.0)
    load_neg = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=-6000.0)
    result_pos = assess_section_crippling(model, material, correlation, load_pos)
    result_neg = assess_section_crippling(model, material, correlation, load_neg)
    assert result_pos.peak_compression_location != result_neg.peak_compression_location
    assert result_pos.peak_compression_location in ("top", "bottom")
    assert result_neg.peak_compression_location in ("top", "bottom")


def test_zero_compression_gives_na_peak_margin(material, correlation):
    model = _i_model()
    load = SectionLoad(axial_force=100e3, shear_force_y=0.0, bending_moment_z=0.0)  # pure tension
    result = assess_section_crippling(model, material, correlation, load)
    assert result.peak_compressive_stress == 0.0
    assert result.peak_compression_margin is None


def test_exact_peak_boundary_passes(material, correlation):
    model = _i_model()
    probe = assess_section_crippling(model, material, correlation, SectionLoad(0.0, 0.0, 0.0))
    sigma_crip = probe.crippling_stress
    # Solve for axial load giving peak compressive stress == sigma_crip exactly.
    N = -sigma_crip * model.section.area
    load = SectionLoad(axial_force=N, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_section_crippling(model, material, correlation, load)
    assert result.peak_compression_margin == pytest.approx(0.0, abs=1e-6)


def test_peak_boundary_above_below(material, correlation):
    model = _i_model()
    probe = assess_section_crippling(model, material, correlation, SectionLoad(0.0, 0.0, 0.0))
    sigma_crip = probe.crippling_stress
    A = model.section.area
    below = assess_section_crippling(
        model, material, correlation, SectionLoad(-0.5 * sigma_crip * A, 0.0, 0.0)
    )
    above = assess_section_crippling(
        model, material, correlation, SectionLoad(-1.5 * sigma_crip * A, 0.0, 0.0)
    )
    assert below.peak_compression_margin > 0
    assert above.peak_compression_margin < 0


# ---- governing mode (AF-AI) ----


def test_axial_average_governed_construction(material, correlation):
    # Pure axial compression (no bending) -> axial-average and peak
    # compression margins coincide (uniform stress); pick a load where
    # both apply and confirm axial_average is (trivially) the governing
    # candidate reported.
    model = _i_model()
    load = SectionLoad(axial_force=-50e3, shear_force_y=0.0, bending_moment_z=0.0)
    result = assess_section_crippling(model, material, correlation, load)
    assert result.axial_average_margin == pytest.approx(result.peak_compression_margin, rel=1e-6)
    # Tied margins -> fixed tie-break order (axial_average first) wins.
    assert result.governing_mode == "axial_average"


def test_peak_compression_governed_construction(material, correlation):
    # Bending-dominated case: peak compressive stress exceeds the mean
    # axial-implied stress, so peak_compression must govern (smaller margin).
    model = _i_model()
    load = SectionLoad(axial_force=-20e3, shear_force_y=0.0, bending_moment_z=6000.0)
    result = assess_section_crippling(model, material, correlation, load)
    assert result.peak_compression_margin < result.axial_average_margin
    assert result.governing_mode == "peak_compression"
    assert result.governing_margin == pytest.approx(result.peak_compression_margin)


def test_repeated_result_deterministic(material, correlation):
    model = _i_model()
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    r1 = assess_section_crippling(model, material, correlation, load)
    r2 = assess_section_crippling(model, material, correlation, load)
    assert r1.governing_mode == r2.governing_mode
    assert r1.governing_margin == pytest.approx(r2.governing_margin)
