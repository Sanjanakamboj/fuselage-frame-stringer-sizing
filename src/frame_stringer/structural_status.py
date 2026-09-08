"""Top-level structural status: yield, local buckling, Euler, amplified yield, crippling.

This module integrates every independent screen built up over Milestones
1-5 into a single side-by-side report. **The individual checks are never
mathematically blended into one synthetic margin.** The "governing margin"
this module reports is simply the minimum of the independently computed
preliminary margins -- a reporting convenience, not a combined interaction
equation.
"""

from __future__ import annotations

from dataclasses import dataclass

from frame_stringer.beam_column import BeamColumnAssessment
from frame_stringer.crippling import CripplingAssessment
from frame_stringer.local_buckling import LocalBucklingAssessment

_TIE_BREAK_ORDER = ("yield", "local_buckling", "euler", "amplified_yield", "crippling")


@dataclass(frozen=True)
class StructuralStatus:
    """Side-by-side summary of every independent preliminary structural check.

    Attributes
    ----------
    yield_pass : bool
    yield_margin : float | None
    local_buckling_pass : bool
    local_buckling_margin : float | None
    euler_pass : bool
    euler_margin : float | None
    amplified_yield_pass : bool
    amplified_yield_margin : float | None
    crippling_pass : bool | None
        ``None`` if crippling is not applicable to this section (e.g. the
        Milestone 1 rectangle, for which the crippling correlation is not
        used -- see :mod:`frame_stringer.crippling`).
    crippling_margin : float | None
    overall_preliminary_pass : bool
        True only if every *applicable* check passes.
    governing_check : str
        The applicable check with the smallest margin: one of "yield",
        "local_buckling", "euler", "amplified_yield", "crippling".
        Deterministic tie-break: that fixed order decides among checks
        tied at the minimum margin.
    governing_margin : float | None
        **governing margin = minimum independently computed preliminary
        margin.** This is a reporting convenience, not a combined
        interaction equation -- the underlying checks remain fully
        independent and separately visible above.
    """

    yield_pass: bool
    yield_margin: float | None
    local_buckling_pass: bool
    local_buckling_margin: float | None
    euler_pass: bool
    euler_margin: float | None
    amplified_yield_pass: bool
    amplified_yield_margin: float | None
    crippling_pass: bool | None
    crippling_margin: float | None
    overall_preliminary_pass: bool
    governing_check: str
    governing_margin: float | None


def assess_structural_status(
    yield_result,
    local_buckling_result: LocalBucklingAssessment,
    beam_column_result: BeamColumnAssessment,
    crippling_result: CripplingAssessment | None = None,
) -> StructuralStatus:
    """Combine every independent check into one side-by-side status report.

    ``crippling_result`` may be omitted (``None``) for a section to which
    the illustrative crippling correlation is not applied (e.g. the
    Milestone 1 rectangle) -- crippling is then reported as not
    applicable and does not affect ``overall_preliminary_pass``.
    """
    amplified_yield_margin = (
        beam_column_result.amplified_yield_result.min_margin
        if beam_column_result.amplified_yield_result is not None
        else None
    )
    crippling_pass = crippling_result.passes if crippling_result is not None else None
    crippling_margin = crippling_result.governing_margin if crippling_result is not None else None

    margins_by_check = {
        "yield": yield_result.min_margin,
        "local_buckling": local_buckling_result.min_margin,
        "euler": beam_column_result.euler_result.margin,
        "amplified_yield": amplified_yield_margin,
        "crippling": crippling_margin if crippling_result is not None else None,
    }

    candidates = [
        (check, margin) for check in _TIE_BREAK_ORDER for margin in [margins_by_check[check]] if margin is not None
    ]

    if not candidates:
        governing_check = "yield"
        governing_margin: float | None = None
    else:
        governing_check, governing_margin = candidates[0]
        for check, margin in candidates[1:]:
            if margin < governing_margin:
                governing_check, governing_margin = check, margin

    overall_pass = (
        yield_result.passes
        and local_buckling_result.passes
        and beam_column_result.euler_passes
        and beam_column_result.amplified_yield_passes
        and (crippling_pass if crippling_pass is not None else True)
    )

    return StructuralStatus(
        yield_pass=yield_result.passes,
        yield_margin=yield_result.min_margin,
        local_buckling_pass=local_buckling_result.passes,
        local_buckling_margin=local_buckling_result.min_margin,
        euler_pass=beam_column_result.euler_passes,
        euler_margin=beam_column_result.euler_result.margin,
        amplified_yield_pass=beam_column_result.amplified_yield_passes,
        amplified_yield_margin=amplified_yield_margin,
        crippling_pass=crippling_pass,
        crippling_margin=crippling_margin,
        overall_preliminary_pass=overall_pass,
        governing_check=governing_check,
        governing_margin=governing_margin,
    )
