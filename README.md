# fuselage-frame-stringer-sizing (STM-09)

## Project objective

Combined bending + shear sizing for a fuselage frame/stringer, built up from
first-principles, independently verifiable beam-section mechanics.

**Milestone 1 intentionally uses a rectangular section so every beam-stress
and strength result can be independently verified before introducing
realistic frame/stringer cross-sections and buckling constraints.**

This repository is a **beam-section mechanics model**, not a shell/frame
finite-element model.

## Milestone 1 scope

Milestone 1 builds and verifies the fundamental mechanics required for later
frame/stringer sizing work:

1. cross-section geometry/properties (rectangular baseline)
2. axial and bending normal stress
3. transverse shear stress
4. combined stress state (sigma_x, tau_xy at a point)
5. simple elastic von Mises yield interaction / margin
6. section mass per unit length
7. a representative sanity case

Explicitly **out of scope** for Milestone 1 (see [Limitations](#limitations)):
section optimization/search, multiple load cases, crippling, local plate
buckling, column buckling, frame instability, skin effective width,
shear flow in arbitrary thin-walled open sections, torsion, warping,
fastener loads, fatigue, damage tolerance, plasticity, nonlinear FEA,
certification allowables, and final portfolio figures.

## Milestone 2 scope

**Milestone 2 extends the verified rectangular mechanics to built-up
frame/stringer sections. The resulting stress model is still an elementary
beam-section treatment; local plate buckling, crippling, torsion,
shear-center effects, and skin interaction remain deferred.**

Milestone 2 extends the Milestone 1 mechanics to realistic built-up
frame/stringer cross-sections assembled from rectangular components:

1. a generic rectangular component primitive
2. built-up section centroid, area, and second moment of area via the
   parallel-axis theorem
3. section moduli to (possibly asymmetric) top/bottom extreme fibers
4. I-section, Z-section, and hat-section factories
5. normal stress under axial + bending loads about the built-up centroid
6. transverse shear via the general `V*Q/(I*b_local)` formulation, with
   `Q` and `b_local` computed geometrically from the components
7. elastic von Mises strength screening at a deterministic set of critical
   points (extreme fibers, neutral axis, and just inside every internal
   component boundary)
8. mass per unit length (reusing the Milestone 1 mass equations unchanged)
9. an equal-area section-efficiency comparison

The central engineering question addressed is: *how much bending
efficiency is gained by moving material away from the neutral axis, and
how does the stress/shear distribution change for realistic
frame/stringer-like sections?*

Explicitly **out of scope** for Milestone 2 (see [Limitations](#limitations)):
local plate buckling, crippling, column buckling, skin effective width,
torsion, shear-center calculations, warping, fastener/joint effects,
fatigue, plasticity, nonlinear FEA, section optimization/search, multiple
flight load cases, certification allowables, and final portfolio figures.

## Coordinate / sign conventions

Local member axes:

- `x` — member longitudinal axis
- `y` — section vertical coordinate, spanning `-h/2 <= y <= +h/2`, centroid at `y = 0`
- `z` — section lateral coordinate

Loads at a section:

- `N` — axial force along `x` (positive = tension)
- `V_y` — transverse shear force in `y`
- `M_z` — bending moment about `z`

Stress:

- positive `sigma_x` = tension, negative `sigma_x` = compression
- `tau_xy` is signed internally (follows `V_y`); the strength screen uses `|tau_xy|` implicitly through `sigma_vm`

Units (SI, used internally throughout):

| Quantity | Unit |
|---|---|
| length | m |
| area | m² |
| second moment of area | m⁴ |
| force | N |
| moment | N·m |
| stress / modulus | Pa |
| density | kg/m³ |
| linear mass | kg/m |

## Rectangular section properties

For a solid rectangle of width `b` and height `h`, symmetric about `y = 0`:

```
A   = b*h
I_z = b*h^3/12
S_z = I_z/(h/2)
```

The rectangle is intentionally the simplest possible section so every result
can be hand-checked.

## Normal stress equations

```
sigma_axial       = N/A
sigma_bending(y)  = -M_z*y/I_z
sigma_x(y)        = N/A - M_z*y/I_z
```

Evaluated (signed, no absolute value taken) at the extreme fibers
`y_top = +h/2` and `y_bottom = -h/2`.

## Transverse shear equation

Exact elementary (parabolic) shear-stress distribution for a solid rectangle:

```
tau_xy(y) = (3/2)*(V_y/A)*[1 - (2y/h)^2],   |y| <= h/2
```

- maximum at the neutral axis: `tau_max = 3*V_y/(2*A)`
- zero at `y = ±h/2`
- symmetric about `y = 0`

Evaluating outside `|y| <= h/2` raises an error.

## Von Mises equation and margin definition

Plane-stress (`sigma_x`, `tau_xy` only):

```
sigma_vm = sqrt(sigma_x^2 + 3*tau_xy^2)
MS_yield = yield_strength/sigma_vm - 1      (for sigma_vm > 0)
```

At `sigma_vm == 0` the margin is undefined and the code returns `None`
(not `inf`) — there is no stress to compare against. `sigma_vm ==
yield_strength` is treated as a **PASS** with margin exactly `0`.

This is labeled the **elastic von Mises yield margin** — it is explicitly
**not** a certification margin.

The section strength assessment evaluates three points (top extreme fiber,
neutral axis, bottom extreme fiber) and determines the governing point by
comparing all three computed `sigma_vm` values — it never assumes the
governing location in advance, since for a rectangular section bending peaks
at the extreme fibers (where shear is zero) while shear peaks at the neutral
axis (where the bending contribution is zero).

## Reference capacities (verification quantities, not allowables)

```
N_y      = yield_strength * A                     (pure axial first yield)
M_y      = yield_strength * S_z                    (pure bending first yield)
tau_y    = yield_strength / sqrt(3)                (von Mises pure shear yield stress)
V_yield  = (2/3) * A * tau_y                        (rectangular pure-shear first yield,
                                                      from tau_max = 3V/(2A))
```

These are closed-form reference/verification quantities only, not design
allowables.

## Representative sanity result

`examples/frame_stringer_sanity.py` runs an illustrative fuselage
frame/stringer-like rectangular segment (`b = 40 mm`, `h = 80 mm`,
illustrative aluminum-like material: `E ≈ 70 GPa`, `nu ≈ 0.33`,
`rho ≈ 2700 kg/m³`, `yield strength ≈ 300 MPa`) under a representative
combined load (`N = -80 kN`, `V_y = 25 kN`, `M_z = 4 kN·m`):

```
GOVERNING
  location           = top
  sigma_vm           = 118.75 MPa
  yield margin       = 1.526
  status             = PASS

MASS
  m' (per unit len)  = 8.640 kg/m
```

Run it yourself with `python examples/frame_stringer_sanity.py` (see
[Installation / testing](#installation--testing)) for the full printed
breakdown (section, material, loads, normal stress, shear, the full
three-point combined-strength table, reference capacities, and mass).

## Engineering interpretation

- Axial load shifts the *entire* normal-stress distribution up or down.
- Bending creates the linear tension/compression gradient across the section.
- Transverse shear is parabolic and peaks at the neutral axis (zero at the
  extreme fibers).
- The location of maximum normal stress is **not necessarily** the location
  of maximum von Mises stress once shear is significant — the neutral axis
  carries zero bending stress but maximum shear, so it must be checked
  explicitly rather than assumed to be non-governing.
- Section sizing must therefore consider the **combined** field rather than
  separately checking only `sigma_max` and `tau_max` in isolation.
- This first milestone verifies the mechanics on a rectangle before
  introducing realistic frame/stringer cross-sections.

## Built-up section mechanics (Milestone 2)

### Rectangular component primitive

A `RectangularComponent` is a single rectangle characterized only by its
`width` (z dimension), `height` (y dimension), and `centroid_y` (position
along a shared y datum) — there is no explicit lateral (z) position, since
Milestone 2 only analyzes bending about z and shear in y. Two physically
distinct, laterally-separated members that happen to share the same
y-extent (e.g. a hat section's two vertical webs) are represented as a
*single* component whose width is the sum of their individual widths; this
is mathematically identical to modeling them as two components at the same
y-range without introducing a same-axis overlap. Lateral (z) centroid and
shear-center effects are explicitly deferred.

### Built-up centroid, area, and parallel-axis theorem

For a `BuiltUpSection` assembled from `N` non-overlapping components:

```
A     = sum(A_i)
y_bar = sum(A_i*y_i) / A
I_z   = sum(I_i,centroid + A_i*(y_i - y_bar)^2)
```

Overlap policy: two components may not have y-ranges overlapping over a
positive length; touching at a shared boundary (e.g. flange-to-web) is
allowed and is exactly how stacked members are represented. This directly
prevents silently double-counting material area.

### Asymmetric top/bottom section moduli

```
y_top, y_bottom = max(component.top_y), min(component.bottom_y)
c_top    = y_top - y_bar
c_bottom = y_bar - y_bottom
S_top    = I_z / c_top
S_bottom = I_z / c_bottom
```

Symmetry (`S_top == S_bottom`) is never assumed — it falls out of the
geometry for the I- and Z-section factories (with equal flanges) and is
explicitly *not* assumed for the hat section, whose centroid and section
moduli are computed from its actual (generally asymmetric) geometry.

### I / Z / hat section factories

- `i_section(flange_width, overall_height, flange_thickness, web_thickness)`
  builds three touching rectangles (top flange, web, bottom flange); the
  web clear height is `overall_height - 2*flange_thickness` and must be > 0.
- `z_section(web_height, web_thickness, flange_width, flange_thickness)`
  builds a vertical web with a top flange and a bottom flange (equal
  geometry here gives `y_bar = 0` and `S_top == S_bottom`, even though the
  section is laterally unsymmetric — z-effects are out of scope).
- `hat_section(crown_width, overall_height, wall_thickness, flange_width)`
  builds a constant-thickness formed-sheet idealization: a crown, a
  combined-width web pair, and a combined-width outward flange pair. Its
  centroid is generally off mid-height and its section moduli are
  generally asymmetric — both are computed, never assumed.

### General transverse shear: Q(y) / (I·b_local(y))

```
tau_xy(y) = V_y * |Q(y)| / (I_z * b_local(y))
```

`Q(y)` (the first moment of the area above the cut at y, about the
built-up neutral axis) and `b_local(y)` (the aggregate material width
intersected by the horizontal cut) are both computed geometrically from
the rectangular components — never hardcoded to a particular shape (e.g.
no separate "I-beam web shear" formula). `Q` is continuous in y and zero
at the top extreme fiber; `b_local` can jump discontinuously at a
component boundary (e.g. a flange/web junction), which is exactly where
transverse shear stress jumps in a real built-up section. At a shared
boundary between two stacked components, the *upper* component's width
applies (a documented, tested, deterministic convention that avoids
double-counting width at the boundary). This is a simplified aggregate-width
beam-shear treatment — **not** a thin-wall shear-flow/shear-center
solution.

### Critical-point stress evaluation

`critical_locations(section)` returns a deterministic, component-order-
independent set of (label, y) points: the top and bottom extreme fibers,
the neutral axis, and a pair of points just inside each side of every
internal component boundary (to capture shear jumps, e.g. at an I-section's
flange/web junctions). `assess_builtup_strength(load, section, material)`
evaluates the combined stress state and the Milestone 1 von Mises
yield-margin convention (reused exactly, unchanged) at every one of these
points and determines the governing point by comparison — never by
assumption.

### Equal-area efficiency comparison

`examples/built_up_section_trade.py` compares a rectangle, an I-section, a
Z-section, and a hat section whose areas (and hence masses per unit
length) are kept within about ±2% of one another, then normalizes bending
stiffness and first-yield bending capacity by area:

```
I_z / A                    (bending-stiffness efficiency)
min(S_top, S_bottom) / A   (first-yield bending efficiency)
```

## Verification summary

**Milestone 1**: 89 tests across 7 test files, covering:

- geometry hand calculations, centroid, positive-dimension and finite-value validation
- material validation (all five fields, including non-finite rejection)
- axial/bending superposition, sign reversal, linearity, zero-load case
- shear distribution (neutral-axis maximum, zero at extremes, symmetry, sign reversal, linearity, out-of-section rejection)
- von Mises reductions to pure axial and pure shear limits, combined hand calculation
- exact yield boundary (PASS at margin = 0), below/above yield, deterministic governing-point tie-break, and computed (not assumed) governing point under mixed load
- closed-form reference capacities each producing exactly zero margin at their own defining load, and scaling linearly with yield strength
- mass linearity in density, area, and length, and invalid-length rejection

**Milestone 2** (all Milestone 1 tests remain unchanged and green): additional
tests across 5 new test files, covering:

- component area/centroidal-I hand calculations, top/bottom coordinates, and validation
- built-up centroid, parallel-axis-theorem, and area-sum hand calculations
- translation invariance and component-order invariance of area, centroid, I_z, and section moduli
- overlap rejection vs. allowed boundary-touching
- I/Z/hat factory hand calculations (area, centroid, I_z independently re-derived), symmetric-flange moduli equality, hat-section asymmetric moduli, and invalid-geometry rejection
- built-up normal stress: pure axial, zero stress at the (nonzero) centroid, top/bottom hand calculations, superposition, translation invariance, moment-reversal
- Q(y): zero at the top extreme, hand-calculated for stacked rectangles, component-order invariance
- b_local(y): hand calculation, and the shear-stress jump across a flange/web junction
- shear sign reversal, linear V-scaling, out-of-section rejection, and a clear error for a genuine material void
- built-up strength: pure-axial/pure-bending/pure-shear reductions, exact yield boundary, computed (not assumed) governing point, deterministic tie-break, component-order invariance
- built-up mass (reusing the Milestone 1 mass function unchanged) and density scaling
- an equal-area I-section vs. compact-rectangle comparison demonstrating higher `I_z` and higher `I_z/A` / `min(S)/A`, and first-yield moment following `min(S_top, S_bottom)`

Run the full suite yourself (see below) — all tests pass.

## Representative built-up-section trade result

`examples/built_up_section_trade.py` compares a rectangle, I-section,
Z-section, and hat section of comparable area (within ~4%) under the
Milestone 1 representative combined load:

```
section        A [mm2]   Iz/A     minS/A     governing            margin   status
Rectangle      1593.28   0.5333   13.3333    top                  0.258    PASS
I-section      1626.00   1.6043   32.0851    boundary_1_below     1.269    PASS
Z-section      1564.00   1.6214   31.7917    boundary_1_below     1.207    PASS
Hat-section    1589.84   0.6452   17.8150    top_extreme          0.648    PASS
```

The I- and Z-sections roughly triple the rectangle's bending-stiffness
efficiency (`I_z/A`) and first-yield bending efficiency (`min(S)/A`) at
essentially the same area and mass per unit length, because more of their
material sits far from the neutral axis. All four sections pass this
particular combined load with this material — the geometries were not
tuned to force a pass or fail; see [Efficiency interpretation](#built-up-section-mechanics-milestone-2)
above for the full discussion, including the I-section's flange/web shear
jump.

## Limitations

Milestone 1:

- Rectangular section only — no I, hat, or Z stringer sections yet.
- Elementary (Euler-Bernoulli) beam-stress assumptions only.
- No torsion.
- No shear-center effects.
- No arbitrary thin-walled open-section shear flow.
- No local plate buckling.
- No crippling.
- No column buckling.
- No skin effective width.
- No fastener/joint effects.
- No plasticity.
- No fatigue or damage tolerance.
- Material properties are illustrative only, not certified allowables (not MMPDS values).
- No certification claim of any kind.

Milestone 2 (in addition to the above, which still apply):

- Components carry no lateral (z) position — only bending about z and
  transverse shear in y are modeled; laterally-paired members (e.g. a hat
  section's two webs) are represented via combined width, not tracked
  individually in z.
- No lateral (z) centroid or shear-center calculation.
- Transverse shear is a simplified aggregate-width `V*Q/(I*b_local)`
  treatment, not a thin-wall shear-flow solution — it does not capture
  shear flow around open or closed thin-wall loops.
- No torsion or warping.
- No local plate buckling or crippling of thin flanges/webs (explicitly
  flagged as a concern in the efficiency discussion, but not analyzed).
- No column buckling or frame instability.
- No skin effective width or skin/stringer interaction.
- No fastener/joint effects.
- No fatigue, damage tolerance, or plasticity.
- No section optimization/search and no multiple-load-case sizing.
- No certification claim of any kind.

## Repository layout

```
pyproject.toml
.gitignore
README.md

src/frame_stringer/
    __init__.py                # conventions, package overview
    geometry.py                # RectangularSection (Milestone 1)
    material.py                # IsotropicMaterial
    section_properties.py      # area / centroid / I_z / S_z API (Milestone 1)
    loads.py                   # SectionLoad
    stress.py                  # axial / bending / shear / combined stress (Milestone 1)
    strength.py                # von Mises margin, section strength, reference capacities (Milestone 1)
    mass.py                    # linear mass, mass for length (reused unchanged in Milestone 2)
    built_up_geometry.py       # RectangularComponent, BuiltUpSection (Milestone 2)
    sections.py                # i_section / z_section / hat_section factories (Milestone 2)
    built_up_stress.py         # built-up normal stress, Q(y)/b_local(y) shear, critical points (Milestone 2)
    built_up_strength.py       # built-up strength assessment, bending yield capacity (Milestone 2)

tests/
    test_geometry.py
    test_material.py
    test_section_properties.py
    test_loads.py
    test_stress.py
    test_strength.py
    test_mass.py
    test_built_up_geometry.py
    test_sections.py
    test_built_up_stress.py
    test_built_up_strength.py
    test_built_up_mass_efficiency.py

examples/
    frame_stringer_sanity.py     # Milestone 1 representative sanity case
    built_up_section_trade.py    # Milestone 2 equal-area section efficiency trade
```

## Installation / testing

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python examples/frame_stringer_sanity.py
python examples/built_up_section_trade.py
```

## License status

No license has been chosen yet. Licensing remains **undecided** — do not
assume MIT or any other license until one is explicitly added.
