"""Section-property API.

Thin, explicit functions on top of a section geometry object (currently
:class:`frame_stringer.geometry.RectangularSection`). Keeping these as
free functions -- rather than only relying on the geometry class's
properties -- gives a stable API surface that later, more complex section
types (I, hat, Z) can plug into without changing calling code.
"""

from __future__ import annotations

from frame_stringer.geometry import RectangularSection


def area(section: RectangularSection) -> float:
    """Cross-sectional area, in m^2."""
    return section.area


def centroid(section: RectangularSection) -> float:
    """Centroid y-coordinate, in m (0.0 for a symmetric rectangle)."""
    return section.centroid_y


def moment_of_inertia_z(section: RectangularSection) -> float:
    """Second moment of area about z, I_z, in m^4."""
    return section.moment_of_inertia_z


def section_modulus_z(section: RectangularSection) -> float:
    """Elastic section modulus about z, S_z = I_z/(h/2), in m^3."""
    return section.section_modulus_z


def extreme_fibers(section: RectangularSection) -> tuple[float, float]:
    """Return (y_top, y_bottom) extreme-fiber coordinates, in m."""
    return section.y_top, section.y_bottom
