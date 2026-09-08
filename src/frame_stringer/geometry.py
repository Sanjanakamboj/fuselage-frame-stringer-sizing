"""Cross-section geometry.

Milestone 1 deliberately uses a simple rectangular section as the verified
mechanics baseline. Every derived property below can be independently
hand-checked. Realistic frame/stringer cross-sections (I, hat, Z, etc.) are
out of scope for this milestone.

Section coordinate convention: the section is symmetric about y = 0, spanning
-h/2 <= y <= +h/2, with centroid y_bar = 0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RectangularSection:
    """A solid rectangular beam cross-section.

    Attributes
    ----------
    width : float
        Section width b, in m (dimension along z). Must be finite and > 0.
    height : float
        Section height h, in m (dimension along y). Must be finite and > 0.
    """

    width: float
    height: float

    def __post_init__(self) -> None:
        for field_name in ("width", "height"):
            value = getattr(self, field_name)
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite, got {value!r}")
            if value <= 0:
                raise ValueError(f"{field_name} must be > 0, got {value!r}")

    @property
    def area(self) -> float:
        """Cross-sectional area A = b*h, in m^2."""
        return self.width * self.height

    @property
    def centroid_y(self) -> float:
        """Centroid y-coordinate, in m. Zero by symmetry."""
        return 0.0

    @property
    def moment_of_inertia_z(self) -> float:
        """Second moment of area about the z-axis, I_z = b*h^3/12, in m^4."""
        return self.width * self.height**3 / 12.0

    @property
    def section_modulus_z(self) -> float:
        """Elastic section modulus S_z = I_z / (h/2), in m^3."""
        return self.moment_of_inertia_z / (self.height / 2.0)

    @property
    def y_top(self) -> float:
        """y-coordinate of the top extreme fiber, +h/2."""
        return self.height / 2.0

    @property
    def y_bottom(self) -> float:
        """y-coordinate of the bottom extreme fiber, -h/2."""
        return -self.height / 2.0
