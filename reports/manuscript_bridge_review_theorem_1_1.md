# Bridge review material — manuscript Theorem 1.1 ↔ Lean `OAI.InfiniteMatroidCounterexample.main`

**Status: PREPARED FOR HUMAN REVIEW. NOT REVIEWED. NOT A PROOF OF EQUIVALENCE.**
Prepared by Claude as an aid to the ratifier. It records a clause-by-clause comparison and the points a reviewer must check.
The gates A–D (see `stage_results_p10_frozen_v1.md`) establish that the Lean statement below is accepted by Comparator; they say nothing about whether it means what the manuscript says. Semantic equivalence stays **Not Demonstrated** until a named human or expert signs off here.

Sources compared (frozen commit `adc7f12…`, hashes in `subject.lock.json`):
- manuscript `preprints/A-Counterexample-…-September-24-2026/build/sections/01-introduction.tex` (Theorem 1.1, definition of packing/covering partition), `02-matroids.tex` (conventions, Lemmas 2.1–2.2); `06`/`07` read earlier.
- Lean `lean/ComparatorChallenges/InfiniteMatroid.lean` (the trusted statement) and Mathlib `d13f23b…` `Mathlib/Combinatorics/Matroid/{Basic,Closure}.lean`.
- **Not read for this table:** §3–5 (filters, local bases, assembly). They contain the construction and proof, which Lean replaces; they matter for the statement only if they redefine notation used in Theorem 1.1.

## Lean statement (challenge file)

```
abbrev D := (m : ℕ) × ((Fin m → Bool) → Bool);  abbrev E := ℤ × D
def contractOnto (M : Matroid α) (C : Set α) : Matroid α := (M.dual ↾ C).dual
def HasPackingCovering (M₀ M₁ : Matroid α) : Prop :=
  ∃ P C S₀ S₁ I₀ I₁ : Set α, Disjoint P C ∧ P ∪ C = M₀.E ∧ M₁.E = M₀.E ∧
    S₀ ⊆ P ∧ S₁ ⊆ P ∧ Disjoint S₀ S₁ ∧ (M₀ ↾ P).Spanning S₀ ∧ (M₁ ↾ P).Spanning S₁ ∧
    I₀ ⊆ C ∧ I₁ ⊆ C ∧ (contractOnto M₀ C).Indep I₀ ∧ (contractOnto M₁ C).Indep I₁ ∧ I₀ ∪ I₁ = C
theorem main : Countable E ∧ Infinite E ∧ ∃ M₀ M₁ : Matroid E,
  M₀.E = Set.univ ∧ M₁.E = Set.univ ∧ M₀.dual = M₀ ∧ M₁.dual = M₁ ∧
  (∀ I₀ I₁ : Set E, M₀.Indep I₀ → M₁.Indep I₁ → I₀ ∪ I₁ ≠ Set.univ) ∧ ¬ HasPackingCovering M₀ M₁
```

## Clause table

