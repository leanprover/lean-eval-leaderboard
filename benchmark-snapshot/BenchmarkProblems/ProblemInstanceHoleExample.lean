import Mathlib

/-!
Minimal example exercising `instance` holes in the multi-hole
eval-problem pipeline. The carrier type is itself a hole so the source
has no non-hole declarations and the generator does not need a
`ChallengeDeps` split.
-/
-- ANCHOR: instance_hole_example__WidgetCarrier
def WidgetCarrier : Type := sorry
-- ANCHOR_END: instance_hole_example__WidgetCarrier
-- ANCHOR: instance_hole_example__instInhabitedWidget
instance instInhabitedWidget : Inhabited WidgetCarrier := sorry
-- ANCHOR_END: instance_hole_example__instInhabitedWidget
