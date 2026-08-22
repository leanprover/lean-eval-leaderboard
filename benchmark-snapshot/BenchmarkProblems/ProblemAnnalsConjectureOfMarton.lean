import Mathlib.Algebra.Field.ZMod
import Mathlib.Combinatorics.Additive.CovBySMul

namespace ProblemAnnalsConjectureOfMarton

/-!
# Main Statement from On a conjecture of Marton

We formalise the statement of the main result from W. T. Gowers, B. Green, F. Manners, and T. Tao,
`On a conjecture of Marton`, Annals of Math, 201 (2) 2025.
-/

set_option autoImplicit false

namespace ConjectureOfMarton

open Pointwise

variable (n : ℕ)

/-- `F n` is the finite vector space `(𝔽₂)ⁿ`. -/
abbrev F := Fin n → ZMod 2



end ConjectureOfMarton

open ConjectureOfMarton
open Pointwise

set_option autoImplicit false
variable (n : ℕ)

-- ANCHOR: annals_conjecture_of_marton__theorem_1_2
theorem theorem_1_2 (A : Set (ConjectureOfMarton.F n)) (K : ℝ) (h₀ : A.Nonempty) (h : (A + A).ncard ≤ K * A.ncard) :
    ∃ H : AddSubgroup (ConjectureOfMarton.F n), Nat.card H ≤ A.ncard ∧ CovByVAdd (ConjectureOfMarton.F n) (2 * K ^ 12) A H := by
  sorry
-- ANCHOR_END: annals_conjecture_of_marton__theorem_1_2

end ProblemAnnalsConjectureOfMarton