| # | Theorem 1.1 / definition (manuscript) | Lean | my reading | reviewer must check |
|---|---|---|---|---|
| 1 | "In ZFC, there exist a countably infinite set E" | one fixed type `E = ℤ × D`, `Countable E ∧ Infinite E` | a specific countable infinite set implies the existential; matches | that `E` is genuinely countable/infinite is machine-checked; the ZFC remark is row 11 |
| 2 | "two infinite matroids M₀, M₁ on E" | `∃ M₀ M₁ : Matroid E`, `M_i.E = Set.univ` | ground set is all of `E`; matches. "Infinite" follows from `E` infinite | — |
| 3 | matroid = BDKPW axioms (I1),(I2),(I3),(IM), maximal extension inside **every** subset (§2) | Mathlib `Matroid`: bases + exchange + `maximality : ∀ X ⊆ E, ExistsMaximalSubsetProperty Indep X` (`Basic.lean:192–212`) | Mathlib's structure states maximality for all `X ⊆ E`, which is the (IM) point the manuscript stresses | that Mathlib's base-exchange presentation is equivalent to the manuscript's independence-axiom presentation (a standard BDKPW result, not re-proved in Lean here) |
| 4 | `M_i^* = M_i` "on the same labelled ground set" | `M₀.dual = M₀ ∧ M₁.dual = M₁` (equality of `Matroid` structures, includes `E`) | matches | Mathlib `dual` is the manuscript's dual (bases = complements of bases) |
| 5 | `I₀ ∪ I₁ ≠ E` for every independent `I₀` of `M₀`, `I₁` of `M₁` | `∀ I₀ I₁ : Set E, M₀.Indep I₀ → M₁.Indep I₁ → I₀ ∪ I₁ ≠ Set.univ` | matches | — |
| 6 | contraction onto X: `M.X = M/(E∖X) = (M*↾X)*` | `contractOnto M C := (M.dual ↾ C).dual` | same formula, defined locally in the challenge file (not Mathlib's `contract`) | that `↾` is restriction `M ↾ R` and the local definition is used consistently in both challenge and solution (Comparator's statement match enforces the latter) |
| 7 | partition `E = P ⊔ C` | `Disjoint P C ∧ P ∪ C = M₀.E ∧ M₁.E = M₀.E` | matches (second ground-set equality is redundant) | — |
| 8 | `S_i ⊆ P`, `S_0 ∩ S_1 = ∅` | `S₀ ⊆ P ∧ S₁ ⊆ P ∧ Disjoint S₀ S₁` | matches (index set Θ = {0,1} written out) | — |
| 9 | `cl_{M_i↾P}(S_i) = P` | `(M_i ↾ P).Spanning S_i`; Mathlib `Spanning S := closure S = E ∧ S ⊆ E` (`Closure.lean:827–829`) | `closure = E(M↾P) = P` plus `S ⊆ P`: matches | that Mathlib's `closure` (intersection of flats containing `X ∩ E`, `Closure.lean:135`) equals the manuscript's `cl` (`X ∪ {e : ∃ independent I ⊆ X, I ∪ e dependent}`); both are the standard closure; the manuscript's Lemma 2.1(2) "spanning iff contains a basis" is also a Mathlib lemma family |
| 10 | `I_i` independent in `M_i.C`, `⋃ I_i = C`; `I_i ⊆ C` | `I_i ⊆ C ∧ (contractOnto M_i C).Indep I_i ∧ I₀ ∪ I₁ = C` | matches | — |
| 11 | "in ZFC" | Lean/Mathlib with `propext`, `Quot.sound`, `Classical.choice` | **not shown equivalent here**: Lean's type theory is not ZFC; transfer of an existence statement of this kind to ZFC needs an argument (absoluteness / relative consistency) that is not part of any gate | an expert statement on transfer, or an explicit "Lean-formal" scoping of the claim |
| 12 | "The pair has no packing/covering partition" | `¬ HasPackingCovering M₀ M₁` | matches rows 6–10 | — |
| 13 | "Consequently, the infinite matroid packing/covering conjecture is false" | **absent from `main`** | the conjecture itself (for set-indexed families) is not formalized in the subject; the step "this pair refutes it" is informal | decide whether the ratified claim includes it; if yes, it needs its own formal or reviewed argument |

## Observations a reviewer should weigh

1. `main` is stated over a fixed concrete `E`; Theorem 1.1 says "there exists a countably infinite set". Implication holds, so no gap — but the reviewer should confirm they accept this reading.
2. The challenge file defines `HasPackingCovering` and `contractOnto` itself. Therefore the trust in the *meaning* of "packing/covering partition" rests on rows 6–10 above, not on any upstream Mathlib definition. This is the single most important item to read in the Lean file by eye.
3. Row 9's closure equivalence and row 3's axiom equivalence are standard but not machine-checked in this pilot.
4. Not in the subject (recorded in `subject.lock.json` under `adjacent_not_in_subject`): the partitional and intersection corollaries, "not finitary", Joó's question, existence of ZFC self-dual uniform matroid claims of §1 ("answers both existence questions") — separate claims of the manuscript with separate (or no) Lean units.

## Pinned-source trace for rows 3, 4, 6, 9 (added after reviewer request; no execution run)

All references are to Mathlib `d13f23b723b8a846827a245b89c10fc7d3f11612` (the pin in `profiles/minimal/lake-manifest.json`), fetched from that revision, not from current documentation. File identities (sha256 of the raw file at that revision, line counts):

