"""Built-up (multi-rectangle) cross-section geometry.

Milestone 2 extends the verified single-rectangle mechanics of
:mod:`frame_stringer.geometry` to realistic built-up frame/stringer sections
(I, Z, hat) assembled from rectangular components.

Modeling simplification
------------------------
A :class:`RectangularComponent` is characterized only by its width (z
dimension), height (y dimension), and centroid_y (position along the shared
y datum) -- there is no explicit lateral (z) position. This is sufficient
for bending-about-z and transverse-shear-in-y analysis (this milestone's
scope), because those quantities only depend on how area is distributed in
y, not on where it sits in z. Two physically distinct, laterally-separated
members that happen to share the same y-extent (e.g. the two vertical webs
of a hat section) are represented as a *single* component whose width is
the sum of their individual widths -- this is mathematically identical to
modeling them as two components at the same y-range, without introducing an
overlap in the model's 1-D (y-only) sense. Lateral (z) centroid and
shear-center effects are explicitly deferred to a later milestone.

Overlap policy
--------------
Two components may not have y-ranges that overlap over a positive length;
touching at a shared boundary (one component's top_y equal to another's
bottom_y) is allowed and is how stacked members (e.g. flange-to-web) are
represented. This directly prevents double-counting material area in y.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

_OVERLAP_TOLERANCE = 1e-9  # m; touching boundaries within this are not an overlap
_BOUNDARY_TOLERANCE = 1e-9  # m; used for boundary-inclusive comparisons


@dataclass(frozen=True)
class RectangularComponent:
    """A single rectangular piece of a built-up section.

    Attributes
    ----------
    width : float
        Dimension along z, in m. Must be finite and > 0. For a pair of
        laterally-separated identical members (e.g. two webs), pass the
        *combined* width (see module docstring).
    height : float
        Dimension along y, in m. Must be finite and > 0.
    centroid_y : float
        Centroid y-coordinate of this component, in m, measured from an
        arbitrary but consistent section datum. Must be finite.
    label : str | None
        Optional non-empty descriptive label (e.g. "top_flange").
    """

    width: float
    height: float
    centroid_y: float
    label: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("width", "height", "centroid_y"):
            value = getattr(self, field_name)
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite, got {value!r}")
        if self.width <= 0:
            raise ValueError(f"width must be > 0, got {self.width!r}")
        if self.height <= 0:
            raise ValueError(f"height must be > 0, got {self.height!r}")
        if self.label is not None and self.label.strip() == "":
            raise ValueError("label, if supplied, must be non-empty")

    @property
    def area(self) -> float:
        """Component area A_i = width * height, in m^2."""
        return self.width * self.height

    @property
    def moment_of_inertia_centroid(self) -> float:
        """Component second moment about its own centroid, b*h^3/12, in m^4."""
        return self.width * self.height**3 / 12.0

    @property
    def top_y(self) -> float:
        """Component top-edge y-coordinate, centroid_y + h/2."""
        return self.centroid_y + self.height / 2.0

    @property
    def bottom_y(self) -> float:
        """Component bottom-edge y-coordinate, centroid_y - h/2."""
        return self.centroid_y - self.height / 2.0


def _check_no_overlap(components: tuple[RectangularComponent, ...]) -> None:
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            a, b = components[i], components[j]
            lo = max(a.bottom_y, b.bottom_y)
            hi = min(a.top_y, b.top_y)
            if hi - lo > _OVERLAP_TOLERANCE:
                raise ValueError(
                    "overlapping rectangular components are not supported: "
                    f"{a.label!r} [{a.bottom_y}, {a.top_y}] overlaps "
                    f"{b.label!r} [{b.bottom_y}, {b.top_y}]"
                )


@dataclass(frozen=True)
class BuiltUpSection:
    """A built-up cross-section assembled from non-overlapping rectangles.

    Attributes
    ----------
    components : tuple[RectangularComponent, ...]
        The rectangular components making up the section. At least one is
        required. Components may touch at shared boundaries but may not
        overlap over a positive y-extent (see module docstring).
    """

    components: tuple[RectangularComponent, ...]

    def __post_init__(self) -> None:
        components = tuple(self.components)
        if len(components) == 0:
            raise ValueError("BuiltUpSection requires at least one component")
        object.__setattr__(self, "components", components)
        _check_no_overlap(components)

    # ---- basic properties ----

    @property
    def area(self) -> float:
        """Total area A = sum(A_i), in m^2."""
        return sum(c.area for c in self.components)

    @property
    def centroid_y(self) -> float:
        """Built-up centroid y_bar = sum(A_i*y_i)/A, in m."""
        A = self.area
        return sum(c.area * c.centroid_y for c in self.components) / A

    @property
    def moment_of_inertia_z(self) -> float:
        """Second moment about the built-up centroid via the parallel-axis theorem.

        I_z = sum(I_i,centroid + A_i*(y_i - y_bar)^2)
        """
        y_bar = self.centroid_y
        return sum(
            c.moment_of_inertia_centroid + c.area * (c.centroid_y - y_bar) ** 2
            for c in self.components
        )

    @property
    def y_top(self) -> float:
        """Top extreme coordinate of the whole section, max(component.top_y)."""
        return max(c.top_y for c in self.components)

    @property
    def y_bottom(self) -> float:
        """Bottom extreme coordinate of the whole section, min(component.bottom_y)."""
        return min(c.bottom_y for c in self.components)

    @property
    def c_top(self) -> float:
        """Distance from the neutral axis to the top extreme fiber, y_top - y_bar."""
        return self.y_top - self.centroid_y

    @property
    def c_bottom(self) -> float:
        """Distance from the neutral axis to the bottom extreme fiber, y_bar - y_bottom."""
        return self.centroid_y - self.y_bottom

    @property
    def section_modulus_top(self) -> float:
        """Section modulus to the top extreme fiber, S_top = I_z / c_top."""
        return self.moment_of_inertia_z / self.c_top

    @property
    def section_modulus_bottom(self) -> float:
        """Section modulus to the bottom extreme fiber, S_bottom = I_z / c_bottom."""
        return self.moment_of_inertia_z / self.c_bottom

    # Backwards/forwards-compatible short aliases matching the Milestone 1
    # naming style (S_top, S_bottom) used in the spec and README.
    @property
    def S_top(self) -> float:  # noqa: N802 (spec-mandated name)
        return self.section_modulus_top

    @property
    def S_bottom(self) -> float:  # noqa: N802 (spec-mandated name)
        return self.section_modulus_bottom

    # ---- ordered component view (for deterministic, order-invariant results) ----

    def _components_sorted_by_position(self) -> tuple[RectangularComponent, ...]:
        """Components ordered by bottom_y, independent of construction order.

        Used internally wherever a deterministic, input-order-independent
        sequence of components is needed (e.g. generating labeled critical
        points), so that a :class:`BuiltUpSection` built from the same
        physical components in a different order produces identical
        derived results.
        """
        return tuple(sorted(self.components, key=lambda c: (c.bottom_y, c.top_y)))

    # ---- shear-related geometry: local width and first moment of area ----

    def _validate_y_in_range(self, y: float) -> None:
        if y < self.y_bottom - _BOUNDARY_TOLERANCE or y > self.y_top + _BOUNDARY_TOLERANCE:
            raise ValueError(
                f"y={y!r} is outside the section "
                f"(must be within [{self.y_bottom!r}, {self.y_top!r}])"
            )

    def b_local(self, y: float) -> float:
        """Local material width at global coordinate y, in m.

        Sum of the widths of every component whose y-range is intersected
        by the horizontal cut at y.

        Boundary convention: a component owns the half-open interval
        ``[bottom_y, top_y)`` -- i.e. at a shared boundary between two
        stacked components, the width of the *upper* component applies,
        never both. The section's absolute top edge is the sole exception:
        it is owned (closed) by whichever component reaches it, so the top
        extreme fiber itself resolves to a well-defined nonzero width
        rather than falling through the half-open gap. This avoids
        double-counting width at any shared edge.

        Raises
        ------
        ValueError
            If y lies outside [y_bottom, y_top].
        """
        self._validate_y_in_range(y)
        total = 0.0
        y_top_overall = self.y_top
        for c in self.components:
            owns_via_half_open = c.bottom_y <= y < c.top_y
            owns_via_top_edge = math.isclose(
                y, y_top_overall, abs_tol=_BOUNDARY_TOLERANCE
            ) and math.isclose(c.top_y, y_top_overall, abs_tol=_BOUNDARY_TOLERANCE)
            if owns_via_half_open or owns_via_top_edge:
                total += c.width
        return total

    def first_moment_above(self, y: float) -> float:
        """Signed first moment of area above the cut at y, about the neutral axis.

        Q_above(y) = sum over components of A_portion * (centroid_y_portion - y_bar)

        where A_portion/centroid_y_portion describe the part of each
        component lying above the cut (a component entirely above the cut
        contributes in full; one entirely below contributes zero; one
        straddling the cut contributes only its upper portion).

        This is continuous in y, is zero at the section's top extreme
        fiber (no material above the topmost point), and is the negative
        of the first moment of the area *below* the cut (by definition of
        the centroid: the two must sum to zero).

        Raises
        ------
        ValueError
            If y lies outside [y_bottom, y_top].
        """
        self._validate_y_in_range(y)
        y_bar = self.centroid_y
        total = 0.0
        for c in self.components:
            if y >= c.top_y:
                continue  # nothing above the cut for this component
            if y <= c.bottom_y:
                area_portion = c.area
                centroid_portion = c.centroid_y
            else:
                height_portion = c.top_y - y
                area_portion = c.width * height_portion
                centroid_portion = (y + c.top_y) / 2.0
            total += area_portion * (centroid_portion - y_bar)
        return total

    def interior_boundaries(self) -> tuple[float, ...]:
        """Distinct interior y-boundaries between components, sorted ascending.

        Excludes the section's overall top and bottom extremes. Used to
        locate flange/web-style transitions where the local width (and
        hence shear stress) changes discontinuously.
        """
        edges = set()
        for c in self.components:
            for edge in (c.top_y, c.bottom_y):
                edges.add(round(edge, 12))
        y_top, y_bottom = self.y_top, self.y_bottom
        interior = sorted(
            e
            for e in edges
            if not math.isclose(e, y_top, abs_tol=_BOUNDARY_TOLERANCE)
            and not math.isclose(e, y_bottom, abs_tol=_BOUNDARY_TOLERANCE)
        )
        return tuple(interior)
