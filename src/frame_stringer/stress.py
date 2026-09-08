"""Axial, bending, and transverse-shear stress for a rectangular beam section.

All formulas are elementary (Euler-Bernoulli) beam-theory results. Normal
stress is signed throughout (positive = tension); shear stress is signed
following V_y internally, with magnitude used only at the strength-screen
layer (see :mod:`frame_stringer.strength`).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from frame_stringer.geometry import RectangularSection
from frame_stringer.loads import SectionLoad


def axial_stress(load: SectionLoad, section: RectangularSection) -> float:
    """Signed axial normal stress sigma_axial = N/A, in Pa.

    Tension (N > 0) gives a positive stress, compression (N < 0) gives a
    negative stress, and N == 0 gives exactly zero.
    """
    return load.axial_force / section.area


def bending_stress(y: float, load: SectionLoad, section: RectangularSection) -> float:
    """Signed bending normal stress sigma_bending(y) = -M_z*y/I_z, in Pa."""
    return -load.bending_moment_z * y / section.moment_of_inertia_z


def normal_stress(y: float, load: SectionLoad, section: RectangularSection) -> float:
    """Signed combined normal stress sigma_x(y) = N/A - M_z*y/I_z, in Pa.

    No absolute value is taken -- tension stays positive, compression stays
    negative.
    """
    return axial_stress(load, section) + bending_stress(y, load, section)


@dataclass(frozen=True)
class NormalStressResult:
    """Signed normal-stress summary at the section's extreme fibers.

    Attributes
    ----------
    axial_stress : float
        sigma_axial = N/A, in Pa.
    top_stress : float
        sigma_x at y = +h/2, in Pa (signed).
    bottom_stress : float
        sigma_x at y = -h/2, in Pa (signed).
    max_tensile_stress : float
        max(top_stress, bottom_stress, 0.0), in Pa (>= 0).
    max_compressive_stress : float
        min(top_stress, bottom_stress, 0.0), in Pa (<= 0).
    governing_tension_location : str
        Which extreme fiber ("top" or "bottom") governs tension, or "none"
        if neither fiber is in tension.
    governing_compression_location : str
        Which extreme fiber governs compression, or "none" if neither fiber
        is in compression.
    """

    axial_stress: float
    top_stress: float
    bottom_stress: float
    max_tensile_stress: float
    max_compressive_stress: float
    governing_tension_location: str
    governing_compression_location: str


def evaluate_normal_stress(
    load: SectionLoad, section: RectangularSection
) -> NormalStressResult:
    """Evaluate signed normal stress at both extreme fibers of the section."""
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

    return NormalStressResult(
        axial_stress=sigma_axial,
        top_stress=top,
        bottom_stress=bottom,
        max_tensile_stress=max_tensile,
        max_compressive_stress=max_compressive,
        governing_tension_location=tension_location,
        governing_compression_location=compression_location,
    )


def shear_stress(y: float, load: SectionLoad, section: RectangularSection) -> float:
    """Signed transverse shear stress tau_xy(y) for a rectangular section.

    tau_xy(y) = (3/2)*(V_y/A)*[1 - (2y/h)^2], for |y| <= h/2.

    This is the exact elementary (parabolic) shear-stress distribution for a
    solid rectangle. It is zero at y = +/- h/2, maximum in magnitude at
    y = 0 (tau_max = 3*V_y/(2*A)), and symmetric about y = 0. The sign
    follows V_y.

    Raises
    ------
    ValueError
        If y lies outside the section, i.e. |y| > h/2.
    """
    half_h = section.height / 2.0
    if abs(y) > half_h:
        raise ValueError(
            f"y={y!r} is outside the section (|y| must be <= h/2 = {half_h!r})"
        )
    return 1.5 * (load.shear_force_y / section.area) * (1.0 - (2.0 * y / section.height) ** 2)


def max_shear_stress(load: SectionLoad, section: RectangularSection) -> float:
    """Signed maximum transverse shear stress at the neutral axis, 3*V_y/(2*A)."""
    return 1.5 * load.shear_force_y / section.area


@dataclass(frozen=True)
class CombinedStressState:
    """The combined stress state (sigma_x, tau_xy) at a single point y.

    Attributes
    ----------
    y : float
        Coordinate at which the state was evaluated, in m.
    sigma_x : float
        Signed normal stress at y, in Pa.
    tau_xy : float
        Signed transverse shear stress at y, in Pa.
    """

    y: float
    sigma_x: float
    tau_xy: float


def evaluate_combined_stress(
    y: float, load: SectionLoad, section: RectangularSection
) -> CombinedStressState:
    """Evaluate the combined (sigma_x, tau_xy) state at coordinate y."""
    return CombinedStressState(
        y=y,
        sigma_x=normal_stress(y, load, section),
        tau_xy=shear_stress(y, load, section),
    )
