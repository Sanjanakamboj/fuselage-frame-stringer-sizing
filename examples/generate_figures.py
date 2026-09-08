"""Generate the STM-09 portfolio figures into figures/ (deterministic PNGs).

Requires the optional `figures` extra: `pip install -e ".[figures]"`.

No new physics or equations are introduced here -- every plotted value
comes directly from the production APIs (the same ones exercised by
`examples/final_frame_stringer_assessment.py`). Regenerating this script
with unchanged code and inputs reproduces byte-identical PNGs (Agg
backend, fixed DPI, no wall-clock/random content).
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from frame_stringer.column_buckling import MemberGeometry
from frame_stringer.crippling import CripplingCorrelation
from frame_stringer.design_study import StudyAssumptions, recommend_family, size_all_families
from frame_stringer.load_cases import CANONICAL_LOAD_CASES
from frame_stringer.material import IsotropicMaterial
from frame_stringer.sizing import FAMILIES, size_section_family

HERE = os.path.dirname(os.path.abspath(__file__))
FIGURES_DIR = os.path.normpath(os.path.join(HERE, "..", "figures"))

PANEL_LENGTH = 0.30
MEMBER_LENGTH = 1.2
K_FACTOR = 1.0
CORRELATION = CripplingCorrelation(
    alpha=1.2, exponent=0.6, label="Illustrative baseline (alpha=1.2, m=0.6)",
    source_note="illustrative only",
)
T_MIN_GAUGE = 1.5e-3
DPI = 150

COLORS = {"I-section": "#2b6cb0", "Z-section": "#c05621", "Hat-section": "#2f855a"}


def _study_results():
    material = IsotropicMaterial(
        name="Illustrative Al 2024-T3-like", elastic_modulus=70e9, poisson_ratio=0.33, density=2700.0,
        yield_strength=300e6,
    )
    member = MemberGeometry(length=MEMBER_LENGTH, effective_length_factor=K_FACTOR)
    assumptions = StudyAssumptions(
        material=material, member=member, load_cases=CANONICAL_LOAD_CASES, correlation=CORRELATION,
        panel_length=PANEL_LENGTH, t_min_gauge=T_MIN_GAUGE,
    )
    results = size_all_families(assumptions)
    best = recommend_family(results)
    return material, member, assumptions, results, best


def _draw_i_section(ax, t, flange_width=0.06, overall_height=0.10):
    h_web = overall_height - 2 * t
    color = COLORS["I-section"]
    # bottom flange
    ax.add_patch(mpatches.Rectangle((-flange_width / 2, -overall_height / 2), flange_width, t, fc=color, ec="black"))
    # top flange
    ax.add_patch(mpatches.Rectangle((-flange_width / 2, overall_height / 2 - t), flange_width, t, fc=color, ec="black"))
    # web
    ax.add_patch(mpatches.Rectangle((-t / 2, -h_web / 2), t, h_web, fc=color, ec="black"))
    return flange_width, overall_height


def _draw_z_section(ax, t, web_height=0.08, flange_width=0.05):
    overall_height = web_height + 2 * t
    color = COLORS["Z-section"]
    # web (centered)
    ax.add_patch(mpatches.Rectangle((-t / 2, -web_height / 2), t, web_height, fc=color, ec="black"))
    # top flange extends to +z
    ax.add_patch(mpatches.Rectangle((-t / 2, web_height / 2), flange_width, t, fc=color, ec="black"))
    # bottom flange extends to -z
    ax.add_patch(mpatches.Rectangle((-flange_width + t / 2, -web_height / 2 - t), flange_width, t, fc=color, ec="black"))
    total_width = flange_width + t / 2
    return total_width, overall_height


def _draw_hat_section(ax, t, crown_width=0.065, overall_height=0.07, flange_width=0.028):
    web_run = overall_height - 2 * t
    color = COLORS["Hat-section"]
    half_crown = crown_width / 2
    # crown (top)
    ax.add_patch(mpatches.Rectangle((-half_crown, overall_height / 2 - t), crown_width, t, fc=color, ec="black"))
    # two webs, at the shoulders under the crown
    ax.add_patch(mpatches.Rectangle((-half_crown, -overall_height / 2 + t), t, web_run, fc=color, ec="black"))
    ax.add_patch(mpatches.Rectangle((half_crown - t, -overall_height / 2 + t), t, web_run, fc=color, ec="black"))
    # two outward flanges at the base
    ax.add_patch(mpatches.Rectangle((-half_crown - flange_width + t, -overall_height / 2), flange_width, t, fc=color, ec="black"))
    ax.add_patch(mpatches.Rectangle((half_crown - t, -overall_height / 2), flange_width, t, fc=color, ec="black"))
    total_width = crown_width + 2 * (flange_width - t)
    return total_width, overall_height


def figure_1_section_geometry(results):
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.2))
    drawers = {"I-section": _draw_i_section, "Z-section": _draw_z_section, "Hat-section": _draw_hat_section}
    for ax, r in zip(axes, results):
        t = r.required_thickness
        w, h = drawers[r.family_name](ax, t)
        margin = max(w, h) * 0.35
        ax.set_xlim(-w / 2 - margin, w / 2 + margin)
        ax.set_ylim(-h / 2 - margin, h / 2 + margin)
        ax.set_aspect("equal")
        ax.set_title(f"{r.family_name}\nt = {t*1e3:.2f} mm, mass = {r.mass_per_length:.2f} kg/m", fontsize=10)
        ax.set_xlabel("z [m]")
        ax.set_ylabel("y [m]")
        ax.grid(alpha=0.25, linewidth=0.5)
    fig.suptitle("STM-09 Final Section Geometries (at selected thickness, schematic in z)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = os.path.join(FIGURES_DIR, "fig1_section_geometry.png")
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def figure_2_family_comparison(results):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    names = [r.family_name for r in results]
    thicknesses = [r.required_thickness * 1e3 for r in results]
    masses = [r.mass_per_length for r in results]
    colors = [COLORS[n] for n in names]

    ax1.bar(names, thicknesses, color=colors, edgecolor="black")
    ax1.set_ylabel("Required uniform thickness [mm]")
    ax1.set_title("Required thickness")
    for i, v in enumerate(thicknesses):
        ax1.text(i, v + 0.05, f"{v:.2f}", ha="center", fontsize=9)
    ax1.tick_params(axis="x", rotation=15)

    ax2.bar(names, masses, color=colors, edgecolor="black")
    ax2.set_ylabel("Mass per unit length [kg/m]")
    ax2.set_title("Mass per unit length")
    for i, v in enumerate(masses):
        ax2.text(i, v + 0.03, f"{v:.2f}", ha="center", fontsize=9)
    ax2.tick_params(axis="x", rotation=15)

    best_idx = min(range(len(masses)), key=lambda i: masses[i])
    ax2.get_children()[best_idx].set_edgecolor("gold")
    ax2.get_children()[best_idx].set_linewidth(2.5)
    fig.suptitle("Family Sizing Comparison -- lowest mass (gold outline) selected", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    path = os.path.join(FIGURES_DIR, "fig2_family_comparison.png")
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def figure_3_constraint_margins(best):
    checks = ["yield", "local", "euler", "amp_yield", "crippling"]
    labels = ["Yield", "Local\nbuckling", "Euler", "Amplified\nyield", "Crippling"]
    case_names = [c.load_case.name for c in best.final_assessment.per_case]

    data = []
    for c in best.final_assessment.per_case:
        row = [
            c.yield_result.min_margin,
            c.local_buckling_result.min_margin,
            c.euler_result.margin,
            c.amplified_yield_result.min_margin if c.amplified_yield_result else None,
            c.crippling_result.governing_margin,
        ]
        data.append(row)

    fig, ax = plt.subplots(figsize=(9, 5))
    n_cases = len(case_names)
    n_checks = len(checks)
    bar_width = 0.8 / n_checks
    x = range(n_cases)
    palette = plt.cm.tab10.colors
    # Euler margins are an order of magnitude larger than the other checks
    # here (Euler has the most headroom); clip the visible axis so the
    # tighter, more decision-relevant margins (yield, amplified yield,
    # crippling) stay readable, and label clipped bars with their true value.
    y_cap = 3.0
    for j in range(n_checks):
        vals = [row[j] if row[j] is not None else 0.0 for row in data]
        offsets = [xi + (j - n_checks / 2) * bar_width + bar_width / 2 for xi in x]
        plotted = [min(v, y_cap) for v in vals]
        bars = ax.bar(offsets, plotted, width=bar_width, label=labels[j].replace("\n", " "), color=palette[j], edgecolor="black", linewidth=0.5)
        for bar, v in zip(bars, vals):
            if v > y_cap:
                ax.text(bar.get_x() + bar.get_width() / 2, y_cap + 0.05, f"{v:.1f}", ha="center", va="bottom", fontsize=7, rotation=90)

    ax.axhline(0.0, color="red", linewidth=1.2, linestyle="--", label="zero-margin boundary")
    ax.set_ylim(top=y_cap + 0.6)
    ax.set_xticks(list(x))
    ax.set_xticklabels(case_names, rotation=12, ha="right")
    ax.set_ylabel(f"Margin (capped at {y_cap:.0f}; true value labeled above)")
    fig.suptitle(f"{best.family_name} -- Constraint Margins by Load Case (t = {best.required_thickness*1e3:.2f} mm)", fontsize=12)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.14), fontsize=8, ncol=3, frameon=False)
    ax.grid(axis="y", alpha=0.3, linewidth=0.5)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    path = os.path.join(FIGURES_DIR, "fig3_constraint_margins.png")
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def figure_4_sizing_sensitivity(material, assumptions):
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)

    lengths = [0.75, 1.0, 1.2, 1.5, 2.0]
    t_vs_L = []
    for L in lengths:
        m = MemberGeometry(length=L, effective_length_factor=K_FACTOR)
        r = size_section_family(FAMILIES[0], material, m, CANONICAL_LOAD_CASES, CORRELATION, PANEL_LENGTH, T_MIN_GAUGE)
        t_vs_L.append(r.required_thickness * 1e3)
    axes[0].plot(lengths, t_vs_L, marker="o", color=COLORS["I-section"])
    axes[0].set_xlabel("Member length L [m]")
    axes[0].set_ylabel("Required I-section thickness [mm]")
    axes[0].set_title("Sensitivity to member length (K=1.0)")
    axes[0].grid(alpha=0.3, linewidth=0.5)

    ks = [0.5, 0.7, 1.0, 1.5, 2.0]
    t_vs_K = []
    for K in ks:
        m = MemberGeometry(length=MEMBER_LENGTH, effective_length_factor=K)
        r = size_section_family(FAMILIES[0], material, m, CANONICAL_LOAD_CASES, CORRELATION, PANEL_LENGTH, T_MIN_GAUGE)
        t_vs_K.append(r.required_thickness * 1e3)
    axes[1].plot(ks, t_vs_K, marker="s", color="#805ad5")
    axes[1].set_xlabel("Effective-length factor K")
    axes[1].set_title(f"Sensitivity to K (L={MEMBER_LENGTH*1e3:.0f} mm)")
    axes[1].grid(alpha=0.3, linewidth=0.5)

    fig.suptitle("I-section Sizing Sensitivity to Global-Stability Assumptions", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    path = os.path.join(FIGURES_DIR, "fig4_sizing_sensitivity.png")
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def figure_5_crippling_alpha_sensitivity(material, member):
    alphas = [0.3, 0.8, 1.0, 1.2, 1.4, 1.6]
    thicknesses = []
    governing = []
    for a in alphas:
        c = CripplingCorrelation(alpha=a, exponent=0.6, label="scaled", source_note="illustrative")
        r = size_section_family(FAMILIES[0], material, member, CANONICAL_LOAD_CASES, c, PANEL_LENGTH, T_MIN_GAUGE)
        thicknesses.append(r.required_thickness * 1e3)
        governing.append(r.governing_constraint)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    colors = ["#e53e3e" if g == "crippling" else COLORS["I-section"] for g in governing]
    bars = ax.bar([str(a) for a in alphas], thicknesses, color=colors, edgecolor="black")
    y_top = max(thicknesses) * 1.35
    for bar, v, g in zip(bars, thicknesses, governing):
        ax.text(bar.get_x() + bar.get_width() / 2, v + y_top * 0.02, g, ha="center", fontsize=7, rotation=90, va="bottom")
    ax.axvline(0.5, color="gray", linestyle=":", linewidth=1)
    ax.text(0.02, 0.97, "alpha=0.3: weak, illustrative-only demonstration\n(not part of the canonical study)",
            transform=ax.transAxes, ha="left", va="top", fontsize=8, color="#e53e3e")
    ax.set_ylim(top=y_top)
    ax.set_xlabel("Crippling correlation alpha")
    ax.set_ylabel("Required I-section thickness [mm]")
    fig.suptitle("Crippling-Alpha Sensitivity: Canonical (alpha=1.2) vs. a Weak Case", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    path = os.path.join(FIGURES_DIR, "fig5_crippling_alpha_sensitivity.png")
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def main() -> None:
    os.makedirs(FIGURES_DIR, exist_ok=True)
    material, member, assumptions, results, best = _study_results()

    paths = [
        figure_1_section_geometry(results),
        figure_2_family_comparison(results),
        figure_3_constraint_margins(best),
        figure_4_sizing_sensitivity(material, assumptions),
        figure_5_crippling_alpha_sensitivity(material, member),
    ]
    for p in paths:
        print(f"wrote {os.path.relpath(p)}")


if __name__ == "__main__":
    main()
