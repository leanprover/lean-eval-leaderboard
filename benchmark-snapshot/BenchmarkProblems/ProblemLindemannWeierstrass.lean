import Mathlib

namespace ProblemLindemannWeierstrass

open Polynomial

-- ANCHOR: lindemann_weierstrass__lindemann_weierstrass
theorem lindemann_weierstrass {n : ℕ} (x : Fin n → ℂ)
    (h_alg : ∀ i, IsAlgebraic ℚ (x i))
    (h_lin : LinearIndependent ℚ x) :
    AlgebraicIndependent ℚ (fun i => Complex.exp (x i)) := by
  sorry
-- ANCHOR_END: lindemann_weierstrass__lindemann_weierstrass

end ProblemLindemannWeierstrass
