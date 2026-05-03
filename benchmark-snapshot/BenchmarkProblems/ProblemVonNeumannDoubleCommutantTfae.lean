import Mathlib.Analysis.VonNeumannAlgebra.Basic
import Mathlib.Analysis.InnerProductSpace.WeakOperatorTopology
import Mathlib.Topology.Algebra.Module.Spaces.PointwiseConvergenceCLM

namespace ProblemVonNeumannDoubleCommutantTfae

-- ANCHOR: vonNeumann_doubleCommutant_tfae__vonNeumann_doubleCommutant_tfae
theorem vonNeumann_doubleCommutant_tfae {H : Type*} [NormedAddCommGroup H] [InnerProductSpace ℂ H] [CompleteSpace H]
    (S : StarSubalgebra ℂ (H →L[ℂ] H)) :
    List.TFAE
      [ Set.centralizer (Set.centralizer (S : Set (H →L[ℂ] H))) = S
      , IsClosed
          (ContinuousLinearMap.toWOT (RingHom.id ℂ) H H '' (S : Set (H →L[ℂ] H)))
      , IsClosed
          (ContinuousLinearMap.toPointwiseConvergenceCLM ℂ (RingHom.id ℂ) H H ''
            (S : Set (H →L[ℂ] H))) ] := by
  sorry
-- ANCHOR_END: vonNeumann_doubleCommutant_tfae__vonNeumann_doubleCommutant_tfae

end ProblemVonNeumannDoubleCommutantTfae
