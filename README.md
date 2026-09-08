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

## Milestone 5 scope

**Milestone 5 adds an explicitly illustrative empirical crippling screen.
Unlike Milestones 3-4's ideal elastic buckling equations (derived from
first-principles eigenvalue theory), crippling correlations are empirical,
configuration-dependent curve fits to test data -- every result here is
labeled an "illustrative preliminary crippling screen," never a sourced
handbook (e.g. MMPDS) or certification value.**

Milestone 5 answers: *even when a thin built-up section passes elastic
material yield, local plate buckling, and global Euler stability, could
the section's flange/web assembly reach a lower empirical crippling limit
first?*

1. an explicit, visible crippling correlation (`alpha`, exponent `m` --
   never hardcoded inside the formula) and a yield cap on the raw
   prediction
2. a conservative, load-independent section-level b/t geometry driver,
   reused directly from the Milestone 3 plate-element mappings
3. an axial-average crippling margin and a peak-compression margin
   (reusing the existing built-up normal-stress extremes -- no new stress
   theory), kept separately visible
4. a section-level crippling assessment with a computed governing mode
5. a `StructuralStatus` integrating yield, local buckling, Euler,
   amplified yield, and crippling side by side -- their margins are never
   mathematically blended; the reported "governing margin" is only the
   minimum of the independently computed preliminary margins
6. sensitivity to thickness, width, the correlation coefficient, and the
   correlation exponent

