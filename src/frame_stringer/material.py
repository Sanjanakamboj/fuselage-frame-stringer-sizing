"""Isotropic material model.

Milestone 1 uses a single, simple, validated isotropic material record. The
values used in examples are illustrative only -- they are NOT certification
allowables or MMPDS values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class IsotropicMaterial:
    """A validated, immutable isotropic material definition.

    Attributes
    ----------
    name : str
        Non-empty descriptive label (e.g. "Illustrative Al 2024-T3-like").
    elastic_modulus : float
        Young's modulus E, in Pa. Must be > 0.
    poisson_ratio : float
        Poisson's ratio nu. Must satisfy -1 < nu < 0.5.
    density : float
        Mass density rho, in kg/m^3. Must be > 0.
    yield_strength : float
        Uniaxial yield strength, in Pa. Must be > 0.
    """

    name: str
    elastic_modulus: float
    poisson_ratio: float
    density: float
    yield_strength: float

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or self.name.strip() == "":
            raise ValueError("name must be a non-empty string")

        for field_name in (
            "elastic_modulus",
            "poisson_ratio",
            "density",
            "yield_strength",
        ):
            value = getattr(self, field_name)
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite, got {value!r}")

        if self.elastic_modulus <= 0:
            raise ValueError(
                f"elastic_modulus must be > 0, got {self.elastic_modulus!r}"
            )
        if not (-1.0 < self.poisson_ratio < 0.5):
            raise ValueError(
                f"poisson_ratio must satisfy -1 < nu < 0.5, got {self.poisson_ratio!r}"
            )
        if self.density <= 0:
            raise ValueError(f"density must be > 0, got {self.density!r}")
        if self.yield_strength <= 0:
            raise ValueError(
                f"yield_strength must be > 0, got {self.yield_strength!r}"
            )
