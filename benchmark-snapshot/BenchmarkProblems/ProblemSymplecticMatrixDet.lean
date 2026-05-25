import Mathlib

namespace ProblemSymplecticMatrixDet

open Matrix

-- ANCHOR: symplectic_matrix_det__symplectic_matrix_det
theorem symplectic_matrix_det {l R : Type*} [DecidableEq l] [Fintype l] [CommRing R]
    {A : Matrix (l ⊕ l) (l ⊕ l) R} (_hA : A ∈ Matrix.symplecticGroup l R) :
    A.det = 1 := by
  sorry
-- ANCHOR_END: symplectic_matrix_det__symplectic_matrix_det

end ProblemSymplecticMatrixDet
