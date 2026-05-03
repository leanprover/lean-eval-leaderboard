import Mathlib.Algebra.Polynomial.Basic
import Mathlib.Analysis.Complex.Circle

namespace ProblemExistsComplementaryPolynomialOnUnitCircle

open Polynomial

-- ANCHOR: exists_complementary_polynomial_on_unit_circle__exists_complementary_polynomial_on_unit_circle
theorem exists_complementary_polynomial_on_unit_circle (P : ℂ[X])
    (hP : ∀ z : Circle, ‖P.eval (z : ℂ)‖ ≤ 1) :
    ∃ Q : ℂ[X],
      Q.natDegree ≤ P.natDegree ∧
        ∀ z : Circle, ‖P.eval (z : ℂ)‖ ^ 2 + ‖Q.eval (z : ℂ)‖ ^ 2 = 1 := by
  sorry
-- ANCHOR_END: exists_complementary_polynomial_on_unit_circle__exists_complementary_polynomial_on_unit_circle

end ProblemExistsComplementaryPolynomialOnUnitCircle
