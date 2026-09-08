"""Elastic von Mises yield screening and reference capacities.

This module implements a first-order elastic yield screen -- it is
explicitly NOT a certification margin. Only sigma_x and tau_xy (plane
stress) are considered, consistent with the elementary beam-stress fields
computed in :mod:`frame_stringer.stress`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from frame_stringer.geometry import RectangularSection
from frame_stringer.loads import SectionLoad
from frame_stringer.material import IsotropicMaterial
from frame_stringer.stress import CombinedStressState, evaluate_combined_stress

_SQRT3 = math.sqrt(3.0)


def von_mises_stress(sigma_x: float, tau_xy: float) -> float:
    """Plane-stress von Mises equivalent stress, sqrt(sigma_x^2 + 3*tau_xy^2)."""
    return math.sqrt(sigma_x**2 + 3.0 * tau_xy**2)


def yield_margin(sigma_vm: float, yield_strength: float) -> float | None:
    """Elastic von Mises yield margin, MS = yield_strength/sigma_vm - 1.

    Convention: at sigma_vm == 0 the margin is undefined (no stress to
    compare against), and this function returns ``None`` rather than
    ``inf``. Callers that need a pass/fail decision at zero stress should
    treat ``None`` as an automatic PASS (there is no stress to fail
    against).
    """
    if sigma_vm == 0.0:
        return None
    return yield_strength / sigma_vm - 1.0


@dataclass(frozen=True)
class SectionStrengthPoint:
    """Strength evaluation at a single section point.

    Attributes
    ----------
    location : str
        Label for the evaluation point ("top", "neutral_axis", "bottom").
    y : float
        Coordinate, in m.
    sigma_x : float
        Signed normal stress, in Pa.
    tau_xy : float
        Signed transverse shear stress, in Pa.
    sigma_vm : float
        Von Mises equivalent stress, in Pa (>= 0).
    margin : float | None
        Elastic von Mises yield margin (``None`` at zero stress).
    passes : bool
        True if sigma_vm <= yield_strength (boundary case passes).
    """

    location: str
    y: float
    sigma_x: float
    tau_xy: float
    sigma_vm: float
    margin: float | None
    passes: bool


def _evaluate_point(
    location: str,
    y: float,
    load: SectionLoad,
    section: RectangularSection,
    material: IsotropicMaterial,
) -> SectionStrengthPoint:
    state: CombinedStressState = evaluate_combined_stress(y, load, section)
    sigma_vm = von_mises_stress(state.sigma_x, state.tau_xy)
    margin = yield_margin(sigma_vm, material.yield_strength)
    passes = sigma_vm <= material.yield_strength
    return SectionStrengthPoint(
        location=location,
        y=y,
        sigma_x=state.sigma_x,
        tau_xy=state.tau_xy,
        sigma_vm=sigma_vm,
        margin=margin,
        passes=passes,
    )


@dataclass(frozen=True)
class SectionStrengthResult:
    """Section strength assessment across the top, neutral-axis, and bottom points.

    Attributes
    ----------
    top : SectionStrengthPoint
    neutral_axis : SectionStrengthPoint
    bottom : SectionStrengthPoint
    governing_location : str
        The location with the highest sigma_vm (deterministic tie-break
        order: top, then neutral_axis, then bottom).
    governing_sigma_vm : float
        The governing (maximum) sigma_vm, in Pa.
    min_margin : float | None
        The minimum yield margin among the three points (``None`` only if
        all three points are at zero stress).
    passes : bool
        True if all three points pass (sigma_vm <= yield_strength).
    """

    top: SectionStrengthPoint
    neutral_axis: SectionStrengthPoint
    bottom: SectionStrengthPoint
    governing_location: str
    governing_sigma_vm: float
    min_margin: float | None
    passes: bool


def assess_section_strength(
    load: SectionLoad, section: RectangularSection, material: IsotropicMaterial
) -> SectionStrengthResult:
    """Evaluate combined stress and elastic von Mises margin at three points.

    Points evaluated: top extreme fiber (y = +h/2), neutral axis (y = 0),
    and bottom extreme fiber (y = -h/2). The governing point is determined
    by comparing computed sigma_vm at all three -- it is never assumed.
    """
    points = [
        _evaluate_point("top", section.y_top, load, section, material),
        _evaluate_point("neutral_axis", 0.0, load, section, material),
        _evaluate_point("bottom", section.y_bottom, load, section, material),
    ]

    # Deterministic tie-break: iterate in a fixed order (top, neutral_axis,
    # bottom) and keep the first strictly-greatest sigma_vm.
    governing = points[0]
    for point in points[1:]:
        if point.sigma_vm > governing.sigma_vm:
            governing = point

    margins = [p.margin for p in points if p.margin is not None]
    min_margin = min(margins) if margins else None

    passes = all(p.passes for p in points)

    return SectionStrengthResult(
        top=points[0],
        neutral_axis=points[1],
        bottom=points[2],
        governing_location=governing.location,
        governing_sigma_vm=governing.sigma_vm,
        min_margin=min_margin,
        passes=passes,
    )


def axial_yield_load(section: RectangularSection, material: IsotropicMaterial) -> float:
    """Pure axial first-yield load, N_y = yield_strength * A, in N."""
    return material.yield_strength * section.area


def bending_yield_moment(
    section: RectangularSection, material: IsotropicMaterial
) -> float:
    """Pure bending first-yield moment, M_y = yield_strength * S_z, in N*m."""
    return material.yield_strength * section.section_modulus_z


def shear_yield_stress(material: IsotropicMaterial) -> float:
    """Von Mises pure-shear yield stress, tau_y = yield_strength / sqrt(3), in Pa."""
    return material.yield_strength / _SQRT3


def shear_yield_load(
    section: RectangularSection, material: IsotropicMaterial
) -> float:
    """Rectangular-section pure-shear first-yield load, V_yield = (2/3)*A*tau_y, in N.

    Derived from tau_max = 3*V/(2*A) = tau_y at first yield.
    """
    return (2.0 / 3.0) * section.area * shear_yield_stress(material)
