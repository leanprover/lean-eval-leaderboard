import Mathlib.Analysis.Fourier.AddCircle
import Mathlib.Analysis.Normed.Operator.Mul
import Mathlib.MeasureTheory.Measure.Complex
import Mathlib.MeasureTheory.VectorMeasure.Decomposition.RadonNikodym
import Mathlib.MeasureTheory.VectorMeasure.Integral

namespace ProblemRieszBrothersTheorem

open MeasureTheory

-- ANCHOR: riesz_brothers_theorem__riesz_brothers_theorem
theorem riesz_brothers_theorem (μ : ComplexMeasure UnitAddCircle)
    (hμ : ∀ n : ℕ, 1 ≤ n → ∫ᵛ z, fourier n z ∂[ContinuousLinearMap.mul ℝ ℂ; μ] = 0) :
    μ ≪ᵥ AddCircle.haarAddCircle.toENNRealVectorMeasure := by
  sorry
-- ANCHOR_END: riesz_brothers_theorem__riesz_brothers_theorem

end ProblemRieszBrothersTheorem
