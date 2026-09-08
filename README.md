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

## Verification summary

89 tests across 7 test files, covering:

- geometry hand calculations, centroid, positive-dimension and finite-value validation
- material validation (all five fields, including non-finite rejection)
- axial/bending superposition, sign reversal, linearity, zero-load case
- shear distribution (neutral-axis maximum, zero at extremes, symmetry, sign reversal, linearity, out-of-section rejection)
- von Mises reductions to pure axial and pure shear limits, combined hand calculation
- exact yield boundary (PASS at margin = 0), below/above yield, deterministic governing-point tie-break, and computed (not assumed) governing point under mixed load
- closed-form reference capacities each producing exactly zero margin at their own defining load, and scaling linearly with yield strength
- mass linearity in density, area, and length, and invalid-length rejection

Run the full suite yourself (see below) — all tests pass.

## Limitations

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

## Repository layout

```
pyproject.toml
.gitignore
README.md

src/frame_stringer/
    __init__.py             # conventions, package overview
    geometry.py              # RectangularSection
    material.py               # IsotropicMaterial
    section_properties.py     # area / centroid / I_z / S_z API
    loads.py                   # SectionLoad
    stress.py                   # axial / bending / shear / combined stress
    strength.py                  # von Mises margin, section strength, reference capacities
    mass.py                        # linear mass, mass for length

tests/
    test_geometry.py
    test_material.py
    test_section_properties.py
    test_loads.py
    test_stress.py
    test_strength.py
    test_mass.py

examples/
    frame_stringer_sanity.py   # representative sanity case (driver script)
```

## Installation / testing

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python examples/frame_stringer_sanity.py
```

## License status

No license has been chosen yet. Licensing remains **undecided** — do not
assume MIT or any other license until one is explicitly added.
