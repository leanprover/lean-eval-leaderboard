import Mathlib

namespace ProblemPascal

namespace LeanEval.Geometry.PascalPappus

/-!
# Pascal's theorem and Pappus's hexagon theorem

`pascal` (Pascal 1639): six points on a non-singular conic give three collinear
intersection points. `pappus` (Pappus, c. 320 AD): the degenerate-conic case
with the six points on two lines. Trusted helpers (`SamePoint`, `OnConic`,
`meet`, `Collinear3`) are non-holes. Mathlib has the cross product `⨯₃` and
projective vocabulary but neither theorem.
Category-(b) candidates from §146 of the Knill survey.
-/

open Matrix

/-- Two homogeneous coordinate vectors represent the same projective point. -/
def SamePoint (v w : Fin 3 → ℝ) : Prop := ∃ c : ℝ, c ≠ 0 ∧ w = c • v

/-- `[v]` lies on the conic `xᵀ M x = 0`. -/
def OnConic (M : Matrix (Fin 3) (Fin 3) ℝ) (v : Fin 3 → ℝ) : Prop :=
  v ⬝ᵥ (M *ᵥ v) = 0

/-- Intersection (meet) of line `[a][b]` and line `[c][d]`. -/
def meet (a b c d : Fin 3 → ℝ) : Fin 3 → ℝ := (a ⨯₃ b) ⨯₃ (c ⨯₃ d)

/-- Three projective points are collinear (vanishing triple product). -/
def Collinear3 (p q r : Fin 3 → ℝ) : Prop := p ⬝ᵥ (q ⨯₃ r) = 0



end LeanEval.Geometry.PascalPappus

open LeanEval.Geometry.PascalPappus
open Matrix

-- ANCHOR: pascal__pascal
theorem pascal (M : Matrix (Fin 3) (Fin 3) ℝ) (hMsymm : M.IsSymm) (hMdet : M.det ≠ 0)
    (a₁ a₂ a₃ b₁ b₂ b₃ : Fin 3 → ℝ)
    (ha₁ : a₁ ≠ 0) (ha₂ : a₂ ≠ 0) (ha₃ : a₃ ≠ 0)
    (hb₁ : b₁ ≠ 0) (hb₂ : b₂ ≠ 0) (hb₃ : b₃ ≠ 0)
    (hdist : [a₁, a₂, a₃, b₁, b₂, b₃].Pairwise (fun v w => ¬ LeanEval.Geometry.PascalPappus.SamePoint v w))
    (hA₁ : LeanEval.Geometry.PascalPappus.OnConic M a₁) (hA₂ : LeanEval.Geometry.PascalPappus.OnConic M a₂) (hA₃ : LeanEval.Geometry.PascalPappus.OnConic M a₃)
    (hB₁ : LeanEval.Geometry.PascalPappus.OnConic M b₁) (hB₂ : LeanEval.Geometry.PascalPappus.OnConic M b₂) (hB₃ : LeanEval.Geometry.PascalPappus.OnConic M b₃) :
    LeanEval.Geometry.PascalPappus.Collinear3 (LeanEval.Geometry.PascalPappus.meet a₁ b₂ a₂ b₁) (LeanEval.Geometry.PascalPappus.meet a₁ b₃ a₃ b₁) (LeanEval.Geometry.PascalPappus.meet a₂ b₃ a₃ b₂) := by
  sorry
-- ANCHOR_END: pascal__pascal

end ProblemPascal
