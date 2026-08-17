import Mathlib.Probability.Distributions.SetBernoulli
import Mathlib.MeasureTheory.Integral.Bochner.Basic

/-!
# Notation for AnnalsChallenge

This file defines notation (mostly probability-theoretic) for the AnnalsChallenge project.

Ported verbatim from `AnnalsChallenge/Notation.lean` in
<https://github.com/ImperialCollegeLondon/AnnalsChallenge> (v1.0.0, `e32eb14`). It is a
trusted support module, not a benchmark problem: it contains no `sorry` and no
`@[eval_problem]` declarations. It is imported by `LeanEval.Analysis.RademacherEnfloType`
and `LeanEval.Analysis.SupremumOfSelectorProcesses`.
-/

set_option autoImplicit false

namespace ProbabilityTheory

open MeasureTheory Lean

/-- Suppose `P : Measure Ω`, `X : Ω → E`:

`𝔼[X; P] = ∫ ω, ↑(X ω) ∂P`

is notation for the integral (expectation) of a function `X` with respect to the measure `P`. -/
macro "𝔼[" X:term "; " P:term "]" : term => `(∫ ω, ↑($X ω) ∂$P)

/-- Suppose `μ : Measure E`

`𝔼[t; X ∼ μ] = ∫ X; t ∂μ`

where `X` is a variable and `t` is a term (possibly) depending on `X`. In probability theory
this represents the expectation of a function of `X` when `X` has law `μ`. For example we
could write `𝔼[X ^ 2; X ∼ μ]` for the second moment of `μ`.
-/
notation "𝔼[" t "; " X " ∼ " μ "]" => MeasureTheory.integral μ (fun X ↦ ↑t)

/-- Suppose `P : Measure Ω`, `X : Ω → ℝ≥0∞`:

`𝔼⁻[X; P] = ∫⁻ ω, ↑(X ω) ∂P`

is notation for the lintegral (expectation) of a function `X` with respect to the measure `P`. -/
macro "𝔼⁻[" X:term "; " P:term "]" : term => `(∫⁻ ω, ↑($X ω) ∂$P)

/-- Suppose `μ : Measure ℝ≥0∞`

`𝔼[t; X ∼ μ] = ∫ X; t ∂μ`

where `X` is a variable and `t` is a term (possibly) depending on `X`. In probability theory
this represents the expectation of a function of `X` when `X` has law `μ`. For example we
could write `𝔼⁻[X ^ 2; X ∼ μ]` for the second moment of `μ`.
-/
notation "𝔼⁻[" t "; " X " ∼ " μ "]" => MeasureTheory.lintegral μ (fun X ↦ ↑t)

end ProbabilityTheory
/-!
# Main Statements from On a conjecture of Talagrand on selector processes and a consequence
# on positive empirical processes

We formalise the statements of the main results from J. Park and H. T. Pham,
`On a conjecture of Talagrand on selector processes and a consequence on positive empirical
processes`, Annals of Math, 199 (3) 2024.
-/

set_option autoImplicit false

namespace SupremumOfSelectorProcesses

open MeasureTheory ProbabilityTheory Measure unitInterval Finset

open scoped NNReal ENNReal

/-- Definition of a binomial random subset of `X` with parameter `p`. -/
noncomputable def binomialSetDistribution (X : Type*) (p : I) : Measure (Set X) :=
  setBernoulli Set.univ p

open Classical in
/-- Definition of a collection of sets being `p-small`. -/
def IsSmall {X : Type*} [Fintype X] (p : I) (𝓕 : Set (Set X)) : Prop :=
  ∃ 𝓖 : Set (Set X), 𝓕 ⊆ ⋃ s ∈ 𝓖, {t | s ⊆ t} ∧ (∑ s ∈ 𝓖, (p : ℝ) ^ s.ncard ≤ 2⁻¹)







/-- Given a sequence of `𝕋`-valued random variables `Y_1, …, Y_N` and a function `f : 𝕋 → ℝ≥0`,
define the random variable

`Z N Y f := N⁻¹ ∑ i ∈ {1,…,N}, f(Yᵢ)`

When the sequence `Y_1, …, Y_N` is i.i.d, we call `Z N Y f` an empirical process.
-/
noncomputable def Z {Ω 𝕋 : Type*} (N : ℕ) (Y : Fin N → Ω → 𝕋) (f : 𝕋 → ℝ≥0) (ω : Ω) : ℝ≥0 :=
  (N : ℝ≥0)⁻¹ * ∑ i : Fin N, f (Y i ω)







end SupremumOfSelectorProcesses

/-
Copyright (c) 2025 David Ledvinka. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: David Ledvinka
-/

/-!
# Main Statements from On a conjecture of Talagrand on selector processes and a consequence
# on positive empirical processes

We formalise the statements of the main results from J. Park and H. T. Pham,
`On a conjecture of Talagrand on selector processes and a consequence on positive empirical
processes`, Annals of Math, 199 (3) 2024.
-/

set_option autoImplicit false

namespace SupremumOfSelectorProcesses

open MeasureTheory ProbabilityTheory Measure unitInterval Finset

open scoped NNReal ENNReal





-- ANCHOR: annals_supremum_of_selector_processes__L₂
/-- The constant `L` of Theorem 1.2. -/
noncomputable def L₂ : ℝ≥0 := sorry
-- ANCHOR_END: annals_supremum_of_selector_processes__L₂

-- ANCHOR: annals_supremum_of_selector_processes__L₂_pos
/-- The constant of Theorem 1.2 is positive. -/
theorem L₂_pos : L₂ > 0 := sorry
-- ANCHOR_END: annals_supremum_of_selector_processes__L₂_pos

