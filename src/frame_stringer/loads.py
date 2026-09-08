"""Section load representation.

A single load case applied at a beam cross-section, expressed in the local
member axes documented in :mod:`frame_stringer`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SectionLoad:
    """A section-level load case.

    Attributes
    ----------
    axial_force : float
        N, in N. Positive = tension, negative = compression. May be zero.
    shear_force_y : float
        V_y, in N. Signed; may be zero.
    bending_moment_z : float
        M_z, in N*m. Signed; may be zero.
    """

    axial_force: float
    shear_force_y: float
    bending_moment_z: float

    def __post_init__(self) -> None:
        for field_name in ("axial_force", "shear_force_y", "bending_moment_z"):
            value = getattr(self, field_name)
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite, got {value!r}")
