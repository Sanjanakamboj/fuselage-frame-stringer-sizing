"""Ideal elastic global (Euler) member buckling.

This module screens whether a *complete member* -- not an individual plate
element -- remains globally stable under axial compression, using the
classical ideal elastic (small-deflection) Euler column formula. It is
kept strictly separate from:

- material yield (:mod:`frame_stringer.strength` / `built_up_strength`)
- local plate buckling of individual thin elements
  (:mod:`frame_stringer.plate_buckling` / `local_buckling`)

Local buckling depends strongly on an individual plate's own width/
thickness; global Euler buckling depends on the *whole section's* I_z/A and
the member's effective length -- these are physically distinct instability
modes and are never blended into one margin.

This is an ideal elastic first-order stability screen: a straight,
prismatic, initially-perfect member with no residual stress, analyzed with
the classical Euler formula and an explicit, user-supplied effective-length
factor K. It is NOT a certification allowable, does not include inelastic
(Johnson/Rankine) column behavior, and does not account for initial
crookedness or eccentricity beyond what the caller explicitly supplies.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from frame_stringer.loads import SectionLoad
from frame_stringer.material import IsotropicMaterial


@dataclass(frozen=True)
class MemberGeometry:
    """A member's length and explicit effective-length (end-restraint) factor.

    Attributes
    ----------
    length : float
        Physical (unsupported) member length L, in m. Must be finite and > 0.
    effective_length_factor : float
        The classical effective-length factor K (a modeling assumption,
        never inferred). Must be finite and > 0. Illustrative classical
        values: K = 0.5 (fixed-fixed idealization), K = 0.7 (restrained-end
        illustrative case), K = 1.0 (pinned-pinned), K = 2.0 (fixed-free).
        These do NOT claim to exactly represent any specific real
        fuselage frame/stringer installation -- K is always an explicit,
        visible modeling choice, never buried inside a section or
        material object.
    label : str | None
        Optional non-empty descriptive label.
    """

    length: float
    effective_length_factor: float
    label: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("length", "effective_length_factor"):
            value = getattr(self, field_name)
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite, got {value!r}")
            if value <= 0:
                raise ValueError(f"{field_name} must be > 0, got {value!r}")
        if self.label is not None and self.label.strip() == "":
            raise ValueError("label, if supplied, must be non-empty")

    @property
    def effective_length(self) -> float:
        """Effective length L_eff = K*L, in m."""
        return self.effective_length_factor * self.length


def radius_of_gyration(area: float, moment_of_inertia: float) -> float:
    """Radius of gyration r_g = sqrt(I/A), in m, for the given bending axis.

    Raises
    ------
    ValueError
        If area or moment_of_inertia is not finite and > 0.
    """
    for name, value in (("area", area), ("moment_of_inertia", moment_of_inertia)):
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite, got {value!r}")
        if value <= 0:
            raise ValueError(f"{name} must be > 0, got {value!r}")
    return math.sqrt(moment_of_inertia / area)


def slenderness_ratio(member: MemberGeometry, radius_of_gyration_value: float) -> float:
    """Slenderness ratio lambda = K*L/r_g (dimensionless)."""
    if not math.isfinite(radius_of_gyration_value) or radius_of_gyration_value <= 0:
        raise ValueError(
            f"radius_of_gyration_value must be finite and > 0, got {radius_of_gyration_value!r}"
        )
    return member.effective_length / radius_of_gyration_value


def euler_critical_load(member: MemberGeometry, elastic_modulus: float, moment_of_inertia: float) -> float:
    """Euler critical (ideal elastic) axial load, P_cr = pi^2*E*I / (K*L)^2, in N."""
    if not math.isfinite(elastic_modulus) or elastic_modulus <= 0:
        raise ValueError(f"elastic_modulus must be finite and > 0, got {elastic_modulus!r}")
    if not math.isfinite(moment_of_inertia) or moment_of_inertia <= 0:
        raise ValueError(f"moment_of_inertia must be finite and > 0, got {moment_of_inertia!r}")
    return math.pi**2 * elastic_modulus * moment_of_inertia / member.effective_length**2


def euler_critical_stress_from_load(critical_load: float, area: float) -> float:
    """Euler critical stress, sigma_cr = P_cr/A, in Pa."""
    if not math.isfinite(area) or area <= 0:
        raise ValueError(f"area must be finite and > 0, got {area!r}")
    return critical_load / area


def euler_critical_stress_from_slenderness(elastic_modulus: float, slenderness: float) -> float:
    """Euler critical stress via the slenderness-ratio form, sigma_cr = pi^2*E/lambda^2, in Pa.

    Provided to verify (and use, where convenient) the equivalence of the
    two classical formulations of the Euler critical stress.
    """
    if not math.isfinite(slenderness) or slenderness <= 0:
        raise ValueError(f"slenderness must be finite and > 0, got {slenderness!r}")
    return math.pi**2 * elastic_modulus / slenderness**2


def global_buckling_margin(critical_load: float, compressive_load_demand: float) -> float | None:
    """Ideal elastic Euler global-buckling margin, P_cr/P_comp - 1.

    Returns ``None`` (trivially passing, not applicable) if
    ``compressive_load_demand`` is exactly zero. The boundary case
    ``compressive_load_demand == critical_load`` gives margin exactly 0
    (PASS). This is labeled the **ideal elastic Euler global-buckling
    margin** -- it is not a flight or certification margin.
    """
    if compressive_load_demand == 0.0:
        return None
    return critical_load / compressive_load_demand - 1.0


@dataclass(frozen=True)
class EulerBucklingResult:
    """Ideal elastic Euler global-buckling assessment for one member/section/load.

    Attributes
    ----------
    length : float
        Physical member length L, in m.
    effective_length_factor : float
        K.
    effective_length : float
        K*L, in m.
    area : float
        Section area A, in m^2.
    moment_of_inertia : float
        Section I_z (about the bending axis considered), in m^4.
    radius_of_gyration : float
        sqrt(I_z/A), in m.
    slenderness_ratio : float
        K*L/r_g (dimensionless).
    compressive_load_demand : float
        P_comp = max(-N, 0), in N (Milestone 1-2 convention: N < 0 = compression).
    critical_load : float
        Euler critical load P_cr, in N.
    critical_stress : float
        Euler critical stress sigma_cr = P_cr/A, in Pa.
    margin : float | None
        Ideal elastic Euler global-buckling margin, or ``None`` if not
        applicable (P_comp == 0, i.e. axial load is zero or tensile).
    applicable : bool
        True if P_comp > 0 (a compressive axial demand exists).
    passes : bool
        True if margin is ``None`` (trivially passing) or margin >= 0.
    """

    length: float
    effective_length_factor: float
    effective_length: float
    area: float
    moment_of_inertia: float
    radius_of_gyration: float
    slenderness_ratio: float
    compressive_load_demand: float
    critical_load: float
    critical_stress: float
    margin: float | None
    applicable: bool
    passes: bool


def assess_euler_buckling(
    member: MemberGeometry, area: float, moment_of_inertia: float, material: IsotropicMaterial, load: SectionLoad
) -> EulerBucklingResult:
    """Assess ideal elastic Euler global buckling for a section/member/load.

    Only the compressive axial load component drives this check (bending
    does not alter the bare Euler load in this milestone -- see
    :mod:`frame_stringer.beam_column` for the combined axial+bending
    beam-column screen). ``area`` and ``moment_of_inertia`` are taken
    directly from the caller's own section object (e.g.
    ``section.area``/``section.moment_of_inertia_z``) -- this module never
    duplicates the section-property equations.
    """
    r_g = radius_of_gyration(area, moment_of_inertia)
    lam = slenderness_ratio(member, r_g)
    P_cr = euler_critical_load(member, material.elastic_modulus, moment_of_inertia)
    sigma_cr = euler_critical_stress_from_load(P_cr, area)

    P_comp = max(-load.axial_force, 0.0)
    margin = global_buckling_margin(P_cr, P_comp)
    applicable = P_comp > 0.0
    passes = True if margin is None else margin >= 0.0

    return EulerBucklingResult(
        length=member.length,
        effective_length_factor=member.effective_length_factor,
        effective_length=member.effective_length,
        area=area,
        moment_of_inertia=moment_of_inertia,
        radius_of_gyration=r_g,
        slenderness_ratio=lam,
        compressive_load_demand=P_comp,
        critical_load=P_cr,
        critical_stress=sigma_cr,
        margin=margin,
        applicable=applicable,
        passes=passes,
    )