open Classical in
-- ANCHOR: annals_supremum_of_selector_processes__theorem_1_2
/--
Statement of Theorem 1.2:

There exists `L > 0` such that for any `0 < p < 1`, finite type `X`, and set `Λ` of functions from
`X` to `ℝ≥0` such that `0 < 𝔼[sup_{f ∈ Λ} ∑ i ∈ Xp, f i] < ∞`, the collection of sets

`{s ⊆ X | sup_{f ∈ Λ} ∑ i ∈ s, f i ≥ L * 𝔼[sup_{f ∈ Λ} ∑ i ∈ Xp, f i]}`

is `p-small`, where `Xp` is a binomial random subset of `X` with parameter `p`.

Note: The assumption `0 < 𝔼[sup_{f ∈ Λ} ∑ i ∈ Xp, f i] < ∞` is not explicitly stated in the theorem
but used in the last step of the proof where `𝔼 ≥ (L/L') * 𝔼` is a contradiction for `L > L'`.
-/
theorem theorem_1_2 (p : I) (hp₀ : 0 < p) (hp₁ : p < 1) (X : Type*) [Fintype X] (Λ : Set (X → ℝ≥0))
    (hE₀ : 0 < 𝔼⁻[⨆ f ∈ Λ, ∑ i ∈ Xp, (f i : ℝ≥0∞); Xp ∼ binomialSetDistribution X p])
    (hE : 𝔼⁻[⨆ f ∈ Λ, ∑ i ∈ Xp, (f i : ℝ≥0∞); Xp ∼ binomialSetDistribution X p] < ∞) :
    IsSmall p {s : Set X | ⨆ f ∈ Λ, ∑ i ∈ s, (f i : ℝ≥0∞) ≥
        L₂ * 𝔼⁻[⨆ f ∈ Λ, ∑ i ∈ Xp, (f i : ℝ≥0∞); Xp ∼ binomialSetDistribution X p]} := by
  sorry
-- ANCHOR_END: annals_supremum_of_selector_processes__theorem_1_2



-- ANCHOR: annals_supremum_of_selector_processes__L₃
/-- The constant `L` of Theorem 1.3. -/
noncomputable def L₃ : ℝ≥0 := sorry
-- ANCHOR_END: annals_supremum_of_selector_processes__L₃

-- ANCHOR: annals_supremum_of_selector_processes__L₃_pos
/-- The constant of Theorem 1.3 is positive. -/
theorem L₃_pos : L₃ > 0 := sorry
-- ANCHOR_END: annals_supremum_of_selector_processes__L₃_pos

open Classical in
-- ANCHOR: annals_supremum_of_selector_processes__theorem_1_3
/--
Statement of Theorem 1.3:

There exists `L > 0` such that for any `N > 0`, i.i.d random variables `Y_1, …, Y_N` distributed
according to a Borel probability measure `ν` on a Polish space `𝕋`, if `𝓕` is a finite set of
non-negative functions in `L∞(𝕋)` and `0 < 𝔼[sup_{f ∈ 𝓕} Z Y f] < ∞` then there exists a finite
collection `𝓒` of pairs `(g, t)` where `g : 𝕋 → ℝ≥0`, `t > 0` such that

`{sup_{f ∈ 𝓕} Z N Y f ≥ L * 𝔼[sup_{f ∈ 𝓕} Z N Y f] } ⊆ ⋃ (g,t) ∈ 𝓒, {t ≤ Z N Y g}`

and

`∑ (g,t) ∈ 𝓒, P(t ≤ Z N Y g) ≤ 2⁻¹`.

Note: The requirement that the collection `𝓒` be finite is not explicitly stated in the paper.
However, `𝓒` must at least be assumed to be countable in order for the sum to make sense,
and the collections `𝓒` produced by the proof are indeed finite.

-/
theorem theorem_1_3 (N : ℕ) (N_pos : N > 0) (𝕋 : Type*) (t𝕋 : TopologicalSpace 𝕋)
    (p𝕋 : PolishSpace 𝕋)
    (m𝕋 : MeasurableSpace 𝕋) (b𝕋 : BorelSpace 𝕋) (ν : Measure 𝕋) (hν : IsProbabilityMeasure ν)
    (Ω : Type*) (mΩ : MeasurableSpace Ω) (P : Measure Ω) (Y : Fin N → Ω → 𝕋)
    (Y_indep : iIndepFun Y P) (Y_law_ν : ∀ i, HasLaw (Y i) ν P)
    (𝓕 : Set {f : 𝕋 → ℝ≥0 // Measurable f ∧ MemLp f ∞ ν}) (h𝓕 : Finite 𝓕)
    (hZ₀ : 0 < 𝔼⁻[⨆ f ∈ 𝓕, (Z N Y f ·); P]) (hZ : 𝔼⁻[⨆ f ∈ 𝓕, (Z N Y f ·); P] < ∞) :
    ∃ 𝓒 : Finset ({g : 𝕋 → ℝ≥0 // Measurable g} × {t : ℝ≥0 | t > 0}),
      {ω | ⨆ f ∈ 𝓕, Z N Y f ω ≥ L₃ * 𝔼⁻[⨆ f ∈ 𝓕, (Z N Y f ·); P]} ⊆ ⋃ c ∈ 𝓒, {ω | c.2 ≤ Z N Y c.1 ω}
      ∧ ∑ c : 𝓒, P {ω | c.val.2 ≤ Z N Y c.val.1 ω} ≤ 2⁻¹ := by
  sorry
-- ANCHOR_END: annals_supremum_of_selector_processes__theorem_1_3

end SupremumOfSelectorProcesses
