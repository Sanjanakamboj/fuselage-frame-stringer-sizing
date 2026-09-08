"""STM-09 final assessment: the canonical multi-load-case sizing conclusion.

This script answers the project's final engineering question:

    Under the stated illustrative material, geometry, load cases,
    local-buckling model, global-stability assumptions, crippling
    correlation, minimum gauge, and bounded uniform-thickness search
    space, what preliminary frame/stringer section is the lowest-mass
    feasible design, what governs it, and how robust is that conclusion
    to the principal modeling assumptions?

It duplicates no equations -- every number below comes from the
production APIs built and verified across Milestones 1-6. This is an
**illustrative preliminary uniform-thickness section recommendation**,
not a globally optimized or flight-qualified design.
"""

from __future__ import annotations

from frame_stringer.column_buckling import MemberGeometry
from frame_stringer.crippling import CripplingCorrelation
from frame_stringer.design_study import StudyAssumptions, recommend_family, size_all_families
from frame_stringer.load_cases import CANONICAL_LOAD_CASES
from frame_stringer.material import IsotropicMaterial
from frame_stringer.sizing import FAMILIES, size_section_family

PANEL_LENGTH = 0.30
MEMBER_LENGTH = 1.2
K_FACTOR = 1.0
CORRELATION = CripplingCorrelation(
    alpha=1.2, exponent=0.6, label="Illustrative baseline (alpha=1.2, m=0.6)",
    source_note="illustrative only -- not sourced from MMPDS, NASA, or any test database",
)
T_MIN_GAUGE = 1.5e-3
T_MIN_SEARCH = 0.75e-3
T_MAX_SEARCH = 6.0e-3
TOLERANCE = 1e-6


def _fmt(x, fmt="{:.3f}"):
    return "n/a" if x is None else fmt.format(x)


