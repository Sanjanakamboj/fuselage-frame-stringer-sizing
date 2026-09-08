"""Illustrative preliminary crippling-strength study for STM-09 Milestone 5.

Uses the same illustrative material and representative I/Z/hat geometries
as the Milestone 2-4 examples, under the common combined load, to answer:

    Even when a thin built-up section passes elastic material yield,
    local plate buckling, and global Euler stability, could the section's
    flange/web assembly reach a lower empirical crippling limit first?

**Crippling correlations are empirical, configuration-dependent curve
fits to test data.** The correlation used here (alpha=1.2, m=0.6) is
explicitly illustrative -- NOT sourced from MMPDS, NASA, or any vendor
test database. It is chosen once (per the milestone's suggested range),
documented, and then applied consistently -- it is not tuned to force a
particular outcome.
"""

from __future__ import annotations

from frame_stringer.beam_column import assess_beam_column
from frame_stringer.built_up_strength import assess_builtup_strength
from frame_stringer.column_buckling import MemberGeometry
from frame_stringer.crippling import CripplingCorrelation, assess_section_crippling
from frame_stringer.geometry import RectangularSection
from frame_stringer.local_buckling import (
    assess_section_local_buckling,
    hat_section_plate_elements,
    i_section_plate_elements,
    z_section_plate_elements,
)
from frame_stringer.loads import SectionLoad
from frame_stringer.mass import linear_mass
from frame_stringer.material import IsotropicMaterial
from frame_stringer.strength import assess_section_strength
from frame_stringer.structural_status import assess_structural_status

PANEL_LENGTH = 0.30  # m -- same illustrative frame/stiffener spacing as Milestone 3
MEMBER_LENGTH = 1.2  # m -- same illustrative member length as Milestone 4
K_FACTOR = 1.0

CORRELATION = CripplingCorrelation(
    alpha=1.2,
    exponent=0.6,
    label="Illustrative baseline (alpha=1.2, m=0.6)",
    source_note="illustrative only -- not sourced from MMPDS, NASA, or any test database",
)


def _fmt(x, fmt="{:.2f}"):
    return "n/a" if x is None else fmt.format(x)


class _TrivialLocalBuckling:
    """Stand-in for the rectangle, which has no Milestone 3 plate mapping."""

    passes = True
    min_margin = None


