import Mathlib

namespace ProblemTuringRecursiveEquiv

open Computability Turing

-- ANCHOR: turing_recursive_equiv__turing_recursive_equiv
theorem turing_recursive_equiv (f : ℕ → ℕ) :
    Computable f ↔ Nonempty (TM2Computable encodeNat encodeNat f) := by
  sorry
-- ANCHOR_END: turing_recursive_equiv__turing_recursive_equiv

end ProblemTuringRecursiveEquiv
