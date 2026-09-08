"""Normal and transverse-shear stress for built-up (multi-rectangle) sections.

Normal stress follows the same elementary superposition as Milestone 1
(:mod:`frame_stringer.stress`), but measured from the built-up section's own
(generally nonzero) centroid rather than assuming ``y_bar = 0``.

Transverse shear uses the general elementary beam-shear formula

    tau_xy(y) = V_y * Q(y) / (I_z * b_local(y))

with Q(y) computed geometrically from the rectangular components
(:meth:`BuiltUpSection.first_moment_above`) and b_local(y) the aggregate
material width intersected by the horizontal cut
(:meth:`BuiltUpSection.b_local`). This is a simplified aggregate-width beam
shear treatment, not a thin-wall shear-flow/shear-center solution.
"""

from __future__ import annotations

from dataclasses import dataclass

from frame_stringer.built_up_geometry import BuiltUpSection
from frame_stringer.loads import SectionLoad
from frame_stringer.stress import CombinedStressState

_EPSILON_Y = 1e-9  # m; small offset used to probe "just inside" a boundary


def axial_stress(load: SectionLoad, section: BuiltUpSection) -> float:
    """Signed axial normal stress sigma_axial = N/A, in Pa."""
    return load.axial_force / section.area


def bending_stress(y: float, load: SectionLoad, section: BuiltUpSection) -> float:
    """Signed bending normal stress about the built-up centroid.

    sigma_bending(y) = -M_z*(y - y_bar)/I_z
    """
    return -load.bending_moment_z * (y - section.centroid_y) / section.moment_of_inertia_z


def normal_stress(y: float, load: SectionLoad, section: BuiltUpSection) -> float:
    """Signed combined normal stress sigma_x(y) = N/A - M_z*(y-y_bar)/I_z, in Pa."""
    return axial_stress(load, section) + bending_stress(y, load, section)


@dataclass(frozen=True)
class BuiltUpNormalStressResult:
    """Signed normal-stress summary at a built-up section's extreme fibers.

    Attributes mirror :class:`frame_stringer.stress.NormalStressResult`.
    """

    axial_stress: float
    top_stress: float
    bottom_stress: float
    max_tensile_stress: float
    max_compressive_stress: float
    governing_tension_location: str
    governing_compression_location: str


def evaluate_normal_stress(
    load: SectionLoad, section: BuiltUpSection
) -> BuiltUpNormalStressResult:
    """Evaluate signed normal stress at both extreme fibers of a built-up section."""
    sigma_axial = axial_stress(load, section)
    top = normal_stress(section.y_top, load, section)
    bottom = normal_stress(section.y_bottom, load, section)

    max_tensile = max(top, bottom, 0.0)
    max_compressive = min(top, bottom, 0.0)

    if max_tensile == 0.0:
        tension_location = "none"
    elif top >= bottom:
        tension_location = "top"
    else:
        tension_location = "bottom"

    if max_compressive == 0.0:
        compression_location = "none"
    elif top <= bottom:
        compression_location = "top"
    else:
        compression_location = "bottom"

    return BuiltUpNormalStressResult(
        axial_stress=sigma_axial,
        top_stress=top,
        bottom_stress=bottom,
        max_tensile_stress=max_tensile,
        max_compressive_stress=max_compressive,
        governing_tension_location=tension_location,
        governing_compression_location=compression_location,
    )


def shear_stress(y: float, load: SectionLoad, section: BuiltUpSection) -> float:
    """Signed transverse shear stress tau_xy(y) = V_y * |Q(y)| / (I_z * b_local(y)).

    The sign follows V_y; the magnitude of Q(y) is used (Q_above and
    Q_below have equal magnitude and opposite sign by definition of the
    centroid, so either would give the same physical shear magnitude).

    Raises
    ------
    ValueError
        If y lies outside the section, or if y falls in a void with no
        material intersected by the cut (b_local(y) == 0) -- this can only
        occur for a user-built :class:`BuiltUpSection` with a genuine gap;
        the factory-built I/Z/hat sections are contiguous and never hit
        this case.
    """
    Q = section.first_moment_above(y)  # validates y range as a side effect
    b = section.b_local(y)
    if b == 0.0:
        raise ValueError(
            f"y={y!r} falls in a void (no material intersects the cut); "
            "transverse shear stress is not applicable there"
        )
    return load.shear_force_y * abs(Q) / (section.moment_of_inertia_z * b)


def evaluate_combined_stress(
    y: float, load: SectionLoad, section: BuiltUpSection
) -> CombinedStressState:
    """Evaluate the combined (sigma_x, tau_xy) state at coordinate y."""
    return CombinedStressState(
        y=y,
        sigma_x=normal_stress(y, load, section),
        tau_xy=shear_stress(y, load, section),
    )


def critical_locations(section: BuiltUpSection) -> tuple[tuple[str, float], ...]:
    """Deterministic, component-order-independent list of (label, y) points.

    Always includes the top extreme fiber, the neutral axis, and the
    bottom extreme fiber. Additionally includes a pair of points just
    inside each side of every interior component boundary (e.g. a
    flange/web junction), since local width -- and therefore shear stress
    -- can jump discontinuously there. This generalizes the Milestone 1
    three-point check to any built-up section without assuming which
    point governs.
    """
    y_top = section.y_top
    y_bottom = section.y_bottom
    y_bar = section.centroid_y

    points: list[tuple[str, float]] = [("top_extreme", y_top)]

    for i, boundary in enumerate(section.interior_boundaries()):
        below = boundary - _EPSILON_Y
        above = boundary + _EPSILON_Y
        if below > y_bottom:
            points.append((f"boundary_{i}_below", below))
        if above < y_top:
            points.append((f"boundary_{i}_above", above))

    points.append(("neutral_axis", y_bar))
    points.append(("bottom_extreme", y_bottom))

    # Sort by y descending (top to bottom) for a stable, readable, and
    # component-order-independent ordering; ties broken by label.
    points.sort(key=lambda p: (-p[1], p[0]))
    return tuple(points)
