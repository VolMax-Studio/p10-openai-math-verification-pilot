# Candidate pilot subjects

**No candidate is selected.** Selection is a normative decision reserved for the ratifier (Ivan).
Ranking criterion is auditability, not prestige. Rows are in alphabetical order of config name; order is not a ranking.
All figures: **O** = OBSERVED from `evidence/discovery/candidates.json` (pinned commit `adc7f12…`), **D** = DERIVED, **N** = NOT DEMONSTRATED.
No candidate was built or run; I did not read any manuscript body, so every manuscript<->formal relation below is **D** from upstream's own `CONTENTS.md`/`lean/docs/*.md` prose.

Selection screen applied to all 405 configs (`challenge_inventory.json`): single theorem, no non-Mathlib package imported anywhere in the solution's local import closure (so the 11 `lana-agents` and other patched third-party packages are not in the closure), documented in `docs/`, one manuscript linked. Closure scan (comment-stripped text) found 0 `sorry`, `axiom`, `native_decide`, `unsafe`, `extern/implemented_by`, `set_option`, `run_cmd/elab/macro/initialize` in all five closures. This is a text scan, not an axiom audit (N).

| | AbhyankarSathaye | FiniteCongruenceGraph | GrahamSpherical | InfiniteMatroid | PlanarAndersonSpectrum |
|---|---|---|---|---|---|
| Family / docs | 049 | 206 | 172 | 185 | 261 |
| Primary declaration | `OAI.AbhyankarSathaye.exists_noncoordinate_polynomial` | `OAI.FiniteCongruence.graph_criterion` | `OAI.GrahamSpherical.full_main` | `OAI.InfiniteMatroidCounterexample.main` | `OAI.PlanarAnderson.anderson_spectrum_ae` |
| Solution module | `…AbhyankarSathaye.Counterexample` | `OAI.Algebra.Universal.GraphCriterion` | `…SphericalRamsey.Main` | `…InfiniteMatroid.Main` | `…PlanarAnderson.Spectrum` |
| Closure (modules / lines, excl. Mathlib) | 15 / 1,460 | 2 / 471 | 18 / 987 | 25 / 4,041 | 1 / 768 |
| Non-Mathlib packages in closure | none | none | none | none | none |
| In `formalization.yaml` `main_results` | yes | **no** | yes | yes | **no** |
| Manuscripts in family / linked by docs | 2 / 1 | 2 / 1 | **1 / 1** | **1 / 1** | 2 / 1 |
| Challenge-local `def/abbrev/structure/instance` (trust surface; `grep` count, O) | 0 (pure Mathlib vocabulary: `MvPolynomial`, `AlgEquiv`) | 10 (`Algebra`, `Compatible`, `Congruence`, `Representable`, `IsGraphWitness`, …; incl. 1 instance) | 12 (`parameter`, `witness`, `EuclideanRamsey`, `FullAuthoredResult`, …) | 4 (`D`, `E`, `contractOnto`, `HasPackingCovering`; uses Mathlib `Matroid`) | 6 (`Site`, `Configuration`, `Hilbert`, `disorderLaw`, `IsAndersonOperator`, `spectralInterval`) |
| Other challenges in same family | `CommutingDerivations` (32 modules / 3,272 lines) | – | 6 more (`EuclideanRamsey*`) | `InfiniteMatroidCorollaries` | – |

## Per-candidate evidence and relation to the manuscript claim (D)

**AbhyankarSathaye (049)** — `lean/docs/049.md` links manuscript *An explicit noncoordinate polynomial with affine three-space zero fibre* (Sep 24). The formal statement is for all `n ≥ 4`: ∃F, `C[x₁..xₙ]/(F) ≅ C[y₁..yₙ₋₁]` ∧ F not an ambient coordinate. **Gap visible in upstream text itself:** `CONTENTS.md` headlines family 049 as a *stable-coordinate* counterexample ("becomes a coordinate after adjoining a single variable… none of its embeddings is rectifiable") and lists a second manuscript (*A stable coordinate that is not a coordinate in four variables*, Oct 5) that `docs/049.md` does not link. The challenge statement does not mention stability (O: file text). Cheapest Mathlib-only statement; weakest family-level binding.

**FiniteCongruenceGraph (206)** — smallest (2 modules). Formal statement is the colored-graph characterization `Representable Lat ↔ HasGraphWitness Lat`. `docs/206.md` says the paper's undecidability and subgroup-interval conclusions are outside it; `CONTENTS.md` headline for 206 is the negative answer to finite lattice representation + undecidability (O). Not in `yaml main_results`. Useful as a **boundary exemplar** (headline substantially outruns the formal statement); poor as a first "clean" pilot.

**GrahamSpherical (172)** — one family, one manuscript, docs links it. But the manuscript has ≥7 formalized results (docs table); this config covers only one (twelve-point spherical non-Ramsey example, `FullAuthoredResult` conjunction incl. a 50-colour obstruction in every dimension). Statement relies on a defined transcendental-style parameter `∑ 1/10^(m+1)!` and 12 challenge-local definitions (larger fidelity-audit surface). 987 lines.

**InfiniteMatroid (185)** — one family, one manuscript, docs links it (strongest binding at family level in this set). Challenge `main`: countable infinite ground set `E`, two self-dual matroids `M₀ M₁` with no independent covering (`I₀ ∪ I₁ ≠ univ`) and `¬HasPackingCovering M₀ M₁`; the family headline additionally claims refuting the intersection conjecture, which `docs/185.md` says follows from the same pair and is covered by the separate `InfiniteMatroidCorollaries` challenge (D: the corollaries config is a second subject unit). Uses Mathlib's `Matroid` plus 4 challenge-local defs (2 type abbreviations, 2 predicates/constructions). Largest of the set (25 modules / 4,041 lines) but moderate.

**PlanarAndersonSpectrum (261)** — 1 module, 768 lines. `docs/261.md`: "supporting spectral statement… does not assert the pure-point spectral type claimed in the accompanying paper" (O). Family headline (pure-point spectrum in d=2; a.c. spectrum for d≥3) is **not** the formal statement. Not in `yaml main_results`. Pure **negative control** for boundary reporting; not a candidate for a "verified claim".

## Recommendation (D; for Ivan to ratify or override)

**First pilot: `InfiniteMatroid`** (family 185), with `AbhyankarSathaye` as the second pilot and `PlanarAndersonSpectrum`/`FiniteCongruenceGraph` as boundary exemplars.

Why: (i) 1 family = 1 manuscript = 1 docs page, so manuscript -> challenge binding has no ambiguity about *which* paper; (ii) the primary declaration is the family's headline counterexample, with the remaining headline (intersection) isolated in a named second config; (iii) Mathlib-only closure, no patched third-party package, no `sorry/axiom/native_decide/unsafe` text hits; (iv) mid-size cost (4,041 lines) — likely cheaper than the full Mathlib build itself (N: not measured). Cost: the statement carries 4 challenge-local definitions that need a human fidelity audit against the manuscript (outside Comparator).
If minimum build cost dominates, `AbhyankarSathaye` is cheaper and has zero local definitions, but its family headline is visibly not what is formalized, which makes it a better *boundary measurement* than a first clean subject.

`subject.lock.json` therefore keeps `selected_candidate: null`; it records SHA-256 of every file in each candidate's binding chain so that selection later requires no re-discovery.
