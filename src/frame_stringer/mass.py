"""Section mass per unit length.

No skin, fittings, fasteners, or joints are included -- this is the bare
section material mass only.
"""

from __future__ import annotations

import math

from frame_stringer.geometry import RectangularSection
from frame_stringer.material import IsotropicMaterial


def linear_mass(section: RectangularSection, material: IsotropicMaterial) -> float:
    """Mass per unit length, m' = rho * A, in kg/m."""
    return material.density * section.area


def mass_for_length(
    section: RectangularSection, material: IsotropicMaterial, length: float
) -> float:
    """Total mass for a given member length, rho * A * L, in kg.

    Raises
    ------
    ValueError
        If length is not finite or not > 0.
    """
    if not math.isfinite(length):
        raise ValueError(f"length must be finite, got {length!r}")
    if length <= 0:
        raise ValueError(f"length must be > 0, got {length!r}")
    return linear_mass(section, material) * length
