"""Family comparison and final preliminary recommendation for Milestone 6 sizing.

Sizes every :data:`frame_stringer.sizing.FAMILIES` entry under identical
assumptions (material, load cases, panel length, member geometry, minimum
gauge, crippling correlation, search bounds/tolerance -- the "fairness
rule"), then recommends the lowest-mass *feasible* result. No weighted
score is invented; ties are broken by the fixed family order.
"""

from __future__ import annotations

from dataclasses import dataclass

from frame_stringer.column_buckling import MemberGeometry
from frame_stringer.crippling import CripplingCorrelation
from frame_stringer.load_cases import FrameStringerLoadCase
from frame_stringer.material import IsotropicMaterial
from frame_stringer.sizing import FAMILIES, SectionFamily, SectionSizingResult, size_section_family


@dataclass(frozen=True)
class StudyAssumptions:
    """The single, shared set of assumptions applied identically to every family.

    Attributes
    ----------
    material : IsotropicMaterial
    member : MemberGeometry
    load_cases : tuple[FrameStringerLoadCase, ...]
    correlation : CripplingCorrelation
    panel_length : float
        In m.
    t_min_gauge : float
        Illustrative minimum manufacturing gauge, in m -- not a
        certification/manufacturer requirement (see
        :mod:`frame_stringer.sizing`).
    t_min_search : float
    t_max_search : float
    tolerance : float
    """

    material: IsotropicMaterial
    member: MemberGeometry
    load_cases: tuple[FrameStringerLoadCase, ...]
    correlation: CripplingCorrelation
    panel_length: float
    t_min_gauge: float
    t_min_search: float = 0.75e-3
    t_max_search: float = 6.0e-3
    tolerance: float = 1e-6


def size_all_families(
    assumptions: StudyAssumptions, families: tuple[SectionFamily, ...] = FAMILIES
) -> tuple[SectionSizingResult, ...]:
    """Size every family under identical assumptions, in the fixed family order."""
    return tuple(
        size_section_family(
            family,
            assumptions.material,
            assumptions.member,
            assumptions.load_cases,
            assumptions.correlation,
            assumptions.panel_length,
            assumptions.t_min_gauge,
            assumptions.t_min_search,
            assumptions.t_max_search,
            assumptions.tolerance,
        )
        for family in families
    )


def recommend_family(results: tuple[SectionSizingResult, ...]) -> SectionSizingResult | None:
    """Recommend the lowest-mass-per-length *feasible* result.

    Feasible means ``status != "upper_bound_infeasible"``. Ties are broken
    by the order ``results`` was supplied in (i.e. the fixed family
    order). Returns ``None`` if every family is infeasible within the
    search bounds -- callers must handle this explicitly rather than
    receiving a misleading default.
    """
    feasible = [r for r in results if r.status != "upper_bound_infeasible"]
    if not feasible:
        return None
    best = feasible[0]
    for candidate in feasible[1:]:
        if candidate.mass_per_length < best.mass_per_length:
            best = candidate
    return best
