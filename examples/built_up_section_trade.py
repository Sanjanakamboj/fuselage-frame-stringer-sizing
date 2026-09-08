"""Equal-area section-efficiency trade study for STM-09 Milestone 2.

Compares a compact rectangle against I-, Z-, and hat-section built-up
members of comparable area, under the Milestone 1 representative combined
load, to answer:

    How much bending efficiency is gained by moving material away from
    the neutral axis, and how does the stress/shear distribution change
    for realistic frame/stringer-like sections?

Uses the same illustrative aluminum-like material as Milestone 1. Section
geometries were chosen to keep areas within a few percent of one another
(not tuned to force every section to pass or fail) -- see the printed
areas for the actual (small) spread.
"""

from __future__ import annotations

from frame_stringer.built_up_geometry import BuiltUpSection
from frame_stringer.built_up_strength import assess_builtup_strength, bending_yield_capacity
from frame_stringer.built_up_stress import evaluate_combined_stress
from frame_stringer.geometry import RectangularSection
from frame_stringer.loads import SectionLoad
from frame_stringer.mass import linear_mass
from frame_stringer.material import IsotropicMaterial
from frame_stringer.sections import hat_section, i_section, z_section
from frame_stringer.strength import assess_section_strength, bending_yield_moment


def main() -> None:
    material = IsotropicMaterial(
        name="Illustrative Al 2024-T3-like",
        elastic_modulus=70e9,
        poisson_ratio=0.33,
        density=2700.0,
        yield_strength=300e6,
    )

    # ---- comparable-area sections (areas kept within ~4% of one another) ----
    rectangle = RectangularSection(width=0.019916, height=0.08)
    i_sec = i_section(
        flange_width=0.06, overall_height=0.10, flange_thickness=0.0095, web_thickness=0.006
    )
    z_sec = z_section(
        web_height=0.08, web_thickness=0.0058, flange_width=0.05, flange_thickness=0.011
    )
    hat_sec = hat_section(
        crown_width=0.065, overall_height=0.07, wall_thickness=0.0068, flange_width=0.028
    )

    sections = [
        ("Rectangle", rectangle),
        ("I-section", i_sec),
        ("Z-section", z_sec),
        ("Hat-section", hat_sec),
    ]

    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)

    print("=" * 100)
    print("STM-09 Milestone 2 -- Equal-Area Section Efficiency Trade")
    print("=" * 100)

    print("\nSECTION PROPERTY TRADE")
    header = (
        f"  {'section':<12}{'A [mm2]':>10}{'m'' [kg/m]':>12}{'cy [mm]':>10}"
        f"{'Iz [1e6 mm4]':>14}{'S_top [1e3 mm3]':>17}{'S_bot [1e3 mm3]':>17}"
        f"{'Iz/A':>10}{'minS/A':>10}"
    )
    print(header)

    props = {}
    for name, section in sections:
        A = section.area
        m_prime = linear_mass(section, material)
        if name == "Rectangle":
            centroid_y = 0.0
            I_z = section.moment_of_inertia_z
            S_top = section.section_modulus_z
            S_bottom = section.section_modulus_z
        else:
            centroid_y = section.centroid_y
            I_z = section.moment_of_inertia_z
            S_top = section.S_top
            S_bottom = section.S_bottom

        iz_over_a = I_z / A
        min_s_over_a = min(S_top, S_bottom) / A
        props[name] = dict(
            A=A, m_prime=m_prime, centroid_y=centroid_y, I_z=I_z,
            S_top=S_top, S_bottom=S_bottom, iz_over_a=iz_over_a, min_s_over_a=min_s_over_a,
        )
        print(
            f"  {name:<12}"
            f"{A * 1e6:>10.2f}"
            f"{m_prime:>12.3f}"
            f"{centroid_y * 1e3:>10.2f}"
            f"{I_z * 1e9:>14.4f}"
            f"{S_top * 1e9:>17.2f}"
            f"{S_bottom * 1e9:>17.2f}"
            f"{iz_over_a * 1e3:>10.4f}"
            f"{min_s_over_a * 1e3:>10.4f}"
        )

    print("\nLOADS (Milestone 1 representative combined load, applied to every section)")
    print(f"  N (axial)          = {load.axial_force / 1e3:.2f} kN")
    print(f"  V_y (shear)        = {load.shear_force_y / 1e3:.2f} kN")
    print(f"  M_z (bending)      = {load.bending_moment_z / 1e3:.2f} kN*m")

    print("\nSTRENGTH TRADE TABLE")
    header2 = f"  {'section':<12}{'governing':>18}{'sigma_vm [MPa]':>16}{'margin':>10}{'status':>8}"
    print(header2)

    strength_results = {}
    for name, section in sections:
        if name == "Rectangle":
            result = assess_section_strength(load, section, material)
        else:
            result = assess_builtup_strength(load, section, material)
        strength_results[name] = result
        margin_str = "n/a" if result.min_margin is None else f"{result.min_margin:.3f}"
        status = "PASS" if result.passes else "FAIL"
        print(
            f"  {name:<12}"
            f"{result.governing_location:>18}"
            f"{result.governing_sigma_vm / 1e6:>16.2f}"
            f"{margin_str:>10}"
            f"{status:>8}"
        )

    print("\nI-SECTION DETAILED STRESS TABLE (demonstrates the flange/web shear jump)")
    header3 = f"  {'location':<20}{'y [mm]':>10}{'sigma_x [MPa]':>16}{'tau_xy [MPa]':>15}{'sigma_vm [MPa]':>17}{'margin':>10}"
    print(header3)
    i_result = strength_results["I-section"]
    for point in i_result.points:
        margin_str = "n/a" if point.margin is None else f"{point.margin:.3f}"
        print(
            f"  {point.label:<20}"
            f"{point.y * 1e3:>10.3f}"
            f"{point.sigma_x / 1e6:>16.2f}"
            f"{point.tau_xy / 1e6:>15.2f}"
            f"{point.sigma_vm / 1e6:>17.2f}"
            f"{margin_str:>10}"
        )

    print("\nENGINEERING INTERPRETATION")
    print(
        "  - The rectangle is the most compact section but the least bending-efficient:\n"
        "    its Iz/A and min(S)/A are the lowest of the four, because most of its area\n"
        "    sits close to the neutral axis.\n"
        "  - The I- and Z-sections push a large fraction of their area into flanges far\n"
        "    from the neutral axis, roughly tripling Iz/A and min(S)/A relative to the\n"
        "    rectangle at essentially the same total area (and mass/length).\n"
        "  - The hat section is intermediate here: its crown and outward flanges move\n"
        "    material outward, but its combined-width web carries a large area fraction\n"
        "    close to the neutral axis, and its asymmetric geometry means S_top and\n"
        "    S_bottom differ -- both must be computed, never assumed equal.\n"
        "  - The I-section detailed stress table shows sigma_x peaking at the extreme\n"
        "    fibers (zero at the flange/web junctions is NOT implied -- only shear\n"
        "    peaks at the neutral axis), while tau_xy jumps sharply at the flange/web\n"
        "    junction because the local width collapses from the flange width down to\n"
        "    the much smaller web thickness -- the web carries much higher shear stress\n"
        "    per unit area than the flanges do.\n"
        "  - All four sections pass this representative combined load with this load\n"
        "    case and material -- none were tuned to force a pass or fail.\n"
        "  - Thin flanges and webs that improve bending efficiency also raise local\n"
        "    plate-buckling and crippling concerns; those are explicitly deferred to a\n"
        "    later milestone."
    )

    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
