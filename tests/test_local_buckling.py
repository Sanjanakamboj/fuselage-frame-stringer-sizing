import pytest

from frame_stringer.built_up_stress import normal_stress, shear_stress
from frame_stringer.local_buckling import (
    assess_section_local_buckling,
    combined_elastic_status,
    extract_plate_demand,
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


PANEL_LENGTH = 0.30


def _i_model():
    return i_section_plate_elements(
        flange_width=0.06,
        overall_height=0.10,
        flange_thickness=0.0095,
        web_thickness=0.006,
        panel_length=PANEL_LENGTH,
    )


def _z_model():
    return z_section_plate_elements(
        web_height=0.08,
        web_thickness=0.0058,
        flange_width=0.05,
        flange_thickness=0.011,
        panel_length=PANEL_LENGTH,
    )


def _hat_model():
    return hat_section_plate_elements(
        crown_width=0.065,
        overall_height=0.07,
        wall_thickness=0.0068,
        flange_width=0.028,
        panel_length=PANEL_LENGTH,
    )


# ---- section mapping (AB-AG) ----


def test_i_section_expected_plate_names():
    model = _i_model()
    names = {m.plate.name for m in model.mappings}
    assert names == {"web", "top_flange_outstand", "bottom_flange_outstand"}
    assert len(model.mappings) == 3


def test_i_section_web_geometry_hand_calc():
    model = _i_model()
    web_mapping = next(m for m in model.mappings if m.plate.name == "web")
    h_web = 0.10 - 2 * 0.0095
    assert web_mapping.plate.width == pytest.approx(h_web)
    assert web_mapping.plate.thickness == pytest.approx(0.006)
    assert web_mapping.plate.boundary_condition == "internal"


def test_i_section_flange_outstand_width_hand_calc():
    model = _i_model()
    top = next(m for m in model.mappings if m.plate.name == "top_flange_outstand")
    expected_b_out = (0.06 - 0.006) / 2.0
    assert top.plate.width == pytest.approx(expected_b_out)
    assert top.plate.boundary_condition == "outstanding"


def test_z_section_mapping():
    model = _z_model()
    names = {m.plate.name for m in model.mappings}
    assert names == {"web", "top_flange_outstand", "bottom_flange_outstand"}
    web = next(m for m in model.mappings if m.plate.name == "web")
    assert web.plate.width == pytest.approx(0.08)
    top = next(m for m in model.mappings if m.plate.name == "top_flange_outstand")
    assert top.plate.width == pytest.approx(0.05)  # full flange width, not halved


def test_hat_section_mapping():
    model = _hat_model()
    names = {m.plate.name for m in model.mappings}
    assert names == {"web_left", "web_right", "flange_left", "flange_right", "crown"}
    assert len(model.mappings) == 5
    crown = next(m for m in model.mappings if m.plate.name == "crown")
    expected_crown_width = 0.065 - 2 * 0.0068
    assert crown.plate.width == pytest.approx(expected_crown_width)


def test_panel_length_propagated_exactly():
    model = _i_model()
    for mapping in model.mappings:
        assert mapping.plate.length == pytest.approx(PANEL_LENGTH)


# ---- stress extraction (AH-AM) ----


def test_tension_only_plate_has_zero_compression_demand(material):
    model = _i_model()
    bottom = next(m for m in model.mappings if m.plate.name == "bottom_flange_outstand")
    # Positive moment puts the bottom flange (y < 0) into tension for this
    # symmetric section, with no axial load (sigma_bending = -M*y/I).
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=6000.0)
    sigma_x_demand, _ = extract_plate_demand(model.section, load, bottom)
    assert sigma_x_demand >= 0.0  # tension or zero, never treated as compression


def test_compression_side_flange_gets_extreme_stress(material):
    model = _i_model()
    top = next(m for m in model.mappings if m.plate.name == "top_flange_outstand")
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=6000.0)
    sigma_x_demand, _ = extract_plate_demand(model.section, load, top)
    expected = min(
        normal_stress(top.y_top, load, model.section),
        normal_stress(top.y_bottom, load, model.section),
    )
    assert sigma_x_demand == pytest.approx(expected)
    assert sigma_x_demand < 0  # compression


def test_reversing_moment_swaps_top_bottom_compression(material):
    model = _i_model()
    top = next(m for m in model.mappings if m.plate.name == "top_flange_outstand")
    bottom = next(m for m in model.mappings if m.plate.name == "bottom_flange_outstand")

    load_pos = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=6000.0)
    load_neg = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=-6000.0)

    top_sigma_pos, _ = extract_plate_demand(model.section, load_pos, top)
    bottom_sigma_pos, _ = extract_plate_demand(model.section, load_pos, bottom)
    top_sigma_neg, _ = extract_plate_demand(model.section, load_neg, top)
    bottom_sigma_neg, _ = extract_plate_demand(model.section, load_neg, bottom)

    assert top_sigma_pos < 0 and bottom_sigma_pos > 0  # top compression, bottom tension
    assert top_sigma_neg > 0 and bottom_sigma_neg < 0  # reversed


def test_web_shear_demand_matches_builtup_stress(material):
    model = _i_model()
    web = next(m for m in model.mappings if m.plate.name == "web")
    load = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=0.0)
    _, tau_demand = extract_plate_demand(model.section, load, web)
    tau_at_na = abs(shear_stress(0.0, load, model.section))
    # The neutral axis lies within the (symmetric) web and is where beam
    # shear peaks -- the extracted demand should be close to it (>=,
    # since the sampling grid may not land exactly on y=0).
    assert tau_demand == pytest.approx(tau_at_na, rel=1e-3)


