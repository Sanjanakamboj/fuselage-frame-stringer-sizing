"""frame_stringer: verified beam-section mechanics for fuselage frame/stringer sizing.

Milestone 1 scope
------------------
This package implements the fundamental beam-section mechanics required before
any realistic frame/stringer sizing can be attempted:

1. cross-section geometry/properties (rectangular section baseline)
2. axial and bending normal stress
3. transverse shear stress
4. combined stress state (sigma_x, tau_xy at a point)
5. simple elastic von Mises yield interaction / margin
6. section mass per unit length
7. a representative sanity case tying it all together

Milestone 2 scope
------------------
Milestone 2 extends the verified rectangular mechanics to built-up
frame/stringer sections assembled from rectangular components (I, Z, hat):

1. a generic rectangular component primitive and built-up section geometry
   (centroid, area, parallel-axis I_z, asymmetric top/bottom section moduli)
2. I-section, Z-section, and hat-section factories
3. normal stress about the built-up (generally nonzero) centroid
4. general Q(y)/(I*b_local(y)) transverse shear, with Q and b_local computed
   geometrically from the components -- not a hardcoded per-shape formula
5. elastic von Mises strength screening at a deterministic set of critical
   points (extreme fibers, neutral axis, and just inside every internal
   component boundary, to capture flange/web-style shear jumps)
6. mass per unit length (reusing the Milestone 1 mass equations unchanged)
7. an equal-area section-efficiency comparison

The resulting stress model is still an elementary beam-section treatment;
local plate buckling, crippling, torsion, shear-center effects, and skin
interaction remain deferred to a later milestone.

Milestone 3 scope
------------------
Milestone 3 adds classical elastic local-plate-buckling screens to the
verified built-up beam sections. These checks identify the onset of ideal
plate instability; they do not model postbuckling, crippling, effective
width, or certification knockdowns.

1. a rectangular plate-element primitive with an explicit "internal" or
   "outstanding" boundary condition
2. classical illustrative elastic compression- and shear-buckling
   coefficients and critical stresses
3. compression, shear, and an illustrative preliminary interaction margin,
   kept strictly separate from (never blended with) the elastic von Mises
   yield margin
4. explicit I/Z/hat plate-element mappings (web, flange outstands, crown)
5. local stress demand sampled from the existing verified built-up beam
   stress solution
6. a section-level local-buckling assessment with a governing plate/mode

Milestone 4 scope
------------------
Milestone 4 adds ideal elastic global member buckling and first-order
beam-column moment amplification. Local plate buckling, global Euler
instability, and material yield remain separate checks; no nonlinear
collapse or certification knockdowns are implied.

1. an explicit member geometry (length, effective-length factor K -- never
   buried inside a section or material object)
2. radius of gyration and slenderness ratio (reusing existing section
   area/I_z, never duplicating the section-property equations)
3. the classical ideal elastic Euler critical load/stress and its margin
4. a first-order elastic beam-column moment-amplification factor, and a
   beam-column amplified-yield screen that reuses the existing
   (unmodified) built-up stress/yield machinery with only the bending
   moment replaced
5. a combined axial-compression + bending global-stability assessment with
   a computed governing mode (never blending Euler and yield margins)
6. a side-by-side yield/local-buckling/global-Euler/amplified-yield summary

This is still an ideal elastic first-order stability screen: a straight,
prismatic, initially-perfect member, with an explicit effective-length
factor as a modeling assumption -- not inelastic column behavior, not
lateral-torsional or flexural-torsional buckling, and not a certification
allowable.

Milestone 5 scope
------------------
Milestone 5 adds an explicitly illustrative empirical crippling screen.
Unlike Milestones 3-4's ideal elastic buckling equations (derived from
first-principles eigenvalue theory), crippling correlations are empirical,
configuration-dependent curve fits to test data -- they are labeled
**illustrative preliminary crippling screen** throughout, never presented
as a sourced handbook (e.g. MMPDS) or certification value.

1. an explicit, visible crippling correlation (alpha, exponent -- never
   hardcoded inside the formula) and a yield cap on the raw prediction
2. a conservative, load-independent section-level b/t geometry driver
   reused directly from the Milestone 3 plate-element mappings
3. an axial-average crippling margin (P_crippling/P_comp - 1) and a
   peak-compression margin (reusing the existing built-up normal-stress
   extremes -- no new stress theory), kept separately visible
4. a section-level crippling assessment with a computed governing mode
5. a `StructuralStatus` integrating yield, local buckling, Euler,
   amplified yield, and crippling side by side -- their margins are never
   mathematically blended; the reported "governing margin" is only the
   minimum of the independently computed preliminary margins

Milestone 6 scope
------------------
Milestone 6 turns the verified single-load structural mechanics into a
constrained multi-load-case sizing study. This is a **preliminary sizing
study, not a general-purpose optimizer**: the design space is a small,
explicit, bounded uniform-thickness search per fixed-geometry section
family, using deterministic bisection over the verified mechanics -- no
scipy, gradient, or genetic optimization.

1. explicit named load cases (`FrameStringerLoadCase`, with a visible,
   never-hidden `load_factor`)
2. uniform-thickness scaling of the I/Z/hat factories, holding outer
   geometry fixed at the Milestone 2 proportions (never duplicating the
   section-property equations)
3. a per-load-case assessment reusing all five existing independent
   checks (yield, local buckling, Euler, amplified yield, crippling)
   unchanged, and a per-section multi-load-case assessment built on top
4. bounded bisection sizing with an explicit illustrative minimum gauge,
   explicit search bounds, and a documented, never-silently-expanded
   search
5. family comparison and a lowest-feasible-mass recommendation -- no
   invented weighted score

This is a beam-section model, NOT a shell/frame finite-element model. It uses
elementary (Euler-Bernoulli) beam theory only.

Coordinate convention (local member axes)
------------------------------------------
- x : member longitudinal axis
- y : section vertical coordinate (through-thickness for the rectangle),
      spanning -h/2 <= y <= +h/2, with y = 0 at the centroid
- z : section lateral coordinate (out of the bending plane for this model)

Load convention
----------------
- N   : axial force along x (positive = tension)
- V_y : transverse shear force in y
- M_z : bending moment about z

Stress convention
------------------
- positive sigma_x = tension, negative sigma_x = compression
- tau_xy is signed internally (follows the sign of V_y); the strength screen
  uses |tau_xy|

Units (SI, used internally throughout)
----------------------------------------
- length            : m
- area              : m^2
- second moment     : m^4
- force             : N
- moment            : N*m
- stress / modulus  : Pa
- density           : kg/m^3
- linear mass       : kg/m
"""

__all__ = [
    "material",
    "geometry",
    "section_properties",
    "loads",
    "stress",
    "strength",
    "mass",
    "built_up_geometry",
    "sections",
    "built_up_stress",
    "built_up_strength",
    "plate_buckling",
    "local_buckling",
    "column_buckling",
    "beam_column",
    "crippling",
    "structural_status",
    "load_cases",
    "sizing",
    "design_study",
]
