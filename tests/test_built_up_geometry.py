import math

import pytest

from frame_stringer.built_up_geometry import BuiltUpSection, RectangularComponent

# ---- component tests (A-F) ----


def test_component_area_hand_calc():
    c = RectangularComponent(width=0.05, height=0.005, centroid_y=0.05, label="top")
    assert c.area == pytest.approx(0.05 * 0.005)


def test_component_centroidal_I_hand_calc():
    c = RectangularComponent(width=0.05, height=0.005, centroid_y=0.05, label="top")
    expected = 0.05 * 0.005**3 / 12.0
    assert c.moment_of_inertia_centroid == pytest.approx(expected)


def test_component_top_bottom_coordinates():
    c = RectangularComponent(width=0.05, height=0.01, centroid_y=0.2, label="x")
    assert c.top_y == pytest.approx(0.205)
    assert c.bottom_y == pytest.approx(0.195)


def test_component_invalid_width():
    with pytest.raises(ValueError):
        RectangularComponent(width=0.0, height=0.01, centroid_y=0.0)
    with pytest.raises(ValueError):
        RectangularComponent(width=-0.01, height=0.01, centroid_y=0.0)


def test_component_invalid_height():
    with pytest.raises(ValueError):
        RectangularComponent(width=0.01, height=0.0, centroid_y=0.0)
    with pytest.raises(ValueError):
        RectangularComponent(width=0.01, height=-0.01, centroid_y=0.0)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("width", math.nan),
        ("height", math.inf),
        ("centroid_y", math.nan),
        ("centroid_y", -math.inf),
    ],
)
def test_component_non_finite_rejected(field, bad_value):
    kwargs = dict(width=0.01, height=0.01, centroid_y=0.0)
    kwargs[field] = bad_value
    with pytest.raises(ValueError):
        RectangularComponent(**kwargs)


def test_component_empty_label_rejected():
    with pytest.raises(ValueError):
        RectangularComponent(width=0.01, height=0.01, centroid_y=0.0, label="   ")


# ---- built-up section property tests (G-P) ----


def _rectangle_as_one_component(b=0.04, h=0.08):
    return BuiltUpSection((RectangularComponent(width=b, height=h, centroid_y=0.0),))


def test_single_component_reproduces_rectangle_properties():
    b, h = 0.04, 0.08
    section = _rectangle_as_one_component(b, h)
    assert section.area == pytest.approx(b * h)
    assert section.centroid_y == pytest.approx(0.0)
    assert section.moment_of_inertia_z == pytest.approx(b * h**3 / 12.0)
    assert section.y_top == pytest.approx(h / 2)
    assert section.y_bottom == pytest.approx(-h / 2)
    assert section.S_top == pytest.approx(section.S_bottom)


def test_two_component_centroid_hand_calc():
    c1 = RectangularComponent(width=0.02, height=0.01, centroid_y=0.0, label="a")
    c2 = RectangularComponent(width=0.02, height=0.01, centroid_y=0.05, label="b")
    section = BuiltUpSection((c1, c2))
    expected_ybar = (c1.area * c1.centroid_y + c2.area * c2.centroid_y) / (
        c1.area + c2.area
    )
    assert section.centroid_y == pytest.approx(expected_ybar)


def test_parallel_axis_theorem_hand_calc():
    c1 = RectangularComponent(width=0.02, height=0.01, centroid_y=0.0, label="a")
    c2 = RectangularComponent(width=0.02, height=0.01, centroid_y=0.05, label="b")
    section = BuiltUpSection((c1, c2))
    y_bar = section.centroid_y
    expected = (
        c1.moment_of_inertia_centroid + c1.area * (c1.centroid_y - y_bar) ** 2
    ) + (c2.moment_of_inertia_centroid + c2.area * (c2.centroid_y - y_bar) ** 2)
    assert section.moment_of_inertia_z == pytest.approx(expected)


def test_area_sum():
    c1 = RectangularComponent(width=0.02, height=0.01, centroid_y=0.0)
    c2 = RectangularComponent(width=0.03, height=0.02, centroid_y=0.05)
    section = BuiltUpSection((c1, c2))
    assert section.area == pytest.approx(c1.area + c2.area)


def test_top_bottom_extremes():
    c1 = RectangularComponent(width=0.02, height=0.01, centroid_y=0.0)  # [-.005,.005]
    c2 = RectangularComponent(width=0.02, height=0.01, centroid_y=0.05)  # [.045,.055]
    section = BuiltUpSection((c1, c2))
    assert section.y_top == pytest.approx(0.055)
    assert section.y_bottom == pytest.approx(-0.005)


