"""Representative sanity case for STM-09 Milestone 1.

A single illustrative fuselage-frame/stringer-like rectangular beam segment,
under a representative combined axial + shear + bending load, run through
the full mechanics chain: geometry -> normal stress -> shear stress ->
combined von Mises strength screen -> reference capacities -> mass.

This is a demonstration of the mechanics, not a design case. Loads are
illustrative and were chosen to give a useful (non-trivial, non-tuned)
combined-stress demonstration -- not to force a PASS or FAIL.
"""

from __future__ import annotations

from frame_stringer.geometry import RectangularSection
from frame_stringer.loads import SectionLoad
from frame_stringer.mass import linear_mass
from frame_stringer.material import IsotropicMaterial
from frame_stringer.strength import (
    assess_section_strength,
    axial_yield_load,
    bending_yield_moment,
    shear_yield_load,
)
from frame_stringer.stress import evaluate_normal_stress, max_shear_stress


def main() -> None:
    # ---- section: illustrative rectangular baseline ----
    section = RectangularSection(width=0.040, height=0.080)  # b=40mm, h=80mm

    # ---- material: illustrative aluminum-like isotropic material ----
    material = IsotropicMaterial(
        name="Illustrative Al 2024-T3-like",
        elastic_modulus=70e9,  # ~70 GPa
        poisson_ratio=0.33,
        density=2700.0,  # kg/m^3
        yield_strength=300e6,  # ~300 MPa (illustrative, not an allowable)
    )

    # ---- representative combined load ----
    load = SectionLoad(
        axial_force=-80e3,  # N, compression
        shear_force_y=25e3,  # N
        bending_moment_z=4e3,  # N*m
    )

    print("=" * 60)
    print("STM-09 Milestone 1 -- Frame/Stringer Sanity Case")
    print("=" * 60)

    print("\nSECTION")
    print(f"  b (width)          = {section.width * 1e3:.2f} mm")
    print(f"  h (height)         = {section.height * 1e3:.2f} mm")
    print(f"  A (area)           = {section.area * 1e6:.3f} mm^2")
    print(f"  I_z                = {section.moment_of_inertia_z * 1e12:.4f} mm^4")
    print(f"  S_z                = {section.section_modulus_z * 1e9:.4f} mm^3")

    print("\nMATERIAL")
    print(f"  name               = {material.name}")
    print(f"  E                  = {material.elastic_modulus / 1e9:.1f} GPa")
    print(f"  yield strength     = {material.yield_strength / 1e6:.1f} MPa")
    print(f"  density            = {material.density:.1f} kg/m^3")

    print("\nLOADS")
    print(f"  N (axial)          = {load.axial_force / 1e3:.2f} kN")
    print(f"  V_y (shear)        = {load.shear_force_y / 1e3:.2f} kN")
    print(f"  M_z (bending)      = {load.bending_moment_z / 1e3:.2f} kN*m")

    normal = evaluate_normal_stress(load, section)
    print("\nNORMAL STRESS")
    print(f"  axial              = {normal.axial_stress / 1e6:.2f} MPa")
    print(f"  top (y=+h/2)       = {normal.top_stress / 1e6:.2f} MPa")
    print(f"  bottom (y=-h/2)    = {normal.bottom_stress / 1e6:.2f} MPa")

    tau_max = max_shear_stress(load, section)
    print("\nSHEAR")
    print(f"  neutral-axis max   = {tau_max / 1e6:.2f} MPa")

    strength = assess_section_strength(load, section, material)
    print("\nCOMBINED STRENGTH TABLE")
    header = f"  {'location':<14}{'y [mm]':>10}{'sigma_x [MPa]':>16}{'tau_xy [MPa]':>15}{'sigma_vm [MPa]':>17}{'margin':>10}{'status':>8}"
    print(header)
    for point in (strength.top, strength.neutral_axis, strength.bottom):
        margin_str = "n/a" if point.margin is None else f"{point.margin:.3f}"
        status = "PASS" if point.passes else "FAIL"
        print(
            f"  {point.location:<14}"
            f"{point.y * 1e3:>10.2f}"
            f"{point.sigma_x / 1e6:>16.2f}"
            f"{point.tau_xy / 1e6:>15.2f}"
            f"{point.sigma_vm / 1e6:>17.2f}"
            f"{margin_str:>10}"
            f"{status:>8}"
        )

    print("\nGOVERNING")
    print(f"  location           = {strength.governing_location}")
    print(f"  sigma_vm           = {strength.governing_sigma_vm / 1e6:.2f} MPa")
    min_margin_str = (
        "n/a" if strength.min_margin is None else f"{strength.min_margin:.3f}"
    )
    print(f"  yield margin       = {min_margin_str}")
    print(f"  status             = {'PASS' if strength.passes else 'FAIL'}")

    N_y = axial_yield_load(section, material)
    M_y = bending_yield_moment(section, material)
    V_yield = shear_yield_load(section, material)
    print("\nREFERENCE CAPACITIES (verification quantities, not allowables)")
    print(f"  N_y (axial)        = {N_y / 1e3:.2f} kN")
    print(f"  M_y (bending)      = {M_y / 1e3:.2f} kN*m")
    print(f"  V_yield (shear)    = {V_yield / 1e3:.2f} kN")

    m_prime = linear_mass(section, material)
    print("\nMASS")
    print(f"  m' (per unit len)  = {m_prime:.3f} kg/m")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
