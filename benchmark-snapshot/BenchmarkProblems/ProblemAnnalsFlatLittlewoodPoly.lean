import Mathlib.Algebra.Polynomial.Degree.Defs
import Mathlib.Algebra.Polynomial.Eval.Defs
import Mathlib.Analysis.Complex.Norm

namespace ProblemAnnalsFlatLittlewoodPoly

/-!
# Main Statement from Flat Littlewood polynomials exist

We formalise the statement of the main result from P. Balister, B. Bollobás, R. Morris,
J. Sahasrabudhe, and M. Tiba, `Flat Littlewood polynomials exist`, Annals of Math, 192 (3) 2020.
-/

set_option autoImplicit false

namespace FlatLittlewoodPoly

open scoped Polynomial

/-- A polynomial is a Littlewood polynomial if all its coefficients are either `-1` or `1`. -/
def IsLittlewoodPolynomial {F : Type*} [Ring F] (P : F[X]) : Prop :=
  ∀ i ≤ P.natDegree, P.coeff i = 1 ∨ P.coeff i = -1



end FlatLittlewoodPoly

open FlatLittlewoodPoly
open scoped Polynomial

set_option autoImplicit false

-- ANCHOR: annals_flat_littlewood_poly__theorem_1_1
theorem theorem_1_1 :
    ∃ Δ δ : ℝ, Δ > δ ∧ δ > 0 ∧ ∀ n ≥ 2,
      ∃ P : ℂ[X], FlatLittlewoodPoly.IsLittlewoodPolynomial P ∧ P.natDegree = n ∧
      ∀ z : ℂ, ‖z‖ = 1 → δ * √n ≤ ‖P.eval z‖ ∧
      ‖P.eval z‖ ≤ Δ * √n := by
  sorry
-- ANCHOR_END: annals_flat_littlewood_poly__theorem_1_1

end ProblemAnnalsFlatLittlewoodPoly
