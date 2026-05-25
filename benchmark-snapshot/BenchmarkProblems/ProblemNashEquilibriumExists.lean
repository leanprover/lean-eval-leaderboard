import Mathlib

namespace ProblemNashEquilibriumExists

namespace LeanEval
namespace GameTheory

/-!
# Nash equilibrium existence theorem

§33 of Oliver Knill's *Some Fundamental Theorems in Mathematics*. Every
finite `n`-player game in mixed strategies admits at least one Nash
equilibrium.

Nash gave two proofs: the 1950 one uses Brouwer's fixed-point theorem; the
1951 one uses Kakutani's set-valued generalization.

mathlib has `stdSimplex ℝ S` (the natural model of a mixed strategy) and the
standard finite-sum/product machinery, but **no game theory at all** —
there is no `Mathlib/GameTheory/` module, and `grep -ri nash`,
`mixed.strategy`, `best.response` returns nothing relevant. No formalization
of Nash equilibrium existence was found in any major proof assistant.
-/

open Set Function

/-- A **mixed strategy** for a player with finite pure-strategy set `S` is a
probability distribution on `S`: a non-negative function summing to `1`. -/
abbrev MixedStrategy (S : Type*) [Fintype S] : Set (S → ℝ) := stdSimplex ℝ S

/-- A **strategy profile** is a tuple assigning each of the `n` players a
pure strategy from their own set. -/
abbrev StrategyProfile (n : ℕ) (S : Fin n → Type*) : Type _ := ∀ i, S i

/-- The **expected payoff** to a player with payoff function `u` when each
player `j` plays the mixed strategy `σ j`. Sum over all pure-strategy
profiles, weighted by the product of marginal probabilities. -/
noncomputable def expectedPayoff {n : ℕ} {S : Fin n → Type*}
    [∀ i, Fintype (S i)]
    (u : StrategyProfile n S → ℝ) (σ : ∀ i, S i → ℝ) : ℝ :=
  ∑ s : StrategyProfile n S, (∏ i, σ i (s i)) * u s

/-- A profile of mixed strategies `σ` is a **Nash equilibrium** for the
payoff functions `u₀, …, uₙ₋₁` if (i) each `σ i` is a probability
distribution on `S i`, and (ii) no player `i` can strictly improve their
expected payoff by switching to a different mixed strategy `τ`, holding the
other players' strategies fixed. -/
def IsNashEquilibrium {n : ℕ} {S : Fin n → Type*} [∀ i, Fintype (S i)]
    (u : Fin n → StrategyProfile n S → ℝ) (σ : ∀ i, S i → ℝ) : Prop :=
  (∀ i, σ i ∈ MixedStrategy (S i)) ∧
    ∀ (i : Fin n) (τ : S i → ℝ), τ ∈ MixedStrategy (S i) →
      expectedPayoff (u i) (Function.update σ i τ) ≤
        expectedPayoff (u i) σ



end GameTheory
end LeanEval

open LeanEval.GameTheory
open Set Function

-- ANCHOR: nash_equilibrium_exists__nash_equilibrium_exists
theorem nash_equilibrium_exists {n : ℕ} {S : Fin n → Type*}
    [∀ i, Fintype (S i)] [∀ i, Nonempty (S i)]
    (u : Fin n → LeanEval.GameTheory.StrategyProfile n S → ℝ) :
    ∃ σ : ∀ i, S i → ℝ, LeanEval.GameTheory.IsNashEquilibrium u σ := by
  sorry
-- ANCHOR_END: nash_equilibrium_exists__nash_equilibrium_exists

end ProblemNashEquilibriumExists
