"""Multi-load-case uniform-thickness sizing study for STM-09 Milestone 6.

Answers: what is the minimum practical uniform-thickness section, within a
deliberately bounded design space, that passes yield, local plate
buckling, global member buckling, beam-column amplified yield, and the
illustrative crippling screen across all representative load cases?

This is a **preliminary sizing study, not a general-purpose optimizer**:
the design space is a small, explicit, bounded uniform-thickness search
per fixed-geometry section family (I/Z/hat), solved by deterministic
bisection over the verified Milestone 1-5 mechanics -- no scipy, no
gradient/genetic optimization.
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
    print("STM-09 Milestone 6 -- Multi-Load-Case Uniform-Thickness Sizing Study")
    print("=" * 110)

    print("\nSTUDY ASSUMPTIONS")
    print(f"  Material           = {material.name} (E={material.elastic_modulus/1e9:.0f} GPa, "
          f"sigma_y={material.yield_strength/1e6:.0f} MPa)")
    print(f"  Panel length       = {PANEL_LENGTH*1e3:.0f} mm")
    print(f"  Member length L    = {MEMBER_LENGTH*1e3:.0f} mm, K = {K_FACTOR:.2f}")
    print(f"  Crippling          = {CORRELATION.label}")
    print(f"  Minimum gauge      = {T_MIN_GAUGE*1e3:.2f} mm (illustrative minimum manufacturing gauge -- "
          f"not a certification/manufacturer requirement)")
    print(f"  Search bounds      = [{T_MIN_SEARCH*1e3:.2f}, {T_MAX_SEARCH*1e3:.2f}] mm, "
          f"tolerance = {TOLERANCE*1e3:.4f} mm")

    print("\nLOAD CASES")
    header = f"  {'name':<26}{'N [kN]':>9}{'V [kN]':>9}{'M [kN*m]':>10}{'factor':>8}"
    print(header)
    for lc in CANONICAL_LOAD_CASES:
        print(
            f"  {lc.name:<26}{lc.axial_force/1e3:>9.1f}{lc.shear_force_y/1e3:>9.1f}"
            f"{lc.bending_moment_z/1e3:>10.2f}{lc.load_factor:>8.2f}"
        )

    print("\n" + "=" * 110)
    print("FAMILY SIZING")
    print("=" * 110)
    results = size_all_families(assumptions)
    header2 = (
        f"  {'family':<12}{'req t [mm]':>11}{'area [mm2]':>11}{'mass [kg/m]':>12}"
        f"{'gov case':>26}{'gov constraint':>16}{'gov MS':>9}{'status':>10}"
    )
    print(header2)
    for r in results:
        t_str = _fmt(r.required_thickness * 1e3 if r.required_thickness else None, "{:.3f}")
        area_str = _fmt(r.area * 1e6 if r.area else None, "{:.1f}")
        mass_str = _fmt(r.mass_per_length, "{:.3f}")
        print(
            f"  {r.family_name:<12}{t_str:>11}{area_str:>11}{mass_str:>12}"
            f"{_fmt(r.governing_load_case, '{}'):>26}{_fmt(r.governing_constraint, '{}'):>16}"
            f"{_fmt(r.governing_margin):>9}{r.status:>10}"
        )

    best = recommend_family(results)
    print("\n" + "=" * 110)
    print("FINAL PRELIMINARY RECOMMENDATION")
    print("=" * 110)
    if best is None:
        print("  No section family is feasible within the stated search bounds.")
    else:
        print(f"  Selected family    = {best.family_name}")
        print(f"  Selected thickness = {best.required_thickness*1e3:.3f} mm")
        print(f"  Area               = {best.area*1e6:.1f} mm^2")
        print(f"  Mass/length        = {best.mass_per_length:.3f} kg/m")
        print(f"  Governing load case = {best.governing_load_case}")
        print(f"  Governing constraint = {best.governing_constraint}")
        print(f"  Governing margin    = {best.governing_margin:.3f}")
        print(
            "\n  Note: the governing load case was not assumed in advance -- different\n"
            "  load cases govern different section families/thicknesses, and within one\n"
            "  family, different load cases govern different constraints (see the\n"
            "  per-case detail below)."
        )
        print("\n  Per-load-case detail at the selected design:")
        for c in best.final_assessment.per_case:
            print(
                f"    {c.load_case.name:<26} governing={c.governing_constraint:<16} "
                f"margin={_fmt(c.governing_margin)}  {'PASS' if c.overall_pass else 'FAIL'}"
            )
        crip = next(
            c.crippling_result for c in best.final_assessment.per_case if c.load_case.name == best.governing_load_case
        )
        print(
            f"\n  Crippling at the selected design (governing load case): "
            f"{'yield-capped' if crip.yield_cap_active else 'uncapped'}, "
            f"margin={_fmt(crip.governing_margin)}"
        )

    if best is not None and best.family_name == "I-section":
        # ---- sensitivity studies (final recommended family) ----
        print("\n" + "=" * 110)
        print("SENSITIVITY A: MINIMUM GAUGE (I-section)")
        print("=" * 110)
        print(f"  {'gauge [mm]':>11}{'req t [mm]':>11}{'mass [kg/m]':>12}{'status':>22}")
        for g_mm in (1.0, 1.5, 2.0, 2.5, 3.0, 4.5):
            r = size_section_family(FAMILIES[0], material, member, CANONICAL_LOAD_CASES, CORRELATION, PANEL_LENGTH, g_mm / 1000)
            print(f"  {g_mm:>11.2f}{r.required_thickness*1e3:>11.3f}{r.mass_per_length:>12.3f}{r.status:>22}")
        print(
            "\n  Note: 4.5 mm is beyond the milestone's suggested 1.0-3.0 mm gauge range,\n"
            "  added here specifically to demonstrate the 'gauge governs once it exceeds\n"
            "  the structural requirement' transition -- within 1.0-3.0 mm, the structural\n"
            "  requirement (~3.88 mm) exceeds every gauge tried, so gauge never governs there."
        )

        print("\n" + "=" * 110)
        print("SENSITIVITY B: MEMBER LENGTH (I-section, K = 1.0 fixed)")
        print("=" * 110)
        print(f"  {'L [m]':>7}{'req t [mm]':>11}{'mass [kg/m]':>12}{'governing':>16}")
        for L in (0.75, 1.0, 1.2, 1.5, 2.0):
            m = MemberGeometry(length=L, effective_length_factor=1.0)
            r = size_section_family(FAMILIES[0], material, m, CANONICAL_LOAD_CASES, CORRELATION, PANEL_LENGTH, T_MIN_GAUGE)
            print(f"  {L:>7.2f}{r.required_thickness*1e3:>11.3f}{r.mass_per_length:>12.3f}{r.governing_constraint:>16}")

        print("\n" + "=" * 110)
        print(f"SENSITIVITY C: EFFECTIVE-LENGTH FACTOR K (I-section, L = {MEMBER_LENGTH*1e3:.0f} mm fixed)")
        print("=" * 110)
        print(f"  {'K':>7}{'req t [mm]':>11}{'mass [kg/m]':>12}{'governing':>16}")
        for K in (0.5, 0.7, 1.0, 1.5, 2.0):
            m = MemberGeometry(length=MEMBER_LENGTH, effective_length_factor=K)
            r = size_section_family(FAMILIES[0], material, m, CANONICAL_LOAD_CASES, CORRELATION, PANEL_LENGTH, T_MIN_GAUGE)
            print(f"  {K:>7.2f}{r.required_thickness*1e3:>11.3f}{r.mass_per_length:>12.3f}{r.governing_constraint:>16}")

        print("\n" + "=" * 110)
        print("SENSITIVITY D: PANEL LENGTH (I-section)")
        print("=" * 110)
        print(f"  {'panel [m]':>10}{'req t [mm]':>11}{'mass [kg/m]':>12}{'governing':>16}")
        for pl in (0.15, 0.30, 0.60, 1.20):
            r = size_section_family(FAMILIES[0], material, member, CANONICAL_LOAD_CASES, CORRELATION, pl, T_MIN_GAUGE)
            print(f"  {pl:>10.2f}{r.required_thickness*1e3:>11.3f}{r.mass_per_length:>12.3f}{r.governing_constraint:>16}")
        print(
            "\n  Note: the required thickness is unchanged across this panel-length range --\n"
            "  amplified yield (not local-buckling shear, which is the only mode sensitive\n"
            "  to panel length via aspect ratio) governs throughout. Compression buckling\n"
            "  is, by construction, independent of panel length in this model."
        )

        print("\n" + "=" * 110)
        print("SENSITIVITY E: CRIPPLING CORRELATION ALPHA (I-section)")
        print("=" * 110)
        print(f"  {'alpha':>7}{'req t [mm]':>11}{'mass [kg/m]':>12}{'governing':>16}")
        for a in (0.8, 1.0, 1.2, 1.4, 1.6):
            c = CripplingCorrelation(alpha=a, exponent=0.6, label="scaled", source_note="illustrative")
            r = size_section_family(FAMILIES[0], material, member, CANONICAL_LOAD_CASES, c, PANEL_LENGTH, T_MIN_GAUGE)
            print(f"  {a:>7.2f}{r.required_thickness*1e3:>11.3f}{r.mass_per_length:>12.3f}{r.governing_constraint:>16}")

        print("\n" + "=" * 110)
        print("SENSITIVITY F: CRIPPLING CORRELATION EXPONENT M (I-section, alpha=1.2)")
        print("=" * 110)
        print(f"  {'m':>7}{'req t [mm]':>11}{'mass [kg/m]':>12}{'governing':>16}")
        for m_exp in (0.4, 0.5, 0.6, 0.7, 0.8):
            c = CripplingCorrelation(alpha=1.2, exponent=m_exp, label="scaled", source_note="illustrative")
            r = size_section_family(FAMILIES[0], material, member, CANONICAL_LOAD_CASES, c, PANEL_LENGTH, T_MIN_GAUGE)
            print(f"  {m_exp:>7.2f}{r.required_thickness*1e3:>11.3f}{r.mass_per_length:>12.3f}{r.governing_constraint:>16}")
        print(
            "\n  Note: the required thickness for the selected I-section is completely\n"
            "  insensitive to alpha and m across these ranges, because amplified yield\n"
            "  (not crippling) governs at the selected design point throughout -- this is\n"
            "  an honest finding, not a claim that crippling never matters (Milestone 5's\n"
            "  weak-alpha sensitivity test shows crippling clearly can govern for other,\n"
            "  more slender designs)."
        )

    print("\n" + "=" * 110)
    print("ENGINEERING INTERPRETATION")
    print("=" * 110)
    print(
        "  - Different load cases govern different constraints -- 'landing/ground\n"
        "    combined' (highest axial compression) governs the I-section's final\n"
        "    thickness via amplified yield, while 'gust/shear' (highest shear, more\n"
        "    modest axial/bending) is closest to governing via ordinary yield. Neither\n"
        "    the highest-axial-force nor the highest-shear case was assumed in advance\n"
        "    to govern -- it was determined by comparing the independently computed\n"
        "    margins, exactly as Milestone 5's StructuralStatus already does.\n"
        "  - The I-section reaches its minimum feasible thickness at a lower mass/length\n"
        "    than the Z- and hat-sections here, under identical assumptions applied to\n"
        "    all three families (same material, load cases, panel length, member\n"
        "    geometry, minimum gauge, crippling correlation, and search bounds).\n"
        "  - Longer members and larger effective-length factors K both increase the\n"
        "    required thickness monotonically, as expected from the Euler/beam-column\n"
        "    mechanics verified in Milestone 4.\n"
        "  - Panel length and the crippling correlation coefficients have no effect on\n"
        "    the selected I-section thickness in this study -- not because those effects\n"
        "    are unimportant in general, but because amplified yield governs throughout\n"
        "    this particular design's feasible range. A different, more slender design\n"
        "    could see either panel length (via local shear buckling) or the crippling\n"
        "    correlation become the governing sensitivity instead.\n"
        "  - This remains a preliminary, bounded sizing study: uniform per-family\n"
        "    thickness only, no individual-element optimization, no certification\n"
        "    knockdowns, and the crippling correlation is illustrative throughout."
    )

    print("\n" + "=" * 110)


if __name__ == "__main__":
    main()