def main() -> None:
    material = IsotropicMaterial(
        name="Illustrative Al 2024-T3-like",
        elastic_modulus=70e9,
        poisson_ratio=0.33,
        density=2700.0,
        yield_strength=300e6,
    )

    rectangle = RectangularSection(width=0.019916, height=0.08)
    i_model = i_section_plate_elements(
        flange_width=0.06, overall_height=0.10, flange_thickness=0.0095, web_thickness=0.006, panel_length=PANEL_LENGTH
    )
    z_model = z_section_plate_elements(
        web_height=0.08, web_thickness=0.0058, flange_width=0.05, flange_thickness=0.011, panel_length=PANEL_LENGTH
    )
    hat_model = hat_section_plate_elements(
        crown_width=0.065, overall_height=0.07, wall_thickness=0.0068, flange_width=0.028, panel_length=PANEL_LENGTH
    )

    sections = [
        ("Rectangle", rectangle, None),
        ("I-section", i_model.section, i_model),
        ("Z-section", z_model.section, z_model),
        ("Hat-section", hat_model.section, hat_model),
    ]

    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    member = MemberGeometry(length=MEMBER_LENGTH, effective_length_factor=K_FACTOR)

    print("=" * 110)
    print("STM-09 Milestone 5 -- Illustrative Preliminary Crippling Screen")
    print("=" * 110)
    print(
        f"\nCorrelation: {CORRELATION.label}\n"
        f"  sigma_cc = alpha*sqrt(E*sigma_y)*(t/b_ref)^m, capped at sigma_y\n"
        f"  Note: {CORRELATION.source_note}"
    )
    print(f"\nMember: L = {MEMBER_LENGTH*1e3:.0f} mm, K = {K_FACTOR:.2f}; panel length = {PANEL_LENGTH*1e3:.0f} mm")
    print(
        "\nLOADS (common combined load, applied to every section)\n"
        f"  N = {load.axial_force/1e3:.2f} kN, V_y = {load.shear_force_y/1e3:.2f} kN, "
        f"M_z = {load.bending_moment_z/1e3:.2f} kN*m"
    )

    print("\nPRELIMINARY STRUCTURAL STATUS")
    header = (
        f"  {'section':<12}{'yield MS':>9}{'local MS':>9}{'Euler MS':>9}{'amp-yld MS':>11}"
        f"{'crip MS':>9}{'governing':>16}{'gov MS':>9}{'status':>8}"
    )
    print(header)

    results = {}
    for name, section, model in sections:
        if model is None:
            yield_r = assess_section_strength(load, section, material)
            lb_r = _TrivialLocalBuckling()
            crip_r = None
        else:
            yield_r = assess_builtup_strength(load, section, material)
            lb_r = assess_section_local_buckling(model, load, material)
            crip_r = assess_section_crippling(model, material, CORRELATION, load)
        bc_r = assess_beam_column(member, section, material, load)
        status = assess_structural_status(yield_r, lb_r, bc_r, crip_r)
        results[name] = (yield_r, lb_r, bc_r, crip_r, status)

        print(
            f"  {name:<12}"
            f"{_fmt(status.yield_margin):>9}"
            f"{_fmt(status.local_buckling_margin):>9}"
            f"{_fmt(status.euler_margin):>9}"
            f"{_fmt(status.amplified_yield_margin):>11}"
            f"{_fmt(status.crippling_margin):>9}"
            f"{status.governing_check:>16}"
            f"{_fmt(status.governing_margin):>9}"
            f"{'PASS' if status.overall_preliminary_pass else 'FAIL':>8}"
        )

    print(
        "\nNote: crippling is reported N/A for the compact rectangle -- it is not a\n"
        "thin-walled built-up section, so the illustrative correlation is not\n"
        "applied to it (see README for the engineering rationale)."
    )

    print("\n" + "=" * 110)
    print("CRIPPLING DETAIL (I/Z/hat)")
    print("=" * 110)
    header2 = (
        f"  {'section':<12} {'gov elem':<12} {'b_ref[mm]':>9} {'t[mm]':>6} {'b/t':>6}"
        f" {'raw sig_cc':>10} {'cap sig_cc':>10} {'cap?':>5} {'Pcrip[kN]':>9}"
        f" {'axial MS':>8} {'peak MS':>8} {'mode':>16} {'status':>6}"
    )
    print(header2)
    for name in ("I-section", "Z-section", "Hat-section"):
        _, _, _, crip_r, _ = results[name]
        print(
            f"  {name:<12} {crip_r.governing_element:<12}"
            f" {crip_r.b_ref * 1e3:>9.1f} {crip_r.t_ref * 1e3:>6.2f} {crip_r.governing_bt:>6.1f}"
            f" {crip_r.raw_crippling_stress / 1e6:>10.0f} {crip_r.crippling_stress / 1e6:>10.0f}"
            f" {'YES' if crip_r.yield_cap_active else 'no':>5}"
            f" {crip_r.equivalent_crippling_load / 1e3:>9.1f}"
            f" {_fmt(crip_r.axial_average_margin, '{:.2f}'):>8}"
            f" {_fmt(crip_r.peak_compression_margin, '{:.2f}'):>8}"
            f" {crip_r.governing_mode:>16}"
            f" {'PASS' if crip_r.passes else 'FAIL':>6}"
        )

    print(
        "\nAll three representative sections show the raw correlation prediction\n"
        "well above material yield -- the yield cap is active in every case, so\n"
        "the CAPPED crippling stress equals sigma_y (300 MPa) throughout, and the\n"
        "reported crippling margins closely track the amplified-yield margins.\n"
        "This is the honest result of applying the milestone's suggested\n"
        "illustrative coefficient range (alpha in [1.0, 2.0], m in [0.5, 0.8]) to\n"
        "these particular, fairly stocky built-up proportions (governing b/t of\n"
        "8-14) -- it was not tuned to produce this outcome."
    )

    # ---- sensitivity studies (I-section) ----
    base = dict(flange_width=0.06, overall_height=0.10, flange_thickness=0.0095, web_thickness=0.006)

    print("\n" + "=" * 110)
    print("SENSITIVITY A: WEB THICKNESS (I-section)")
    print("=" * 110)
    print(f"  {'scale':>7}{'b/t':>7}{'raw [MPa]':>11}{'cap [MPa]':>11}{'margin':>9}{'mass [kg/m]':>13}")
    for scale in (0.75, 1.0, 1.25, 1.5):
        params = dict(base)
        params["web_thickness"] = base["web_thickness"] * scale
        model = i_section_plate_elements(panel_length=PANEL_LENGTH, **params)
        r = assess_section_crippling(model, material, CORRELATION, load)
        m_prime = linear_mass(model.section, material)
        print(
            f"  {scale:>7.2f}{r.governing_bt:>7.1f}{r.raw_crippling_stress/1e6:>11.0f}"
            f"{r.crippling_stress/1e6:>11.0f}{_fmt(r.governing_margin):>9}{m_prime:>13.3f}"
        )

    print("\n" + "=" * 110)
    print("SENSITIVITY B: FLANGE OUTSTAND WIDTH (I-section)")
    print("=" * 110)
    print(f"  {'scale':>7} {'gov elem':<12} {'b/t':>6} {'raw [MPa]':>10} {'cap [MPa]':>10} {'margin':>8}")
    for scale in (0.75, 1.0, 1.25, 1.5):
        params = dict(base)
        b_out_base = (base["flange_width"] - base["web_thickness"]) / 2.0
        params["flange_width"] = base["web_thickness"] + 2 * (b_out_base * scale)
        model = i_section_plate_elements(panel_length=PANEL_LENGTH, **params)
        r = assess_section_crippling(model, material, CORRELATION, load)
        print(
            f"  {scale:>7.2f} {r.governing_element:<12} {r.governing_bt:>6.1f}"
            f" {r.raw_crippling_stress/1e6:>10.0f} {r.crippling_stress/1e6:>10.0f} {_fmt(r.governing_margin):>8}"
        )
    print(
        "\n  Note: the web (b/t=13.5) remains more slender than the flange outstand\n"
        "  throughout this range, so it continues to govern -- widening the flange\n"
        "  here changes section area (and hence compressive stress demand) but does\n"
        "  not itself change the governing element or its b/t."
    )

    print("\n" + "=" * 110)
    print("SENSITIVITY C: CORRELATION COEFFICIENT ALPHA (I-section, baseline geometry)")
    print("=" * 110)
    print(f"  {'scale':>7}{'alpha':>7}{'raw [MPa]':>11}{'cap [MPa]':>11}{'margin':>9}{'cap active?':>13}")
    i_model_baseline = i_section_plate_elements(panel_length=PANEL_LENGTH, **base)
    for scale in (0.75, 1.0, 1.25, 1.5):
        corr = CripplingCorrelation(
            alpha=1.2 * scale, exponent=0.6, label="scaled", source_note="illustrative"
        )
        r = assess_section_crippling(i_model_baseline, material, corr, load)
        print(
            f"  {scale:>7.2f}{corr.alpha:>7.2f}{r.raw_crippling_stress/1e6:>11.0f}"
            f"{r.crippling_stress/1e6:>11.0f}{_fmt(r.governing_margin):>9}"
            f"{'YES' if r.yield_cap_active else 'no':>13}"
        )
    print(
        "\n  The yield cap remains active across this entire alpha range for the\n"
        "  baseline geometry -- the capped crippling stress (and hence margin) does\n"
        "  not change with alpha here. This is an honest plateau, not a modeling\n"
        "  error: it shows the coefficient's effect is masked once the raw\n"
        "  correlation already predicts well above yield."
    )

    print("\n" + "=" * 110)
    print("SENSITIVITY D: CORRELATION EXPONENT M (I-section, baseline geometry, alpha=1.2)")
    print("=" * 110)
    print(f"  {'m':>7}{'raw [MPa]':>11}{'cap [MPa]':>11}{'margin':>9}{'cap active?':>13}")
    for m in (0.4, 0.5, 0.6, 0.7, 0.8):
        corr = CripplingCorrelation(alpha=1.2, exponent=m, label="scaled", source_note="illustrative")
        r = assess_section_crippling(i_model_baseline, material, corr, load)
        print(
            f"  {m:>7.2f}{r.raw_crippling_stress/1e6:>11.0f}{r.crippling_stress/1e6:>11.0f}"
            f"{_fmt(r.governing_margin):>9}{'YES' if r.yield_cap_active else 'no':>13}"
        )
    print(
        "\n  The raw correlation varies strongly with the exponent (686-1942 MPa over\n"
        "  m=0.8-0.4), demonstrating the model's real sensitivity to an assumption\n"
        "  that is itself illustrative -- but every value here still exceeds yield\n"
        "  for this geometry, so the capped result and margin again plateau. No\n"
        "  single exponent is claimed to be 'correct'."
    )

    print("\n" + "=" * 110)
    print("ENGINEERING INTERPRETATION")
    print("=" * 110)
    print(
        "  - Bending-efficient thin-walled sections (Milestone 2) can, in principle,\n"
        "    have an empirical crippling strength below material yield -- but whether\n"
        "    that happens depends heavily on the section's actual b/t proportions and\n"
        "    on the (here illustrative, unsourced) correlation coefficients.\n"
        "  - For these particular I/Z/hat proportions (governing b/t of 8-14), the\n"
        "    illustrative correlation with alpha in [1.0, 2.0] and m in [0.5, 0.8]\n"
        "    predicts strength above yield throughout -- crippling does not govern\n"
        "    below yield here. A more slender (thinner, wider) built-up element would\n"
        "    be needed to see this illustrative model predict crippling below yield.\n"
        "  - Local plate buckling (Milestone 3) is an instability of one individual\n"
        "    plate element, derived from first-principles elastic theory. Crippling\n"
        "    is a broader, empirical, section-collapse phenomenon fitted to test\n"
        "    data -- it can (in general, for other proportions/coefficients) predict\n"
        "    a lower capacity than the ideal elastic local-buckling stress, because\n"
        "    real thin elements often fail before reaching that ideal eigenvalue.\n"
        "  - Global Euler buckling (Milestone 4) is a whole-member instability,\n"
        "    essentially independent of individual element b/t.\n"
        "  - The governing mechanism among yield, local buckling, Euler, amplified\n"
        "    yield, and crippling can shift as section proportions change -- none of\n"
        "    these checks is blended into the others; `StructuralStatus` reports\n"
        "    them side by side and the 'governing check' is simply whichever\n"
        "    independently computed margin is smallest.\n"
        "  - None of this is a certification allowable, and the crippling numbers\n"
        "    above should not be read with more precision than the underlying\n"
        "    (illustrative, unsourced) correlation coefficients warrant."
    )

    print("\n" + "=" * 110)


if __name__ == "__main__":
    main()
