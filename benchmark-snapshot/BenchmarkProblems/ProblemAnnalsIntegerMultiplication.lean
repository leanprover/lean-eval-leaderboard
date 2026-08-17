import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Computability.TuringMachine.Computable

namespace ProblemAnnalsIntegerMultiplication

/-!
# Main Statement from Integer multiplication in time O(n log n)

We formalise the statement of the main result from D. Harvey and J. van der Hoeven,
`Integer multiplication in time O(n log n)`, Annals of Math, 193 (2) 2021.

## Implementation Details

The paper works in the "multitape Turing model, in which the time complexity of
an algorithm refers to the number of steps performed by a deterministic Turing
machine with a fixed, finite number of linear tapes". In this formalisation, we
use mathlib's multi-stack machines (TM2), which are equivalent to multitape
machines by an O(1) reduction (use two stacks to simulate one tape).
-/

set_option autoImplicit false

namespace IntegerMultiplication

open Computability Turing Real

/-- Given two encodings `ea` and `eb` of types `α` and `β` in alphabets `αΓ` and `βΓ`, the encoding
of `α × β` in the alphabet `Option αΓ × Option βΓ`. If one encoding is shorter than
the other, the resulting list will be padded with `none` for the shorter list. -/
def encodeProd {α β αΓ βΓ : Type*} (ea : α → List αΓ) (eb : β → List βΓ) (x : α × β) :
    List (Option αΓ × Option βΓ) :=
  List.zipWithAll Prod.mk (ea x.1) (eb x.2)



end IntegerMultiplication

open IntegerMultiplication
open Computability Turing Real

-- ANCHOR: annals_integer_multiplication__theorem_1_1
theorem theorem_1_1 :
    ∃ T : TM2ComputableInTime (IntegerMultiplication.encodeProd encodeNat encodeNat) encodeNat (fun (x, y) ↦ x * y),
      (fun n ↦ (T.time n : ℝ)) =O[Filter.atTop] (fun n ↦ n * log n) := by
  sorry
-- ANCHOR_END: annals_integer_multiplication__theorem_1_1

end ProblemAnnalsIntegerMultiplication
