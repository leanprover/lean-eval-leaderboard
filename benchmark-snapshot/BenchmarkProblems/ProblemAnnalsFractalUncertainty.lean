import Mathlib.Analysis.Fourier.LpSpace

namespace ProblemAnnalsFractalUncertainty

/-!
# Main Statement from Fractal uncertainty in higher dimensions

We formalise the statement of the main result from A. Cohen,
`Fractal uncertainty in higher dimensions`, Annals of Math, 202 (1) 2025.
-/

set_option autoImplicit false

namespace FractalUncertainty

open MeasureTheory FourierTransform Metric

open scoped ENNReal

variable {d : ℕ}

local notation "ℝᵈ" => EuclideanSpace ℝ (Fin d)

/-- We say a set `X ⊂ ℝᵈ` is `ν`-porous on balls from scales `α₀` to `α₁` if, for every ball `B` of
diameter `α₀ < R < α₁`, there is some `x ∈ B` such that `closedBall x (ν * R) ∩ X = ∅`. -/
def PorousOnBalls (ν α₀ α₁ : ℝ) (X : Set ℝᵈ) : Prop :=
  ∀ y, ∀ R ∈ Set.Ioo α₀ α₁, ∃ x ∈ closedBall y (R / 2), closedBall x (ν * R) ∩ X = ∅

/-- We say a set `X` is `ν`-porous on lines from scales `α₀` to `α₁` if for all line segments `τ`
with length `α₀ < R < α₁`, there is some `x ∈ τ` such that `closedBall x (ν * R) ∩ X = ∅`. -/
def PorousOnLines (ν α₀ α₁ : ℝ) (X : Set ℝᵈ) : Prop :=
  ∀ (R : ℝ), R ∈ Set.Ioo α₀ α₁ → ∀ (y₁ y₂ : ℝᵈ), dist y₁ y₂ = R →
    ∃ x ∈ segment ℝ y₁ y₂, closedBall x (ν * R) ∩ X = ∅

/-- Given `a b : ℝ`, the cube `[a,b]ᵈ` in `ℝᵈ`. -/
abbrev cube (a b : ℝ) : Set ℝᵈ := EuclideanSpace.equiv (Fin d) ℝ ⁻¹' Set.univ.pi fun _ ↦ Set.Icc a b



end FractalUncertainty

open FractalUncertainty
open MeasureTheory FourierTransform Metric
open scoped ENNReal

set_option autoImplicit false
variable {d : ℕ}
local notation "ℝᵈ" => EuclideanSpace ℝ (Fin d)

-- ANCHOR: annals_fractal_uncertainty__theorem_1_1
theorem theorem_1_1 (ν : ℝ) (hν₀ : 0 < ν) :
    ∃ (β C : ℝ), β > 0 ∧ C > 0 ∧ ∀ (h : ℝ) (X Y : Set ℝᵈ)
      (hX : MeasurableSet X) (hY : MeasurableSet Y), h ∈ Set.Ioo 0 (1 / 100) →
        X ⊆ FractalUncertainty.cube (-1) 1 → FractalUncertainty.PorousOnBalls ν h 1 X → Y ⊆ FractalUncertainty.cube (-h⁻¹) h⁻¹ →
          FractalUncertainty.PorousOnLines ν 1 h⁻¹ Y → ∀ (f : Lp ℂ 2), (𝓕 f : Lp ℂ 2) =ᵐ[volume.restrict Yᶜ] 0 →
            (eLpNorm (X.indicator f) 2).toReal ≤ C * h ^ β * ‖f‖ := by
  sorry
-- ANCHOR_END: annals_fractal_uncertainty__theorem_1_1

end ProblemAnnalsFractalUncertainty
