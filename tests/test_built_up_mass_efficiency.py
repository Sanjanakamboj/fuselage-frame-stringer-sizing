import pytest

from frame_stringer.built_up_geometry import BuiltUpSection, RectangularComponent
from frame_stringer.built_up_strength import bending_yield_capacity
from frame_stringer.geometry import RectangularSection
from frame_stringer.mass import linear_mass
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


def test_builtup_mass_equals_rho_times_area(material):
    section = i_section(
        flange_width=0.05, overall_height=0.10, flange_thickness=0.005, web_thickness=0.004
    )
    assert linear_mass(section, material) == pytest.approx(material.density * section.area)


def test_builtup_mass_density_scaling(material):
    section = i_section(
        flange_width=0.05, overall_height=0.10, flange_thickness=0.005, web_thickness=0.004
    )
    material2 = IsotropicMaterial(
        name=material.name,
        elastic_modulus=material.elastic_modulus,
        poisson_ratio=material.poisson_ratio,
        density=2.0 * material.density,
        yield_strength=material.yield_strength,
    )
    assert linear_mass(section, material2) == pytest.approx(2.0 * linear_mass(section, material))


def test_equal_area_i_section_beats_compact_rectangle_in_Iz(material):
    i = i_section(
        flange_width=0.05, overall_height=0.10, flange_thickness=0.006, web_thickness=0.004
    )
    # Build a rectangle with (approximately) the same area as the I-section.
    target_area = i.area
    h = 0.06
    b = target_area / h
    rect = RectangularSection(width=b, height=h)

    assert rect.area == pytest.approx(i.area, rel=1e-9)
    assert i.moment_of_inertia_z > rect.moment_of_inertia_z


def test_normalized_Iz_over_A_comparison(material):
    i = i_section(
        flange_width=0.05, overall_height=0.10, flange_thickness=0.006, web_thickness=0.004
    )
    target_area = i.area
    h = 0.06
    b = target_area / h
    rect = RectangularSection(width=b, height=h)

    i_efficiency = i.moment_of_inertia_z / i.area
    rect_efficiency = rect.moment_of_inertia_z / rect.area
    assert i_efficiency > rect_efficiency


def test_normalized_min_section_modulus_over_A_comparison(material):
    i = i_section(
        flange_width=0.05, overall_height=0.10, flange_thickness=0.006, web_thickness=0.004
    )
    target_area = i.area
    h = 0.06
    b = target_area / h
    rect = RectangularSection(width=b, height=h)

    i_min_S = min(i.S_top, i.S_bottom)
    rect_min_S = rect.section_modulus_z  # symmetric: S_top == S_bottom

    assert (i_min_S / i.area) > (rect_min_S / rect.area)


def test_first_yield_moment_follows_minimum_section_modulus(material):
    top = RectangularComponent(width=0.01, height=0.01, centroid_y=0.10, label="top")
    web = RectangularComponent(width=0.005, height=0.08, centroid_y=0.05, label="web")
    bottom = RectangularComponent(width=0.05, height=0.01, centroid_y=0.005, label="bottom")
    section = BuiltUpSection((top, web, bottom))

    result = bending_yield_capacity(section, material)
    expected = material.yield_strength * min(section.S_top, section.S_bottom)
    assert result.moment_yield == pytest.approx(expected)
