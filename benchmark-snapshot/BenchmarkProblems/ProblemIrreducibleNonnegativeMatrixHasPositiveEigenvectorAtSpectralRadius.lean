import Mathlib.Analysis.Normed.Algebra.Spectrum
import Mathlib.LinearAlgebra.Eigenspace.Basic
import Mathlib.LinearAlgebra.Matrix.Irreducible.Defs

namespace ProblemIrreducibleNonnegativeMatrixHasPositiveEigenvectorAtSpectralRadius

open scoped NNReal

-- ANCHOR: irreducible_nonnegative_matrix_has_positive_eigenvector_at_spectralRadius__irreducible_nonnegative_matrix_has_positive_eigenvector_at_spectralRadius
theorem irreducible_nonnegative_matrix_has_positive_eigenvector_at_spectralRadius {n : Type*} [Fintype n] [DecidableEq n]
    (A : Matrix n n ℝ)
    (hA : A.IsIrreducible) :
    ∃ v : n → ℝ,
      Module.End.HasEigenvector (Matrix.toLin' A) (spectralRadius ℝ A).toReal v ∧
      (∀ i, 0 < v i) := by
  sorry
-- ANCHOR_END: irreducible_nonnegative_matrix_has_positive_eigenvector_at_spectralRadius__irreducible_nonnegative_matrix_has_positive_eigenvector_at_spectralRadius

end ProblemIrreducibleNonnegativeMatrixHasPositiveEigenvectorAtSpectralRadius
