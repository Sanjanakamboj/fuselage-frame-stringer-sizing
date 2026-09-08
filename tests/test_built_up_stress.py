import pytest

from frame_stringer.built_up_geometry import BuiltUpSection, RectangularComponent
from frame_stringer.built_up_stress import (
    axial_stress,
    critical_locations,
    evaluate_combined_stress,
    evaluate_normal_stress,
    normal_stress,
    shear_stress,
)
from frame_stringer.loads import SectionLoad
from frame_stringer.sections import i_section


def _i_section():
    return i_section(
        flange_width=0.05, overall_height=0.10, flange_thickness=0.005, web_thickness=0.004
    )


def _asymmetric_section():
    # centroid_y != 0, to exercise the "don't assume y_bar=0" requirement
    top = RectangularComponent(width=0.01, height=0.01, centroid_y=0.10, label="top")
    web = RectangularComponent(width=0.005, height=0.08, centroid_y=0.05, label="web")
    bottom = RectangularComponent(width=0.05, height=0.01, centroid_y=0.005, label="bottom")
    return BuiltUpSection((top, web, bottom))


# ---- normal stress (AG-AL) ----


def test_pure_axial_uniform_stress():
    section = _i_section()
    load = SectionLoad(axial_force=43000.0, shear_force_y=0.0, bending_moment_z=0.0)
    expected = 43000.0 / section.area
    for y in (section.y_top, 0.0, section.y_bottom):
        assert normal_stress(y, load, section) == pytest.approx(expected)


def test_pure_bending_zero_stress_at_centroid():
    section = _asymmetric_section()
    load = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=5000.0)
    assert normal_stress(section.centroid_y, load, section) == pytest.approx(0.0, abs=1e-6)


def test_top_bottom_stress_hand_calc():
    section = _asymmetric_section()
    load = SectionLoad(axial_force=1000.0, shear_force_y=0.0, bending_moment_z=2000.0)
    y_bar = section.centroid_y
    I = section.moment_of_inertia_z
    expected_top = 1000.0 / section.area - 2000.0 * (section.y_top - y_bar) / I
    expected_bottom = 1000.0 / section.area - 2000.0 * (section.y_bottom - y_bar) / I
    result = evaluate_normal_stress(load, section)
    assert result.top_stress == pytest.approx(expected_top)
    assert result.bottom_stress == pytest.approx(expected_bottom)


def test_axial_bending_superposition():
    section = _i_section()
    load = SectionLoad(axial_force=-80e3, shear_force_y=0.0, bending_moment_z=4e3)
    y = section.y_top
    expected = axial_stress(load, section) - 4e3 * (y - section.centroid_y) / section.moment_of_inertia_z
    assert normal_stress(y, load, section) == pytest.approx(expected)


def test_translation_invariance_of_stress():
    section = _asymmetric_section()
    dy = 0.5
    shifted = BuiltUpSection(
        tuple(
            RectangularComponent(c.width, c.height, c.centroid_y + dy, c.label)
            for c in section.components
        )
    )
    load = SectionLoad(axial_force=-20e3, shear_force_y=0.0, bending_moment_z=1500.0)
    y = section.y_top
    original = normal_stress(y, load, section)
    translated = normal_stress(y + dy, load, shifted)
    assert translated == pytest.approx(original)


def test_reversing_moment_reverses_bending_contribution():
    section = _asymmetric_section()
    load_pos = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=3000.0)
    load_neg = SectionLoad(axial_force=0.0, shear_force_y=0.0, bending_moment_z=-3000.0)
    y = section.y_top
    assert normal_stress(y, load_pos, section) == pytest.approx(
        -normal_stress(y, load_neg, section)
    )


# ---- Q / shear (AM-AV) ----


def test_Q_zero_at_top():
    section = _i_section()
    assert section.first_moment_above(section.y_top) == pytest.approx(0.0, abs=1e-12)


def test_Q_hand_calc_simple_stacked_rectangles():
    c1 = RectangularComponent(width=0.02, height=0.02, centroid_y=0.0, label="a")  # [-.01,.01]
    c2 = RectangularComponent(width=0.02, height=0.02, centroid_y=0.02, label="b")  # [.01,.03]
    section = BuiltUpSection((c1, c2))
    y_bar = section.centroid_y

    # Cut at y=0: all of c2 is above, plus the top half of c1.
    y = 0.0
    Q_expected = c2.area * (c2.centroid_y - y_bar) + (0.02 * 0.01) * (0.005 - y_bar)
    assert section.first_moment_above(y) == pytest.approx(Q_expected)


