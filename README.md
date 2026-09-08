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

## Milestone 3 scope

**Milestone 3 adds classical elastic local-plate-buckling screens to the
verified built-up beam sections. These checks identify the onset of ideal
plate instability; they do not model postbuckling, crippling, effective
width, or certification knockdowns.**

Milestone 3 answers: *does a built-up section that passes the elastic von
Mises stress check remain locally stable in its thin web/flange/crown
elements under the same axial+bending+shear load state?*

1. a rectangular plate-element primitive with an explicit "internal" or
   "outstanding" boundary condition
2. classical illustrative elastic compression-buckling and shear-buckling
   coefficients and critical stresses
3. compression, shear, and an illustrative preliminary interaction margin
   -- kept strictly separate from (never blended with) the elastic von
   Mises yield margin
4. explicit I/Z/hat plate-element mappings (web, flange outstands, crown)
   built directly from the same factory geometry parameters
5. local stress demand sampled from the existing, already-verified
   built-up beam stress solution (no new stress theory)
6. a section-level local-buckling assessment with a computed (never
   assumed) governing plate and mode
7. a thickness/width/panel-length/boundary-condition sensitivity study

Explicitly **out of scope** for Milestone 3 (see [Limitations](#limitations)):
empirical crippling, postbuckling, plasticity, effective-width iteration,
overall Euler/beam-column buckling, skin-stringer interaction, frame-ring
global instability, torsional/distortional buckling, warping,
fastener/joint effects, fatigue, damage tolerance, nonlinear shell FEA,
certification knockdowns, sourced aerospace allowables, multi-load-case
sizing search, mass optimization, and final portfolio figures.

## Milestone 4 scope

**Milestone 4 adds ideal elastic global member buckling and first-order
beam-column moment amplification. Local plate buckling, global Euler
instability, and material yield remain separate checks; no nonlinear
collapse or certification knockdowns are implied.**

Milestone 4 answers: *a section may pass yield and local plate buckling,
but will the complete frame/stringer member remain globally stable under
compressive axial load and combined axial compression + bending?*

1. an explicit member geometry (length, effective-length factor K -- never
   buried inside a section or material object)
2. radius of gyration and slenderness ratio, reusing existing section
   area/I_z
3. the classical ideal elastic Euler critical load/stress and its margin
4. a first-order elastic beam-column moment-amplification factor
5. a beam-column amplified-yield screen that reuses the existing
   (unmodified) built-up stress/yield machinery, with only the bending
   moment replaced
6. a combined axial-compression + bending global-stability assessment with
   a computed (never assumed) governing mode
7. a side-by-side yield/local-buckling/global-Euler/amplified-yield summary
8. member-length, K, and section-stiffness sensitivity studies

Explicitly **out of scope** for Milestone 4 (see [Limitations](#limitations)):
empirical crippling, Johnson/inelastic column formulas, local-global
interaction knockdowns, postbuckling, nonlinear geometry, nonlinear
beam-column FEA, torsional buckling, flexural-torsional buckling, warping,
frame-ring global modes, skin effective width, skin-stringer interaction,
fastener/joint effects, fatigue, damage tolerance, certification
knockdowns, multi-load-case sizing search, mass optimization, and final
portfolio figures.

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

## Local plate buckling mechanics (Milestone 3)

### Plate-element model and boundary conditions

A `PlateElement` is an idealized rectangular plate: width `b` (unsupported
width transverse to the compressive stress direction), thickness `t`,
length `a` (in the loading/longitudinal direction -- the panel length /
frame spacing), and an explicit boundary condition, one of:

- `"internal"` -- both unloaded (longitudinal) edges simply supported
  (e.g. a web, held by a flange on each side).
- `"outstanding"` -- one unloaded edge simply supported, the other free
  (e.g. an I-flange half-outstand, a Z-flange, a hat's crown-to-flange leg).

These are **classical illustrative plate coefficients** for a first-order
elastic screen -- not a certification standard and not a complete
aerospace design rule (no elastic edge restraint, no postbuckling).

### Compression buckling

```
k_c(internal) = 4.0
k_c(outstanding) = 0.43

sigma_cr = k_c * pi^2*E / [12*(1-nu^2)] * (t/b)^2
```

`sigma_cr` is the ideal elastic local compression-buckling stress, kept
strictly separate from material yield.

### Shear buckling

For an **internal** plate only, using the classical simply-supported-plate
relation (symmetric in which side is "length" vs. "width"):

```
ratio = max(a/b, b/a)
k_s   = 5.34 + 4.0/ratio^2

tau_cr = k_s * pi^2*E / [12*(1-nu^2)] * (t/b)^2
```

For an **outstanding** plate, no defensible classical shear-buckling
coefficient is implemented -- shear buckling of a one-edge-free flange is
a materially different problem from the simply-supported case, and is not
verified here. `shear_buckling_coefficient("outstanding", ...)` and
`critical_shear_stress` both return `None` (**not applicable**, never
silently reused from the internal-plate formula), and the interaction
screen (below) is skipped for that plate -- only its compression margin
applies.

### Margins and the interaction screen

```
sigma_comp = max(-sigma_x, 0)              (Milestone 1-2 convention: negative sigma_x = compression)
MS_comp    = sigma_cr/sigma_comp - 1       (None, trivially passing, if sigma_comp == 0)

MS_shear   = tau_cr/|tau_xy| - 1           (None, trivially passing, if tau_cr is N/A or tau_xy == 0)

FI              = (sigma_comp/sigma_cr)^2 + (|tau_xy|/tau_cr)^2   (only when tau_cr applies)
MS_interaction  = 1/sqrt(FI) - 1           (None if FI is N/A or exactly 0)
```

The interaction relation is labeled an **illustrative elastic
local-buckling interaction screen** -- it is *not* a universally
applicable plate-buckling interaction law. The individual compression and
shear margins remain separately visible in every result; nothing is
blended into the interaction number silently. The governing mode
("compression", "shear", or "interaction") is the one with the smallest
margin among those that apply, determined by comparison, with a fixed
(compression, shear, interaction) tie-break order.

Local buckling is kept **strictly separate** from the elastic von Mises
yield screen -- `assess_section_local_buckling` and
`assess_builtup_strength` produce two independent margins that are never
numerically blended; `combined_elastic_status` only reports the two
pass/fail flags and their two minimum margins side by side, plus
`yield_passes AND local_buckling_passes`.

### Mapping I/Z/hat sections to plate elements

Plate topology is mapped **explicitly** per shape -- generic inference
from arbitrary rectangles is not attempted:

- **I-section**: the web is an internal plate (width = clear web height).
  Each flange's outstand beyond the web, `(flange_width -
  web_thickness)/2`, is a separate outstanding plate (top and bottom kept
  distinct, since one may be in compression while the other is in tension).
- **Z-section**: the web is internal (width = web height). Each Z-flange
  is a *single-sided* cantilevered arm off the web (unlike the I-flange,
  which continues through the web on both sides), so its *full*
  `flange_width` is one outstanding plate; top and bottom kept distinct.
- **Hat section**: the crown is an internal plate spanning the clear
  distance between the two webs (`crown_width - 2*wall_thickness`). Each
  web is an internal plate (width = the clear web run, supported by the
  crown above and the flange below). Each bottom flange is an outstanding
  plate of width `flange_width`. Because the underlying model carries no
  lateral (z) position, the two webs (and the two flanges) are
  geometrically identical here, but are still reported as distinct named
  plates (`web_left`/`web_right`, `flange_left`/`flange_right`).

All plate elements from one section share the same explicit `panel_length`
(frame/stiffener spacing) -- it is never invented inside the material or
section objects; it is always an explicit input to the mapping.

### Local stress demand extraction

Local stress demand is sampled from the existing, already-verified
built-up beam stress solution -- no new stress theory:

- **Normal stress** is linear in y, so the most-compressive value within a
  plate's y-range is always at one of its two endpoints; both are
  evaluated and the more negative one is kept (a net-tension plate
  correctly yields zero compression demand).
- **Shear stress** is a smooth (piecewise-quadratic) function of y within
  a single homogeneous component; a fixed number of evenly-spaced interior
  sample points (inset slightly from the exact edges, which can otherwise
  resolve to a neighboring component under the documented `b_local`
  boundary convention) is evaluated, and the largest magnitude is taken as
  the representative demand.

## Representative local-buckling result

`examples/local_plate_buckling_study.py` screens the same I/Z/hat
geometries as the Milestone 2 trade study, with an illustrative panel
length of 300 mm, under the Milestone 1 representative combined load:

```
section       yield margin   buckling margin     governing plate   governing mode   status
I-section            1.269            11.158                 web      interaction    PASS
Z-section            1.207             9.218  top_flange_outstand      compression    PASS
Hat-section          0.648            22.869            web_left      interaction    PASS
```

All three (relatively stocky) Milestone 2 geometries remain locally stable
under this load -- this was not tuned; the sections simply are not thin
enough here to buckle first. The accompanying I-section sensitivity study
(flange thickness, web thickness, panel length, and outstand width, each
scaled 0.75x-1.5x) confirms the expected classical trends: thickness
scaling improves margin roughly with the square of the thickness ratio;
outstand widening reduces the flange's own compression margin; and panel
length shifts the web's shear margin slightly via the aspect ratio, while
leaving its compression margin unaffected. A separate thinner, wider
flange construction in the same example (and in the test suite) is shown
to fail local buckling while comfortably passing yield -- the key
Milestone 2-vs-3 lesson: elastic beam-stress/yield checks alone do not
guarantee that a bending-efficient section's thin elements are locally
stable.

## Global member buckling and beam-column mechanics (Milestone 4)

### Member geometry and the effective-length convention

A `MemberGeometry` carries only `length` (L, the physical unsupported
member length) and `effective_length_factor` (K) -- both must be finite
and > 0. K is always an **explicit, visible modeling assumption**, never
buried inside a section or material object. Illustrative classical values:
K = 0.5 (fixed-fixed idealization), K = 0.7 (restrained-end illustrative
case), K = 1.0 (pinned-pinned), K = 2.0 (fixed-free) -- none of these claim
to exactly represent a specific real fuselage frame/stringer installation.

```
L_eff = K * L
```

### Radius of gyration and slenderness

```
r_g = sqrt(I_z / A)          (reuses the section's own .area / .moment_of_inertia_z -- never duplicated)
lambda = K*L / r_g            (slenderness ratio, dimensionless)
```

### Euler critical load and stress

```
P_cr      = pi^2 * E * I_z / (K*L)^2
sigma_cr  = P_cr / A   =   pi^2*E / lambda^2      (both forms verified equivalent)

P_comp = max(-N, 0)            (Milestone 1-2 convention: N < 0 = compression)
MS_Euler = P_cr/P_comp - 1     (None, trivially passing, if P_comp == 0 -- i.e. N >= 0)
```

This is the **ideal elastic Euler global-buckling margin** -- not a flight
or certification margin. `P_comp == P_cr` gives margin exactly 0 (PASS).
Only the compressive axial component drives this bare Euler check; bending
does not alter it (bending's effect is handled separately, below).

### First-order beam-column amplification

Axial compression amplifies bending demand *before* Euler collapse:

```
B = 1 / (1 - P_comp/P_cr)              for 0 <= P_comp < P_cr
M_amplified = M_applied * B

e = |M_applied| / P_comp               (first-order eccentricity diagnostic; None at P_comp = 0)
```

This is the **first-order elastic beam-column amplification** -- not a
nonlinear collapse solution. At `P_comp = 0`, `B = 1` (no amplification);
as `P_comp` approaches `P_cr`, `B` grows without bound; at `P_comp >=
P_cr`, `B` and `M_amplified` are `None` (global instability -- reported
explicitly, never a divide-by-zero or a misleadingly finite number).

### Beam-column amplified-yield screen

The amplified moment is fed back into the **existing, unmodified**
built-up (or rectangular) stress/von-Mises machinery -- `N` and `V_y`
unchanged, only `M_z` replaced by `M_amplified`:

```
sigma_x(y) = N/A - M_amplified*(y - y_bar)/I_z
```

No stress equation is duplicated. This is labeled the **beam-column
amplified yield screen**, and the ordinary (unamplified, Milestone 1/2)
yield result remains separately visible alongside it -- never overwritten.

### Combined assessment and section-level summary

`assess_beam_column` returns Euler and amplified-yield results together,
with a governing mode ("euler" or "amplified_yield") chosen by comparing
margins -- never assumed, with a fixed (euler, amplified_yield) tie-break.
Overall pass requires `euler_passes AND amplified_yield_passes`.
`section_stability_summary` reports yield, local-buckling, Euler, and
amplified-yield pass/fail and their four margins **side by side** -- these
are never blended into one synthetic combined margin.

### Local vs. global stability

Local buckling (Milestone 3) depends on an individual plate's own `b/t`
and is essentially insensitive to overall member length. Global Euler
buckling (Milestone 4) depends on the *whole section's* `I_z/A` and is
highly sensitive to member length and end restraint (K). A section can be
globally strong but locally weak, or locally stocky but globally slender
-- neither implies the other, and both remain separately reported.

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

**Milestone 3** (all Milestones 1-2 tests remain unchanged and green):
additional tests across 3 new test files, covering:

- plate-element validation (width/thickness/length/boundary-condition/non-finite rejection) and aspect-ratio hand calculation
- compression coefficient (internal = 4.0, outstanding = 0.43), shear coefficient hand calculation (including the reciprocal-equivalent case for aspect ratio < 1), and rejection of an unrecognized boundary condition
- critical-stress hand calculations for compression and shear, t² scaling, b⁻² scaling, linear E scaling, the internal/outstanding critical-stress ratio, and Poisson-ratio sensitivity following the `1/(1-nu^2)` denominator
- margins: zero-demand → `None`, exact boundary → margin 0 (PASS), below/above for both compression and shear, the interaction hand calculation (0.6²+0.8²=1 → margin 0), and a deterministic mode tie-break (shear vs. interaction, both reducing to the identical expression at zero compression demand)
- I/Z/hat plate-element mapping: expected plate names/counts, I-section web and flange-outstand geometry hand calculations, Z-section's full-width (not halved) flange outstand, hat-section's clear crown width, and exact panel-length propagation
- stress extraction: zero compression demand for a tension-only plate, correct extreme-fiber stress for the compression-side flange, moment-reversal swapping which side is in compression, web shear demand matching the existing built-up shear result, linear load scaling, and component-order independence
- section-level assessment: an all-safe PASS, constructed compression-buckling and shear-buckling failures, a case with both compression and shear margins present, deterministic governing-plate tie-break, repeated-call determinism, yield-passes-while-buckling-fails and buckling-passes-while-yield-fails constructions, and the combined (never-blended) overall status
- section-level sensitivity: flange/web thickness scaling, panel-length effect on shear (not compression) critical stress, and outstand-width scaling -- each verified through the full I-section factory mapping, not just the raw plate formulas

**Milestone 4** (all Milestones 1-3 tests remain unchanged and green):
additional tests across 3 new test files, covering:

- member-geometry validation (length/K/non-finite rejection) and effective-length hand calculation
- radius-of-gyration and slenderness hand calculations, linearity in K and L, and the decrease in slenderness as radius of gyration increases
- Euler hand calculation, the stress/load-form identity (`P_cr/A` vs. `pi^2*E/lambda^2`), L⁻² scaling, K⁻² scaling, linear E scaling, linear I scaling, zero-compression and tension both giving "not applicable", and the exact/below/above `P_cr` boundary
- amplification factor: `B=1` at zero compression, the 0.5·P_cr → B=2 hand calculation, monotonic increase, strong growth approaching `P_cr`, and explicit (never silently divided) handling at/above `P_cr`
- amplified moment: zero applied moment stays zero, linear scaling at fixed `P/P_cr`, and moment reversal flipping only the sign
- amplified stress/yield: zero compression reproduces the ordinary built-up strength result exactly, compressive load increases bending magnitude, amplified top/bottom stress hand calculation, moment reversal swapping top/bottom, shear left unchanged, and a constructed case where amplified yield fails while the unamplified screen still passes
- global assessment: an all-safe PASS, a constructed Euler-governed failure, a constructed amplified-yield-governed failure, deterministic governing-mode selection, component-order invariance, repeated-call determinism, and the combined (never-blended) overall status requiring both Euler and amplified yield to pass
- section-level sensitivity through the full beam-column path: `P_cr` falling and amplification rising with member length, `P_cr` and Euler margin worsening with K, linear `EI` scaling, and the I-section's larger radius of gyration and Euler load vs. an equal-area compact rectangle

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

## Representative global-stability result

`examples/global_member_buckling_study.py` screens the same rectangle/I/Z/hat
geometries at an illustrative member length L = 1200 mm, K = 1.0
(pinned-pinned), under the Milestone 1 representative combined load:

```
section       Pcr [kN]   P/Pcr      B   unamp MS   amp MS   Euler MS   status
Rectangle       407.7   0.1962 1.2441      0.258    0.055      4.096     PASS
I-section      1251.5   0.0639 1.0683      1.269    1.209     14.644     PASS
Z-section      1216.6   0.0658 1.0704      1.207    1.148     14.208     PASS
Hat-section     492.1   0.1626 1.1941      0.648    0.445      5.152     PASS
```

The I- and Z-sections' larger `I_z/A` (and hence radius of gyration) gives
them roughly 3x the compact rectangle's Euler critical load at comparable
area -- the same material redistribution that helped Milestone 2's bending
efficiency also helps Milestone 4's global stability. All four sections
pass at this length; the rectangle's *amplified* yield margin (0.055) is
far thinner than its unamplified one (0.258), and far thinner than the
I-section's (1.209) at the same load and length, showing the beam-column
amplification effect concretely. The accompanying length and K sensitivity
studies (I-section, L from 0.5-3.0 m and K from 0.5-2.0) show `P_cr`
falling and the amplification factor `B` rising monotonically in both
directions, without forcing a crossover to FAIL that does not occur at
these illustrative values.

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

Milestone 3 (in addition to the above, which still apply):

- Classical illustrative elastic plate coefficients only (k_c = 4.0
  internal / 0.43 outstanding; k_s from the simply-supported-plate
  relation) — not a sourced aerospace allowable, not edge-restraint-aware,
  not a complete design rule.
- No empirical crippling — this is an ideal elastic eigenvalue screen, not
  a post-buckling ultimate-strength prediction.
- No postbuckling behavior or effective-width iteration.
- No plasticity.
- Outstanding-plate shear buckling is explicitly **not implemented**
  (reported as not-applicable) rather than reusing the internal-plate
  formula without justification.
- No overall Euler/beam-column buckling (added in Milestone 4), skin-stringer
  interaction, frame-ring global instability, torsional or distortional
  buckling, or warping.
- No fastener/joint effects, fatigue, or damage tolerance.
- No nonlinear shell FEA.
- No certification knockdowns or sourced aerospace allowables.
- No multi-load-case sizing search, mass optimization, or section resizing
  (Milestone 3 only screens the Milestone 2 geometries as given).
- Plate topology is mapped explicitly per factory shape (I/Z/hat) — no
  generic inference of plate topology from arbitrary user-built
  `BuiltUpSection` objects.
- Local stress demand is sampled at a fixed, non-adaptive set of points
  (both endpoints for normal stress; 21 evenly-spaced interior points for
  shear) rather than derived from a closed-form extremum search; this is
  accurate for the linear-normal-stress / smooth-quadratic-shear fields
  produced by this beam model, but is a numerical approximation, not an
  exact analytical optimum.
- No certification claim of any kind.

Milestone 4 (in addition to the above, which still apply):

- Ideal elastic Euler buckling only — a straight, prismatic, initially
  perfect member; no initial crookedness, no residual stress.
- No plastic/inelastic column behavior — no Johnson, Rankine, or other
  inelastic-column correction formulas.
- The effective-length factor K is an idealized, explicit, user-supplied
  modeling assumption (e.g. K = 0.5/0.7/1.0/2.0 illustrative cases) — it
  does not claim to represent the true end restraint of any specific real
  fuselage frame/stringer installation.
- No lateral-torsional buckling and no flexural-torsional buckling.
- No geometric nonlinear analysis and no nonlinear beam-column FEA — the
  beam-column amplification used is the classical linear (first-order)
  `1/(1-P/Pcr)` result, not a large-deflection solution.
- No local-global buckling interaction — Milestone 3's local-buckling
  margin and Milestone 4's Euler/amplified-yield margins are reported
  side by side, never combined into one interaction check.
- No postbuckling behavior and no crippling.
- No skin effective width or skin-stringer interaction, no frame-ring
  global modes.
- No fastener/joint effects, fatigue, or damage tolerance.
- No certification knockdowns of any kind.
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
    plate_buckling.py          # PlateElement, compression/shear buckling, margins, interaction (Milestone 3)
    local_buckling.py          # I/Z/hat plate mappings, stress extraction, section assessment (Milestone 3)
    column_buckling.py         # MemberGeometry, radius of gyration, slenderness, Euler buckling (Milestone 4)
    beam_column.py             # beam-column amplification, amplified-yield screen, global assessment (Milestone 4)

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
    test_plate_buckling.py
    test_local_buckling.py
    test_local_buckling_sensitivity.py
    test_column_buckling.py
    test_beam_column.py
    test_global_stability_sensitivity.py

examples/
    frame_stringer_sanity.py         # Milestone 1 representative sanity case
    built_up_section_trade.py        # Milestone 2 equal-area section efficiency trade
    local_plate_buckling_study.py    # Milestone 3 local-buckling screening + sensitivity study
    global_member_buckling_study.py  # Milestone 4 global buckling + beam-column screening + sensitivity study
```

## Installation / testing

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python examples/frame_stringer_sanity.py
python examples/built_up_section_trade.py
python examples/local_plate_buckling_study.py
python examples/global_member_buckling_study.py
```

## License status

No license has been chosen yet. Licensing remains **undecided** — do not
assume MIT or any other license until one is explicitly added.
