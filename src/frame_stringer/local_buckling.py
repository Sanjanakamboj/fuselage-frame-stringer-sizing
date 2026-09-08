"""Mapping built-up frame/stringer sections to plate elements, and section-level
local-buckling assessment.

Plate topology is mapped **explicitly** per factory section shape
(I / Z / hat) -- this module does not attempt to infer generic plate
topology from arbitrary rectangles, since that inference is not robust in
general (see :mod:`frame_stringer.plate_buckling` module docstring for why
outstanding vs. internal boundary conditions and outstand widths need
shape-specific knowledge).

Local stress demand is sampled from the existing, already-verified
built-up beam stress solution (:mod:`frame_stringer.built_up_stress`) --
no new stress theory is introduced here. Longitudinal normal stress is
linear in y, so its extreme within a plate's y-range is always at one of
the two range endpoints; transverse shear is a smooth (piecewise
quadratic) function of y within a single homogeneous component, so a
modest number of interior sample points is enough to capture its maximum
without a dense numerical mesh.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from frame_stringer.built_up_geometry import BuiltUpSection
from frame_stringer.built_up_stress import normal_stress, shear_stress
from frame_stringer.loads import SectionLoad
from frame_stringer.material import IsotropicMaterial
from frame_stringer.plate_buckling import PlateBucklingResult, PlateElement, assess_plate_buckling
from frame_stringer.sections import hat_section, i_section, z_section

_SHEAR_SAMPLE_POINTS = 21
_RELATIVE_EDGE_INSET = 1e-6


@dataclass(frozen=True)
class PlateElementMapping:
    """One plate element plus the section y-range used to sample its stress demand.

    Attributes
    ----------
    plate : PlateElement
        The idealized plate for local-buckling screening.
    y_bottom : float
        Bottom of the y-range (in the built-up section's own datum) used
        to sample the beam-stress solution for this plate's demand.
    y_top : float
        Top of that y-range.
    """

    plate: PlateElement
    y_bottom: float
    y_top: float


@dataclass(frozen=True)
class SectionPlateModel:
    """A built-up section together with its explicit plate-element mapping."""

    section: BuiltUpSection
    mappings: tuple[PlateElementMapping, ...]


def _component(section: BuiltUpSection, label: str):
    for c in section.components:
        if c.label == label:
            return c
    raise ValueError(f"section has no component labeled {label!r}")


def i_section_plate_elements(
    flange_width: float,
    overall_height: float,
    flange_thickness: float,
    web_thickness: float,
    panel_length: float,
) -> SectionPlateModel:
    """Idealize an I-section as three plate elements: web, top and bottom flange outstands.

    Web: internal plate, width = web clear height, thickness = web
    thickness. Flange outstands: each flange's half-width outside the web
    (``(flange_width - web_thickness)/2``) is treated as an outstanding
    plate; top and bottom are kept separate since one may be in
    compression while the other is in tension.
    """
    section = i_section(flange_width, overall_height, flange_thickness, web_thickness)
    web = _component(section, "web")
    top_flange = _component(section, "top_flange")
    bottom_flange = _component(section, "bottom_flange")

    b_out = (flange_width - web_thickness) / 2.0
    if not math.isfinite(b_out) or b_out <= 0:
        raise ValueError(
            "I-section flange outstand width (flange_width - web_thickness)/2 "
            f"must be > 0, got {b_out!r}"
        )

    mappings = (
        PlateElementMapping(
            PlateElement(
                name="web",
                width=web.height,
                thickness=web_thickness,
                length=panel_length,
                boundary_condition="internal",
                role="web",
            ),
            web.bottom_y,
            web.top_y,
        ),
        PlateElementMapping(
            PlateElement(
                name="top_flange_outstand",
                width=b_out,
                thickness=flange_thickness,
                length=panel_length,
                boundary_condition="outstanding",
                role="flange_outstand",
            ),
            top_flange.bottom_y,
            top_flange.top_y,
        ),
        PlateElementMapping(
            PlateElement(
                name="bottom_flange_outstand",
                width=b_out,
                thickness=flange_thickness,
                length=panel_length,
                boundary_condition="outstanding",
                role="flange_outstand",
            ),
            bottom_flange.bottom_y,
            bottom_flange.top_y,
        ),
    )
    return SectionPlateModel(section, mappings)


def z_section_plate_elements(
    web_height: float,
    web_thickness: float,
    flange_width: float,
    flange_thickness: float,
    panel_length: float,
) -> SectionPlateModel:
    """Idealize a Z-section as three plate elements: web, top flange, bottom flange.

    The web is an internal plate (both edges supported, by the top and
    bottom flanges). Each Z-flange is a single-sided cantilevered arm off
    the web (unlike the I-section's flange, which continues through the
    web on both sides), so its full width is treated as one outstanding
    plate. Top and bottom flanges are kept separate.
    """
    section = z_section(web_height, web_thickness, flange_width, flange_thickness)
    web = _component(section, "web")
    top_flange = _component(section, "top_flange")
    bottom_flange = _component(section, "bottom_flange")

    mappings = (
        PlateElementMapping(
            PlateElement(
                name="web",
                width=web.height,
                thickness=web_thickness,
                length=panel_length,
                boundary_condition="internal",
                role="web",
            ),
            web.bottom_y,
            web.top_y,
        ),
        PlateElementMapping(
            PlateElement(
                name="top_flange_outstand",
                width=flange_width,
                thickness=flange_thickness,
                length=panel_length,
                boundary_condition="outstanding",
                role="flange_outstand",
            ),
            top_flange.bottom_y,
            top_flange.top_y,
        ),
        PlateElementMapping(
            PlateElement(
                name="bottom_flange_outstand",
                width=flange_width,
                thickness=flange_thickness,
                length=panel_length,
                boundary_condition="outstanding",
                role="flange_outstand",
            ),
            bottom_flange.bottom_y,
            bottom_flange.top_y,
        ),
    )
    return SectionPlateModel(section, mappings)


def hat_section_plate_elements(
    crown_width: float,
    overall_height: float,
    wall_thickness: float,
    flange_width: float,
    panel_length: float,
) -> SectionPlateModel:
    """Idealize a hat section as five plate elements: crown, two webs, two flange outstands.

    The crown is treated as an internal plate spanning the clear distance
    between the two webs (``crown_width - 2*wall_thickness``). Each web is
    an internal plate (supported by the crown above and the flange below)
    of width equal to the clear web run. Each bottom flange is an
    outstanding plate of width ``flange_width``, cantilevered from its
    web. Because the model carries no lateral (z) position, left and right
    legs are geometrically identical here; they are still reported as
    distinct named plates (see module docstring / README).
    """
    section = hat_section(crown_width, overall_height, wall_thickness, flange_width)
    flange_pair = _component(section, "flange_pair")
    web_pair = _component(section, "web_pair")
    crown = _component(section, "crown")

    crown_clear_width = crown_width - 2.0 * wall_thickness
    if not math.isfinite(crown_clear_width) or crown_clear_width <= 0:
        raise ValueError(
            "hat-section crown clear width (crown_width - 2*wall_thickness) "
            f"must be > 0, got {crown_clear_width!r}"
        )

    web_leg = PlateElement(
        name="web_left",
        width=web_pair.height,
        thickness=wall_thickness,
        length=panel_length,
        boundary_condition="internal",
        role="web",
    )
    web_leg_2 = PlateElement(
        name="web_right",
        width=web_pair.height,
        thickness=wall_thickness,
        length=panel_length,
        boundary_condition="internal",
        role="web",
    )
    flange_leg = PlateElement(
        name="flange_left",
        width=flange_width,
        thickness=wall_thickness,
        length=panel_length,
        boundary_condition="outstanding",
        role="flange_outstand",
    )
    flange_leg_2 = PlateElement(
        name="flange_right",
        width=flange_width,
        thickness=wall_thickness,
        length=panel_length,
        boundary_condition="outstanding",
        role="flange_outstand",
    )
    crown_plate = PlateElement(
        name="crown",
        width=crown_clear_width,
        thickness=wall_thickness,
        length=panel_length,
        boundary_condition="internal",
        role="crown",
    )

    mappings = (
        PlateElementMapping(web_leg, web_pair.bottom_y, web_pair.top_y),
        PlateElementMapping(web_leg_2, web_pair.bottom_y, web_pair.top_y),
        PlateElementMapping(flange_leg, flange_pair.bottom_y, flange_pair.top_y),
        PlateElementMapping(flange_leg_2, flange_pair.bottom_y, flange_pair.top_y),
        PlateElementMapping(crown_plate, crown.bottom_y, crown.top_y),
    )
    return SectionPlateModel(section, mappings)


def extract_plate_demand(
    section: BuiltUpSection, load: SectionLoad, mapping: PlateElementMapping
) -> tuple[float, float]:
    """Sample (signed sigma_x demand, |tau_xy| demand) for one plate mapping.

    Normal stress is linear in y, so the most-compressive value within
    ``[y_bottom, y_top]`` is always at one of the two endpoints -- both are
    evaluated and the more negative (more compressive) one is returned
    signed (a positive value, meaning net tension at both ends, correctly
    yields zero compression demand downstream).

    Transverse shear is a smooth function of y within a single homogeneous
    component; a fixed number of evenly-spaced interior points (inset
    slightly from the exact edges, which can otherwise resolve to a
    neighboring component under the documented b_local boundary
    convention) is sampled and the largest magnitude is taken as the
    representative shear demand.
    """
    sigma_top = normal_stress(mapping.y_top, load, section)
    sigma_bottom = normal_stress(mapping.y_bottom, load, section)
    sigma_x_demand = min(sigma_top, sigma_bottom)

    span = mapping.y_top - mapping.y_bottom
    inset = span * _RELATIVE_EDGE_INSET
    lo = mapping.y_bottom + inset
    hi = mapping.y_top - inset
    if hi <= lo:
        sample_ys = [(mapping.y_bottom + mapping.y_top) / 2.0]
    else:
        n = _SHEAR_SAMPLE_POINTS
        sample_ys = [lo + (hi - lo) * i / (n - 1) for i in range(n)]

    tau_demand = max(abs(shear_stress(y, load, section)) for y in sample_ys)

    return sigma_x_demand, tau_demand


@dataclass(frozen=True)
class LocalBucklingAssessment:
    """Section-level local-buckling assessment across all mapped plate elements.

    Attributes
    ----------
    plates : tuple[PlateBucklingResult, ...]
        Per-plate results, in the mapping's fixed (shape-defined) order.
    governing_plate : str
        Name of the plate with the smallest governing margin.
    governing_mode : str
        That plate's governing mode ("compression", "shear", or "interaction").
    min_margin : float | None
        The minimum margin across all plates (``None`` only if every
        plate is trivially passing with no applicable margin).
    passes : bool
        True if every plate passes.
    """

    plates: tuple[PlateBucklingResult, ...]
    governing_plate: str
    governing_mode: str
    min_margin: float | None
    passes: bool


def assess_section_local_buckling(
    model: SectionPlateModel, load: SectionLoad, material: IsotropicMaterial
) -> LocalBucklingAssessment:
    """Assess local buckling of every mapped plate element under one load state.

    The governing plate is determined by comparing the governing margin of
    every plate -- never assumed. Deterministic tie-break: the mapping's
    fixed (shape-defined) order decides among ties, matching the tie-break
    convention used elsewhere in this package.
    """
    results = []
    for mapping in model.mappings:
        sigma_x_demand, tau_demand = extract_plate_demand(model.section, load, mapping)
        results.append(
            assess_plate_buckling(mapping.plate, material, sigma_x_demand, tau_demand)
        )

    governing = results[0]
    for r in results[1:]:
        if governing.governing_margin is None:
            if r.governing_margin is not None:
                governing = r
        elif r.governing_margin is not None and r.governing_margin < governing.governing_margin:
            governing = r

    margins = [r.governing_margin for r in results if r.governing_margin is not None]
    min_margin = min(margins) if margins else None

    passes = all(r.passes for r in results)

    return LocalBucklingAssessment(
        plates=tuple(results),
        governing_plate=governing.plate_name,
        governing_mode=governing.governing_mode,
        min_margin=min_margin,
        passes=passes,
    )


@dataclass(frozen=True)
class CombinedElasticStatus:
    """A small summary combining (but not numerically blending) yield and buckling status.

    Attributes
    ----------
    yield_passes : bool
    local_buckling_passes : bool
    min_yield_margin : float | None
    min_local_buckling_margin : float | None
    overall_preliminary_pass : bool
        ``yield_passes AND local_buckling_passes``. This is a status
        combination, not a synthetic combined margin -- yield and
        buckling remain two distinct failure modes with two distinct
        margins.
    """

    yield_passes: bool
    local_buckling_passes: bool
    min_yield_margin: float | None
    min_local_buckling_margin: float | None
    overall_preliminary_pass: bool


def combined_elastic_status(strength_result, buckling_result: LocalBucklingAssessment) -> CombinedElasticStatus:
    """Summarize yield and local-buckling status side by side (never blended)."""
    return CombinedElasticStatus(
        yield_passes=strength_result.passes,
        local_buckling_passes=buckling_result.passes,
        min_yield_margin=strength_result.min_margin,
        min_local_buckling_margin=buckling_result.min_margin,
        overall_preliminary_pass=strength_result.passes and buckling_result.passes,
    )