| file (under `Mathlib/Combinatorics/Matroid/`) | sha256 | lines |
|---|---|---|
| `Basic.lean` | `d67ac4aa1362336ace8dd451562629cb27c9ced5c37cf25d85dfba526d14a62f` | 1142 |
| `Closure.lean` | `5881107273de87e804323c058e5120af058fa7774076248a8ecbac08bbbfee0b` | 1068 |
| `Dual.lean` | `aff6c92b0364734ed53ecfc440998c96f4c2eb3c47ee35a48e4e572716ed580f` | 260 |
| `Minor/Restrict.lean` | `163bc051bfcaca9758f070de5bc7d2509887153ab719c48d7e4d5a6682cbc40d` | 480 |

**Row 4 (dual).** `Dual.lean:108–109`: docstring "The dual of a matroid; the bases are the complements (w.r.t. `M.E`) of the bases of `M`", `def dual (M : Matroid α) : Matroid α := M.dualIndepMatroid.matroid`. `Dual.lean:118` `dual_ground : M✶.E = M.E`; `:135` `dual_isBase_iff`; `:141` `dual_isBase_iff' : M✶.IsBase B ↔ M.IsBase (M.E \ B) ∧ B ⊆ M.E`; `:154` `dual_dual : M✶✶ = M`; `:158` `dual_involutive`. This is the manuscript's duality (bases of N* are complements of bases of N, §2). Row 4 is a statement-level match on pinned source; the only residual is the representation caveat of row 3.

**Row 9 (spanning, restriction).** `Closure.lean:135` `def closure (M) (X) : Set α := ⋂₀ {F | M.IsFlat F ∧ X ∩ M.E ⊆ F}`; `:827–829` `structure Spanning (M) (S) : Prop where closure_eq : M.closure S = M.E; subset_ground : S ⊆ M.E`; `:833–835` `spanning_iff_closure_eq`. `Minor/Restrict.lean:122` `def restrict (M) (R) := (M.restrictIndepMatroid R).matroid`, `:124–125` notation `M ↾ R`, **`:135` `@[simp] theorem restrict_ground_eq : (M ↾ R).E = R := rfl`** (the ground set of `M ↾ P` is exactly `P`, by `rfl`). Hence `(M_i ↾ P).Spanning S_i` unfolds to `closure_{M_i↾P}(S_i) = P ∧ S_i ⊆ P`, which has the shape of the manuscript's `cl_{M_i↾P}(S_i) = P` with `S_i ⊆ P`. What this trace does **not** establish: that Mathlib's flat-intersection `closure` coincides with the manuscript's `cl(X) = X ∪ {e : ∃ independent I ⊆ X, I ∪ {e} dependent}` (a standard equivalence, not re-proved here); Mathlib also proves `IsBase.closure_eq` (`Closure.lean:437`) and `isBase_iff_indep_closure_eq` (`:443`), consistent with the manuscript's Lemma 2.1(2).

**Row 3 (representation).** `Basic.lean:192–210` `structure Matroid` carries `E`, `IsBase`, `Indep`, `indep_iff'` (independent = contained in a base), `exists_isBase`, `isBase_exchange`, and `maximality : ∀ X, X ⊆ E → Matroid.ExistsMaximalSubsetProperty Indep X`, `subset_ground`. Maximality quantifies over **all** `X ⊆ E`, i.e. the manuscript's (IM). Equivalence of this base-exchange presentation with the (I1–I3, IM) independence presentation is a known result and is **not** machine-checked in this pilot: row 3 stays an explicit representation assumption.

**Row 6 (local `contractOnto`).** Not a Mathlib definition; defined in the challenge file as `(M.dual ↾ C).dual`, i.e. the manuscript's `M.C = (M*↾C)*` built from the Mathlib `dual` (row 4) and `restrict` (row 9) above.

Status of these rows after the trace: 4 and 6 are matches on pinned source for the reviewer to accept; 9 matches in shape with the closure-definition caveat above; 3 remains an open representation assumption. **No row has been accepted by anyone; the sign-off block below is still empty.** Rows 11 and 13 are unchanged (outside any claim derived from the machine gates).

## Sign-off block (to be completed by a human; empty = not reviewed)

```
reviewer:            
date:                
rows 1–13 accepted:  
exceptions / notes:  
decision on row 13 (is "conjecture is false" part of the ratified claim?):  
decision on row 11 (ZFC vs Lean-formal scoping):  
```
