"""Uniform-thickness multi-load-case sizing for the built-up I/Z/hat sections.

This is a **preliminary sizing study, not a general-purpose optimizer**.
The design space is deliberately small and explicit: for each section
family, the outer geometry (flange width, overall height, crown width,
etc.) is held fixed at the Milestone 2 canonical proportions, and every
wall/flange/web thickness is scaled together to one uniform design
thickness ``t``. Milestone 6 sizes a uniform-gauge version of each fixed
outer geometry; it does not optimize individual element thicknesses, and
it does not use scipy or any black-box/gradient/genetic optimizer --
only deterministic bisection (or, if monotonicity fails, deterministic
enumeration) over the verified Milestone 1-5 mechanics.

Every assessment reuses the existing, unmodified equations from earlier
milestones: :func:`frame_stringer.built_up_strength.assess_builtup_strength`,
:func:`frame_stringer.local_buckling.assess_section_local_buckling`,
:func:`frame_stringer.beam_column.assess_beam_column`,
:func:`frame_stringer.crippling.assess_section_crippling`, and
:func:`frame_stringer.structural_status.assess_structural_status` (whose
fixed constraint tie-break order -- yield, local_buckling, euler,
amplified_yield, crippling -- is reused directly here rather than
re-implemented).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from frame_stringer.beam_column import assess_beam_column
from frame_stringer.built_up_geometry import BuiltUpSection
from frame_stringer.built_up_strength import assess_builtup_strength
from frame_stringer.column_buckling import MemberGeometry
from frame_stringer.crippling import CripplingCorrelation, assess_section_crippling
from frame_stringer.load_cases import FrameStringerLoadCase
from frame_stringer.local_buckling import (
    SectionPlateModel,
    assess_section_local_buckling,
    hat_section_plate_elements,
    i_section_plate_elements,
    z_section_plate_elements,
)
from frame_stringer.mass import linear_mass
from frame_stringer.material import IsotropicMaterial
from frame_stringer.sections import hat_section, i_section, z_section
from frame_stringer.structural_status import assess_structural_status

# ---- canonical (Milestone 2) fixed outer geometry ----

I_FLANGE_WIDTH = 0.06
I_OVERALL_HEIGHT = 0.10

Z_WEB_HEIGHT = 0.08
Z_FLANGE_WIDTH = 0.05

HAT_CROWN_WIDTH = 0.065
HAT_OVERALL_HEIGHT = 0.07
HAT_FLANGE_WIDTH = 0.028


def build_uniform_i_section(t: float) -> BuiltUpSection:
    """I-section with fixed M2 outer geometry and uniform flange/web thickness t."""
    return i_section(flange_width=I_FLANGE_WIDTH, overall_height=I_OVERALL_HEIGHT, flange_thickness=t, web_thickness=t)


def build_uniform_i_plate_model(t: float, panel_length: float) -> SectionPlateModel:
    return i_section_plate_elements(
        flange_width=I_FLANGE_WIDTH, overall_height=I_OVERALL_HEIGHT, flange_thickness=t, web_thickness=t,
        panel_length=panel_length,
    )


def build_uniform_z_section(t: float) -> BuiltUpSection:
    """Z-section with fixed M2 outer geometry and uniform flange/web thickness t."""
    return z_section(web_height=Z_WEB_HEIGHT, web_thickness=t, flange_width=Z_FLANGE_WIDTH, flange_thickness=t)


def build_uniform_z_plate_model(t: float, panel_length: float) -> SectionPlateModel:
    return z_section_plate_elements(
        web_height=Z_WEB_HEIGHT, web_thickness=t, flange_width=Z_FLANGE_WIDTH, flange_thickness=t,
        panel_length=panel_length,
    )


def build_uniform_hat_section(t: float) -> BuiltUpSection:
    """Hat section with fixed M2 outer geometry and uniform crown/web/flange thickness t."""
    return hat_section(crown_width=HAT_CROWN_WIDTH, overall_height=HAT_OVERALL_HEIGHT, wall_thickness=t, flange_width=HAT_FLANGE_WIDTH)


def build_uniform_hat_plate_model(t: float, panel_length: float) -> SectionPlateModel:
    return hat_section_plate_elements(
        crown_width=HAT_CROWN_WIDTH, overall_height=HAT_OVERALL_HEIGHT, wall_thickness=t, flange_width=HAT_FLANGE_WIDTH,
        panel_length=panel_length,
    )


@dataclass(frozen=True)
class SectionFamily:
    """A uniform-thickness section family: fixed outer geometry, one design thickness t.

    Attributes
    ----------
    name : str
    build_section : callable(t) -> BuiltUpSection
    build_plate_model : callable(t, panel_length) -> SectionPlateModel
    """

    name: str
    build_section: object
    build_plate_model: object


#: The three families sized in Milestone 6, in a fixed (deterministic) order.
#: The rectangle is intentionally excluded from sizing -- it is not a
#: thin-walled built-up section (see Milestone 5's crippling rationale).
FAMILIES: tuple[SectionFamily, ...] = (
    SectionFamily("I-section", build_uniform_i_section, build_uniform_i_plate_model),
    SectionFamily("Z-section", build_uniform_z_section, build_uniform_z_plate_model),
    SectionFamily("Hat-section", build_uniform_hat_section, build_uniform_hat_plate_model),
)

#: Fixed deterministic tie-break order for individual constraints, matching
#: frame_stringer.structural_status._TIE_BREAK_ORDER exactly (reused, not
#: redefined, via assess_structural_status below).
CONSTRAINT_ORDER = ("yield", "local_buckling", "euler", "amplified_yield", "crippling")


@dataclass(frozen=True)
class LoadCaseAssessment:
    """All five independent structural checks for one section/thickness under one load case.

    Attributes
    ----------
    load_case : FrameStringerLoadCase
    design_load : SectionLoad
        The load case's factored design load.
    yield_result : BuiltUpStrengthResult
    local_buckling_result : LocalBucklingAssessment
    euler_result : EulerBucklingResult
    amplified_yield_result : BuiltUpStrengthResult | None
        ``None`` only if the member is globally unstable under this load
        (P_comp >= P_cr).
    crippling_result : CripplingAssessment
    overall_pass : bool
    governing_constraint : str
        The applicable constraint with the smallest margin -- one of
        "yield", "local_buckling", "euler", "amplified_yield", "crippling".
        This is **reporting only**, reusing
        :func:`frame_stringer.structural_status.assess_structural_status`'s
        fixed tie-break order -- it is not an interaction equation.
    governing_margin : float | None
    """

    load_case: FrameStringerLoadCase
    design_load: object
    yield_result: object
    local_buckling_result: object
    euler_result: object
    amplified_yield_result: object | None
    crippling_result: object
    overall_pass: bool
    governing_constraint: str
    governing_margin: float | None


def assess_load_case(
    section: BuiltUpSection,
    plate_model: SectionPlateModel,
    material: IsotropicMaterial,
    member: MemberGeometry,
    load_case: FrameStringerLoadCase,
    correlation: CripplingCorrelation,
) -> LoadCaseAssessment:
    """Run all five independent structural checks for one section/thickness/load case.

    Reuses the existing, unmodified assessment functions from Milestones
    2-5 -- no stress, buckling, or crippling equation is duplicated here.
    """
    design_load = load_case.design_load
    yield_result = assess_builtup_strength(design_load, section, material)
    local_result = assess_section_local_buckling(plate_model, design_load, material)
    bc_result = assess_beam_column(member, section, material, design_load)
    crip_result = assess_section_crippling(plate_model, material, correlation, design_load)
    status = assess_structural_status(yield_result, local_result, bc_result, crip_result)

    return LoadCaseAssessment(
        load_case=load_case,
        design_load=design_load,
        yield_result=yield_result,
        local_buckling_result=local_result,
        euler_result=bc_result.euler_result,
        amplified_yield_result=bc_result.amplified_yield_result,
        crippling_result=crip_result,
        overall_pass=status.overall_preliminary_pass,
        governing_constraint=status.governing_check,
        governing_margin=status.governing_margin,
    )


@dataclass(frozen=True)
class MultiLoadCaseAssessment:
    """All load cases assessed for one section/thickness.

    Attributes
    ----------
    per_case : tuple[LoadCaseAssessment, ...]
        In the same order the load cases were supplied.
    all_cases_pass : bool
    governing_load_case : str
        Name of the load case containing the governing (minimum
        applicable) margin. Deterministic tie-break: the supplied
        load-case order decides among ties (first occurrence wins); within
        one load case, the constraint tie-break is
        :data:`CONSTRAINT_ORDER` (reused from ``assess_structural_status``).
    governing_constraint : str
    governing_margin : float | None
    """

    per_case: tuple[LoadCaseAssessment, ...]
    all_cases_pass: bool
    governing_load_case: str
    governing_constraint: str
    governing_margin: float | None


def assess_multi_load_case(
    section: BuiltUpSection,
    plate_model: SectionPlateModel,
    material: IsotropicMaterial,
    member: MemberGeometry,
    load_cases: tuple[FrameStringerLoadCase, ...],
    correlation: CripplingCorrelation,
) -> MultiLoadCaseAssessment:
    """Assess one section/thickness across every supplied load case.

    Duplicate load-case names are handled by processing order only: if two
    cases happen to be identical, the earlier one in ``load_cases``
    determines the governing selection on a tie (see
    :attr:`MultiLoadCaseAssessment.governing_load_case`).
    """
    per_case = tuple(
        assess_load_case(section, plate_model, material, member, lc, correlation) for lc in load_cases
    )
    all_pass = all(c.overall_pass for c in per_case)

    candidates = [(c.load_case.name, c.governing_constraint, c.governing_margin) for c in per_case if c.governing_margin is not None]
    if not candidates:
        first = per_case[0]
        governing_load_case = first.load_case.name
        governing_constraint = first.governing_constraint
        governing_margin: float | None = None
    else:
        governing_load_case, governing_constraint, governing_margin = candidates[0]
        for name, constraint, margin in candidates[1:]:
            if margin < governing_margin:
                governing_load_case, governing_constraint, governing_margin = name, constraint, margin

    return MultiLoadCaseAssessment(
        per_case=per_case,
        all_cases_pass=all_pass,
        governing_load_case=governing_load_case,
        governing_constraint=governing_constraint,
        governing_margin=governing_margin,
    )


def _evaluate_family_at_thickness(
    family: SectionFamily,
    t: float,
    material: IsotropicMaterial,
    member: MemberGeometry,
    load_cases: tuple[FrameStringerLoadCase, ...],
    correlation: CripplingCorrelation,
    panel_length: float,
) -> tuple[BuiltUpSection, MultiLoadCaseAssessment]:
    section = family.build_section(t)
    plate_model = family.build_plate_model(t, panel_length)
    assessment = assess_multi_load_case(section, plate_model, material, member, load_cases, correlation)
    return section, assessment


@dataclass(frozen=True)
class SectionSizingResult:
    """The result of sizing one section family to a minimum uniform thickness.

    Attributes
    ----------
    family_name : str
    required_thickness : float | None
        The minimum uniform thickness (in m) at which every load case
        passes, or ``None`` if infeasible within the search bounds.
    section : BuiltUpSection | None
        The section built at ``required_thickness`` (``None`` if infeasible).
    area : float | None
    mass_per_length : float | None
        Reuses :func:`frame_stringer.mass.linear_mass` unchanged.
    status : str
        One of "minimum_gauge_governs", "converged", or
        "upper_bound_infeasible".
    iterations : int
        Number of bisection midpoint evaluations performed (0 if the
        minimum-gauge/search lower bound already passed).
    t_min_gauge : float
        The illustrative minimum manufacturing gauge used, in m.
    governing_load_case : str | None
    governing_constraint : str | None
    governing_margin : float | None
    final_assessment : MultiLoadCaseAssessment | None
        The multi-load-case assessment at ``required_thickness`` (or, if
        infeasible, at the search upper bound, for diagnostics).
    """

    family_name: str
    required_thickness: float | None
    section: BuiltUpSection | None
    area: float | None
    mass_per_length: float | None
    status: str
    iterations: int
    t_min_gauge: float
    governing_load_case: str | None
    governing_constraint: str | None
    governing_margin: float | None
    final_assessment: MultiLoadCaseAssessment | None


def size_section_family(
    family: SectionFamily,
    material: IsotropicMaterial,
    member: MemberGeometry,
    load_cases: tuple[FrameStringerLoadCase, ...],
    correlation: CripplingCorrelation,
    panel_length: float,
    t_min_gauge: float,
    t_min_search: float = 0.75e-3,
    t_max_search: float = 6.0e-3,
    tolerance: float = 1e-6,
) -> SectionSizingResult:
    """Find the minimum uniform thickness at which every load case passes.

    Uses bounded bisection over ``[max(t_min_search, t_min_gauge),
    t_max_search]`` on the boolean "all load cases pass" predicate, which
    is verified (in the test suite) to be monotonic for the canonical
    geometries and load cases over this range. The search never expands
    the upper bound and never returns a failing thickness as the result.
    """
    for name, value in (
        ("t_min_search", t_min_search),
        ("t_max_search", t_max_search),
        ("t_min_gauge", t_min_gauge),
        ("tolerance", tolerance),
    ):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and > 0, got {value!r}")
    if t_max_search <= t_min_search:
        raise ValueError("t_max_search must exceed t_min_search")

    t_lower = max(t_min_search, t_min_gauge)

    lower_section, lower_assessment = _evaluate_family_at_thickness(
        family, t_lower, material, member, load_cases, correlation, panel_length
    )

    if lower_assessment.all_cases_pass:
        status = "minimum_gauge_governs" if math.isclose(t_lower, t_min_gauge, rel_tol=0, abs_tol=1e-12) else "converged"
        area = lower_section.area
        return SectionSizingResult(
            family_name=family.name,
            required_thickness=t_lower,
            section=lower_section,
            area=area,
            mass_per_length=linear_mass(lower_section, material),
            status=status,
            iterations=0,
            t_min_gauge=t_min_gauge,
            governing_load_case=lower_assessment.governing_load_case,
            governing_constraint=lower_assessment.governing_constraint,
            governing_margin=lower_assessment.governing_margin,
            final_assessment=lower_assessment,
        )

    upper_section, upper_assessment = _evaluate_family_at_thickness(
        family, t_max_search, material, member, load_cases, correlation, panel_length
    )
    if not upper_assessment.all_cases_pass:
        return SectionSizingResult(
            family_name=family.name,
            required_thickness=None,
            section=None,
            area=None,
            mass_per_length=None,
            status="upper_bound_infeasible",
            iterations=0,
            t_min_gauge=t_min_gauge,
            governing_load_case=upper_assessment.governing_load_case,
            governing_constraint=upper_assessment.governing_constraint,
            governing_margin=upper_assessment.governing_margin,
            final_assessment=upper_assessment,
        )

    t_low, t_high = t_lower, t_max_search
    high_section, high_assessment = upper_section, upper_assessment
    iterations = 0
    while t_high - t_low > tolerance:
        t_mid = 0.5 * (t_low + t_high)
        mid_section, mid_assessment = _evaluate_family_at_thickness(
            family, t_mid, material, member, load_cases, correlation, panel_length
        )
        iterations += 1
        if mid_assessment.all_cases_pass:
            t_high, high_section, high_assessment = t_mid, mid_section, mid_assessment
        else:
            t_low = t_mid

    return SectionSizingResult(
        family_name=family.name,
        required_thickness=t_high,
        section=high_section,
        area=high_section.area,
        mass_per_length=linear_mass(high_section, material),
        status="converged",
        iterations=iterations,
        t_min_gauge=t_min_gauge,
        governing_load_case=high_assessment.governing_load_case,
        governing_constraint=high_assessment.governing_constraint,
        governing_margin=high_assessment.governing_margin,
        final_assessment=high_assessment,
    )
