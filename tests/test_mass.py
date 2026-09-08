import pytest

from frame_stringer.geometry import RectangularSection
from frame_stringer.mass import linear_mass, mass_for_length
from frame_stringer.material import IsotropicMaterial


@pytest.fixture
def section():
    return RectangularSection(width=0.04, height=0.08)


@pytest.fixture
def material():
    return IsotropicMaterial(
        name="Illustrative Al-like",
        elastic_modulus=70e9,
        poisson_ratio=0.33,
        density=2700.0,
        yield_strength=300e6,
    )


def test_linear_mass_hand_calc(section, material):
    expected = 2700.0 * section.area
    assert linear_mass(section, material) == pytest.approx(expected)


def test_density_doubling_doubles_mass(section, material):
    material2 = IsotropicMaterial(
        name=material.name,
        elastic_modulus=material.elastic_modulus,
        poisson_ratio=material.poisson_ratio,
        density=2.0 * material.density,
        yield_strength=material.yield_strength,
    )
    assert linear_mass(section, material2) == pytest.approx(
        2.0 * linear_mass(section, material)
    )


def test_area_doubling_doubles_mass(material):
    section1 = RectangularSection(width=0.04, height=0.08)
    section2 = RectangularSection(width=0.08, height=0.08)  # double area
    assert linear_mass(section2, material) == pytest.approx(
        2.0 * linear_mass(section1, material)
    )


def test_total_mass_scales_linearly_with_length(section, material):
    m1 = mass_for_length(section, material, 1.0)
    m3 = mass_for_length(section, material, 3.0)
    assert m3 == pytest.approx(3.0 * m1)


@pytest.mark.parametrize("bad_length", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_length_rejected(section, material, bad_length):
    with pytest.raises(ValueError):
        mass_for_length(section, material, bad_length)
