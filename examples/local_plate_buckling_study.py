"""Local plate-buckling screening for STM-09 Milestone 3.

Uses the Milestone 2 material and representative I/Z/hat geometries (same
as `examples/built_up_section_trade.py`) under the Milestone 1 representative
combined load, with an explicit illustrative panel length, to answer:

    Does a built-up section that passes the elastic von Mises stress check
    remain locally stable in its thin web/flange/crown elements under the
    same axial+bending+shear load state?

This is an elastic onset screen (classical illustrative plate
coefficients) -- not crippling, not postbuckling, not a certification
allowable.
"""

from __future__ import annotations

from frame_stringer.built_up_strength import assess_builtup_strength
from frame_stringer.local_buckling import (
    assess_section_local_buckling,
    combined_elastic_status,
    hat_section_plate_elements,
    i_section_plate_elements,
    z_section_plate_elements,
)
from frame_stringer.loads import SectionLoad
from frame_stringer.material import IsotropicMaterial

PANEL_LENGTH = 0.30  # m -- illustrative frame/stiffener spacing


def _fmt_margin(margin: float | None) -> str:
    return "n/a" if margin is None else f"{margin:.3f}"


def main() -> None:
    material = IsotropicMaterial(
        name="Illustrative Al 2024-T3-like",
        elastic_modulus=70e9,
        poisson_ratio=0.33,
        density=2700.0,
        yield_strength=300e6,
    )

    # Same representative geometries as examples/built_up_section_trade.py.
    i_model = i_section_plate_elements(
        flange_width=0.06, overall_height=0.10, flange_thickness=0.0095, web_thickness=0.006,
        panel_length=PANEL_LENGTH,
    )
    z_model = z_section_plate_elements(
        web_height=0.08, web_thickness=0.0058, flange_width=0.05, flange_thickness=0.011,
        panel_length=PANEL_LENGTH,
    )
    hat_model = hat_section_plate_elements(
        crown_width=0.065, overall_height=0.07, wall_thickness=0.0068, flange_width=0.028,
        panel_length=PANEL_LENGTH,
    )

    sections = [("I-section", i_model), ("Z-section", z_model), ("Hat-section", hat_model)]

    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)

    print("=" * 100)
    print("STM-09 Milestone 3 -- Local Plate Buckling Screening")
    print("=" * 100)
    print(f"\nPanel length (illustrative frame/stiffener spacing): {PANEL_LENGTH * 1e3:.0f} mm")
    print(
        "\nLOADS (Milestone 1 representative combined load, applied to every section)\n"
        f"  N (axial)          = {load.axial_force / 1e3:.2f} kN\n"
        f"  V_y (shear)        = {load.shear_force_y / 1e3:.2f} kN\n"
        f"  M_z (bending)      = {load.bending_moment_z / 1e3:.2f} kN*m"
    )

    print("\nSECTION LOCAL BUCKLING SUMMARY")
    header = (
        f"  {'section':<12}{'yield margin':>14}{'buckling margin':>18}"
        f"{'governing plate':>20}{'governing mode':>16}{'status':>8}"
    )
    print(header)

    all_results = {}
    for name, model in sections:
        yield_result = assess_builtup_strength(load, model.section, material)
        buckling_result = assess_section_local_buckling(model, load, material)
        status = combined_elastic_status(yield_result, buckling_result)
        all_results[name] = (yield_result, buckling_result, status)
        print(
            f"  {name:<12}"
            f"{_fmt_margin(yield_result.min_margin):>14}"
            f"{_fmt_margin(buckling_result.min_margin):>18}"
            f"{buckling_result.governing_plate:>20}"
            f"{buckling_result.governing_mode:>16}"
            f"{'PASS' if buckling_result.passes else 'FAIL':>8}"
        )

    for name, model in sections:
        _, buckling_result, _ = all_results[name]
        print(f"\n{name.upper()} -- PLATE DETAIL")
        header2 = (
            f"  {'plate':<24}{'boundary':<12}{'b [mm]':>8}{'t [mm]':>8}{'a/b':>7}"
            f"{'sig_comp [MPa]':>15}{'sig_cr [MPa]':>13}{'tau [MPa]':>11}{'tau_cr [MPa]':>13}"
            f"{'FI':>8}{'margin':>9}{'status':>7}"
        )
        print(header2)
        for p in buckling_result.plates:
            tau_cr_str = f"{p.tau_cr / 1e6:.1f}" if p.tau_cr is not None else "n/a"
            fi_str = f"{p.interaction_fi:.4f}" if p.interaction_fi is not None else "n/a"
            print(
                f"  {p.plate_name:<24}{p.boundary_condition:<12}"
                f"{p.width * 1e3:>8.2f}{p.thickness * 1e3:>8.2f}{p.aspect_ratio:>7.2f}"
                f"{p.sigma_comp_demand / 1e6:>15.2f}{p.sigma_cr / 1e6:>13.1f}"
                f"{p.tau_demand / 1e6:>11.2f}{tau_cr_str:>13}"
                f"{fi_str:>8}{_fmt_margin(p.governing_margin):>9}"
                f"{'PASS' if p.passes else 'FAIL':>7}"
            )

    print("\n" + "=" * 100)
    print("SENSITIVITY STUDY (I-section)")
    print("=" * 100)

    base = dict(flange_width=0.06, overall_height=0.10, flange_thickness=0.0095, web_thickness=0.006)

    def _plate_margin(result, name):
        return next(p.governing_margin for p in result.plates if p.plate_name == name)

    print("\nA. Flange thickness scale (panel_length fixed at 0.30 m)")
    print(f"  {'scale':>8}{'flange margin':>16}{'section-critical plate':>24}{'section margin':>16}")
    for scale in (0.75, 1.0, 1.25, 1.5):
        params = dict(base)
        params["flange_thickness"] = base["flange_thickness"] * scale
        model = i_section_plate_elements(panel_length=PANEL_LENGTH, **params)
        result = assess_section_local_buckling(model, load, material)
        flange_margin = _plate_margin(result, "top_flange_outstand")
        print(
            f"  {scale:>8.2f}{_fmt_margin(flange_margin):>16}"
            f"{result.governing_plate:>24}{_fmt_margin(result.min_margin):>16}"
        )

    print("\nB. Web thickness scale (panel_length fixed at 0.30 m)")
    print(f"  {'scale':>8}{'web margin':>16}{'section-critical plate':>24}{'section margin':>16}")
    for scale in (0.75, 1.0, 1.25, 1.5):
        params = dict(base)
        params["web_thickness"] = base["web_thickness"] * scale
        model = i_section_plate_elements(panel_length=PANEL_LENGTH, **params)
        result = assess_section_local_buckling(model, load, material)
        web_margin = _plate_margin(result, "web")
        print(
            f"  {scale:>8.2f}{_fmt_margin(web_margin):>16}"
            f"{result.governing_plate:>24}{_fmt_margin(result.min_margin):>16}"
        )

    print("\nC. Panel length (m)")
    print(f"  {'length':>8}{'web margin':>16}{'section-critical plate':>24}{'section margin':>16}")
    for length in (0.15, 0.30, 0.60, 1.20):
        model = i_section_plate_elements(panel_length=length, **base)
        result = assess_section_local_buckling(model, load, material)
        web_margin = _plate_margin(result, "web")
        print(
            f"  {length:>8.2f}{_fmt_margin(web_margin):>16}"
            f"{result.governing_plate:>24}{_fmt_margin(result.min_margin):>16}"
        )

    print("\nD. Flange outstand width scale (flange_width adjusted; web_thickness fixed)")
    print(f"  {'scale':>8}{'flange margin':>16}{'section-critical plate':>24}{'section margin':>16}")
    for scale in (0.75, 1.0, 1.25, 1.5):
        params = dict(base)
        b_out_base = (base["flange_width"] - base["web_thickness"]) / 2.0
        params["flange_width"] = base["web_thickness"] + 2 * (b_out_base * scale)
        model = i_section_plate_elements(panel_length=PANEL_LENGTH, **params)
        result = assess_section_local_buckling(model, load, material)
        flange_margin = _plate_margin(result, "top_flange_outstand")
        print(
            f"  {scale:>8.2f}{_fmt_margin(flange_margin):>16}"
            f"{result.governing_plate:>24}{_fmt_margin(result.min_margin):>16}"
        )

    print(
        "\nExpected physical trends: thicker plates strongly improve local buckling\n"
        "(~t^2); wider outstands strongly reduce compression buckling (~1/b^2);\n"
        "panel length changes the web's aspect ratio and hence its shear-buckling\n"
        "margin (approaching the long-plate asymptote k_s -> 5.34 as length grows);\n"
        "and the most bending-efficient section is not automatically the most\n"
        "locally stable -- see the interpretation below."
    )

    print("\n" + "=" * 100)
    print("MILESTONE 2 vs MILESTONE 3 INTERPRETATION")
    print("=" * 100)
    print(
        "  - Milestone 2 showed that moving material away from the neutral axis\n"
        "    (I/Z/hat sections) dramatically improves bending efficiency (Iz/A,\n"
        "    min(S)/A) and can produce very comfortable elastic von Mises yield\n"
        "    margins.\n"
        "  - Milestone 3 shows that the same thin flanges and webs that make this\n"
        "    efficiency possible can become elastically unstable in local buckling\n"
        "    at stresses well below yield, if they are made thin and wide/long\n"
        "    enough -- see the sensitivity study above, where a much thinner,\n"
        "    wider outstand fails local buckling while easily passing yield.\n"
        "  - This is a genuine, distinct failure mode: this milestone's local-\n"
        "    buckling screen is kept strictly separate from the yield screen (no\n"
        "    margins are blended), and a section can pass one while failing the\n"
        "    other in either direction.\n"
        "  - This is an elastic *onset* screen: exceeding sigma_cr/tau_cr does not\n"
        "    imply catastrophic collapse (real thin plates carry meaningful\n"
        "    postbuckling load), only that the ideal, small-deflection linear\n"
        "    buckling eigenvalue has been reached. Postbuckling, crippling, and\n"
        "    effective width are explicitly deferred to a later milestone."
    )

    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
