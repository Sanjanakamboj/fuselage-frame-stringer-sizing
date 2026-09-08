import pytest

from frame_stringer.geometry import RectangularSection
from frame_stringer.section_properties import (
    area,
    centroid,
    extreme_fibers,
    moment_of_inertia_z,
    section_modulus_z,
)


@pytest.fixture
def section():
    return RectangularSection(width=0.04, height=0.08)


def test_area_matches_geometry(section):
    assert area(section) == pytest.approx(section.area)


def test_centroid_matches_geometry(section):
    assert centroid(section) == 0.0


def test_moment_of_inertia_matches_geometry(section):
    assert moment_of_inertia_z(section) == pytest.approx(section.moment_of_inertia_z)


def test_section_modulus_matches_geometry(section):
    assert section_modulus_z(section) == pytest.approx(section.section_modulus_z)


def test_extreme_fibers(section):
    top, bottom = extreme_fibers(section)
    assert top == pytest.approx(0.04)
    assert bottom == pytest.approx(-0.04)
