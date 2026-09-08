import math

import pytest

from frame_stringer.crippling import (
    CripplingCorrelation,
    capped_crippling_stress,
    element_slenderness,
    raw_crippling_stress,
)


def _corr(alpha=1.2, exponent=0.6):
    return CripplingCorrelation(
        alpha=alpha, exponent=exponent, label="Illustrative", source_note="illustrative, not sourced"
    )


# ---- correlation model (A-D) ----


def test_valid_correlation():
    c = _corr()
    assert c.alpha == pytest.approx(1.2)
    assert c.exponent == pytest.approx(0.6)


def test_invalid_alpha():
    with pytest.raises(ValueError):
        _corr(alpha=0.0)
    with pytest.raises(ValueError):
        _corr(alpha=-1.0)


def test_invalid_exponent():
    with pytest.raises(ValueError):
        _corr(exponent=0.0)
    with pytest.raises(ValueError):
        _corr(exponent=-0.5)


@pytest.mark.parametrize("field,bad_value", [("alpha", math.nan), ("exponent", math.inf)])
def test_non_finite_rejected(field, bad_value):
    kwargs = dict(alpha=1.2, exponent=0.6, label="x", source_note="y")
    kwargs[field] = bad_value
    with pytest.raises(ValueError):
        CripplingCorrelation(**kwargs)


def test_empty_label_or_source_note_rejected():
    with pytest.raises(ValueError):
        CripplingCorrelation(alpha=1.2, exponent=0.6, label="", source_note="y")
    with pytest.raises(ValueError):
        CripplingCorrelation(alpha=1.2, exponent=0.6, label="x", source_note="")


# ---- hand calculation / cap (E-G) ----


def test_hand_calculation():
    E, sy, alpha, m, t, b = 70e9, 300e6, 1.2, 0.6, 0.002, 0.040
    corr = _corr(alpha=alpha, exponent=m)
    expected_raw = alpha * math.sqrt(E * sy) * (t / b) ** m
    raw = raw_crippling_stress(corr, E, sy, t, b)
    assert raw == pytest.approx(expected_raw)
    # This particular (fairly stocky, b/t = 20) hand-calc case comes out
    # well above yield -- the raw prediction is capped at yield.
    capped, active = capped_crippling_stress(raw, sy)
    assert raw > sy
    assert capped == pytest.approx(sy)
    assert active is True


def test_yield_cap_inactive_case():
    # A much more slender element (b/t = 150) with the same coefficients
    # brings the raw prediction below yield -- cap inactive.
    E, sy, alpha, m = 70e9, 300e6, 1.2, 0.6
    t, b = 0.001, 0.150
    corr = _corr(alpha=alpha, exponent=m)
    raw = raw_crippling_stress(corr, E, sy, t, b)
    capped, active = capped_crippling_stress(raw, sy)
    assert raw < sy
    assert capped == pytest.approx(raw)
    assert active is False


def test_yield_cap_active_case_stocky_element():
    # A thick/stocky element (small b/t) drives the raw correlation well
    # above yield.
    E, sy, alpha, m = 70e9, 300e6, 1.2, 0.6
    t, b = 0.010, 0.040  # b/t = 4
    corr = _corr(alpha=alpha, exponent=m)
    raw = raw_crippling_stress(corr, E, sy, t, b)
    capped, active = capped_crippling_stress(raw, sy)
    assert raw > sy
    assert capped == pytest.approx(sy)
    assert active is True


def test_exact_yield_boundary_not_flagged_active():
    # Constructed so raw == yield exactly.
    sy = 300e6
    capped, active = capped_crippling_stress(sy, sy)
    assert capped == pytest.approx(sy)
    assert active is False


# ---- scaling (H-L), all in the pre-cap (uncapped) regime ----

_THIN_E = 70e9
_THIN_SY = 300e6
_THIN_T = 0.0005
_THIN_B = 0.500  # b/t = 1000, comfortably pre-cap across all scaling tests below


def test_alpha_linear_scaling():
    corr1 = _corr(alpha=1.0)
    corr2 = _corr(alpha=2.0)
    raw1 = raw_crippling_stress(corr1, _THIN_E, _THIN_SY, _THIN_T, _THIN_B)
    raw2 = raw_crippling_stress(corr2, _THIN_E, _THIN_SY, _THIN_T, _THIN_B)
    assert raw1 < _THIN_SY and raw2 < _THIN_SY  # confirm pre-cap
    assert raw2 == pytest.approx(2.0 * raw1)


def test_thickness_power_m_scaling():
    corr = _corr(alpha=1.2, exponent=0.6)
    t1, t2 = 0.0005, 0.0010  # doubled
    raw1 = raw_crippling_stress(corr, _THIN_E, _THIN_SY, t1, _THIN_B)
    raw2 = raw_crippling_stress(corr, _THIN_E, _THIN_SY, t2, _THIN_B)
    assert raw1 < _THIN_SY and raw2 < _THIN_SY
    assert raw2 == pytest.approx(raw1 * 2.0**0.6)


def test_width_inverse_power_m_scaling():
    corr = _corr(alpha=1.2, exponent=0.6)
    b1, b2 = 0.150, 0.300  # doubled
    raw1 = raw_crippling_stress(corr, _THIN_E, _THIN_SY, _THIN_T, b1)
    raw2 = raw_crippling_stress(corr, _THIN_E, _THIN_SY, _THIN_T, b2)
    assert raw1 < _THIN_SY and raw2 < _THIN_SY
    assert raw2 == pytest.approx(raw1 * 2.0**-0.6)


def test_sqrt_elastic_modulus_scaling():
    corr = _corr()
    raw1 = raw_crippling_stress(corr, _THIN_E, _THIN_SY, _THIN_T, _THIN_B)
    raw2 = raw_crippling_stress(corr, 4.0 * _THIN_E, _THIN_SY, _THIN_T, _THIN_B)
    assert raw1 < _THIN_SY
    # sigma_cc ~ sqrt(E); might exceed yield at 4x E, so only check the ratio.
    assert raw2 == pytest.approx(2.0 * raw1)  # sqrt(4) = 2


def test_sqrt_yield_strength_scaling_before_cap():
    corr = _corr()
    sy1 = 100e6
    sy2 = 400e6
    raw1 = raw_crippling_stress(corr, _THIN_E, sy1, _THIN_T, _THIN_B)
    raw2 = raw_crippling_stress(corr, _THIN_E, sy2, _THIN_T, _THIN_B)
    assert raw1 < sy1 and raw2 < sy2  # confirm both remain pre-cap
    assert raw2 == pytest.approx(raw1 * math.sqrt(sy2 / sy1))


def test_element_slenderness_hand_calc():
    assert element_slenderness(width=0.08, thickness=0.004) == pytest.approx(20.0)


def test_element_slenderness_invalid_inputs():
    with pytest.raises(ValueError):
        element_slenderness(width=0.0, thickness=0.004)
    with pytest.raises(ValueError):
        element_slenderness(width=0.08, thickness=0.0)
