import pytest

from frame_stringer.beam_column import assess_beam_column
from frame_stringer.built_up_strength import assess_builtup_strength
from frame_stringer.column_buckling import MemberGeometry
from frame_stringer.crippling import CripplingCorrelation, assess_section_crippling
from frame_stringer.local_buckling import assess_section_local_buckling, i_section_plate_elements
from frame_stringer.loads import SectionLoad
from frame_stringer.material import IsotropicMaterial
from frame_stringer.sections import i_section
from frame_stringer.structural_status import assess_structural_status


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
    return CripplingCorrelation(alpha=1.2, exponent=0.6, label="Illustrative", source_note="illustrative")


@pytest.fixture
def model():
    return i_section_plate_elements(
        flange_width=0.06, overall_height=0.10, flange_thickness=0.0095, web_thickness=0.006, panel_length=0.30
    )


def _assess_all(model, material, correlation, member, load):
    yield_result = assess_builtup_strength(load, model.section, material)
    lb_result = assess_section_local_buckling(model, load, material)
    bc_result = assess_beam_column(member, model.section, material, load)
    crip_result = assess_section_crippling(model, material, correlation, load)
    return yield_result, lb_result, bc_result, crip_result


def test_all_safe_gives_overall_pass(material, correlation, model):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    yield_r, lb_r, bc_r, crip_r = _assess_all(model, material, correlation, member, load)
    status = assess_structural_status(yield_r, lb_r, bc_r, crip_r)
    assert status.overall_preliminary_pass is True


def test_yield_only_failure_gives_overall_fail(material, correlation, model):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    # Huge moment fails yield while other checks (at this length/geometry)
    # remain comfortable.
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=20_000.0)
    yield_r, lb_r, bc_r, crip_r = _assess_all(model, material, correlation, member, load)
    assert yield_r.passes is False
    status = assess_structural_status(yield_r, lb_r, bc_r, crip_r)
    assert status.overall_preliminary_pass is False
    assert status.yield_pass is False


def test_local_buckling_only_failure_gives_overall_fail(material, correlation):
    # Thin wide flange: fails local buckling while other checks pass.
    thin_model = i_section_plate_elements(
        flange_width=0.20, overall_height=0.10, flange_thickness=0.001, web_thickness=0.003, panel_length=1.0
    )
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=800.0)
    yield_r, lb_r, bc_r, crip_r = _assess_all(thin_model, material, correlation, member, load)
    assert yield_r.passes is True
    assert lb_r.passes is False
    status = assess_structural_status(yield_r, lb_r, bc_r, crip_r)
    assert status.overall_preliminary_pass is False
    assert status.local_buckling_pass is False


def test_euler_only_failure_gives_overall_fail(material, correlation, model):
    member = MemberGeometry(length=6.0, effective_length_factor=2.0)  # very slender
    load = SectionLoad(axial_force=-50e3, shear_force_y=0.0, bending_moment_z=0.0)
    yield_r, lb_r, bc_r, crip_r = _assess_all(model, material, correlation, member, load)
    assert bc_r.euler_passes is False
    status = assess_structural_status(yield_r, lb_r, bc_r, crip_r)
    assert status.overall_preliminary_pass is False
    assert status.euler_pass is False


def test_amplified_yield_only_failure_gives_overall_fail(material, correlation):
    section_thin = i_section(flange_width=0.06, overall_height=0.10, flange_thickness=0.006, web_thickness=0.004)
    thin_model = i_section_plate_elements(
        flange_width=0.06, overall_height=0.10, flange_thickness=0.006, web_thickness=0.004, panel_length=0.30
    )
    member = MemberGeometry(length=3.0, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=0.0, bending_moment_z=4e3)
    yield_r, lb_r, bc_r, crip_r = _assess_all(thin_model, material, correlation, member, load)
    assert yield_r.passes is True
    assert bc_r.amplified_yield_passes is False
    status = assess_structural_status(yield_r, lb_r, bc_r, crip_r)
    assert status.overall_preliminary_pass is False
    assert status.amplified_yield_pass is False


def test_crippling_only_failure_gives_overall_fail(material, model):
    # Use a correlation forcing crippling far below all other margins.
    weak_corr = CripplingCorrelation(alpha=0.05, exponent=0.6, label="weak", source_note="illustrative-weak")
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    yield_r = assess_builtup_strength(load, model.section, material)
    lb_r = assess_section_local_buckling(model, load, material)
    bc_r = assess_beam_column(member, model.section, material, load)
    crip_r = assess_section_crippling(model, material, weak_corr, load)
    assert yield_r.passes and lb_r.passes and bc_r.overall_pass
    assert crip_r.passes is False
    status = assess_structural_status(yield_r, lb_r, bc_r, crip_r)
    assert status.overall_preliminary_pass is False
    assert status.crippling_pass is False


def test_governing_check_is_minimum_applicable_margin(material, correlation, model):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    yield_r, lb_r, bc_r, crip_r = _assess_all(model, material, correlation, member, load)
    status = assess_structural_status(yield_r, lb_r, bc_r, crip_r)

    margins = {
        "yield": status.yield_margin,
        "local_buckling": status.local_buckling_margin,
        "euler": status.euler_margin,
        "amplified_yield": status.amplified_yield_margin,
        "crippling": status.crippling_margin,
    }
    applicable = {k: v for k, v in margins.items() if v is not None}
    expected_check = min(applicable, key=lambda k: applicable[k])
    assert status.governing_check == expected_check
    assert status.governing_margin == pytest.approx(applicable[expected_check])


def test_no_synthetic_blended_margin_exposed(material, correlation, model):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    yield_r, lb_r, bc_r, crip_r = _assess_all(model, material, correlation, member, load)
    status = assess_structural_status(yield_r, lb_r, bc_r, crip_r)
    # governing_margin must exactly equal one of the independently
    # computed margins -- never an average or any other blended value.
    independent_margins = [
        status.yield_margin,
        status.local_buckling_margin,
        status.euler_margin,
        status.amplified_yield_margin,
        status.crippling_margin,
    ]
    assert any(
        m is not None and status.governing_margin == pytest.approx(m) for m in independent_margins
    )


def test_crippling_none_is_handled_gracefully(material, model):
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    yield_r = assess_builtup_strength(load, model.section, material)
    lb_r = assess_section_local_buckling(model, load, material)
    bc_r = assess_beam_column(member, model.section, material, load)
    status = assess_structural_status(yield_r, lb_r, bc_r, crippling_result=None)
    assert status.crippling_pass is None
    assert status.crippling_margin is None
    # Overall pass must not be penalized by an inapplicable check.
    assert status.overall_preliminary_pass == (
        yield_r.passes and lb_r.passes and bc_r.euler_passes and bc_r.amplified_yield_passes
    )
