"""First-order elastic beam-column (combined axial compression + bending) screening.

This module answers the second half of the Milestone 4 question: given a
member that carries both axial compression and bending, axial compression
amplifies the bending moment (and hence the bending stress) *before* Euler
collapse is reached. This uses the classical **first-order elastic
beam-column amplification** -- it is NOT a nonlinear collapse solution, it
does not track post-buckling deformation, and it diverges (by design, not
by accident) as the axial demand approaches the Euler load.

Yield is re-screened using the *unchanged* Milestone 1/2 stress and von
Mises machinery, with only the bending moment replaced by its amplified
value -- no new stress theory or failure criterion is introduced. The
unamplified (ordinary) yield result remains visible and unmodified
alongside the amplified one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from frame_stringer.built_up_geometry import BuiltUpSection
from frame_stringer.built_up_strength import assess_builtup_strength
from frame_stringer.column_buckling import EulerBucklingResult, MemberGeometry, assess_euler_buckling
from frame_stringer.geometry import RectangularSection
from frame_stringer.loads import SectionLoad
from frame_stringer.local_buckling import LocalBucklingAssessment
from frame_stringer.material import IsotropicMaterial
from frame_stringer.strength import assess_section_strength


def _assess_yield(section, load: SectionLoad, material: IsotropicMaterial):
    """Dispatch to the correct (unmodified) Milestone 1/2 yield screen by section type.

    Reuses :func:`frame_stringer.strength.assess_section_strength` for a
    :class:`RectangularSection` and
    :func:`frame_stringer.built_up_strength.assess_builtup_strength` for a
    :class:`BuiltUpSection` -- no stress or yield equation is duplicated here.
    """
    if isinstance(section, BuiltUpSection):
        return assess_builtup_strength(load, section, material)
    if isinstance(section, RectangularSection):
        return assess_section_strength(load, section, material)
    raise TypeError(f"unsupported section type: {type(section)!r}")


def amplification_factor(compressive_load_demand: float, critical_load: float) -> float | None:
    """First-order elastic beam-column amplification factor, B = 1/(1 - P_comp/P_cr).

    - At P_comp = 0: B = 1 (no amplification).
    - As P_comp approaches P_cr from below: B grows without bound.
    - At P_comp >= P_cr: returns ``None`` -- global instability / an
      invalid (non-convergent) first-order amplification, rather than
      dividing by zero or returning a misleadingly finite number.
    """
    if compressive_load_demand < 0:
        raise ValueError(
            f"compressive_load_demand must be >= 0, got {compressive_load_demand!r}"
        )
    if not math.isfinite(critical_load) or critical_load <= 0:
        raise ValueError(f"critical_load must be finite and > 0, got {critical_load!r}")
    if compressive_load_demand >= critical_load:
        return None
    return 1.0 / (1.0 - compressive_load_demand / critical_load)


def amplified_moment(applied_moment: float, compressive_load_demand: float, critical_load: float) -> float | None:
    """Amplified bending moment, M_amplified = M_applied * B.

    Returns ``None`` if the member is unstable (P_comp >= P_cr; see
    :func:`amplification_factor`).
    """
    B = amplification_factor(compressive_load_demand, critical_load)
    if B is None:
        return None
    return applied_moment * B


def eccentricity(applied_moment: float, compressive_load_demand: float) -> float | None:
    """First-order eccentricity diagnostic, e = |M|/P_comp, in m.

    Returns ``None`` at zero compressive demand. This is a diagnostic
    only -- it does NOT reinterpret an arbitrary applied moment as
    literally caused by a physical load eccentricity; it simply reports
    the moment-to-axial-load ratio for engineering context.
    """
    if compressive_load_demand == 0.0:
        return None
    return abs(applied_moment) / compressive_load_demand


@dataclass(frozen=True)
class BeamColumnAssessment:
    """Combined axial-compression + bending global-stability screen for one member.

    Attributes
    ----------
    euler_result : EulerBucklingResult
        The bare (bending-independent) Euler global-buckling result.
    original_load : SectionLoad
        The unamplified applied load.
    p_over_pcr : float
        compressive_load_demand / critical_load (can be >= 1 if unstable).
    stable : bool
        True if compressive_load_demand < critical_load (a finite
        first-order amplification exists).
    amplification_factor : float | None
        B, or ``None`` if unstable.
    amplified_moment : float | None
        M_amplified, or ``None`` if unstable.
    eccentricity : float | None
        |M|/P_comp diagnostic, or ``None`` at zero compressive demand.
    unamplified_yield_result : object
        The ordinary (Milestone 1/2, unmodified) yield result under
        ``original_load``.
    amplified_yield_result : object | None
        The **beam-column amplified yield screen**: the same yield
        assessment, but using the amplified moment (N and V_y unchanged).
        ``None`` if unstable.
    euler_passes : bool
    amplified_yield_passes : bool
        False if unstable (no valid amplified state exists).
    governing_mode : str
        "euler" or "amplified_yield" -- whichever has the smaller
        (governing) margin among applicable modes; "euler" by convention
        if neither is applicable (e.g. zero compression and comfortable
        amplified yield) or if the member is unstable.
    governing_margin : float | None
    overall_pass : bool
        euler_passes AND amplified_yield_passes.
    """

    euler_result: EulerBucklingResult
    original_load: SectionLoad
    p_over_pcr: float
    stable: bool
    amplification_factor: float | None
    amplified_moment: float | None
    eccentricity: float | None
    unamplified_yield_result: object
    amplified_yield_result: object | None
    euler_passes: bool
    amplified_yield_passes: bool
    governing_mode: str
    governing_margin: float | None
    overall_pass: bool


def assess_beam_column(
    member: MemberGeometry, section, material: IsotropicMaterial, load: SectionLoad
) -> BeamColumnAssessment:
    """Assess combined axial-compression + bending global stability for one member.

    ``section`` may be a :class:`RectangularSection` or a
    :class:`BuiltUpSection` -- the correct (unmodified) yield screen is
    dispatched automatically. Shear (V_y) is left unchanged by this
    Milestone 4 beam-column approximation.
    """
    euler_result = assess_euler_buckling(member, section.area, section.moment_of_inertia_z, material, load)
    P_comp = euler_result.compressive_load_demand
    P_cr = euler_result.critical_load
    p_over_pcr = P_comp / P_cr
    stable = P_comp < P_cr

    unamplified_yield = _assess_yield(section, load, material)
    ecc = eccentricity(load.bending_moment_z, P_comp)

    if stable:
        B = amplification_factor(P_comp, P_cr)
        M_amp = load.bending_moment_z * B
        amplified_load = SectionLoad(
            axial_force=load.axial_force, shear_force_y=load.shear_force_y, bending_moment_z=M_amp
        )
        amplified_yield = _assess_yield(section, amplified_load, material)
        amplified_yield_passes = amplified_yield.passes
    else:
        B = None
        M_amp = None
        amplified_yield = None
        amplified_yield_passes = False

    euler_passes = euler_result.passes

    candidates: list[tuple[str, float]] = []
    if euler_result.applicable:
        candidates.append(("euler", euler_result.margin))
    if amplified_yield is not None and amplified_yield.min_margin is not None:
        candidates.append(("amplified_yield", amplified_yield.min_margin))

    if not candidates:
        governing_mode = "euler"
        governing_margin = None
    else:
        governing_mode, governing_margin = candidates[0]
        for mode, margin in candidates[1:]:
            if margin < governing_margin:
                governing_mode, governing_margin = mode, margin

    overall_pass = euler_passes and amplified_yield_passes

    return BeamColumnAssessment(
        euler_result=euler_result,
        original_load=load,
        p_over_pcr=p_over_pcr,
        stable=stable,
        amplification_factor=B,
        amplified_moment=M_amp,
        eccentricity=ecc,
        unamplified_yield_result=unamplified_yield,
        amplified_yield_result=amplified_yield,
        euler_passes=euler_passes,
        amplified_yield_passes=amplified_yield_passes,
        governing_mode=governing_mode,
        governing_margin=governing_margin,
        overall_pass=overall_pass,
    )


@dataclass(frozen=True)
class SectionStabilitySummary:
    """Side-by-side (never numerically blended) summary of all four independent checks.

    Attributes
    ----------
    yield_pass : bool
    local_buckling_pass : bool
    global_euler_pass : bool
    amplified_yield_pass : bool
    overall_preliminary_pass : bool
        True only if every applicable check passes.
    min_yield_margin : float | None
    min_local_buckling_margin : float | None
    euler_margin : float | None
    min_amplified_yield_margin : float | None
    """

    yield_pass: bool
    local_buckling_pass: bool
    global_euler_pass: bool
    amplified_yield_pass: bool
    overall_preliminary_pass: bool
    min_yield_margin: float | None
    min_local_buckling_margin: float | None
    euler_margin: float | None
    min_amplified_yield_margin: float | None


def section_stability_summary(
    yield_result, local_buckling_result: LocalBucklingAssessment, beam_column_result: BeamColumnAssessment
) -> SectionStabilitySummary:
    """Combine yield, local-buckling, Euler, and amplified-yield status without blending margins."""
    amplified_margin = (
        beam_column_result.amplified_yield_result.min_margin
        if beam_column_result.amplified_yield_result is not None
        else None
    )
    overall = (
        yield_result.passes
        and local_buckling_result.passes
        and beam_column_result.euler_passes
        and beam_column_result.amplified_yield_passes
    )
    return SectionStabilitySummary(
        yield_pass=yield_result.passes,
        local_buckling_pass=local_buckling_result.passes,
        global_euler_pass=beam_column_result.euler_passes,
        amplified_yield_pass=beam_column_result.amplified_yield_passes,
        overall_preliminary_pass=overall,
        min_yield_margin=yield_result.min_margin,
        min_local_buckling_margin=local_buckling_result.min_margin,
        euler_margin=beam_column_result.euler_result.margin,
        min_amplified_yield_margin=amplified_margin,
    )