def test_b_local_hand_calc():
    section = _i_section()
    # Deep inside the web (well away from flange boundaries).
    assert section.b_local(0.0) == pytest.approx(0.004)
    # Deep inside the top flange.
    assert section.b_local(section.y_top - 0.001) == pytest.approx(0.05)


def test_i_section_web_neutral_axis_shear_hand_calc():
    section = _i_section()
    load = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=0.0)
    Q = section.first_moment_above(0.0)
    b = section.b_local(0.0)
    expected = 25e3 * abs(Q) / (section.moment_of_inertia_z * b)
    assert shear_stress(0.0, load, section) == pytest.approx(expected)


def test_shear_changes_across_flange_web_transition():
    section = _i_section()
    load = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=0.0)
    boundary = section.interior_boundaries()[-1]  # top flange/web junction
    tau_web_side = shear_stress(boundary - 1e-7, load, section)
    tau_flange_side = shear_stress(boundary + 1e-7, load, section)
    assert tau_web_side > tau_flange_side  # web is much thinner -> higher stress
    assert tau_web_side / tau_flange_side == pytest.approx(
        section.b_local(boundary + 1e-7) / section.b_local(boundary - 1e-7), rel=1e-3
    )


def test_reversing_shear_force_reverses_tau():
    section = _i_section()
    load_pos = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=0.0)
    load_neg = SectionLoad(axial_force=0.0, shear_force_y=-25e3, bending_moment_z=0.0)
    assert shear_stress(0.0, load_pos, section) == pytest.approx(
        -shear_stress(0.0, load_neg, section)
    )


def test_shear_scales_linearly_with_V():
    section = _i_section()
    load1 = SectionLoad(axial_force=0.0, shear_force_y=10e3, bending_moment_z=0.0)
    load2 = SectionLoad(axial_force=0.0, shear_force_y=30e3, bending_moment_z=0.0)
    tau1 = shear_stress(0.0, load1, section)
    tau2 = shear_stress(0.0, load2, section)
    assert tau2 == pytest.approx(3.0 * tau1)


def test_shear_rejects_y_outside_section():
    section = _i_section()
    load = SectionLoad(axial_force=0.0, shear_force_y=25e3, bending_moment_z=0.0)
    with pytest.raises(ValueError):
        shear_stress(section.y_top + 0.01, load, section)
    with pytest.raises(ValueError):
        shear_stress(section.y_bottom - 0.01, load, section)


def test_shear_void_raises_clear_error():
    # Two disjoint components with a genuine gap between them.
    a = RectangularComponent(width=0.02, height=0.01, centroid_y=0.0, label="a")  # [-.005,.005]
    b = RectangularComponent(width=0.02, height=0.01, centroid_y=0.05, label="b")  # [.045,.055]
    section = BuiltUpSection((a, b))
    load = SectionLoad(axial_force=0.0, shear_force_y=10e3, bending_moment_z=0.0)
    with pytest.raises(ValueError):
        shear_stress(0.02, load, section)  # in the gap


def test_Q_and_b_local_component_order_invariance():
    c1 = RectangularComponent(width=0.05, height=0.005, centroid_y=0.05, label="top")
    c2 = RectangularComponent(width=0.005, height=0.09, centroid_y=0.0, label="web")
    c3 = RectangularComponent(width=0.05, height=0.005, centroid_y=-0.05, label="bottom")
    s_forward = BuiltUpSection((c1, c2, c3))
    s_reversed = BuiltUpSection((c3, c2, c1))
    for y in (0.0, 0.02, -0.03):
        assert s_forward.b_local(y) == pytest.approx(s_reversed.b_local(y))
        assert s_forward.first_moment_above(y) == pytest.approx(
            s_reversed.first_moment_above(y)
        )


def test_critical_locations_includes_expected_labels():
    section = _i_section()
    labels = [label for label, _ in critical_locations(section)]
    assert "top_extreme" in labels
    assert "bottom_extreme" in labels
    assert "neutral_axis" in labels
    # I-section has two interior boundaries (top and bottom flange/web junctions),
    # each contributing a "just below" and "just above" point.
    assert sum(1 for l in labels if "boundary" in l) == 4


def test_combined_stress_state_point():
    section = _i_section()
    load = SectionLoad(axial_force=-80e3, shear_force_y=25e3, bending_moment_z=4e3)
    state = evaluate_combined_stress(0.0, load, section)
    assert state.sigma_x == pytest.approx(normal_stress(0.0, load, section))
    assert state.tau_xy == pytest.approx(shear_stress(0.0, load, section))
