import Mathlib.GroupTheory.CommutingProbability
import Mathlib.Topology.MetricSpace.Pseudo.Defs

namespace ProblemCommProbClosed

-- ANCHOR: commProb_closed__commProb_closed
theorem commProb_closed : IsClosed ({p : ℝ | ∃ (G : Type) (hG : Group G), commProb G = p}) := by
  sorry
-- ANCHOR_END: commProb_closed__commProb_closed

end ProblemCommProbClosed
