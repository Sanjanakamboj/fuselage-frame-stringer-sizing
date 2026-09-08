"""Elastic von Mises strength screening for built-up sections.

Reuses the Milestone 1 von Mises equation and yield-margin convention
exactly (:func:`frame_stringer.strength.von_mises_stress`,
:func:`frame_stringer.strength.yield_margin`) -- no new failure criterion is
introduced.
"""

from __future__ import annotations

from dataclasses import dataclass

from frame_stringer.built_up_geometry import BuiltUpSection
from frame_stringer.built_up_stress import critical_locations, evaluate_combined_stress
from frame_stringer.loads import SectionLoad
from frame_stringer.material import IsotropicMaterial
from frame_stringer.strength import von_mises_stress, yield_margin


@dataclass(frozen=True)
class BuiltUpStrengthPoint:
    """Strength evaluation at a single labeled built-up-section point.

    Attributes
    ----------
    label : str
        Descriptive location label (e.g. "top_extreme", "boundary_0_below").
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

    label: str
    y: float
    sigma_x: float
    tau_xy: float
    sigma_vm: float
    margin: float | None
    passes: bool


@dataclass(frozen=True)
class BuiltUpStrengthResult:
    """Strength assessment across all critical points of a built-up section.

    Attributes
    ----------
    points : tuple[BuiltUpStrengthPoint, ...]
        All evaluated points, in a deterministic order (see
        :func:`frame_stringer.built_up_stress.critical_locations`).
    governing_location : str
        Label of the point with the highest sigma_vm. Deterministic
        tie-break: the first point (in the fixed, position-based
        ``points`` order) achieving the maximum sigma_vm wins.
    governing_sigma_vm : float
        The governing (maximum) sigma_vm, in Pa.
    min_margin : float | None
        The minimum yield margin among all points (``None`` only if every
        point is at zero stress).
    passes : bool
        True if every point passes (sigma_vm <= yield_strength).
    """

    points: tuple[BuiltUpStrengthPoint, ...]
    governing_location: str
    governing_sigma_vm: float
    min_margin: float | None
    passes: bool


def assess_builtup_strength(
    load: SectionLoad, section: BuiltUpSection, material: IsotropicMaterial
) -> BuiltUpStrengthResult:
    """Evaluate combined stress and elastic von Mises margin at all critical points.

    The governing point is determined by comparing computed sigma_vm at
    every critical location -- it is never assumed. The set of critical
    locations depends only on section geometry (via
    :func:`~frame_stringer.built_up_stress.critical_locations`), not on the
    order in which components were supplied to the section, so the result
    is invariant to component order.
    """
    points: list[BuiltUpStrengthPoint] = []
    for label, y in critical_locations(section):
        state = evaluate_combined_stress(y, load, section)
        sigma_vm = von_mises_stress(state.sigma_x, state.tau_xy)
        margin = yield_margin(sigma_vm, material.yield_strength)
        passes = sigma_vm <= material.yield_strength
        points.append(
            BuiltUpStrengthPoint(
                label=label,
                y=y,
                sigma_x=state.sigma_x,
                tau_xy=state.tau_xy,
                sigma_vm=sigma_vm,
                margin=margin,
                passes=passes,
            )
        )

    governing = points[0]
    for point in points[1:]:
        if point.sigma_vm > governing.sigma_vm:
            governing = point

    margins = [p.margin for p in points if p.margin is not None]
    min_margin = min(margins) if margins else None

    overall_passes = all(p.passes for p in points)

    return BuiltUpStrengthResult(
        points=tuple(points),
        governing_location=governing.label,
        governing_sigma_vm=governing.sigma_vm,
        min_margin=min_margin,
        passes=overall_passes,
    )


@dataclass(frozen=True)
class BendingYieldResult:
    """Pure-bending first-yield capacity for a (possibly asymmetric) section.

    Attributes
    ----------
    moment_yield_top : float
        Bending moment magnitude at which the top extreme fiber first
        reaches yield_strength, sigma_y * S_top, in N*m.
    moment_yield_bottom : float
        Bending moment magnitude at which the bottom extreme fiber first
        reaches yield_strength, sigma_y * S_bottom, in N*m.
    moment_yield : float
        First-yield bending moment magnitude, min(moment_yield_top,
        moment_yield_bottom), in N*m.
    governing_side : str
        Which side ("top" or "bottom") reaches yield first.
    """

    moment_yield_top: float
    moment_yield_bottom: float
    moment_yield: float
    governing_side: str


def bending_yield_capacity(
    section: BuiltUpSection, material: IsotropicMaterial
) -> BendingYieldResult:
    """Pure-bending first-yield moment for a built-up section.

    For a symmetric section (S_top == S_bottom, e.g. the I- and Z-section
    factories with equal flanges) both sides yield at the same moment. For
    an asymmetric section (e.g. the hat-section factory), the two sides
    are not assumed equal -- both are computed independently and the
    smaller governs.
    """
    M_top = material.yield_strength * section.section_modulus_top
    M_bottom = material.yield_strength * section.section_modulus_bottom
    if M_top <= M_bottom:
        return BendingYieldResult(
            moment_yield_top=M_top,
            moment_yield_bottom=M_bottom,
            moment_yield=M_top,
            governing_side="top",
        )
    return BendingYieldResult(
        moment_yield_top=M_top,
        moment_yield_bottom=M_bottom,
        moment_yield=M_bottom,
        governing_side="bottom",
    )
