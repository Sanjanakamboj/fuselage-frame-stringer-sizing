"""Factory functions for realistic built-up frame/stringer cross-sections.

Each factory assembles a small number of :class:`RectangularComponent`
instances (see :mod:`frame_stringer.built_up_geometry` for the modeling
convention, especially how laterally-paired members such as a hat
section's two webs are represented as a single combined-width component)
into a :class:`BuiltUpSection`, validates the input geometry, and returns
the result. All factories build sections whose components are contiguous
(touching, non-overlapping) by construction.
"""

from __future__ import annotations

import math

from frame_stringer.built_up_geometry import BuiltUpSection, RectangularComponent


def _require_finite_positive(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value!r}")
    if value <= 0:
        raise ValueError(f"{name} must be > 0, got {value!r}")


def i_section(
    flange_width: float,
    overall_height: float,
    flange_thickness: float,
    web_thickness: float,
) -> BuiltUpSection:
    """Build a symmetric I-section from three rectangles.

    Parameters
    ----------
    flange_width : float
        Width of the top and bottom flanges, in m.
    overall_height : float
        Total section height (outer flange face to outer flange face), in m.
    flange_thickness : float
        Thickness of each flange, in m.
    web_thickness : float
        Web thickness, in m.

    The web clear height is ``h_web = overall_height - 2*flange_thickness``,
    which must be > 0. ``web_thickness`` must not exceed ``flange_width``.
    The section is centered so that y = 0 is at mid-height; for equal top
    and bottom flanges this makes the centroid exactly zero.
    """
    for name, value in (
        ("flange_width", flange_width),
        ("overall_height", overall_height),
        ("flange_thickness", flange_thickness),
        ("web_thickness", web_thickness),
    ):
        _require_finite_positive(name, value)

    h_web = overall_height - 2.0 * flange_thickness
    if h_web <= 0:
        raise ValueError(
            "overall_height must exceed 2*flange_thickness "
            f"(got overall_height={overall_height!r}, "
            f"flange_thickness={flange_thickness!r})"
        )
    if web_thickness > flange_width:
        raise ValueError(
            f"web_thickness ({web_thickness!r}) must be <= "
            f"flange_width ({flange_width!r})"
        )

    half_height = overall_height / 2.0
    top_flange = RectangularComponent(
        width=flange_width,
        height=flange_thickness,
        centroid_y=half_height - flange_thickness / 2.0,
        label="top_flange",
    )
    web = RectangularComponent(
        width=web_thickness,
        height=h_web,
        centroid_y=0.0,
        label="web",
    )
    bottom_flange = RectangularComponent(
        width=flange_width,
        height=flange_thickness,
        centroid_y=-(half_height - flange_thickness / 2.0),
        label="bottom_flange",
    )
    return BuiltUpSection((top_flange, web, bottom_flange))


def z_section(
    web_height: float,
    web_thickness: float,
    flange_width: float,
    flange_thickness: float,
) -> BuiltUpSection:
    """Build a thin-walled Z-like section from three rectangles.

    A vertical web with a top flange extending to one side (in z) and a
    bottom flange extending to the opposite side. Because
    :class:`RectangularComponent` tracks no lateral (z) position, the
    lateral offset between the two flanges is not represented -- only
    bending about z and transverse shear in y (this milestone's scope) are
    affected by y-extent and width, which are captured exactly. Lateral
    (z) centroid and shear-center effects are deferred.

    For identical top and bottom flange geometry, the section is
    centroidally symmetric in y (``y_bar = 0``, ``S_top == S_bottom``)
    even though it is laterally (z) unsymmetric.
    """
    for name, value in (
        ("web_height", web_height),
        ("web_thickness", web_thickness),
        ("flange_width", flange_width),
        ("flange_thickness", flange_thickness),
    ):
        _require_finite_positive(name, value)

    half_web = web_height / 2.0
    web = RectangularComponent(
        width=web_thickness,
        height=web_height,
        centroid_y=0.0,
        label="web",
    )
    top_flange = RectangularComponent(
        width=flange_width,
        height=flange_thickness,
        centroid_y=half_web + flange_thickness / 2.0,
        label="top_flange",
    )
    bottom_flange = RectangularComponent(
        width=flange_width,
        height=flange_thickness,
        centroid_y=-(half_web + flange_thickness / 2.0),
        label="bottom_flange",
    )
    return BuiltUpSection((web, top_flange, bottom_flange))


def hat_section(
    crown_width: float,
    overall_height: float,
    wall_thickness: float,
    flange_width: float,
) -> BuiltUpSection:
    """Build an open hat/stiffener-like section from three rectangles.

    A constant-thickness (``wall_thickness``) formed-sheet idealization:
    a horizontal crown at the top, two vertical webs connecting the crown
    down to two outward-turned bottom flanges. The two webs (combined
    width ``2*wall_thickness``) and the two flanges (combined width
    ``2*flange_width``) are each represented as a single combined-width
    component, since they share identical y-extents (see
    :mod:`frame_stringer.built_up_geometry`).

    ``overall_height`` is the total height from the outer face of the
    bottom flanges to the outer face of the crown; the clear web run is
    ``overall_height - 2*wall_thickness``, which must be > 0.

    Even with left/right geometry identical (guaranteed here, since the
    model carries no lateral position), the y-centroid is *not* generally
    at mid-height, because the crown, web-pair, and flange-pair areas
    differ. The centroid is computed from the actual geometry, never
    assumed.
    """
    for name, value in (
        ("crown_width", crown_width),
        ("overall_height", overall_height),
        ("wall_thickness", wall_thickness),
        ("flange_width", flange_width),
    ):
        _require_finite_positive(name, value)

    web_run = overall_height - 2.0 * wall_thickness
    if web_run <= 0:
        raise ValueError(
            "overall_height must exceed 2*wall_thickness "
            f"(got overall_height={overall_height!r}, wall_thickness={wall_thickness!r})"
        )

    half_height = overall_height / 2.0
    flange_pair = RectangularComponent(
        width=2.0 * flange_width,
        height=wall_thickness,
        centroid_y=-half_height + wall_thickness / 2.0,
        label="flange_pair",
    )
    web_pair = RectangularComponent(
        width=2.0 * wall_thickness,
        height=web_run,
        centroid_y=-half_height + wall_thickness + web_run / 2.0,
        label="web_pair",
    )
    crown = RectangularComponent(
        width=crown_width,
        height=wall_thickness,
        centroid_y=half_height - wall_thickness / 2.0,
        label="crown",
    )
    return BuiltUpSection((flange_pair, web_pair, crown))
