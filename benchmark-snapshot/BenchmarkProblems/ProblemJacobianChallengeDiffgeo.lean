import Mathlib

/-!
# Jacobians of compact Riemann surfaces

Kevin Buzzard's "Jacobian Challenge" v0.3, posted to leanprover Zulip
(`#Autoformalization > Jacobian challenge`):
<https://leanprover.zulipchat.com/#narrow/stream/583336-Autoformalization/topic/Jacobian%20challenge>.
The original source uses anonymous instances; here every `instance` is
named explicitly so the eval-problem pipeline can address it.

## Main missing definitions

* `genus` -- genus of a compact Riemann surface
* `Jacobian` -- the Jacobian of a compact Riemann surface
* `Jacobian.ofCurve` -- the Abel-Jacobi map from a compact Riemann surface to its Jacobian
* `ContMDiff.degree` -- the degree of a holomorphic map between compact Riemann surfaces.
    Equal to 0 if the map is constant, otherwise equal to the usual degree.
* `Jacobian.pushforward` -- the pushforward map on Jacobians induced by a holomorphic map between
  compact Riemann surfaces.
* `Jacobian.pullback` -- the pullback map on Jacobians induced by a holomorphic map between
  compact Riemann surfaces.

## Main missing theorems

* `genus_eq_zero_iff_homeo` -- a compact Riemann surface has genus 0 iff it is homeomorphic to the sphere
* `ofCurve_inj` -- the Abel-Jacobi map is injective iff the genus is positive
* `Jacobian.ofCurve_contMDiff` -- the Abel-Jacobi map is holomorphic
* `Jacobian.pushforward_contMDiff` -- the pushforward map is holomorphic
* `Jacobian.pullback_contMDiff` -- the pullback map is holomorphic
* `pushforward_pullback` -- pullback then pushforward is multiplication by degree
-/

open scoped ContDiff -- for ω notation

namespace JacobianChallenge

universe u v w

-- let X be a compact Riemann surface
variable {X : Type u} [TopologicalSpace X] [T2Space X] [CompactSpace X] [ConnectedSpace X]
  [ChartedSpace ℂ X] [IsManifold (modelWithCornersSelf ℂ ℂ) ω X]

-- data
-- ANCHOR: jacobian_challenge_diffgeo__genus
def genus (X : Type u) [TopologicalSpace X] [T2Space X] [CompactSpace X] [ConnectedSpace X]
    [Nonempty X] [ChartedSpace ℂ X] [IsManifold (modelWithCornersSelf ℂ ℂ) ω X] : ℕ := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__genus

-- this proof avoids the hack answer `∀ X, genus X = 0`
-- Prop
-- ANCHOR: jacobian_challenge_diffgeo__genus_eq_zero_iff_homeo
theorem genus_eq_zero_iff_homeo :
    genus X = 0 ↔ Nonempty (X ≃ₜ (Metric.sphere (0 : EuclideanSpace ℝ (Fin 3)) 1)) :=
  sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__genus_eq_zero_iff_homeo

-- data
-- ANCHOR: jacobian_challenge_diffgeo__Jacobian
def Jacobian (X : Type u) [TopologicalSpace X] [T2Space X] [CompactSpace X] [ConnectedSpace X]
    [Nonempty X] [ChartedSpace ℂ X] [IsManifold (modelWithCornersSelf ℂ ℂ) ω X] : Type u := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__Jacobian

namespace Jacobian

-- data
-- ANCHOR: jacobian_challenge_diffgeo__instAddCommGroup
instance instAddCommGroup : AddCommGroup (Jacobian X) := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__instAddCommGroup

-- data
-- ANCHOR: jacobian_challenge_diffgeo__instTopologicalSpace
instance instTopologicalSpace : TopologicalSpace (Jacobian X) := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__instTopologicalSpace

-- Prop
-- ANCHOR: jacobian_challenge_diffgeo__instT2Space
instance instT2Space : T2Space (Jacobian X) := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__instT2Space

-- Prop
-- ANCHOR: jacobian_challenge_diffgeo__instCompactSpace
instance instCompactSpace : CompactSpace (Jacobian X) := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__instCompactSpace
-- ANCHOR: jacobian_challenge_diffgeo__instChartedSpace
instance instChartedSpace : ChartedSpace (Fin (genus X) → ℂ) (Jacobian X) := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__instChartedSpace

-- Prop
-- ANCHOR: jacobian_challenge_diffgeo__instIsManifold
instance instIsManifold :
    IsManifold (modelWithCornersSelf ℂ (Fin (genus X) → ℂ)) ω (Jacobian X) := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__instIsManifold

-- Prop
-- ANCHOR: jacobian_challenge_diffgeo__instLieAddGroup
instance instLieAddGroup :
    LieAddGroup (modelWithCornersSelf ℂ (Fin (genus X) → ℂ)) ω (Jacobian X) := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__instLieAddGroup
-- ANCHOR: jacobian_challenge_diffgeo__ofCurve
def ofCurve (P : X) : X → Jacobian X := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__ofCurve
-- ANCHOR: jacobian_challenge_diffgeo__ofCurve_contMDiff
theorem ofCurve_contMDiff (P : X) :
    ContMDiff (modelWithCornersSelf ℂ ℂ)
      (modelWithCornersSelf ℂ (Fin (genus X) → ℂ)) ω (ofCurve P) := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__ofCurve_contMDiff
-- ANCHOR: jacobian_challenge_diffgeo__ofCurve_self
theorem ofCurve_self (P : X) : ofCurve P P = 0 := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__ofCurve_self