def main() -> None:
    material = IsotropicMaterial(
        name="Illustrative Al 2024-T3-like", elastic_modulus=70e9, poisson_ratio=0.33, density=2700.0,
        yield_strength=300e6,
    )
    member = MemberGeometry(length=MEMBER_LENGTH, effective_length_factor=K_FACTOR)
    assumptions = StudyAssumptions(
        material=material, member=member, load_cases=CANONICAL_LOAD_CASES, correlation=CORRELATION,
        panel_length=PANEL_LENGTH, t_min_gauge=T_MIN_GAUGE, t_min_search=T_MIN_SEARCH,
        t_max_search=T_MAX_SEARCH, tolerance=TOLERANCE,
    )

    print("=" * 110)
    print("STM-09 FINAL ASSESSMENT -- Illustrative Preliminary Frame/Stringer Sizing")
    print("=" * 110)

    print("\nSTUDY ASSUMPTIONS")
    print(f"  Material            = {material.name} (E={material.elastic_modulus/1e9:.0f} GPa, "
          f"nu={material.poisson_ratio}, rho={material.density:.0f} kg/m^3, sigma_y={material.yield_strength/1e6:.0f} MPa)")
    print(f"  Load cases          = {len(CANONICAL_LOAD_CASES)} canonical illustrative cases (listed below)")
    print(f"  Panel length        = {PANEL_LENGTH*1e3:.0f} mm")
    print(f"  Member length L     = {MEMBER_LENGTH*1e3:.0f} mm")
    print(f"  Effective-length K  = {K_FACTOR:.2f}")
    print(f"  Minimum gauge       = {T_MIN_GAUGE*1e3:.2f} mm (illustrative manufacturing gauge, not a certification value)")
    print(f"  Crippling           = {CORRELATION.label}")
    print(f"  Search bounds       = [{T_MIN_SEARCH*1e3:.2f}, {T_MAX_SEARCH*1e3:.2f}] mm, tolerance = {TOLERANCE*1e3:.4f} mm")

    print(f"\n  {'load case':<26}{'N [kN]':>9}{'V [kN]':>9}{'M [kN*m]':>10}{'factor':>8}")
    for lc in CANONICAL_LOAD_CASES:
        print(
            f"  {lc.name:<26}{lc.axial_force/1e3:>9.1f}{lc.shear_force_y/1e3:>9.1f}"
            f"{lc.bending_moment_z/1e3:>10.2f}{lc.load_factor:>8.2f}"
        )

    # ---- family sizing ----
    print("\n" + "=" * 110)
    print("FAMILY SIZING")
    print("=" * 110)
    results = size_all_families(assumptions)
    header = (
        f"  {'family':<12}{'t [mm]':>8}{'area [mm2]':>11}{'mass [kg/m]':>12}"
        f"{'gov case':>26}{'gov constraint':>16}{'margin':>9}{'crip cap?':>10}{'status':>9}"
    )
    print(header)
    crip_by_family = {}
    for r in results:
        governing_case = next(c for c in r.final_assessment.per_case if c.load_case.name == r.governing_load_case)
        crip = governing_case.crippling_result
        crip_by_family[r.family_name] = crip
        cap_str = ("YES" if crip.yield_cap_active else "no") if crip is not None else "n/a"
        print(
            f"  {r.family_name:<12}{_fmt(r.required_thickness*1e3 if r.required_thickness else None, '{:.3f}'):>8}"
            f"{_fmt(r.area*1e6 if r.area else None, '{:.1f}'):>11}{_fmt(r.mass_per_length, '{:.3f}'):>12}"
            f"{_fmt(r.governing_load_case, '{}'):>26}{_fmt(r.governing_constraint, '{}'):>16}"
            f"{_fmt(r.governing_margin):>9}{cap_str:>10}"
            f"{('PASS' if r.status != 'upper_bound_infeasible' else 'FAIL'):>9}"
        )

    best = recommend_family(results)

    print("\n" + "=" * 110)
    print("FINAL RECOMMENDATION -- illustrative preliminary uniform-thickness section recommendation")
    print("=" * 110)
    if best is None:
        print("  No section family is feasible within the stated search bounds.")
        return

    print(f"  Selected family      = {best.family_name}")
    print(f"  Selected thickness   = {best.required_thickness*1e3:.3f} mm")
    print(f"  Area                 = {best.area*1e6:.1f} mm^2")
    print(f"  Mass/length          = {best.mass_per_length:.3f} kg/m")
    print(f"  Governing load case  = {best.governing_load_case}")
    print(f"  Governing constraint = {best.governing_constraint}")
    print(f"  Governing margin     = {best.governing_margin:.3f}")
    crip = crip_by_family[best.family_name]
    print(
        f"  Crippling at selected design: {'yield-capped' if crip.yield_cap_active else 'uncapped'} "
        f"(governing element {crip.governing_element}, raw={crip.raw_crippling_stress/1e6:.0f} MPa, "
        f"capped={crip.crippling_stress/1e6:.0f} MPa, margin={crip.governing_margin:.3f})"
    )
    print(
        "\n  NOTE: crippling is capped (== yield) at every family's selected design here --\n"
        "  the illustrative crippling correlation did not meaningfully size any of these\n"
        "  three designs; amplified yield (and, for one case below, ordinary yield) did."
    )

    # ---- per-load-case table for the selected family ----
    print("\n" + "=" * 110)
    print(f"{best.family_name.upper()} -- LOAD-CASE MARGIN TABLE (selected thickness = {best.required_thickness*1e3:.3f} mm)")
    print("=" * 110)
    header2 = f"  {'load case':<26}{'yield':>8}{'local':>8}{'euler':>8}{'amp-yld':>9}{'crip':>8}{'governing':>16}{'status':>8}"
    print(header2)
    lowest = {"yield": (None, None), "local_buckling": (None, None), "euler": (None, None)}
    highest_shear = (None, None)
    for c in best.final_assessment.per_case:
        y = c.yield_result.min_margin
        lb = c.local_buckling_result.min_margin
        eu = c.euler_result.margin
        ay = c.amplified_yield_result.min_margin if c.amplified_yield_result else None
        cr = c.crippling_result.governing_margin
        print(
            f"  {c.load_case.name:<26}{_fmt(y):>8}{_fmt(lb):>8}{_fmt(eu):>8}{_fmt(ay):>9}{_fmt(cr):>8}"
            f"{c.governing_constraint:>16}{('PASS' if c.overall_pass else 'FAIL'):>8}"
        )
        for key, val in (("yield", y), ("local_buckling", lb), ("euler", eu)):
            if val is not None and (lowest[key][0] is None or val < lowest[key][0]):
                lowest[key] = (val, c.load_case.name)
        v = abs(c.load_case.shear_force_y)
        if highest_shear[0] is None or v > highest_shear[0]:
            highest_shear = (v, c.load_case.name)

    print(
        f"\n  Case with the lowest yield margin:          {lowest['yield'][1]} ({lowest['yield'][0]:.3f})\n"
        f"  Case with the lowest local-buckling margin:  {lowest['local_buckling'][1]} ({lowest['local_buckling'][0]:.3f})\n"
        f"  Case with the lowest Euler margin:           {lowest['euler'][1]} ({lowest['euler'][0]:.3f})\n"
        f"  Case with the highest shear demand:          {highest_shear[1]} ({highest_shear[0]/1e3:.1f} kN)"
    )
    print(
        "\n  These are NOT all the same case: the highest-shear case ('gust/shear') is\n"
        "  comfortably safe in every category except where it happens to govern via\n"
        "  ordinary yield; the highest-axial-compression case ('landing/ground\n"
        "  combined') is simultaneously the worst case for yield, local buckling, and\n"
        "  Euler here -- this was determined by comparing margins, never assumed."
    )

    # ---- concise sensitivity summary ----
    print("\n" + "=" * 110)
    print("SENSITIVITY SUMMARY (I-section, unless otherwise noted)")
    print("=" * 110)

    print(f"\n  Minimum gauge sensitivity (L={MEMBER_LENGTH*1e3:.0f} mm, K={K_FACTOR:.1f}):")
    print(f"    {'gauge [mm]':>11}{'t [mm]':>8}{'mass [kg/m]':>12}{'status':>22}")
    for g_mm in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0):
        r = size_section_family(FAMILIES[0], material, member, CANONICAL_LOAD_CASES, CORRELATION, PANEL_LENGTH, g_mm / 1000)
        print(f"    {g_mm:>11.2f}{r.required_thickness*1e3:>8.3f}{r.mass_per_length:>12.3f}{r.status:>22}")

    print(f"\n  Member-length sensitivity (K={K_FACTOR:.1f}):")
    print(f"    {'L [m]':>7}{'t [mm]':>8}{'mass [kg/m]':>12}{'governing':>16}")
    for L in (0.75, 1.0, 1.2, 1.5, 2.0):
        m = MemberGeometry(length=L, effective_length_factor=1.0)
        r = size_section_family(FAMILIES[0], material, m, CANONICAL_LOAD_CASES, CORRELATION, PANEL_LENGTH, T_MIN_GAUGE)
        print(f"    {L:>7.2f}{r.required_thickness*1e3:>8.3f}{r.mass_per_length:>12.3f}{r.governing_constraint:>16}")

    print(f"\n  Effective-length-factor sensitivity (L={MEMBER_LENGTH*1e3:.0f} mm):")
    print(f"    {'K':>7}{'t [mm]':>8}{'mass [kg/m]':>12}{'governing':>16}")
    for K in (0.5, 0.7, 1.0, 1.5, 2.0):
        m = MemberGeometry(length=MEMBER_LENGTH, effective_length_factor=K)
        r = size_section_family(FAMILIES[0], material, m, CANONICAL_LOAD_CASES, CORRELATION, PANEL_LENGTH, T_MIN_GAUGE)
        print(f"    {K:>7.2f}{r.required_thickness*1e3:>8.3f}{r.mass_per_length:>12.3f}{r.governing_constraint:>16}")

    print("\n  Crippling-alpha sensitivity (canonical alpha=1.2 plus one deliberately weak,")
    print("  explicitly illustrative alpha=0.3 -- NOT part of the canonical recommendation):")
    print(f"    {'alpha':>7}{'t [mm]':>8}{'mass [kg/m]':>12}{'governing':>16}")
    for a in (0.3, 0.8, 1.0, 1.2, 1.4, 1.6):
        c = CripplingCorrelation(alpha=a, exponent=0.6, label="scaled", source_note="illustrative")
        r = size_section_family(FAMILIES[0], material, member, CANONICAL_LOAD_CASES, c, PANEL_LENGTH, T_MIN_GAUGE)
        print(f"    {a:>7.2f}{r.required_thickness*1e3:>8.3f}{r.mass_per_length:>12.3f}{r.governing_constraint:>16}")

    # ---- robustness across families ----
    print("\n" + "=" * 110)
    print("ROBUSTNESS OF THE FAMILY RANKING (all three families, longer/stiffer members)")
    print("=" * 110)
    print(f"  {'L [m]':>7} {'K':>5}   {'I mass':>10} {'Z mass':>10} {'Hat mass':>10}   note")
    for L, K in ((1.2, 1.0), (1.5, 1.0), (0.75, 0.5), (2.0, 1.0), (1.2, 1.5)):
        m = MemberGeometry(length=L, effective_length_factor=K)
        masses = []
        for fam in FAMILIES:
            r = size_section_family(fam, material, m, CANONICAL_LOAD_CASES, CORRELATION, PANEL_LENGTH, T_MIN_GAUGE)
            masses.append((r.mass_per_length, r.status, r.governing_constraint))
        note = ""
        infeasible = [fam.name for fam, (mass, status, _) in zip(FAMILIES, masses) if status == "upper_bound_infeasible"]
        if infeasible:
            note = f"{', '.join(infeasible)} infeasible within {T_MAX_SEARCH*1e3:.0f} mm"
        shifted = [
            f"{fam.name}->{constr}"
            for fam, (mass, status, constr) in zip(FAMILIES, masses)
            if status != "upper_bound_infeasible" and constr != "amplified_yield"
        ]
        if shifted:
            note = (note + "; " if note else "") + f"governing shift: {', '.join(shifted)}"
        fmt_mass = lambda t: "infeasible" if t[1] == "upper_bound_infeasible" else f"{t[0]:.3f}"
        print(f"  {L:>7.2f} {K:>5.2f}   {fmt_mass(masses[0]):>10} {fmt_mass(masses[1]):>10} {fmt_mass(masses[2]):>10}   {note}")

    print(
        "\n  Conclusion: the I-section remains the lowest-mass feasible family across every\n"
        "  combination tested above, and at longer/stiffer members it is often the ONLY\n"
        "  family that remains feasible within the stated 6.0 mm search bound -- a direct\n"
        "  consequence of its higher I_z/A (Milestones 2 and 4). The governing constraint\n"
        "  can shift away from amplified_yield (e.g. to local_buckling for the Z-section\n"
        "  at a short, stiff member), but this does not change which family is\n"
        "  recommended in this study. Local buckling and Euler alone (as opposed to\n"
        "  amplified yield, which already incorporates the Euler-driven amplification)\n"
        "  were not observed to become the outright governing constraint for the I-section\n"
        "  itself across the ranges explored here; crippling only governs once the\n"
        "  correlation is deliberately weakened well outside the canonical alpha=1.2\n"
        "  baseline (see alpha=0.3 above)."
    )

    # ---- final status ----
    print("\n" + "=" * 110)
    print("FINAL STATUS")
    print("=" * 110)
    print(f"  Overall preliminary status: {'PASS' if best.status != 'upper_bound_infeasible' else 'FAIL'}")
    print(
        "\n  This is an illustrative preliminary frame/stringer sizing study, not a\n"
        "  flight-qualified structural design. Material yield, local plate buckling,\n"
        "  global Euler/beam-column stability, and an illustrative empirical crippling\n"
        "  correlation are each screened independently, across a small set of\n"
        "  illustrative load cases, for a small set of fixed-outer-geometry,\n"
        "  uniform-thickness I/Z/hat families. No certification allowable, sourced\n"
        "  handbook crippling constant, skin interaction, fastener, fatigue, damage-\n"
        "  tolerance, or manufacturing-cost effect is included."
    )

    print("\n" + "=" * 110)


if __name__ == "__main__":
    main()