Explicitly **out of scope** for Milestone 5 (see [Limitations](#limitations)):
sourced handbook/MMPDS/NASA crippling constants, certification allowables,
plastic collapse, nonlinear postbuckling, effective-width iteration,
local-global interaction knockdowns, nonlinear shell/beam FEA,
torsional/flexural-torsional buckling, skin effective width,
skin-stringer interaction, fasteners, fatigue, damage tolerance, multiple
flight load cases, section optimization/search, and final portfolio
figures.

## Milestone 6 scope

**Milestone 6 turns the verified single-load structural mechanics into a
constrained multi-load-case sizing study. This is a preliminary sizing
study, not a general-purpose optimizer: a small, explicit, bounded
uniform-thickness search per fixed-geometry section family, solved by
deterministic bisection over the verified mechanics -- no scipy, no
gradient/genetic/black-box optimization.**

Milestone 6 answers: *what is the minimum practical uniform-thickness
section, within a deliberately bounded design space, that passes yield,
local plate buckling, global member buckling, beam-column amplified
yield, and the illustrative crippling screen across all representative
load cases?*

1. explicit named load cases (`FrameStringerLoadCase`, with a visible,
   never-hidden `load_factor`)
2. uniform-thickness scaling of the I/Z/hat factories, holding outer
   geometry fixed at the Milestone 2 proportions -- never duplicating the
   section-property equations
3. a per-load-case assessment reusing all five existing independent
   checks (yield, local buckling, Euler, amplified yield, crippling)
   unchanged, and a per-section multi-load-case assessment built on top
4. bounded bisection sizing with an explicit illustrative minimum gauge,
   explicit never-silently-expanded search bounds, and an explicit
   tolerance
5. family comparison and a lowest-feasible-mass final recommendation --
   no invented weighted score
6. sensitivity to minimum gauge, member length, K, panel length, and the
   crippling correlation's coefficients

Explicitly **out of scope** for Milestone 6 (see [Limitations](#limitations)):
topology optimization, continuous multi-variable optimization, genetic or
gradient optimization, arbitrary geometry optimization, skin effective
width, skin-stringer interaction, torsion, flexural-torsional buckling,
nonlinear FEA, postbuckling, fatigue, damage tolerance, certification
knockdowns, sourced handbook crippling coefficients, a manufacturing cost
model, final portfolio figures, README consolidation, and licensing.

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

## Crippling and structural-status integration (Milestone 5)

### Crippling-model philosophy

Crippling correlations are empirical and depend on cross-section type,
material, manufacturing, corner radii, element proportions, and the
specific test database they were fitted to. This project therefore:

- does **not** present one formula as universally authoritative,
- does **not** silently invent aerospace handbook constants,
- uses an explicitly illustrative correlation framework with every
  coefficient (`alpha`, exponent `m`) a visible, explicit input, and
- labels every result an **illustrative preliminary crippling screen**.

The architecture keeps the correlation coefficients (`CripplingCorrelation`)
fully separate from the assessment logic, so sourced coefficients could
later replace the illustrative ones without changing how the section-level
screen is computed.

### Generic correlation and yield cap

```
sigma_cc = alpha * sqrt(E * sigma_y) * (t / b_ref)^m

sigma_crippling = min(sigma_cc, sigma_y)   (a correlation should never predict
                                             useful strength above yield)
```

Both the raw and yield-capped values, and whether the cap was active, are
reported. This project's example study uses one illustrative baseline
(`alpha = 1.2`, `m = 0.6`, within the milestone's suggested `alpha` in
`[1.0, 2.0]`, `m` in `[0.5, 0.8]` range) chosen once and applied
consistently -- never tuned after the fact to manufacture a particular
governing mode.

### Section-level geometry driver

`section_geometry_driver` reuses the Milestone 3 plate-element mappings
directly (no dimensional formula duplicated): it considers every mapped
plate element and picks the **most slender** one (largest `b/t`) as the
conservative representative `b_ref`/`t_ref` -- a larger `b/t` drives a
*lower* (more conservative) crippling stress through `(t/b)^m`. This is a
geometry-only, load-independent driver (matching the "pure axial
compression: all longitudinal elements may participate" case).

### Axial-average and peak-compression margins

```
P_comp = max(-N, 0)
P_crippling = sigma_crippling * A            (section-average equivalent capacity)
MS_axial_average = P_crippling/P_comp - 1    (None, trivial pass, at P_comp = 0)

sigma_comp,max = |max_compressive_stress|    (reused directly from the existing
                                               built-up normal-stress result --
                                               accounts for bending, unlike the
                                               axial-average check)
MS_peak_compression = sigma_crippling/sigma_comp,max - 1  (None at zero compression)
```

Both margins stay separately visible; the governing mode ("axial_average"
or "peak_compression") is whichever is smaller, determined by comparison
-- the peak-compression location (top/bottom) swaps correctly when the
bending moment reverses, since it is reused directly from the existing
`evaluate_normal_stress` result.

### Rectangle: reference-only

The compact Milestone 1 rectangle is **not** a thin-walled built-up
section, so the crippling correlation is not applied to it -- it is
reported as not applicable (N/A) rather than forced through a correlation
framework built for flange/web assemblies. The rectangle remains fully
part of the yield/local/global comparisons.

### Structural-status integration

`StructuralStatus` reports yield, local buckling, Euler, amplified yield,
and crippling **side by side** -- their margins are never mathematically
blended into one synthetic interaction margin. The reported "governing
check" and "governing margin" are simply the minimum of the independently
computed, individually valid preliminary margins -- a reporting
convenience, not a combined interaction equation. Overall preliminary pass
requires every *applicable* check to pass.

## Multi-load-case sizing study (Milestone 6)

### Load cases

`FrameStringerLoadCase` bundles a name with the three signed load
components and an explicit `load_factor` (default 1.0) -- `design_load`
applies the factor and returns a `SectionLoad`; no factor is ever hidden
elsewhere in the package. `CANONICAL_LOAD_CASES` is a small, illustrative
set of four structurally different cases (pressure/compression, maneuver
bending, gust/shear, landing/ground combined) -- verified in the test
suite to produce genuinely different governing constraints, not tuned to
force a particular failure mode.

### Uniform-thickness scaling policy

To keep the design space bounded and interpretable, each factory
section's *outer* geometry (flange width, overall height, crown width,
etc.) is held fixed at the Milestone 2 canonical proportions, and every
wall/flange/web thickness is scaled together to one uniform design
thickness `t` (`build_uniform_i_section(t)`, `build_uniform_z_section(t)`,
`build_uniform_hat_section(t)`, each calling the existing, unmodified
factory constructors -- no dimensional formula is duplicated). **Milestone
6 sizes a uniform-gauge version of each fixed outer geometry; it does not
optimize individual element thicknesses.**

### Minimum gauge and bounded bisection

An explicit `t_min_gauge` (illustrative minimum manufacturing gauge --
not a certification/manufacturer requirement) and explicit search bounds
`[t_min_search, t_max_search]` are always visible inputs. The effective
lower bound is `max(t_min_search, t_min_gauge)`; the search upper bound is
never silently expanded. Because the "all load cases pass" predicate was
verified (in the test suite, over a thickness grid, for every family) to
be monotonic non-decreasing in `t` for the canonical geometries and load
cases, bounded bisection is used (tolerance `1e-6` m by default) rather
than a black-box optimizer -- if the lower bound already passes, it is
returned directly (`"minimum_gauge_governs"` if that bound came from the
gauge); if the upper bound fails, the search reports
`"upper_bound_infeasible"` rather than silently expanding; otherwise
bisection converges to the minimum passing thickness (`"converged"`),
which is always returned as a *passing* thickness, never a failing one.

### Per-load-case and multi-case assessment

`assess_load_case` reuses all five existing, unmodified checks (yield,
local buckling, Euler, amplified yield, crippling) and
`assess_structural_status`'s fixed tie-break order (`yield`,
`local_buckling`, `euler`, `amplified_yield`, `crippling`) directly --
no new equation or tie-break convention is introduced.
`assess_multi_load_case` runs every supplied load case and selects the
governing one by the same minimum-applicable-margin convention, with a
deterministic tie-break on the supplied load-case order.

### Family comparison and recommendation

Every family is sized under **identical** assumptions (material, load
cases, panel length, member geometry, K, minimum gauge, crippling
correlation, and search bounds/tolerance -- the fairness rule).
`recommend_family` returns the lowest-mass-per-length *feasible* result
(ties broken by the fixed family order); mass reuses
`frame_stringer.mass.linear_mass` unchanged. No weighted score is
invented, and an all-infeasible study returns `None` explicitly rather
than a misleading default.

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

**Milestone 5** (all Milestones 1-4 tests remain unchanged and green):
additional tests across 4 new test files, covering:

- correlation validation (alpha/exponent/non-finite/empty-label rejection), the hand-calculated correlation value at the milestone's own worked example (which comes out capped -- confirmed explicitly), a separate slender-element case confirming the cap can be inactive, and the exact-boundary case (raw == yield) correctly *not* flagged as cap-active
- scaling verified entirely in the pre-cap regime (as required, using a deliberately slender constructed element): linear in alpha, `t^m`, `b^-m`, `sqrt(E)`, and `sqrt(sigma_y)`
- section geometry driver: I/Z/hat governing-element (largest b/t) hand verification, a deterministic tie-break between the hat's two identical webs, component-order independence, and confirmation that panel length does not affect the geometry driver
- axial capacity: `P_crippling = sigma_crippling * A`, zero-compression and tension both giving "not applicable", and the exact/below/above capacity boundary
- peak-compression screen: pure-axial, pure-bending, and combined hand calculations (all reusing the existing built-up normal-stress result), moment-reversal swapping the governing compression side, zero-compression giving N/A, and the exact/below/above boundary
- governing mode: an axial-average-vs-peak-compression tie (pure axial, no bending) resolved by the fixed tie-break order, a peak-compression-governed bending-dominated construction, and repeated-call determinism
- structural-status integration: an all-safe overall PASS, six single-check-only failure constructions (yield, local buckling, Euler, amplified yield, and crippling each in turn, holding the other four safe) each correctly failing the overall status, the governing check matching the true minimum of the applicable margins, confirmation that the reported margin is never a synthetic blend (it always equals one of the independent margins exactly), and graceful handling when crippling is not applicable (e.g. the rectangle)
- a dedicated regression test confirming that, for the Milestone 2/3 representative (fairly stocky) I/Z/hat proportions, the illustrative baseline correlation is honestly yield-capped for all three -- documenting rather than hiding this finding

Run the full suite yourself (see below) — all tests pass.

**Milestone 6** (all Milestones 1-5 tests remain unchanged and green):
additional tests across 4 new test files, covering:

- load-case validation (name/non-finite/load-factor rejection), design-load scaling, and signed-load preservation
- uniform-thickness factory wrappers: thickness propagation to every I/Z/hat wall element, fixed outer geometry (overall height, flange width) preserved while `t` changes, and invalid-thickness rejection
- single-load-case assessment returning all five checks, a safe PASS, five separate constructed single-constraint failures (one per check: yield, local buckling, Euler, amplified yield, crippling), the governing constraint matching the true minimum applicable margin, deterministic exact-tie behavior, and repeated-call determinism
- multi-case assessment: all-safe PASS, one-failing-case FAIL, governing-load-case selection by minimum margin, load-case order preservation, deterministic ties, and identical duplicate cases using the first occurrence
- thickness monotonicity: area and mass strictly increasing with `t`, and "all load cases pass" verified non-decreasing (no oscillation) over a thickness grid for all three families -- the precondition the sizing search's bisection relies on
- sizing: an already-passing lower bound, minimum-gauge-governs, lower-fails/upper-passes convergence, the returned thickness verified to actually pass (and a slightly thinner point verified to fail), explicit upper-bound-infeasible handling with diagnostics still exposed, repeated-call determinism, bounds/tolerance respected, and the returned mass matching `linear_mass` exactly
- family comparison: identical assumptions applied to every family, the recommendation matching the true minimum feasible mass, family-order invariance when masses differ, a deterministic tie-break with synthetic equal masses, an infeasible family excluded honestly, and an all-infeasible study returning `None` rather than a misleading default
- sensitivity: increasing minimum gauge can only increase (never decrease) the selected thickness and mass, gauge governing exactly once it exceeds the structural requirement, increasing member length or K never improving the Euler capacity (and both propagating into a higher required sizing thickness), a genuinely crippling-governed weak-correlation case requiring more thickness than a strong one, and panel length leaving the compression-buckling critical stress unchanged for a fixed section

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

## Representative crippling-screen result

`examples/crippling_strength_study.py` screens the same I/Z/hat geometries
(rectangle excluded -- see below) with one illustrative baseline
correlation (`alpha = 1.2`, `m = 0.6`) under the common combined load:

```
section       gov elem    b/t   raw sig_cc  cap sig_cc  cap?  axial MS  peak MS   status
I-section     web         13.5      1154         300    YES      5.10     1.38     PASS
Z-section     web         13.8      1139         300    YES      4.87     1.28     PASS
Hat-section   web_left     8.3      1545         300    YES      4.96     0.65     PASS
```

For these representative (fairly stocky, governing `b/t` of 8-14)
proportions, the illustrative correlation predicts a raw crippling stress
well above material yield in every case -- **the yield cap is active
throughout**, so the capped crippling stress equals `sigma_y` and the
crippling margins closely track the amplified-yield margins. This is the
honest, un-tuned result of applying the milestone's own suggested
coefficient range to these particular geometries; a dedicated regression
test locks this finding in (see [Verification summary](#verification-summary)).
The accompanying thickness, width, alpha, and exponent sensitivity studies
(I-section) show the same plateau persisting across the entire ±50%
sensitivity range explored, while separately-constructed thinner elements
in the test suite confirm the correlation, cap, and all scaling laws
behave correctly once genuinely below yield.

The compact rectangle is excluded from the crippling screen entirely
(reported N/A) -- it is not a thin-walled built-up section, so applying a
flange/web crippling correlation to it would not be a meaningful
comparison; it remains part of the yield/local/global comparisons.

## Representative multi-load-case sizing result

`examples/multi_load_case_sizing.py` sizes uniform-thickness I/Z/hat
sections across the four canonical load cases, under the same material,
panel length (300 mm), member length (1200 mm), K (1.0), crippling
correlation, and search bounds (0.75-6.0 mm, 1e-6 m tolerance) for every
family:

```
family       req t [mm]  area [mm2]  mass [kg/m]           gov case      gov constraint  status
I-section         3.877       823.0        2.222  landing/ground comb.   amplified_yield  converged
Z-section         5.132       923.8        2.494  landing/ground comb.   amplified_yield  converged
Hat-section       5.076      1221.7        3.298  landing/ground comb.   amplified_yield  converged
```

**Final recommendation: I-section at t = 3.877 mm, 2.222 kg/m** -- the
lowest feasible mass among the three families under identical assumptions.
The governing load case ("landing/ground combined", the highest
compressive axial force) and constraint (amplified yield) were not
assumed in advance: at the selected design, "gust/shear" (the highest
shear case) instead governs via ordinary yield, and the other two cases
have comfortable margins -- exactly the kind of load-case-dependent
governance the milestone set out to demonstrate. The accompanying
sensitivity studies show required thickness rising monotonically with
member length (3.63-4.73 mm over L = 0.75-2.0 m) and with K (3.58-5.43 mm
over K = 0.5-2.0), while panel length and the crippling correlation's
coefficients have *no* effect on this particular selected design, because
amplified yield -- not local-buckling shear or crippling -- governs
throughout its feasible range; a more slender design could see either
become the governing sensitivity instead (as Milestone 5's dedicated
weak-correlation test confirms).

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
- No postbuckling behavior and no crippling (added in Milestone 5).
- No skin effective width or skin-stringer interaction, no frame-ring
  global modes.
- No fastener/joint effects, fatigue, or damage tolerance.
- No certification knockdowns of any kind.
- No certification claim of any kind.

Milestone 5 (in addition to the above, which still apply):

- The crippling correlation coefficients (`alpha`, `m`) are **explicitly
  illustrative** — not sourced from MMPDS, NASA, or any vendor/test
  database, and not claimed to be accurate for any real material,
  cross-section family, or manufacturing process. Every crippling result
  is labeled an "illustrative preliminary crippling screen."
- No plastic collapse, no nonlinear postbuckling, no effective-width
  iteration.
- No local-global interaction knockdown — Milestone 3's local-buckling
  margin and Milestone 5's crippling margin are reported side by side in
  `StructuralStatus`, never combined into one interaction check.
- No nonlinear shell/beam FEA.
- No torsional or flexural-torsional buckling (unchanged from Milestone 4).
- No skin effective width or skin-stringer interaction.
- No fasteners, fatigue, or damage tolerance.
- No multiple flight load cases and no section optimization/search (added
  as a *bounded, deterministic* uniform-thickness search in Milestone 6 --
  see below; still not a general-purpose optimizer) — the crippling
  screen is applied to the geometries as given, never resized to force a
  particular outcome.
- The section-level geometry driver considers the *most slender* mapped
  plate element only (a single conservative b/t) — it does not model
  interaction between multiple simultaneously-critical elements, corner
  radii, or fastener/rivet-line effects on effective width.
- `StructuralStatus`'s "governing margin" is explicitly documented as the
  minimum of independently computed preliminary margins — a reporting
  convenience, not a combined interaction equation.
- No certification claim of any kind.

Milestone 6 (in addition to the above, which still apply):

- **This is a preliminary sizing study, not a general-purpose
  optimizer.** No scipy, gradient, genetic, or other black-box
  optimization is used — only deterministic bounded bisection (verified
  monotonic for the canonical geometries/load cases) over the unmodified
  Milestone 1-5 mechanics.
- Uniform-thickness scaling only — each family's outer geometry is held
  fixed and every wall/flange/web thickness is scaled together to one
  design value `t`; individual element thicknesses are never optimized
  independently, and no topology or continuous multi-variable
  optimization is performed.
- The illustrative minimum manufacturing gauge (`t_min_gauge`) is exactly
  that — illustrative. It is not a certification or manufacturer
  requirement, and it does not itself model damage tolerance, handling
  robustness, corrosion allowance, or manufacturing detail (e.g. corner
  radii, fastener holes).
- The load cases in `CANONICAL_LOAD_CASES` are explicitly illustrative,
  chosen only to be structurally distinct — they are not derived from any
  certified flight-loads envelope.
- No skin effective width, skin-stringer interaction, torsion, or
  flexural-torsional buckling (unchanged from earlier milestones).
- No nonlinear FEA, postbuckling, fatigue, damage tolerance, or
  certification knockdowns.
- No sourced handbook crippling coefficients (unchanged from Milestone 5)
  and no manufacturing cost model.
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
    crippling.py               # CripplingCorrelation, geometry driver, section crippling assessment (Milestone 5)
    structural_status.py       # StructuralStatus: yield/local/Euler/amplified-yield/crippling side by side (Milestone 5)
    load_cases.py              # FrameStringerLoadCase, CANONICAL_LOAD_CASES (Milestone 6)
    sizing.py                  # uniform-thickness factories, per-case/multi-case assessment, bisection sizing (Milestone 6)
    design_study.py            # StudyAssumptions, family comparison and recommendation (Milestone 6)

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
    test_crippling.py
    test_crippling_section.py
    test_crippling_sensitivity.py
    test_structural_status.py
    test_load_cases.py
    test_sizing.py
    test_design_study.py
    test_sizing_sensitivity.py

examples/
    frame_stringer_sanity.py         # Milestone 1 representative sanity case
    built_up_section_trade.py        # Milestone 2 equal-area section efficiency trade
    local_plate_buckling_study.py    # Milestone 3 local-buckling screening + sensitivity study
    global_member_buckling_study.py  # Milestone 4 global buckling + beam-column screening + sensitivity study
    crippling_strength_study.py      # Milestone 5 crippling screening + structural-status integration + sensitivity study
    multi_load_case_sizing.py        # Milestone 6 multi-load-case uniform-thickness sizing study + sensitivity study
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
python examples/crippling_strength_study.py
python examples/multi_load_case_sizing.py
```

## License status

No license has been chosen yet. Licensing remains **undecided** — do not
assume MIT or any other license until one is explicitly added.
