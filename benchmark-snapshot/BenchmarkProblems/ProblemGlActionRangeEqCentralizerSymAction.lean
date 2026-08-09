import Mathlib.LinearAlgebra.TensorPower.Basic
import Mathlib.LinearAlgebra.PiTensorProduct.Basic
import Mathlib.Algebra.Algebra.Subalgebra.Centralizer
import Mathlib.LinearAlgebra.FiniteDimensional.Defs

namespace ProblemGlActionRangeEqCentralizerSymAction

namespace LeanEval
namespace RepresentationTheory

open scoped TensorProduct

/-!
Schur–Weyl duality on `V^⊗k`.

Two commuting actions on `V^⊗k`:

* `symAction`: the symmetric group `S_k` acts by permuting tensor factors.
* `glAction`: the general linear group `GL(V)` acts diagonally as `g · (v₁ ⊗ ⋯ ⊗ v_k) =
  (g v₁) ⊗ ⋯ ⊗ (g v_k)`.

Schur–Weyl duality says their images in `End(V^⊗k)` generate mutual centralizers. We state
the two directions as separate `eval_problem`s.
-/

/-- The symmetric group `S_k` acts on `V^⊗k` by permuting the tensor factors. -/
def symAction (R M : Type*) [CommSemiring R] [AddCommMonoid M] [Module R M] (k : ℕ) :
    Equiv.Perm (Fin k) →* Module.End R (⨂[R]^k M) where
  toFun σ := (PiTensorProduct.reindex R (fun _ : Fin k => M) σ).toLinearMap
  map_one' := by
    ext x
    simp only [LinearEquiv.coe_coe, LinearMap.coe_compMultilinearMap, Function.comp_apply,
      PiTensorProduct.reindex_tprod, Module.End.one_apply]
    rfl
  map_mul' σ τ := by
    ext x
    simp only [Module.End.mul_apply, LinearEquiv.coe_coe, LinearMap.coe_compMultilinearMap,
      Function.comp_apply, PiTensorProduct.reindex_tprod]
    rfl

/-- The general linear group `GL(V)` acts diagonally on `V^⊗k`:
`g · (v₁ ⊗ ⋯ ⊗ v_k) = (g v₁) ⊗ ⋯ ⊗ (g v_k)`. -/
def glAction (R M : Type*) [CommSemiring R] [AddCommMonoid M] [Module R M] (k : ℕ) :
    (M →ₗ[R] M)ˣ →* Module.End R (⨂[R]^k M) where
  toFun g := PiTensorProduct.map (fun _ : Fin k => (g : M →ₗ[R] M))
  map_one' := by ext x; simp
  map_mul' g h := by ext x; simp





end RepresentationTheory
end LeanEval

open LeanEval.RepresentationTheory
open scoped TensorProduct

-- ANCHOR: glAction_range_eq_centralizer_symAction__glAction_range_eq_centralizer_symAction
theorem glAction_range_eq_centralizer_symAction {R : Type*} [Field R]
    {M : Type*} [AddCommGroup M] [Module R M] [FiniteDimensional R M]
    {k : ℕ} [Invertible (k.factorial : R)] :
    Algebra.adjoin R (Set.range (LeanEval.RepresentationTheory.glAction R M k)) =
      Subalgebra.centralizer R (Set.range (LeanEval.RepresentationTheory.symAction R M k)) := by
  sorry
-- ANCHOR_END: glAction_range_eq_centralizer_symAction__glAction_range_eq_centralizer_symAction

end ProblemGlActionRangeEqCentralizerSymAction
