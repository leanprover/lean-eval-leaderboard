import Mathlib

namespace ProblemKirkNormalStructure

namespace LeanEval.Topology.KirkNormalStructure

/-!
# Kirk's normal-structure fixed point theorem

`kirk_normal_structure`: a nonexpansive self-map of a nonempty bounded closed
convex subset of a reflexive Banach space with normal structure has a fixed
point. Reflexivity is genuine Banach-space reflexivity (surjectivity of the
canonical embedding into the bidual), avoiding the collapse to the
finite-dimensional case caused by algebraic reflexivity. Helpers
`metricDiameter`, `pointRadiusIn`, `IsDiametralPoint`, `HasNormalStructure`
and `IsNonexpansiveSelfMap` express the geometric hypotheses. Category-(b)
candidate from §228 of the Knill survey.
-/

open Function

variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]

/-- The diameter of a set, as a real supremum of all pairwise distances inside
the set.  This keeps the normal-structure statement in ordinary metric
language. -/
noncomputable def metricDiameter (s : Set E) : ℝ :=
  sSup {r : ℝ | ∃ x ∈ s, ∃ y ∈ s, dist x y = r}

/-- Radius of a point relative to a set, i.e. the supremum of its distances to
points of the set. -/
noncomputable def pointRadiusIn (x : E) (s : Set E) : ℝ :=
  sSup {r : ℝ | ∃ y ∈ s, dist x y = r}

/-- A point is diametral in `s` if its radius in `s` is the diameter of `s`. -/
def IsDiametralPoint (s : Set E) (x : E) : Prop :=
  x ∈ s ∧ pointRadiusIn x s = metricDiameter s

/-- A bounded convex set has normal structure if every nontrivial convex subset
contains a non-diametral point. -/
def HasNormalStructure (K : Set E) : Prop :=
  ∀ H : Set E,
    H ⊆ K →
      Convex ℝ H →
        H.Nontrivial →
          ∃ x ∈ H, ¬ IsDiametralPoint H x

/-- A self-map of a set is nonexpansive when it is `1`-Lipschitz for the
subtype metric. -/
def IsNonexpansiveSelfMap (K : Set E) (T : K → K) : Prop :=
  LipschitzWith 1 T



end LeanEval.Topology.KirkNormalStructure

open LeanEval.Topology.KirkNormalStructure
open Function

variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]

-- ANCHOR: kirk_normal_structure__kirk_normal_structure
theorem kirk_normal_structure [CompleteSpace E]
    (hE_reflexive : Function.Surjective (NormedSpace.inclusionInDoubleDual ℝ E))
    (K : Set E) (hK_nonempty : K.Nonempty) (hK_closed : IsClosed K)
    (hK_bounded : Bornology.IsBounded K) (hK_convex : Convex ℝ K)
    (hK_normal : LeanEval.Topology.KirkNormalStructure.HasNormalStructure K) (T : K → K)
    (hT : LeanEval.Topology.KirkNormalStructure.IsNonexpansiveSelfMap K T) :
    ∃ x : K, IsFixedPt T x := by
  sorry
-- ANCHOR_END: kirk_normal_structure__kirk_normal_structure

end ProblemKirkNormalStructure
