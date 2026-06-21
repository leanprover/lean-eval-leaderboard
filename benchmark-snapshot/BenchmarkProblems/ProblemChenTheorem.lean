import Mathlib

namespace ProblemChenTheorem

namespace LeanEval.NumberTheory.ChenTheorem

/-!
# Chen's theorem

§224 of Oliver Knill's *Some Fundamental Theorems in Mathematics*. Chen's
theorem states that there are infinitely many primes `p` such that `p + 2` is
either prime or a product of two primes (a "prime or semiprime").

mathlib has `Nat.Prime` and prime factorization, but no Brun-style sieve and
hence no proof of Chen's theorem.
-/

open Filter Finset MeasureTheory
open scoped BigOperators Topology

/-- `n` has at most two prime factors, counted with multiplicity.  This is the
standard "prime or semiprime" condition in Chen's theorem. -/
def HasAtMostTwoPrimeFactors (n : ℕ) : Prop :=
  (∃ a : ℕ, a.Prime ∧ n = a) ∨
    ∃ a b : ℕ, a.Prime ∧ b.Prime ∧ n = a * b



end LeanEval.NumberTheory.ChenTheorem

open LeanEval.NumberTheory.ChenTheorem
open Filter Finset MeasureTheory
open scoped BigOperators Topology

-- ANCHOR: chen_theorem__chen_theorem
theorem chen_theorem :
    {p : ℕ | p.Prime ∧ LeanEval.NumberTheory.ChenTheorem.HasAtMostTwoPrimeFactors (p + 2)}.Infinite := by
  sorry
-- ANCHOR_END: chen_theorem__chen_theorem

end ProblemChenTheorem