-- this is the lemma which stops the hack answer "J(X)=0 for all X"
-- ANCHOR: jacobian_challenge_diffgeo__ofCurve_inj
theorem ofCurve_inj (P : X) (h : 0 < genus X) : Function.Injective (ofCurve P) := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__ofCurve_inj

variable {Y : Type v} [TopologicalSpace Y] [T2Space Y] [CompactSpace Y] [ConnectedSpace Y]
  [Nonempty Y] [ChartedSpace ℂ Y] [IsManifold (modelWithCornersSelf ℂ ℂ) ω Y]

variable (f : X → Y) (hf : ContMDiff (modelWithCornersSelf ℂ ℂ) (modelWithCornersSelf ℂ ℂ) ω f)
-- ANCHOR: jacobian_challenge_diffgeo__pushforward
def pushforward (f : X → Y)
    (hf : ContMDiff (modelWithCornersSelf ℂ ℂ) (modelWithCornersSelf ℂ ℂ) ω f) :
    Jacobian X →ₜ+ Jacobian Y := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__pushforward
-- ANCHOR: jacobian_challenge_diffgeo__pushforward_contMDiff
theorem pushforward_contMDiff (f : X → Y)
    (hf : ContMDiff (modelWithCornersSelf ℂ ℂ) (modelWithCornersSelf ℂ ℂ) ω f) :
    ContMDiff (modelWithCornersSelf ℂ (Fin (genus X) → ℂ))
      (modelWithCornersSelf ℂ (Fin (genus Y) → ℂ)) ω (pushforward f hf) := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__pushforward_contMDiff

-- functoriality
-- ANCHOR: jacobian_challenge_diffgeo__pushforward_id_apply
theorem pushforward_id_apply (P : Jacobian X) :
    pushforward id contMDiff_id P = P := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__pushforward_id_apply

variable {Z : Type w} [TopologicalSpace Z] [T2Space Z] [CompactSpace Z] [ConnectedSpace Z]
  [Nonempty Z] [ChartedSpace ℂ Z] [IsManifold (modelWithCornersSelf ℂ ℂ) ω Z]

variable (g : Y → Z) (hg : ContMDiff (modelWithCornersSelf ℂ ℂ) (modelWithCornersSelf ℂ ℂ) ω g)
-- ANCHOR: jacobian_challenge_diffgeo__pushforward_comp_apply
theorem pushforward_comp_apply (f : X → Y)
    (hf : ContMDiff (modelWithCornersSelf ℂ ℂ) (modelWithCornersSelf ℂ ℂ) ω f)
    (g : Y → Z) (hg : ContMDiff (modelWithCornersSelf ℂ ℂ) (modelWithCornersSelf ℂ ℂ) ω g)
    (P : Jacobian X) :
    pushforward (g ∘ f) (hg.comp hf) P = pushforward g hg (pushforward f hf P) :=
  sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__pushforward_comp_apply

-- if f is constant then the pullback should be the zero map, otherwise it's
-- the usual pullback
-- ANCHOR: jacobian_challenge_diffgeo__pullback
def pullback (f : X → Y)
    (hf : ContMDiff (modelWithCornersSelf ℂ ℂ) (modelWithCornersSelf ℂ ℂ) ω f) :
    Jacobian Y →ₜ+ Jacobian X := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__pullback
-- ANCHOR: jacobian_challenge_diffgeo__pullback_contMDiff
theorem pullback_contMDiff (f : X → Y)
    (hf : ContMDiff (modelWithCornersSelf ℂ ℂ) (modelWithCornersSelf ℂ ℂ) ω f) :
    ContMDiff (modelWithCornersSelf ℂ (Fin (genus Y) → ℂ))
      (modelWithCornersSelf ℂ (Fin (genus X) → ℂ)) ω (pullback f hf) := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__pullback_contMDiff
-- ANCHOR: jacobian_challenge_diffgeo__pullback_id_apply
theorem pullback_id_apply (P : Jacobian X) :
    pullback id contMDiff_id P = P := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__pullback_id_apply
-- ANCHOR: jacobian_challenge_diffgeo__pullback_comp_apply
theorem pullback_comp_apply (f : X → Y)
    (hf : ContMDiff (modelWithCornersSelf ℂ ℂ) (modelWithCornersSelf ℂ ℂ) ω f)
    (g : Y → Z) (hg : ContMDiff (modelWithCornersSelf ℂ ℂ) (modelWithCornersSelf ℂ ℂ) ω g)
    (P : Jacobian Z) :
    pullback (g.comp f) (hg.comp hf) P = pullback f hf (pullback g hg P) := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__pullback_comp_apply
-- ANCHOR: jacobian_challenge_diffgeo__degree
def degree (f : X → Y)
    (hf : ContMDiff (modelWithCornersSelf ℂ ℂ) (modelWithCornersSelf ℂ ℂ) ω f) : ℕ :=
  sorry -- 0 for constant case
-- ANCHOR_END: jacobian_challenge_diffgeo__degree
-- ANCHOR: jacobian_challenge_diffgeo__pushforward_pullback
theorem pushforward_pullback (f : X → Y)
    (hf : ContMDiff (modelWithCornersSelf ℂ ℂ) (modelWithCornersSelf ℂ ℂ) ω f)
    (P : Jacobian Y) :
    pushforward f hf (pullback f hf P) = (degree f hf) • P := sorry
-- ANCHOR_END: jacobian_challenge_diffgeo__pushforward_pullback

end Jacobian

end JacobianChallenge
