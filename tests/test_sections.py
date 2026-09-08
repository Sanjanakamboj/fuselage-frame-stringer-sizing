import pytest

from frame_stringer.sections import hat_section, i_section, z_section

# ---- I-section (Q-V) ----


def _i_params():
    return dict(
        flange_width=0.05, overall_height=0.10, flange_thickness=0.005, web_thickness=0.004
    )


def test_i_section_area_hand_calc():
    p = _i_params()
    section = i_section(**p)
    h_web = p["overall_height"] - 2 * p["flange_thickness"]
    expected = 2 * (p["flange_width"] * p["flange_thickness"]) + p["web_thickness"] * h_web
    assert section.area == pytest.approx(expected)


def test_i_section_centroid_is_zero():
    section = i_section(**_i_params())
    assert section.centroid_y == pytest.approx(0.0, abs=1e-12)


def test_i_section_moment_of_inertia_hand_calc():
    p = _i_params()
    section = i_section(**p)
    b, H, tf, tw = (
        p["flange_width"],
        p["overall_height"],
        p["flange_thickness"],
        p["web_thickness"],
    )
    h_web = H - 2 * tf
    # Standard I-beam formula: I = (b*H^3 - (b-tw)*h_web^3) / 12
    expected = (b * H**3 - (b - tw) * h_web**3) / 12.0
    assert section.moment_of_inertia_z == pytest.approx(expected, rel=1e-9)


def test_i_section_symmetric_moduli():
    section = i_section(**_i_params())
    assert section.S_top == pytest.approx(section.S_bottom)


def test_i_section_web_clear_height_validation():
    with pytest.raises(ValueError):
        i_section(
            flange_width=0.05, overall_height=0.01, flange_thickness=0.006, web_thickness=0.004
        )


def test_i_section_invalid_geometry_rejected():
    with pytest.raises(ValueError):
        i_section(flange_width=0.0, overall_height=0.1, flange_thickness=0.005, web_thickness=0.004)
    with pytest.raises(ValueError):
        # web_thickness > flange_width
        i_section(flange_width=0.01, overall_height=0.1, flange_thickness=0.005, web_thickness=0.02)


# ---- Z-section (W-AA) ----


def _z_params():
    return dict(web_height=0.08, web_thickness=0.003, flange_width=0.03, flange_thickness=0.004)


def test_z_section_area_hand_calc():
    p = _z_params()
    section = z_section(**p)
    expected = p["web_height"] * p["web_thickness"] + 2 * (
        p["flange_width"] * p["flange_thickness"]
    )
    assert section.area == pytest.approx(expected)


def test_z_section_centroid_expected():
    section = z_section(**_z_params())
    assert section.centroid_y == pytest.approx(0.0, abs=1e-12)


def test_z_section_moment_of_inertia_positive_and_plausible():
    section = z_section(**_z_params())
    assert section.moment_of_inertia_z > 0
    # Must exceed the web-alone contribution (flanges add material away from NA).
    p = _z_params()
    web_alone = p["web_thickness"] * p["web_height"] ** 3 / 12.0
    assert section.moment_of_inertia_z > web_alone


def test_z_section_equal_flanges_gives_equal_moduli():
    section = z_section(**_z_params())
    assert section.S_top == pytest.approx(section.S_bottom)


def test_z_section_invalid_geometry_rejected():
    with pytest.raises(ValueError):
        z_section(web_height=-0.08, web_thickness=0.003, flange_width=0.03, flange_thickness=0.004)
    with pytest.raises(ValueError):
        z_section(web_height=0.08, web_thickness=0.0, flange_width=0.03, flange_thickness=0.004)


# ---- hat section (AB-AF) ----


def _hat_params():
    return dict(crown_width=0.05, overall_height=0.06, wall_thickness=0.002, flange_width=0.02)


def test_hat_section_area_hand_calc():
    p = _hat_params()
    section = hat_section(**p)
    web_run = p["overall_height"] - 2 * p["wall_thickness"]
    expected = (
        p["crown_width"] * p["wall_thickness"]
        + 2 * p["wall_thickness"] * web_run
        + 2 * p["flange_width"] * p["wall_thickness"]
    )
    assert section.area == pytest.approx(expected)


def test_hat_section_centroid_hand_calc():
    p = _hat_params()
    section = hat_section(**p)
    web_run = p["overall_height"] - 2 * p["wall_thickness"]
    half_h = p["overall_height"] / 2.0

    A_flange = 2 * p["flange_width"] * p["wall_thickness"]
    y_flange = -half_h + p["wall_thickness"] / 2.0

    A_web = 2 * p["wall_thickness"] * web_run
    y_web = -half_h + p["wall_thickness"] + web_run / 2.0

    A_crown = p["crown_width"] * p["wall_thickness"]
    y_crown = half_h - p["wall_thickness"] / 2.0

    A_total = A_flange + A_web + A_crown
    expected_ybar = (A_flange * y_flange + A_web * y_web + A_crown * y_crown) / A_total

    assert section.centroid_y == pytest.approx(expected_ybar)
    # For these parameters (crown_width != 2*flange_width) the section is
    # genuinely asymmetric -- the centroid must not be at mid-height.
    assert section.centroid_y != pytest.approx(0.0, abs=1e-6)


def test_hat_section_moment_of_inertia_hand_calc():
    p = _hat_params()
    section = hat_section(**p)
    web_run = p["overall_height"] - 2 * p["wall_thickness"]
    half_h = p["overall_height"] / 2.0

    components = [
        (2 * p["flange_width"], p["wall_thickness"], -half_h + p["wall_thickness"] / 2.0),
        (2 * p["wall_thickness"], web_run, -half_h + p["wall_thickness"] + web_run / 2.0),
        (p["crown_width"], p["wall_thickness"], half_h - p["wall_thickness"] / 2.0),
    ]
    A_total = sum(b * h for b, h, _ in components)
    y_bar = sum(b * h * y for b, h, y in components) / A_total
    expected_I = sum(
        b * h**3 / 12.0 + b * h * (y - y_bar) ** 2 for b, h, y in components
    )
    assert section.moment_of_inertia_z == pytest.approx(expected_I)


def test_hat_section_asymmetric_moduli():
    section = hat_section(**_hat_params())
    assert section.S_top != pytest.approx(section.S_bottom)


def test_hat_section_invalid_geometry_rejected():
    with pytest.raises(ValueError):
        hat_section(crown_width=0.05, overall_height=0.003, wall_thickness=0.002, flange_width=0.02)
    with pytest.raises(ValueError):
        hat_section(crown_width=-0.05, overall_height=0.06, wall_thickness=0.002, flange_width=0.02)
