import Mathlib.Analysis.CStarAlgebra.Classes
import Mathlib.LinearAlgebra.Dimension.Basic
import Mathlib.RingTheory.Ideal.Quotient.Defs
import Mathlib.RingTheory.MvPowerSeries.Derivative
import Mathlib.Topology.UnitInterval

namespace ProblemAnnalsSymplecticMonodromy

/-!
# Main Statement from Symplectic monodromy at radius zero and equimultiplicity of
# μ-constant families

We formalise the statement of the main result from J. Fernández de Bobadilla and T. Pełka,
`Symplectic monodromy at radius zero and equimultiplicity of μ-constant families`,
Annals of Math, 200 (1) 2024.
-/

set_option autoImplicit false

namespace SymplecticMonodromy

open MvPowerSeries

/-- The Milnor number of `f` is `dim_ℂ ℂ⟦z₁, ⋯, zₙ⟧ / ⟨∂f/∂z₁, ⋯, ∂f/∂zₙ⟩`. -/
noncomputable def milnorNumber {σ R : Type*} [CommRing R] (f : MvPowerSeries σ R) : ℕ∞ :=
  (Module.rank R (MvPowerSeries σ R ⧸ Ideal.span (Set.range (pderiv R · f)))).toENat



end SymplecticMonodromy

open SymplecticMonodromy
open MvPowerSeries

set_option autoImplicit false

-- ANCHOR: annals_symplectic_monodromy__theorem_1_1
theorem theorem_1_1 (n : ℕ) (f : unitInterval → MvPowerSeries (Fin n) ℂ)
    (cont : ∀ d, Continuous fun t ↦ coeff d (f t)) (h_const : ∀ t, constantCoeff (f t) = 0)
    (h : ∃ μ : ℕ, ∀ t, milnorNumber (f t) = μ) : ∀ t₁ t₂, (f t₁).order = (f t₂).order := by
  sorry
-- ANCHOR_END: annals_symplectic_monodromy__theorem_1_1

end ProblemAnnalsSymplecticMonodromy
