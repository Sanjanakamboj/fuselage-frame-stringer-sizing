"""Illustrative preliminary crippling-strength screen for built-up sections.

**Crippling correlations are empirical, configuration-dependent, and
sourced from test-fitted correlations for a specific material, cross-
section family, and manufacturing process.** They are fundamentally
different in kind from the ideal elastic buckling equations in Milestones
3-4: a plate-buckling or Euler critical stress is derived from first
principles (linear eigenvalue theory), while a crippling stress is a
curve-fit to test data expressing how much post-buckling / local-collapse
strength a real element retains beyond its ideal elastic buckling stress.

This module implements an explicitly **illustrative** correlation
framework, not a sourced handbook (e.g. MMPDS, NASA, or vendor-specific)
crippling equation. Every coefficient (`alpha`, the exponent `m`) is a
visible, explicit input -- never hardcoded inside the formula -- so that
sourced coefficients could later replace the illustrative ones without
changing the surrounding assessment logic. Every result from this module
is labeled an **illustrative preliminary crippling screen**.

Crippling is kept strictly separate from (never blended with) the elastic
von Mises yield screen, local plate buckling, and Euler global buckling
computed elsewhere in this package.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from frame_stringer.built_up_stress import evaluate_normal_stress
from frame_stringer.local_buckling import SectionPlateModel
from frame_stringer.loads import SectionLoad
from frame_stringer.material import IsotropicMaterial


@dataclass(frozen=True)
class CripplingCorrelation:
    """An explicit, visible empirical crippling correlation.

    Attributes
    ----------
    alpha : float
        Empirical dimensionless coefficient. Must be finite and > 0.
    exponent : float
        Empirical exponent `m`. Must be finite and > 0.
    label : str
        Non-empty descriptive label for this correlation.
    source_note : str
        Non-empty note stating the correlation's provenance -- e.g.
        "illustrative, not sourced from a handbook or test database" for
        the illustrative coefficients used in this project's examples.
    """

    alpha: float
    exponent: float
    label: str
    source_note: str

    def __post_init__(self) -> None:
        for field_name in ("alpha", "exponent"):
            value = getattr(self, field_name)
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite, got {value!r}")
            if value <= 0:
                raise ValueError(f"{field_name} must be > 0, got {value!r}")
        if not isinstance(self.label, str) or self.label.strip() == "":
            raise ValueError("label must be a non-empty string")
        if not isinstance(self.source_note, str) or self.source_note.strip() == "":
            raise ValueError("source_note must be a non-empty string")


def raw_crippling_stress(
    correlation: CripplingCorrelation,
    elastic_modulus: float,
    yield_strength: float,
    thickness: float,
    width: float,
) -> float:
    """Raw (uncapped) illustrative crippling-stress correlation, in Pa.

        sigma_cc = alpha * sqrt(E * sigma_y) * (t / b_ref)^m

    This is an illustrative correlation framework, not a sourced design
    equation.
    """
    for name, value in (
        ("elastic_modulus", elastic_modulus),
        ("yield_strength", yield_strength),
        ("thickness", thickness),
        ("width", width),
    ):
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite, got {value!r}")
        if value <= 0:
            raise ValueError(f"{name} must be > 0, got {value!r}")
    return (
        correlation.alpha
        * math.sqrt(elastic_modulus * yield_strength)
        * (thickness / width) ** correlation.exponent
    )


def capped_crippling_stress(raw_stress: float, yield_strength: float) -> tuple[float, bool]:
    """Cap the raw crippling-stress prediction at material yield.

    Returns ``(capped_stress, yield_cap_active)``. The empirical
    correlation should never predict a useful elastic strength above
    material yield in this preliminary model:

        sigma_crippling = min(sigma_cc, sigma_y)

    ``yield_cap_active`` is True only if the raw correlation value
    strictly exceeds yield (the boundary case ``raw == yield`` is not
    flagged as "active", since the cap changes nothing there).
    """
    capped = min(raw_stress, yield_strength)
    yield_cap_active = raw_stress > yield_strength
    return capped, yield_cap_active


def element_slenderness(width: float, thickness: float) -> float:
    """b/t slenderness ratio for a crippling-relevant element."""
    if not math.isfinite(width) or width <= 0:
        raise ValueError(f"width must be finite and > 0, got {width!r}")
    if not math.isfinite(thickness) or thickness <= 0:
        raise ValueError(f"thickness must be finite and > 0, got {thickness!r}")
    return width / thickness


def section_geometry_driver(model: SectionPlateModel) -> tuple[str, float, float, float]:
    """Conservative section-level representative b/t, from ALL mapped plate elements.

    Reuses the existing Milestone 3 plate-element mapping
    (:class:`frame_stringer.local_buckling.SectionPlateModel`) -- no
    dimensional formula is duplicated here. This is the geometry-only,
    load-independent driver: it considers every mapped element (matching
    the "pure axial compression: all longitudinal elements may
    participate" case), and picks the *most slender* one (largest b/t) as
    the conservative driver -- a larger b/t drives a *lower* (more
    conservative) crippling stress through ``(t/b)^m``.

    Returns
    -------
    (name, b_ref, t_ref, bt_ratio) : tuple[str, float, float, float]
        The governing element's name, representative width, thickness,
        and b/t. Deterministic tie-break: the mapping's fixed
        (shape-defined) order decides among elements tied at the maximum
        b/t -- the first one wins.
    """
    governing_name = None
    governing_b = governing_t = governing_bt = None
    for mapping in model.mappings:
        bt = element_slenderness(mapping.plate.width, mapping.plate.thickness)
        if governing_bt is None or bt > governing_bt:
            governing_name = mapping.plate.name
            governing_b = mapping.plate.width
            governing_t = mapping.plate.thickness
            governing_bt = bt
    return governing_name, governing_b, governing_t, governing_bt


@dataclass(frozen=True)
class CripplingAssessment:
    """An illustrative preliminary crippling-strength screen for one section/load state.

    Attributes
    ----------
    correlation : CripplingCorrelation
    governing_element : str
        Name of the most slender (largest b/t) mapped plate element,
        which drives the conservative representative b_ref/t_ref.
    b_ref : float
        Representative unsupported width, in m.
    t_ref : float
        Representative thickness, in m.
    governing_bt : float
        b_ref / t_ref.
    raw_crippling_stress : float
        Uncapped correlation value, in Pa.
    crippling_stress : float
        Yield-capped crippling stress, in Pa.
    yield_cap_active : bool
    area : float
        Section area, in m^2.
    equivalent_crippling_load : float
        P_crippling = crippling_stress * area, in N -- a **section-average
        equivalent** capacity derived from the illustrative correlation,
        not a claim that every element simultaneously reaches this stress.
    compressive_load_demand : float
        P_comp = max(-N, 0), in N.
    peak_compressive_stress : float
        The section's peak (largest-magnitude) compressive normal stress
        under the given load, in Pa (reused directly from
        :func:`frame_stringer.built_up_stress.evaluate_normal_stress`).
    peak_compression_location : str
        "top", "bottom", or "none" -- which extreme fiber governs peak
        compression (swaps with a reversed bending moment).
    axial_average_margin : float | None
        MS = P_crippling/P_comp - 1, or ``None`` if P_comp == 0.
    peak_compression_margin : float | None
        MS = crippling_stress/peak_compressive_stress - 1, or ``None`` if
        there is no compression anywhere in the section.
    governing_mode : str
        "axial_average" or "peak_compression" -- whichever has the
        smaller (governing) margin among those applicable; "axial_average"
        by convention if neither applies (no compression at all).
    governing_margin : float | None
    passes : bool
    """

    correlation: CripplingCorrelation
    governing_element: str
    b_ref: float
    t_ref: float
    governing_bt: float
    raw_crippling_stress: float
    crippling_stress: float
    yield_cap_active: bool
    area: float
    equivalent_crippling_load: float
    compressive_load_demand: float
    peak_compressive_stress: float
    peak_compression_location: str
    axial_average_margin: float | None
    peak_compression_margin: float | None
    governing_mode: str
    governing_margin: float | None
    passes: bool


def assess_section_crippling(
    model: SectionPlateModel, material: IsotropicMaterial, correlation: CripplingCorrelation, load: SectionLoad
) -> CripplingAssessment:
    """Assess an illustrative preliminary crippling screen for a built-up section.

    Both the axial-average margin (using the mean compressive stress
    P_comp/A implied by the applied axial load) and the peak-compression
    margin (using the section's actual peak compressive normal stress,
    which accounts for bending) are computed and kept separately visible.
    The governing mode is determined by comparison -- never assumed.
    """
    name, b_ref, t_ref, bt = section_geometry_driver(model)
    raw = raw_crippling_stress(correlation, material.elastic_modulus, material.yield_strength, t_ref, b_ref)
    capped, yield_cap_active = capped_crippling_stress(raw, material.yield_strength)

    area = model.section.area
    P_crippling = capped * area
    P_comp = max(-load.axial_force, 0.0)
    axial_margin = None if P_comp == 0.0 else P_crippling / P_comp - 1.0

    normal_result = evaluate_normal_stress(load, model.section)
    peak_compressive_stress = abs(normal_result.max_compressive_stress)
    peak_location = normal_result.governing_compression_location
    peak_margin = None if peak_compressive_stress == 0.0 else capped / peak_compressive_stress - 1.0

    candidates: list[tuple[str, float]] = []
    if axial_margin is not None:
        candidates.append(("axial_average", axial_margin))
    if peak_margin is not None:
        candidates.append(("peak_compression", peak_margin))

    if not candidates:
        governing_mode = "axial_average"
        governing_margin: float | None = None
        passes = True
    else:
        governing_mode, governing_margin = candidates[0]
        for mode, margin in candidates[1:]:
            if margin < governing_margin:
                governing_mode, governing_margin = mode, margin
        passes = governing_margin >= 0.0

    return CripplingAssessment(
        correlation=correlation,
        governing_element=name,
        b_ref=b_ref,
        t_ref=t_ref,
        governing_bt=bt,
        raw_crippling_stress=raw,
        crippling_stress=capped,
        yield_cap_active=yield_cap_active,
        area=area,
        equivalent_crippling_load=P_crippling,
        compressive_load_demand=P_comp,
        peak_compressive_stress=peak_compressive_stress,
        peak_compression_location=peak_location,
        axial_average_margin=axial_margin,
        peak_compression_margin=peak_margin,
        governing_mode=governing_mode,
        governing_margin=governing_margin,
        passes=passes,
    )
