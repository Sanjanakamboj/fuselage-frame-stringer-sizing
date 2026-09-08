import math

import pytest

from frame_stringer.material import IsotropicMaterial
from frame_stringer.plate_buckling import (
    PlateElement,
    assess_plate_buckling,
    compression_buckling_coefficient,
    compression_margin,
    critical_compression_stress,
    critical_shear_stress,
    interaction_index,
    interaction_margin,
    shear_buckling_coefficient,
    shear_margin,
)


@pytest.fixture
def material():
    return IsotropicMaterial(
        name="Illustrative Al-like",
        elastic_modulus=70e9,
        poisson_ratio=0.33,
        density=2700.0,
        yield_strength=300e6,
    )


# ---- plate model (A-G) ----


def test_valid_plate_element():
    p = PlateElement(
        name="web", width=0.05, thickness=0.002, length=0.30, boundary_condition="internal"
    )
    assert p.width == 0.05
    assert p.thickness == 0.002
    assert p.length == 0.30
    assert p.boundary_condition == "internal"


def test_invalid_width():
    with pytest.raises(ValueError):
        PlateElement(name="web", width=0.0, thickness=0.002, length=0.3, boundary_condition="internal")
    with pytest.raises(ValueError):
        PlateElement(name="web", width=-0.05, thickness=0.002, length=0.3, boundary_condition="internal")


def test_invalid_thickness():
    with pytest.raises(ValueError):
        PlateElement(name="web", width=0.05, thickness=0.0, length=0.3, boundary_condition="internal")


def test_invalid_length():
    with pytest.raises(ValueError):
        PlateElement(name="web", width=0.05, thickness=0.002, length=0.0, boundary_condition="internal")
    with pytest.raises(ValueError):
        PlateElement(name="web", width=0.05, thickness=0.002, length=-0.3, boundary_condition="internal")


def test_invalid_boundary_condition():
    with pytest.raises(ValueError):
        PlateElement(name="web", width=0.05, thickness=0.002, length=0.3, boundary_condition="clamped")


@pytest.mark.parametrize(
    "field,bad_value",
    [("width", math.nan), ("thickness", math.inf), ("length", math.nan)],
)
def test_plate_non_finite_rejected(field, bad_value):
    kwargs = dict(name="web", width=0.05, thickness=0.002, length=0.3, boundary_condition="internal")
    kwargs[field] = bad_value
    with pytest.raises(ValueError):
        PlateElement(**kwargs)


def test_aspect_ratio_hand_calc():
    p = PlateElement(name="web", width=0.05, thickness=0.002, length=0.30, boundary_condition="internal")
    assert p.aspect_ratio == pytest.approx(0.30 / 0.05)


# ---- coefficients (H-K) ----


def test_internal_compression_coefficient():
    assert compression_buckling_coefficient("internal") == pytest.approx(4.0)


def test_outstanding_compression_coefficient():
    assert compression_buckling_coefficient("outstanding") == pytest.approx(0.43)


def test_shear_coefficient_hand_calc():
    aspect_ratio = 2.0
    expected = 5.34 + 4.0 / aspect_ratio**2
    assert shear_buckling_coefficient("internal", aspect_ratio) == pytest.approx(expected)


def test_shear_coefficient_reciprocal_for_ratio_below_one():
    aspect_ratio = 0.5  # b > a; effective ratio = 1/0.5 = 2.0
    expected = 5.34 + 4.0 / (2.0) ** 2
    assert shear_buckling_coefficient("internal", aspect_ratio) == pytest.approx(expected)


def test_shear_coefficient_not_applicable_for_outstanding():
    assert shear_buckling_coefficient("outstanding", 2.0) is None


def test_invalid_boundary_condition_rejected_by_coefficients():
    with pytest.raises(ValueError):
        compression_buckling_coefficient("clamped")
    with pytest.raises(ValueError):
        shear_buckling_coefficient("clamped", 2.0)


# ---- critical stress (L-R) ----


def test_compression_hand_calc(material):
    b, t, k_c = 0.050, 0.002, 4.0
    expected = k_c * math.pi**2 * material.elastic_modulus / (12 * (1 - material.poisson_ratio**2)) * (t / b) ** 2
    assert critical_compression_stress("internal", b, t, material) == pytest.approx(expected)


def test_shear_hand_calc(material):
    b, a, t = 0.050, 0.15, 0.002
    aspect_ratio = a / b
    k_s = 5.34 + 4.0 / aspect_ratio**2
    expected = k_s * math.pi**2 * material.elastic_modulus / (12 * (1 - material.poisson_ratio**2)) * (t / b) ** 2
    assert critical_shear_stress("internal", b, a, t, material) == pytest.approx(expected)


def test_thickness_squared_scaling(material):
    b = 0.05
    t1, t2 = 0.002, 0.004  # doubled
    s1 = critical_compression_stress("internal", b, t1, material)
    s2 = critical_compression_stress("internal", b, t2, material)
    assert s2 == pytest.approx(4.0 * s1)

    tau1 = critical_shear_stress("internal", b, 0.15, t1, material)
    tau2 = critical_shear_stress("internal", b, 0.15, t2, material)
    assert tau2 == pytest.approx(4.0 * tau1)


