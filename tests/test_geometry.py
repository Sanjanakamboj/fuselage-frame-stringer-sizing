import math

import pytest

from frame_stringer.geometry import RectangularSection


def test_area_hand_calculation():
    # b=0.04 m, h=0.08 m -> A = 0.0032 m^2
    section = RectangularSection(width=0.04, height=0.08)
    assert section.area == pytest.approx(0.0032)


def test_moment_of_inertia_hand_calculation():
    # I_z = b*h^3/12 = 0.04*0.08^3/12 = 1.706667e-6 m^4
    section = RectangularSection(width=0.04, height=0.08)
    expected = 0.04 * 0.08**3 / 12.0
    assert section.moment_of_inertia_z == pytest.approx(expected)
    assert section.moment_of_inertia_z == pytest.approx(1.706667e-6, rel=1e-4)


def test_section_modulus_hand_calculation():
    # S_z = I_z / (h/2)
    section = RectangularSection(width=0.04, height=0.08)
    expected = (0.04 * 0.08**3 / 12.0) / (0.08 / 2.0)
    assert section.section_modulus_z == pytest.approx(expected)


def test_centroid_is_zero():
    section = RectangularSection(width=0.04, height=0.08)
    assert section.centroid_y == 0.0


@pytest.mark.parametrize(
    "width,height",
    [(0.0, 0.08), (-0.01, 0.08), (0.04, 0.0), (0.04, -0.08)],
)
def test_positive_dimensions_required(width, height):
    with pytest.raises(ValueError):
        RectangularSection(width=width, height=height)


@pytest.mark.parametrize(
    "width,height",
    [(math.nan, 0.08), (0.04, math.nan), (math.inf, 0.08), (0.04, -math.inf)],
)
def test_non_finite_rejected(width, height):
    with pytest.raises(ValueError):
        RectangularSection(width=width, height=height)


def test_extreme_fiber_coordinates():
    section = RectangularSection(width=0.04, height=0.08)
    assert section.y_top == pytest.approx(0.04)
    assert section.y_bottom == pytest.approx(-0.04)
