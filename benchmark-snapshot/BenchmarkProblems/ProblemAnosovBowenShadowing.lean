import Mathlib

namespace ProblemAnosovBowenShadowing

namespace LeanEval
namespace Dynamics
namespace HyperbolicShadowingProblem

/-!
# Anosov–Bowen shadowing lemma

Every compact hyperbolic invariant set of a `C¹` diffeomorphism admits
an open neighbourhood on which every approximate orbit is `δ`-close to
a true `T`-orbit. Anosov 1967; Bowen 1975. §67 in Knill's *Some
Fundamental Theorems in Mathematics*.

The statement here is the Euclidean special case on
`E d := EuclideanSpace ℝ (Fin d)` — a faithful finite-dimensional local
model that captures the hyperbolic-dynamics content while avoiding the
smooth-manifold and tangent-bundle infrastructure mathlib does not yet
package. The hyperbolic-set predicate is bundled as a `HyperbolicStructure`:
a pointwise stable/unstable splitting with the uniform exponential
contraction/expansion estimates of Anosov's original definition. The
textbook definition additionally asks for the splitting to be continuous
in `x`; we encode only the pointwise content with uniform constants,
which is the minimal data the shadowing proof depends on.
-/

open scoped Topology

/-- The Euclidean model space `ℝᵈ`. -/
abbrev E (d : ℕ) := EuclideanSpace ℝ (Fin d)

variable {d : ℕ}

/-- A **hyperbolic structure** for a homeomorphism `T : ℝᵈ → ℝᵈ` on a
`T`-invariant set `K`: at each point `x ∈ K` the ambient space `ℝᵈ`
splits as a direct sum of a stable subspace `Eˢ x` and an unstable
subspace `Eᵘ x`; the derivative `dT_x` preserves the splitting; and
forward (resp. backward) iteration contracts `Eˢ` (resp. `Eᵘ`)
exponentially at a uniform rate `λ ∈ (0, 1)` with a uniform constant
`C > 0`. -/
structure HyperbolicStructure (T : E d ≃ₜ E d) (K : Set (E d)) where
  contDiff_fwd : ContDiff ℝ 1 (T : E d → E d)
  contDiff_bwd : ContDiff ℝ 1 (T.symm : E d → E d)
  invariant : (T : E d → E d) '' K = K
  stable : E d → Submodule ℝ (E d)
  unstable : E d → Submodule ℝ (E d)
  isCompl_stable_unstable : ∀ x ∈ K, IsCompl (stable x) (unstable x)
  stable_invariant : ∀ x ∈ K,
    (stable x).map (fderiv ℝ (T : E d → E d) x : E d →ₗ[ℝ] E d) = stable (T x)
  unstable_invariant : ∀ x ∈ K,
    (unstable x).map (fderiv ℝ (T : E d → E d) x : E d →ₗ[ℝ] E d) = unstable (T x)
  rate : ℝ
  rate_pos : 0 < rate
  rate_lt_one : rate < 1
  const : ℝ
  const_pos : 0 < const
  contract_stable : ∀ x ∈ K, ∀ v : E d, v ∈ stable x → ∀ n : ℕ,
    ‖fderiv ℝ ((T : E d → E d)^[n]) x v‖ ≤ const * rate ^ n * ‖v‖
  contract_unstable : ∀ x ∈ K, ∀ v : E d, v ∈ unstable x → ∀ n : ℕ,
    ‖fderiv ℝ ((T.symm : E d → E d)^[n]) x v‖ ≤ const * rate ^ n * ‖v‖

/-- `K ⊆ ℝᵈ` is a **hyperbolic invariant set** for `T` if it admits a
hyperbolic splitting. -/
def IsHyperbolic (T : E d ≃ₜ E d) (K : Set (E d)) : Prop :=
  Nonempty (HyperbolicStructure T K)

/-- `(xₙ)_{n : ℕ}` is an **ε-pseudo orbit** of `T : ℝᵈ → ℝᵈ`:
`‖x (n+1) − T (xₙ)‖ < ε` for every `n`. -/
def IsPseudoOrbit (T : E d → E d) (ε : ℝ) (x : ℕ → E d) : Prop :=
  ∀ n : ℕ, ‖x (n + 1) - T (x n)‖ < ε

/-- `K ⊆ ℝᵈ` has the **shadowing property** for `T`: some neighbourhood
`U ⊇ K` (open in `ℝᵈ`) admits, for every accuracy `δ > 0`, a tolerance
`ε > 0` such that every `ε`-pseudo orbit inside `U` stays within `δ` of
a real forward `T`-orbit. -/
def HasShadowing (T : E d → E d) (K : Set (E d)) : Prop :=
  ∃ U : Set (E d), IsOpen U ∧ K ⊆ U ∧
    ∀ δ > 0, ∃ ε > 0, ∀ x : ℕ → E d,
      (∀ n, x n ∈ U) → IsPseudoOrbit T ε x →
      ∃ y : E d, ∀ n : ℕ, ‖x n - T^[n] y‖ < δ



end HyperbolicShadowingProblem
end Dynamics
end LeanEval

open LeanEval.Dynamics.HyperbolicShadowingProblem
open scoped Topology

variable {d : ℕ}

-- ANCHOR: anosov_bowen_shadowing__hyperbolic_has_shadowing
theorem hyperbolic_has_shadowing (T : LeanEval.Dynamics.HyperbolicShadowingProblem.E d ≃ₜ LeanEval.Dynamics.HyperbolicShadowingProblem.E d) (K : Set (LeanEval.Dynamics.HyperbolicShadowingProblem.E d))
    (_hKc : IsCompact K) (_hK : LeanEval.Dynamics.HyperbolicShadowingProblem.IsHyperbolic T K) :
    LeanEval.Dynamics.HyperbolicShadowingProblem.HasShadowing (T : LeanEval.Dynamics.HyperbolicShadowingProblem.E d → LeanEval.Dynamics.HyperbolicShadowingProblem.E d) K := by
  sorry
-- ANCHOR_END: anosov_bowen_shadowing__hyperbolic_has_shadowing

end ProblemAnosovBowenShadowing