def test_load_scaling_is_linear(material):
    model = _i_model()
    web = next(m for m in model.mappings if m.plate.name == "web")
    load1 = SectionLoad(axial_force=-40e3, shear_force_y=10e3, bending_moment_z=2000.0)
    load2 = SectionLoad(axial_force=-80e3, shear_force_y=20e3, bending_moment_z=4000.0)
    sigma1, tau1 = extract_plate_demand(model.section, load1, web)
    sigma2, tau2 = extract_plate_demand(model.section, load2, web)
    assert sigma2 == pytest.approx(2.0 * sigma1)
    assert tau2 == pytest.approx(2.0 * tau1)


def test_stress_extraction_component_order_independence(material):
    from frame_stringer.built_up_geometry import BuiltUpSection

    model = _i_model()
    reordered_section = BuiltUpSection(tuple(reversed(model.section.components)))
    web = next(m for m in model.mappings if m.plate.name == "web")
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    sigma_a, tau_a = extract_plate_demand(model.section, load, web)
    sigma_b, tau_b = extract_plate_demand(reordered_section, load, web)
    assert sigma_a == pytest.approx(sigma_b)
    assert tau_a == pytest.approx(tau_b)


# ---- section assessment (AN-AV) ----


def test_all_safe_construction_passes(material):
    model = _i_model()
    load = SectionLoad(axial_force=-10e3, shear_force_y=2e3, bending_moment_z=200.0)
    result = assess_section_local_buckling(model, load, material)
    assert result.passes is True


def test_compression_buckling_failure_construction(material):
    # A thin, wide, long outstanding flange under heavy bending compression.
    model = i_section_plate_elements(
        flange_width=0.20,
        overall_height=0.10,
        flange_thickness=0.001,
        web_thickness=0.003,
        panel_length=1.0,
    )
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=20000.0)
    result = assess_section_local_buckling(model, load, material)
    assert result.passes is False
    assert result.governing_mode in ("compression", "interaction")


def test_shear_buckling_failure_construction(material):
    # A thin, deep, long web under heavy shear, negligible bending.
    model = i_section_plate_elements(
        flange_width=0.06,
        overall_height=0.30,
        flange_thickness=0.006,
        web_thickness=0.0015,
        panel_length=1.0,
    )
    load = SectionLoad(axial_force=0.0, shear_force_y=200e3, bending_moment_z=0.0)
    result = assess_section_local_buckling(model, load, material)
    assert result.passes is False
    assert result.governing_mode in ("shear", "interaction")


def test_interaction_governed_construction(material):
    model = i_section_plate_elements(
        flange_width=0.06,
        overall_height=0.20,
        flange_thickness=0.005,
        web_thickness=0.0025,
        panel_length=0.8,
    )
    load = SectionLoad(axial_force=-20e3, shear_force_y=60e3, bending_moment_z=8000.0)
    result = assess_section_local_buckling(model, load, material)
    web_result = next(p for p in result.plates if p.plate_name == "web")
    assert web_result.compression_margin is not None
    assert web_result.shear_margin is not None


def test_deterministic_governing_plate(material):
    model = _i_model()
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    result1 = assess_section_local_buckling(model, load, material)
    result2 = assess_section_local_buckling(model, load, material)
    assert result1.governing_plate == result2.governing_plate


def test_repeated_assessment_deterministic(material):
    model = _hat_model()
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    r1 = assess_section_local_buckling(model, load, material)
    r2 = assess_section_local_buckling(model, load, material)
    assert r1.governing_plate == r2.governing_plate
    assert r1.min_margin == pytest.approx(r2.min_margin) if r1.min_margin is not None else r2.min_margin is None


def test_yield_may_pass_while_buckling_fails(material):
    from frame_stringer.built_up_strength import assess_builtup_strength

    model = i_section_plate_elements(
        flange_width=0.20,
        overall_height=0.10,
        flange_thickness=0.001,
        web_thickness=0.003,
        panel_length=1.0,
    )
    # Small enough moment that yield passes comfortably, but the thin wide
    # flange still buckles locally at a much lower stress than yield.
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=800.0)
    yield_result = assess_builtup_strength(load, model.section, material)
    buckling_result = assess_section_local_buckling(model, load, material)
    assert yield_result.passes is True
    assert buckling_result.passes is False

    status = combined_elastic_status(yield_result, buckling_result)
    assert status.yield_passes is True
    assert status.local_buckling_passes is False
    assert status.overall_preliminary_pass is False


def test_local_buckling_may_pass_while_yield_fails(material):
    from frame_stringer.built_up_strength import assess_builtup_strength

    model = _i_model()
    # A moment large enough to fail yield, while the (relatively stocky)
    # plates in this section remain elastically stable in local buckling.
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=20_000.0)
    yield_result = assess_builtup_strength(load, model.section, material)
    buckling_result = assess_section_local_buckling(model, load, material)
    assert yield_result.passes is False
    assert buckling_result.passes is True

    status = combined_elastic_status(yield_result, buckling_result)
    assert status.overall_preliminary_pass is False


def test_overall_preliminary_status_requires_both(material):
    from frame_stringer.built_up_strength import assess_builtup_strength

    model = _i_model()
    load = SectionLoad(axial_force=-10e3, shear_force_y=2e3, bending_moment_z=200.0)
    yield_result = assess_builtup_strength(load, model.section, material)
    buckling_result = assess_section_local_buckling(model, load, material)
    status = combined_elastic_status(yield_result, buckling_result)
    assert status.overall_preliminary_pass == (status.yield_passes and status.local_buckling_passes)
