"""Named, explicit load cases for multi-load-case sizing.

A :class:`FrameStringerLoadCase` bundles a descriptive name with the same
three signed load components used throughout this package
(:class:`frame_stringer.loads.SectionLoad`), plus an explicit
``load_factor``. No safety/design factor is ever applied silently
elsewhere in the package -- it is always visible here, on the load case
itself, via :attr:`FrameStringerLoadCase.design_load`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from frame_stringer.loads import SectionLoad


@dataclass(frozen=True)
class FrameStringerLoadCase:
    """A named, explicit structural load case.

    Attributes
    ----------
    name : str
        Non-empty descriptive label (e.g. "maneuver bending").
    axial_force : float
        N, in N. Positive = tension, negative = compression (Milestone 1-2
        convention).
    shear_force_y : float
        V_y, in N. Signed.
    bending_moment_z : float
        M_z, in N*m. Signed.
    load_factor : float
        An explicit multiplier applied to all three load components via
        :attr:`design_load`. Must be finite and > 0. Defaults to 1.0 (no
        additional factor).
    """

    name: str
    axial_force: float
    shear_force_y: float
    bending_moment_z: float
    load_factor: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or self.name.strip() == "":
            raise ValueError("name must be a non-empty string")
        for field_name in ("axial_force", "shear_force_y", "bending_moment_z", "load_factor"):
            value = getattr(self, field_name)
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite, got {value!r}")
        if self.load_factor <= 0:
            raise ValueError(f"load_factor must be > 0, got {self.load_factor!r}")

    @property
    def design_load(self) -> SectionLoad:
        """The factored design load: every component times ``load_factor``."""
        return SectionLoad(
            axial_force=self.axial_force * self.load_factor,
            shear_force_y=self.shear_force_y * self.load_factor,
            bending_moment_z=self.bending_moment_z * self.load_factor,
        )


#: A small, explicitly illustrative set of structurally different
#: representative load cases (verified in the test suite to produce
#: genuinely different governing constraints across the sizing study's
#: thickness range -- not tuned to force any one failure mode).
CANONICAL_LOAD_CASES: tuple[FrameStringerLoadCase, ...] = (
    FrameStringerLoadCase("pressure/compression", axial_force=-80e3, shear_force_y=10e3, bending_moment_z=2e3),
    FrameStringerLoadCase("maneuver bending", axial_force=-40e3, shear_force_y=25e3, bending_moment_z=5e3),
    FrameStringerLoadCase("gust/shear", axial_force=-25e3, shear_force_y=40e3, bending_moment_z=2.5e3),
    FrameStringerLoadCase(
        "landing/ground combined", axial_force=-100e3, shear_force_y=20e3, bending_moment_z=4e3
    ),
)
