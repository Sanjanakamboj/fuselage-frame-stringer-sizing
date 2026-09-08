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
]
