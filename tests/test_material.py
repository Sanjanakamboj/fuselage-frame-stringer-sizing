import math

import pytest

from frame_stringer.material import IsotropicMaterial


def _valid_kwargs(**overrides):
    kwargs = dict(
        name="Illustrative Al-like",
        elastic_modulus=70e9,
        poisson_ratio=0.33,
        density=2700.0,
        yield_strength=300e6,
    )
    kwargs.update(overrides)
    return kwargs


def test_valid_construction():
    mat = IsotropicMaterial(**_valid_kwargs())
    assert mat.name == "Illustrative Al-like"
    assert mat.elastic_modulus == pytest.approx(70e9)
    assert mat.poisson_ratio == pytest.approx(0.33)
    assert mat.density == pytest.approx(2700.0)
    assert mat.yield_strength == pytest.approx(300e6)


def test_empty_name_rejected():
    with pytest.raises(ValueError):
        IsotropicMaterial(**_valid_kwargs(name=""))


@pytest.mark.parametrize("bad_E", [0.0, -70e9])
def test_invalid_elastic_modulus(bad_E):
    with pytest.raises(ValueError):
        IsotropicMaterial(**_valid_kwargs(elastic_modulus=bad_E))


@pytest.mark.parametrize("bad_nu", [-1.0, 0.5, -1.5, 0.6])
def test_invalid_poisson_ratio(bad_nu):
    with pytest.raises(ValueError):
        IsotropicMaterial(**_valid_kwargs(poisson_ratio=bad_nu))


@pytest.mark.parametrize("bad_rho", [0.0, -2700.0])
def test_invalid_density(bad_rho):
    with pytest.raises(ValueError):
        IsotropicMaterial(**_valid_kwargs(density=bad_rho))


@pytest.mark.parametrize("bad_sy", [0.0, -300e6])
def test_invalid_yield_strength(bad_sy):
    with pytest.raises(ValueError):
        IsotropicMaterial(**_valid_kwargs(yield_strength=bad_sy))


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("elastic_modulus", math.nan),
        ("elastic_modulus", math.inf),
        ("poisson_ratio", math.nan),
        ("density", math.nan),
        ("density", math.inf),
        ("yield_strength", math.nan),
        ("yield_strength", math.inf),
    ],
)
def test_non_finite_rejected(field, bad_value):
    with pytest.raises(ValueError):
        IsotropicMaterial(**_valid_kwargs(**{field: bad_value}))
