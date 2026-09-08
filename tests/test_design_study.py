import pytest

from frame_stringer.column_buckling import MemberGeometry
from frame_stringer.crippling import CripplingCorrelation
from frame_stringer.design_study import StudyAssumptions, recommend_family, size_all_families
from frame_stringer.load_cases import CANONICAL_LOAD_CASES
from frame_stringer.material import IsotropicMaterial
from frame_stringer.sizing import FAMILIES, SectionSizingResult


@pytest.fixture
def assumptions():
    material = IsotropicMaterial(
        name="Illustrative Al-like", elastic_modulus=70e9, poisson_ratio=0.33, density=2700.0, yield_strength=300e6
    )
    member = MemberGeometry(length=1.2, effective_length_factor=1.0)
    correlation = CripplingCorrelation(alpha=1.2, exponent=0.6, label="Illustrative", source_note="illustrative")
    return StudyAssumptions(
        material=material,
        member=member,
        load_cases=CANONICAL_LOAD_CASES,
        correlation=correlation,
        panel_length=0.30,
        t_min_gauge=1.5e-3,
    )


def test_all_families_assessed_with_identical_assumptions(assumptions):
    results = size_all_families(assumptions)
    assert len(results) == len(FAMILIES)
    assert [r.family_name for r in results] == [f.name for f in FAMILIES]
    for r in results:
        assert r.t_min_gauge == pytest.approx(assumptions.t_min_gauge)


def test_recommendation_is_minimum_mass_feasible(assumptions):
    results = size_all_families(assumptions)
    best = recommend_family(results)
    feasible = [r for r in results if r.status != "upper_bound_infeasible"]
    assert best.mass_per_length == pytest.approx(min(r.mass_per_length for r in feasible))


def test_family_order_invariance_when_masses_distinct(assumptions):
    results = size_all_families(assumptions)
    reversed_results = tuple(reversed(results))
    best_forward = recommend_family(results)
    best_reversed = recommend_family(reversed_results)
    # Same section family recommended regardless of list order, since
    # masses genuinely differ here.
    assert best_forward.family_name == best_reversed.family_name


def test_deterministic_tie_break_with_synthetic_equal_masses():
    a = SectionSizingResult(
        family_name="A", required_thickness=0.003, section=None, area=0.001, mass_per_length=5.0,
        status="converged", iterations=1, t_min_gauge=0.0015, governing_load_case="x",
        governing_constraint="yield", governing_margin=0.1, final_assessment=None,
    )
    b = SectionSizingResult(
        family_name="B", required_thickness=0.003, section=None, area=0.001, mass_per_length=5.0,
        status="converged", iterations=1, t_min_gauge=0.0015, governing_load_case="x",
        governing_constraint="yield", governing_margin=0.1, final_assessment=None,
    )
    assert recommend_family((a, b)).family_name == "A"
    assert recommend_family((b, a)).family_name == "B"  # first-in-order wins the tie either way


def test_infeasible_family_excluded_honestly(assumptions):
    from frame_stringer.sizing import size_section_family

    infeasible = size_section_family(
        FAMILIES[0], assumptions.material, assumptions.member, assumptions.load_cases, assumptions.correlation,
        assumptions.panel_length, assumptions.t_min_gauge, t_max_search=1.0e-3,
    )
    feasible = size_section_family(
        FAMILIES[1], assumptions.material, assumptions.member, assumptions.load_cases, assumptions.correlation,
        assumptions.panel_length, assumptions.t_min_gauge,
    )
    assert infeasible.status == "upper_bound_infeasible"
    best = recommend_family((infeasible, feasible))
    assert best.family_name == feasible.family_name


def test_all_infeasible_returns_none(assumptions):
    from frame_stringer.sizing import size_section_family

    results = tuple(
        size_section_family(
            f, assumptions.material, assumptions.member, assumptions.load_cases, assumptions.correlation,
            assumptions.panel_length, assumptions.t_min_gauge, t_max_search=1.0e-3,
        )
        for f in FAMILIES
    )
    assert all(r.status == "upper_bound_infeasible" for r in results)
    assert recommend_family(results) is None
