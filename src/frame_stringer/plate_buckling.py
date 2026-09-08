"""Classical elastic local-plate-buckling screening for thin rectangular elements.

This module implements the *ideal elastic* (small-deflection, linear
eigenvalue) local buckling stress for a simply-idealized rectangular plate
element under uniform longitudinal compression and/or shear, using
**classical illustrative plate coefficients** -- not a sourced aerospace
design allowable, not a certification standard, and not a complete design
rule. It answers a narrower question: does this thin element remain
locally stable (in the classical elastic sense) under the stress state
extracted from the verified built-up beam solution?

Explicitly out of scope here (see the package/README limitations):
empirical crippling, postbuckling behavior, plasticity, effective-width
iteration, overall column/Euler buckling, skin-stringer interaction, and
certification knockdowns.

Buckling is kept strictly separate from the elastic von Mises yield screen
in :mod:`frame_stringer.strength` / :mod:`frame_stringer.built_up_strength`
-- the two failure modes are never blended into a single margin.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from frame_stringer.material import IsotropicMaterial

BOUNDARY_CONDITIONS = frozenset({"internal", "outstanding"})

#: Classical illustrative plate coefficients for uniform longitudinal
#: compression of a simply-supported rectangular plate. These are the
#: standard long-plate asymptotic values (4 unloaded edges simply
#: supported -> k_c = 4.0; one unloaded edge simply supported, one free
#: -> k_c = 0.43) commonly used for a first-order elastic screen. They are
#: NOT a certification allowable and do not account for edge fixity,
#: elastic edge restraint, or postbuckling behavior.
_COMPRESSION_COEFFICIENTS = {
    "internal": 4.0,
    "outstanding": 0.43,
}


def compression_buckling_coefficient(boundary_condition: str) -> float:
    """Classical illustrative compression-buckling coefficient k_c.

    - "internal" (both unloaded edges simply supported): k_c = 4.0
    - "outstanding" (one unloaded edge simply supported, one free): k_c = 0.43

    Raises
    ------
    ValueError
        If boundary_condition is not one of the recognized values.
    """
    if boundary_condition not in _COMPRESSION_COEFFICIENTS:
        raise ValueError(
            f"boundary_condition must be one of {sorted(BOUNDARY_CONDITIONS)}, "
            f"got {boundary_condition!r}"
        )
    return _COMPRESSION_COEFFICIENTS[boundary_condition]


def shear_buckling_coefficient(boundary_condition: str, aspect_ratio: float) -> float | None:
    """Classical illustrative shear-buckling coefficient k_s, or None if not applicable.

    Only defined here for an "internal" (both long edges simply supported)
    plate -- the standard simply-supported-plate shear-buckling relation:

        k_s = 5.34 + 4.0/(ratio^2)

    where ``ratio`` is the ratio of the longer plate side to the shorter
    plate side (>= 1), i.e. ``ratio = max(aspect_ratio, 1/aspect_ratio)``
    with ``aspect_ratio = length/width = a/b``. This makes the relation
    symmetric under swapping which side is called "length" vs. "width",
    which is physically required (a plate does not care which of its two
    edge lengths we happen to have labeled `a` vs. `b`).

    For an "outstanding" plate, no defensible classical shear-buckling
    coefficient is implemented here -- shear buckling of an outstanding
    (one-edge-free) flange is a materially different, more involved
    problem than the simply-supported-plate case, and is not verified in
    this milestone. This function returns ``None`` for "outstanding",
    meaning "not applicable" rather than silently reusing the internal-
    plate formula.

    Raises
    ------
    ValueError
        If boundary_condition is not one of the recognized values, or if
        aspect_ratio is not finite and > 0.
    """
    if boundary_condition not in BOUNDARY_CONDITIONS:
        raise ValueError(
            f"boundary_condition must be one of {sorted(BOUNDARY_CONDITIONS)}, "
            f"got {boundary_condition!r}"
        )
    if not math.isfinite(aspect_ratio) or aspect_ratio <= 0:
        raise ValueError(f"aspect_ratio must be finite and > 0, got {aspect_ratio!r}")

    if boundary_condition == "outstanding":
        return None

    ratio = max(aspect_ratio, 1.0 / aspect_ratio)
    return 5.34 + 4.0 / ratio**2


def _plate_buckling_prefactor(material: IsotropicMaterial, thickness: float, width: float) -> float:
    """pi^2*E / [12*(1-nu^2)] * (t/b)^2, shared by compression and shear."""
    return (
        math.pi**2
        * material.elastic_modulus
        / (12.0 * (1.0 - material.poisson_ratio**2))
        * (thickness / width) ** 2
    )


def critical_compression_stress(
    boundary_condition: str, width: float, thickness: float, material: IsotropicMaterial
) -> float:
    """Classical ideal elastic local compression-buckling stress, in Pa.

        sigma_cr = k_c * pi^2*E / [12*(1-nu^2)] * (t/b)^2

    This is the ideal elastic local plate buckling stress -- distinct from
    (and not blended with) material yield.
    """
    k_c = compression_buckling_coefficient(boundary_condition)
    return k_c * _plate_buckling_prefactor(material, thickness, width)


def critical_shear_stress(
    boundary_condition: str, width: float, length: float, thickness: float, material: IsotropicMaterial
) -> float | None:
    """Classical ideal elastic local shear-buckling stress, in Pa, or None if not applicable.

        tau_cr = k_s * pi^2*E / [12*(1-nu^2)] * (t/b)^2

    Returns ``None`` when :func:`shear_buckling_coefficient` returns
    ``None`` (currently: any "outstanding" plate).
    """
    aspect_ratio = length / width
    k_s = shear_buckling_coefficient(boundary_condition, aspect_ratio)
    if k_s is None:
        return None
    return k_s * _plate_buckling_prefactor(material, thickness, width)


@dataclass(frozen=True)
class PlateElement:
    """An idealized rectangular plate element for local buckling screening.

    Attributes
    ----------
    name : str
        Non-empty descriptive label (e.g. "web", "top_flange_outstand").
    width : float
        Unsupported plate width `b`, in m, transverse to the compressive
        stress direction (e.g. clear web height for a web, half the
        outstand for an I-flange).
    thickness : float
        Plate thickness `t`, in m.
    length : float
        Plate length `a`, in m, in the loading (longitudinal) direction --
        i.e. the panel length / frame spacing, used for the shear-buckling
        aspect ratio.
    boundary_condition : str
        "internal" or "outstanding" (see module docstring).
    role : str | None
        Optional free-form descriptive role (e.g. "web", "flange_outstand").
    """

    name: str
    width: float
    thickness: float
    length: float
    boundary_condition: str
    role: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or self.name.strip() == "":
            raise ValueError("name must be a non-empty string")
        for field_name in ("width", "thickness", "length"):
            value = getattr(self, field_name)
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite, got {value!r}")
            if value <= 0:
                raise ValueError(f"{field_name} must be > 0, got {value!r}")
        if self.boundary_condition not in BOUNDARY_CONDITIONS:
            raise ValueError(
                f"boundary_condition must be one of {sorted(BOUNDARY_CONDITIONS)}, "
                f"got {self.boundary_condition!r}"
            )
        if self.role is not None and self.role.strip() == "":
            raise ValueError("role, if supplied, must be non-empty")

    @property
    def aspect_ratio(self) -> float:
        """a/b, the plate length-to-width ratio."""
        return self.length / self.width


def compression_margin(sigma_cr: float, sigma_comp: float) -> float | None:
    """Compression-buckling margin, sigma_cr/sigma_comp - 1.

    ``sigma_comp`` must already be the non-negative compressive-stress
    magnitude (see module convention: negative sigma_x = compression).
    Returns ``None`` (trivially passing, not applicable) if sigma_comp is
    exactly zero. The boundary case sigma_comp == sigma_cr gives margin
    exactly 0 (PASS).
    """
    if sigma_comp == 0.0:
        return None
    return sigma_cr / sigma_comp - 1.0


def shear_margin(tau_cr: float | None, tau_demand: float) -> float | None:
    """Shear-buckling margin, tau_cr/|tau_demand| - 1.

    Returns ``None`` (trivially passing, not applicable) if tau_cr is
    ``None`` (shear buckling not applicable for this boundary condition)
    or if tau_demand is exactly zero.
    """
    if tau_cr is None:
        return None
    if tau_demand == 0.0:
        return None
    return tau_cr / abs(tau_demand) - 1.0


def interaction_index(
    sigma_comp: float, sigma_cr: float, tau_demand: float, tau_cr: float | None
) -> float | None:
    """Illustrative elastic local-buckling interaction index.

        FI = (sigma_comp/sigma_cr)^2 + (|tau_demand|/tau_cr)^2

    This is an **illustrative elastic local-buckling interaction screen**,
    not a universally applicable plate-buckling interaction law. Returns
    ``None`` if tau_cr is ``None`` (shear buckling not applicable -- no
    combined check is formed in that case; the compression margin alone
    governs).
    """
    if tau_cr is None:
        return None
    return (sigma_comp / sigma_cr) ** 2 + (abs(tau_demand) / tau_cr) ** 2


def interaction_margin(fi: float | None) -> float | None:
    """Margin on the interaction index, 1/sqrt(FI) - 1.

    Returns ``None`` if FI is ``None`` or exactly zero (zero combined
    demand -- trivially passing). FI == 1 gives margin exactly 0 (PASS).
    """
    if fi is None or fi == 0.0:
        return None
    return 1.0 / math.sqrt(fi) - 1.0


@dataclass(frozen=True)
class PlateBucklingResult:
    """Local-buckling assessment of a single plate element under one load state.

    Attributes
    ----------
    plate_name : str
    boundary_condition : str
    width : float
        Plate width b, in m.
    thickness : float
        Plate thickness t, in m.
    length : float
        Plate length a, in m.
    aspect_ratio : float
        a/b.
    k_c : float
        Compression-buckling coefficient used.
    k_s : float | None
        Shear-buckling coefficient used, or None if not applicable.
    sigma_cr : float
        Critical (ideal elastic) compression-buckling stress, in Pa.
    tau_cr : float | None
        Critical (ideal elastic) shear-buckling stress, in Pa, or None.
    sigma_comp_demand : float
        Compressive stress demand magnitude, in Pa (>= 0; 0 if the plate
        is entirely in tension at both sampled extremes).
    tau_demand : float
        Shear stress demand magnitude, in Pa (>= 0).
    compression_margin : float | None
    shear_margin : float | None
    interaction_fi : float | None
    interaction_margin : float | None
    governing_mode : str
        "compression", "shear", or "interaction" -- whichever gives the
        smallest (governing) margin among the modes that are applicable
        (not None). If every mode is not applicable (zero demand
        entirely), defaults to "compression" with margin None (trivial
        pass).
    governing_margin : float | None
    passes : bool
    """

    plate_name: str
    boundary_condition: str
    width: float
    thickness: float
    length: float
    aspect_ratio: float
    k_c: float
    k_s: float | None
    sigma_cr: float
    tau_cr: float | None
    sigma_comp_demand: float
    tau_demand: float
    compression_margin: float | None
    shear_margin: float | None
    interaction_fi: float | None
    interaction_margin: float | None
    governing_mode: str
    governing_margin: float | None
    passes: bool


def assess_plate_buckling(
    plate: PlateElement, material: IsotropicMaterial, sigma_x: float, tau_xy: float
) -> PlateBucklingResult:
    """Assess one plate element's local buckling margins under a stress state.

    Parameters
    ----------
    plate : PlateElement
    material : IsotropicMaterial
    sigma_x : float
        Signed longitudinal normal stress demand, in Pa (Milestone 1-2
        convention: negative = compression). The compressive-stress
        magnitude used in the buckling checks is ``max(-sigma_x, 0)``.
    tau_xy : float
        Shear stress demand, in Pa (sign irrelevant here -- magnitude used).

    The governing mode is determined by comparing the margins of every
    applicable mode ("compression", "shear", "interaction") -- never
    assumed. Deterministic tie-break: among modes tied at the minimum
    margin, the fixed order (compression, shear, interaction) decides.
    """
    sigma_comp = max(-sigma_x, 0.0)
    tau_demand = abs(tau_xy)

    k_c = compression_buckling_coefficient(plate.boundary_condition)
    sigma_cr = critical_compression_stress(
        plate.boundary_condition, plate.width, plate.thickness, material
    )
    k_s = shear_buckling_coefficient(plate.boundary_condition, plate.aspect_ratio)
    tau_cr = critical_shear_stress(
        plate.boundary_condition, plate.width, plate.length, plate.thickness, material
    )

    comp_margin = compression_margin(sigma_cr, sigma_comp)
    shr_margin = shear_margin(tau_cr, tau_demand)
    fi = interaction_index(sigma_comp, sigma_cr, tau_demand, tau_cr)
    inter_margin = interaction_margin(fi)

    candidates: list[tuple[str, float]] = []
    for mode, margin in (
        ("compression", comp_margin),
        ("shear", shr_margin),
        ("interaction", inter_margin),
    ):
        if margin is not None:
            candidates.append((mode, margin))

    if not candidates:
        governing_mode = "compression"
        governing_margin: float | None = None
        passes = True
    else:
        governing_mode, governing_margin = candidates[0]
        for mode, margin in candidates[1:]:
            if margin < governing_margin:
                governing_mode, governing_margin = mode, margin
        passes = governing_margin >= 0.0

    return PlateBucklingResult(
        plate_name=plate.name,
        boundary_condition=plate.boundary_condition,
        width=plate.width,
        thickness=plate.thickness,
        length=plate.length,
        aspect_ratio=plate.aspect_ratio,
        k_c=k_c,
        k_s=k_s,
        sigma_cr=sigma_cr,
        tau_cr=tau_cr,
        sigma_comp_demand=sigma_comp,
        tau_demand=tau_demand,
        compression_margin=comp_margin,
        shear_margin=shr_margin,
        interaction_fi=fi,
        interaction_margin=inter_margin,
        governing_mode=governing_mode,
        governing_margin=governing_margin,
        passes=passes,
    )