def test_width_inverse_squared_scaling(material):
    t = 0.002
    b1, b2 = 0.05, 0.10  # doubled
    s1 = critical_compression_stress("internal", b1, t, material)
    s2 = critical_compression_stress("internal", b2, t, material)
    assert s2 == pytest.approx(s1 / 4.0)


def test_elastic_modulus_linear_scaling(material):
    material2 = IsotropicMaterial(
        name=material.name,
        elastic_modulus=2.0 * material.elastic_modulus,
        poisson_ratio=material.poisson_ratio,
        density=material.density,
        yield_strength=material.yield_strength,
    )
    s1 = critical_compression_stress("internal", 0.05, 0.002, material)
    s2 = critical_compression_stress("internal", 0.05, 0.002, material2)
    assert s2 == pytest.approx(2.0 * s1)


def test_boundary_condition_ratio(material):
    b, t = 0.05, 0.002
    s_internal = critical_compression_stress("internal", b, t, material)
    s_outstanding = critical_compression_stress("outstanding", b, t, material)
    assert s_outstanding / s_internal == pytest.approx(0.43 / 4.0)


def test_poisson_ratio_sensitivity_follows_denominator(material):
    material2 = IsotropicMaterial(
        name=material.name,
        elastic_modulus=material.elastic_modulus,
        poisson_ratio=0.0,
        density=material.density,
        yield_strength=material.yield_strength,
    )
    s1 = critical_compression_stress("internal", 0.05, 0.002, material)
    s2 = critical_compression_stress("internal", 0.05, 0.002, material2)
    ratio = s1 / s2
    expected_ratio = (1 - 0.0**2) / (1 - material.poisson_ratio**2)
    assert ratio == pytest.approx(expected_ratio)


# ---- margins (S-AA) ----


def test_zero_compression_demand_margin_is_none():
    assert compression_margin(sigma_cr=100e6, sigma_comp=0.0) is None


def test_zero_shear_demand_margin_is_none():
    assert shear_margin(tau_cr=50e6, tau_demand=0.0) is None


def test_exact_compression_boundary_margin_zero():
    assert compression_margin(sigma_cr=100e6, sigma_comp=100e6) == pytest.approx(0.0)


def test_compression_below_above():
    assert compression_margin(sigma_cr=100e6, sigma_comp=50e6) > 0
    assert compression_margin(sigma_cr=100e6, sigma_comp=150e6) < 0


def test_exact_shear_boundary_margin_zero():
    assert shear_margin(tau_cr=50e6, tau_demand=50e6) == pytest.approx(0.0)


def test_shear_below_above():
    assert shear_margin(tau_cr=50e6, tau_demand=25e6) > 0
    assert shear_margin(tau_cr=50e6, tau_demand=75e6) < 0


def test_interaction_exact_boundary():
    sigma_comp, sigma_cr = 0.6, 1.0
    tau, tau_cr = 0.8, 1.0
    fi = interaction_index(sigma_comp, sigma_cr, tau, tau_cr)
    assert fi == pytest.approx(1.0)
    assert interaction_margin(fi) == pytest.approx(0.0, abs=1e-12)


def test_interaction_below_above():
    fi_below = interaction_index(0.5, 1.0, 0.5, 1.0)  # 0.25+0.25=0.5
    fi_above = interaction_index(0.8, 1.0, 0.8, 1.0)  # 0.64+0.64=1.28
    assert interaction_margin(fi_below) > 0
    assert interaction_margin(fi_above) < 0


def test_interaction_none_when_shear_not_applicable():
    assert interaction_index(sigma_comp=50e6, sigma_cr=100e6, tau_demand=10e6, tau_cr=None) is None
    assert interaction_margin(None) is None


def test_interaction_none_at_zero_demand():
    fi = interaction_index(0.0, 1.0, 0.0, 1.0)
    assert fi == 0.0
    assert interaction_margin(fi) is None


def test_deterministic_governing_mode_tie_break(material):
    # With zero compression demand, the interaction index reduces to
    # exactly (tau/tau_cr)^2, so the shear and interaction margins are
    # numerically identical -- a genuine tie. Fixed tie-break order
    # (compression, shear, interaction) means "shear" must win.
    plate = PlateElement(
        name="test", width=0.05, thickness=0.002, length=0.15, boundary_condition="internal"
    )
    result = assess_plate_buckling(plate, material, sigma_x=0.0, tau_xy=1e6)
    assert result.compression_margin is None
    assert result.shear_margin == pytest.approx(result.interaction_margin, rel=1e-9)
    assert result.governing_mode == "shear"


def test_assess_plate_buckling_zero_demand_trivially_passes(material):
    plate = PlateElement(
        name="test", width=0.05, thickness=0.002, length=0.15, boundary_condition="internal"
    )
    result = assess_plate_buckling(plate, material, sigma_x=0.0, tau_xy=0.0)
    assert result.governing_margin is None
    assert result.passes is True


def test_assess_plate_buckling_tension_gives_zero_compression_demand(material):
    plate = PlateElement(
        name="test", width=0.05, thickness=0.002, length=0.15, boundary_condition="internal"
    )
    result = assess_plate_buckling(plate, material, sigma_x=50e6, tau_xy=0.0)  # tension
    assert result.sigma_comp_demand == 0.0
    assert result.compression_margin is None
