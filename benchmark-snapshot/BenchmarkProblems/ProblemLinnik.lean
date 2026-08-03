import Mathlib

namespace ProblemLinnik

namespace LeanEval.NumberTheory.Linnik

/-!
# Linnik's theorem (L = 5.5)

The least prime in the arithmetic progression `a mod d` (for `a` coprime to `d`)
is bounded polynomially in `d`, with the explicit Linnik constant `L = 5.5`
(due to Heath-Brown, 1992).

See D. R. Heath-Brown, *Zero-free regions for Dirichlet L-functions, and the
least prime in an arithmetic progression*, Proc. London Math. Soc. (3) 64
(1992), no. 2, 265–338. <https://doi.org/10.1112/plms/s3-64.2.265>
-/

/-- The least prime in the progression `a, a + d, a + 2d, …`
(or `0` if no such prime exists). -/
noncomputable def p (a d : ℕ) : ℕ := sInf ({a + k * d | k : ℕ} ∩ {p | p.Prime})



end LeanEval.NumberTheory.Linnik

open LeanEval.NumberTheory.Linnik

-- ANCHOR: linnik__linnik
theorem linnik : ∃ c : ℝ, ∀ ⦃a d : ℕ⦄,
    0 < a → a < d → a.Coprime d → p a d ≤ c * d ^ (5.5 : ℝ) := by
  sorry
-- ANCHOR_END: linnik__linnik

end ProblemLinnik