def test_asymmetric_construction_gives_unequal_section_moduli():
    # A small top cap and a much larger bottom cap -> asymmetric about y_bar.
    top = RectangularComponent(width=0.01, height=0.005, centroid_y=0.05, label="top")
    bottom = RectangularComponent(
        width=0.05, height=0.02, centroid_y=-0.02, label="bottom"
    )
    section = BuiltUpSection((top, bottom))
    assert section.S_top != pytest.approx(section.S_bottom)


def test_translation_invariance():
    c1 = RectangularComponent(width=0.05, height=0.005, centroid_y=0.05, label="top")
    c2 = RectangularComponent(width=0.005, height=0.09, centroid_y=0.0, label="web")
    c3 = RectangularComponent(
        width=0.05, height=0.005, centroid_y=-0.05, label="bottom"
    )
    section = BuiltUpSection((c1, c2, c3))

    dy = 0.73
    shifted = BuiltUpSection(
        tuple(
            RectangularComponent(c.width, c.height, c.centroid_y + dy, c.label)
            for c in (c1, c2, c3)
        )
    )

    assert shifted.area == pytest.approx(section.area)
    assert shifted.centroid_y == pytest.approx(section.centroid_y + dy)
    assert shifted.moment_of_inertia_z == pytest.approx(section.moment_of_inertia_z)
    assert shifted.c_top == pytest.approx(section.c_top)
    assert shifted.c_bottom == pytest.approx(section.c_bottom)
    assert shifted.S_top == pytest.approx(section.S_top)
    assert shifted.S_bottom == pytest.approx(section.S_bottom)


def test_component_order_invariance():
    c1 = RectangularComponent(width=0.05, height=0.005, centroid_y=0.05, label="top")
    c2 = RectangularComponent(width=0.005, height=0.09, centroid_y=0.0, label="web")
    c3 = RectangularComponent(
        width=0.05, height=0.005, centroid_y=-0.05, label="bottom"
    )
    s_forward = BuiltUpSection((c1, c2, c3))
    s_reversed = BuiltUpSection((c3, c2, c1))

    assert s_forward.area == pytest.approx(s_reversed.area)
    assert s_forward.centroid_y == pytest.approx(s_reversed.centroid_y)
    assert s_forward.moment_of_inertia_z == pytest.approx(s_reversed.moment_of_inertia_z)
    assert s_forward.S_top == pytest.approx(s_reversed.S_top)
    assert s_forward.S_bottom == pytest.approx(s_reversed.S_bottom)


def test_deterministic_repeated_result():
    c1 = RectangularComponent(width=0.05, height=0.005, centroid_y=0.05)
    c2 = RectangularComponent(width=0.005, height=0.09, centroid_y=0.0)
    section = BuiltUpSection((c1, c2))
    assert section.area == section.area
    assert section.centroid_y == section.centroid_y
    assert section.moment_of_inertia_z == section.moment_of_inertia_z
    assert section.b_local(0.0) == section.b_local(0.0)
    assert section.first_moment_above(0.0) == section.first_moment_above(0.0)


def test_overlap_rejected():
    a = RectangularComponent(width=0.02, height=0.02, centroid_y=0.0, label="a")
    b = RectangularComponent(width=0.02, height=0.02, centroid_y=0.01, label="b")
    with pytest.raises(ValueError):
        BuiltUpSection((a, b))


def test_touching_boundary_is_allowed_not_overlap():
    a = RectangularComponent(width=0.02, height=0.02, centroid_y=0.0, label="a")
    b = RectangularComponent(width=0.02, height=0.02, centroid_y=0.02, label="b")
    # a spans [-0.01, 0.01], b spans [0.01, 0.03] -- share only the edge.
    section = BuiltUpSection((a, b))
    assert section.area == pytest.approx(a.area + b.area)


def test_builtup_requires_at_least_one_component():
    with pytest.raises(ValueError):
        BuiltUpSection(())


# ---- b_local / Q boundary and range behavior used across the geometry API ----


def test_b_local_rejects_y_outside_section():
    section = _rectangle_as_one_component()
    with pytest.raises(ValueError):
        section.b_local(section.y_top + 0.01)
    with pytest.raises(ValueError):
        section.b_local(section.y_bottom - 0.01)


def test_first_moment_rejects_y_outside_section():
    section = _rectangle_as_one_component()
    with pytest.raises(ValueError):
        section.first_moment_above(section.y_top + 0.01)
