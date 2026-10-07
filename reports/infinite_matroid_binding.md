# Binding report: openai/math family 185 — `InfiniteMatroid`

Status: **analysis of bindings only. No Lean build, no Comparator run, no verdict.** Nothing here states that the
manuscript result has been independently verified. Subject selected by Ivan (ratifier) on 2026-10-07; frozen in `subject.lock.json`.
Labels: **O** observed (path @ commit / command / hash) · **D** derived (method stated) · **N** not demonstrated.

---
## SUBJECT
- Upstream `https://github.com/openai/math` @ `adc7f1241b42e322a6451854ab7e4b4c146bf78a` (2026-10-06T14:58:50-07:00); frozen by `subject.lock.json` (schema `p10-subject-lock/1`).
- Family 185 "Counterexamples to infinite matroid intersection and packing/covering"; one manuscript, *A Counterexample to the Infinite Matroid Packing/Covering Conjecture* (OpenAI, 2026-09-24, 20 pp.).
- Comparator unit: `lean/ComparatorChallenges/InfiniteMatroid.{lean,json}`; solution module `OAI.Combinatorics.InfiniteMatroid.Main`; primary declaration `OAI.InfiniteMatroidCounterexample.main`.
- Adjacent unit **not** frozen as part of this subject: `InfiniteMatroidCorollaries` (partitional + intersection + separate covering/packing). Hashes recorded under `adjacent_not_in_subject`.

### The question this report answers
> What exact mathematical statement can the current OpenAI/Comparator machinery establish, and what additional inference is required before anyone may say that this verifies the associated manuscript result?

**Short answer (D).** If every gate ran and passed, the machinery would establish one thing: *in Lean 4 (kernel-checked, axioms ⊆ {propext, Quot.sound, Classical.choice}) with Mathlib at `d13f23b`, there exist two `Matroid`s `M₀ M₁` on the concrete type `E = ℤ × (Σ m, ((Fin m → Bool) → Bool))`, both with ground set all of `E`, both equal to their duals, such that no pair of independent sets covers `E`, and `HasPackingCovering M₀ M₁` (as defined in the challenge file) is false; and `E` is countable and infinite.* That is the content of `InfiniteMatroid.lean`'s `main`. It does **not** by itself say "the manuscript is verified": that needs the inference chain in **DERIVED** below, most steps of which are human-audited correspondences, not machine-enforced.

---
## OBSERVED
**O1 Frozen files (sha256).**
| id | path | sha256 |
|---|---|---|
| E1 | `CONTENTS.md` | `c492802b…bf9` (full hashes in lock) |
| E2 | `preprints/A-Counterexample-…-September-24-2026/paper.pdf` | `320eb5d3…77b9e` (+ 11 further files: README, `build/paper.tex`, `build/sections/01…07*.tex`, `references.bib`, `figures/double-ray.tex`) |
| E3 | `lean/docs/185.md` | `00d22dbd…a64d` |
| E4 | `lean/formalization.yaml` | `2dcbd0d6…edb9` |
| E5 | `lean/ComparatorChallenges/InfiniteMatroid.lean` | `802e9bf6…ae3a7` |
| E6 | `lean/ComparatorChallenges/InfiniteMatroid.json` | `8d565944…13b82` |
| E7 | `lean/OAI/Combinatorics/InfiniteMatroid/Main.lean` (+24 closure modules; closure digest `4be7bf5f…b37a`) | `4c47af8f…b25b` |

**O2 Challenge statement** (`InfiniteMatroid.lean`, namespace `OAI.InfiniteMatroidCounterexample`):
```lean
theorem main :
    Countable E ∧ Infinite E ∧
    ∃ M₀ M₁ : Matroid E,
      M₀.E = Set.univ ∧ M₁.E = Set.univ ∧
      M₀.dual = M₀ ∧ M₁.dual = M₁ ∧
      (∀ I₀ I₁ : Set E, M₀.Indep I₀ → M₁.Indep I₁ → I₀ ∪ I₁ ≠ Set.univ) ∧
      ¬ HasPackingCovering M₀ M₁ := by sorry
```
with challenge-local `abbrev D := (m : ℕ) × ((Fin m → Bool) → Bool)`, `abbrev E := ℤ × D`, `def contractOnto M C := (M.dual ↾ C).dual`, and
`HasPackingCovering M₀ M₁ := ∃ P C S₀ S₁ I₀ I₁, Disjoint P C ∧ P ∪ C = M₀.E ∧ M₁.E = M₀.E ∧ S₀ ⊆ P ∧ S₁ ⊆ P ∧ Disjoint S₀ S₁ ∧ (M₀ ↾ P).Spanning S₀ ∧ (M₁ ↾ P).Spanning S₁ ∧ I₀ ⊆ C ∧ I₁ ⊆ C ∧ (contractOnto M₀ C).Indep I₀ ∧ (contractOnto M₁ C).Indep I₁ ∧ I₀ ∪ I₁ = C`.

**O3 Config** (`InfiniteMatroid.json`): `challenge_module=ComparatorChallenges.InfiniteMatroid`, `solution_module=OAI.Combinatorics.InfiniteMatroid.Main`, `theorem_names=[OAI.InfiniteMatroidCounterexample.main]`, `definition_names=[]`, `permitted_axioms=[propext, Quot.sound, Classical.choice]`, `enable_nanoda=false`.

**O4 Solution side.** `Main.lean` states `theorem main` with the textually identical statement and proves it (no `sorry` token in any of the 25 closure modules, comment-stripped scan). `Basic.lean` contains `D`, `E`, `contractOnto`, `HasPackingCovering` with text identical to the challenge's. Closure imports: local modules + `Mathlib` only; 0 hits for `axiom`, `native_decide`, `unsafe`, `implemented_by`, `extern`, `set_option`, `run_cmd`, `elab`, `macro`, `initialize` (text scan, not an axiom audit).

**O5 Manuscript text read** (TeX `build/` sources; numbering confirmed on rendered `paper.pdf` via `pdftotext`):
- Abstract and all of §1 Introduction (`01-introduction.tex`), §7 (`07-consequences.tex`), the first half of §6 (direct sums, bundles, double ray). **Not read:** §2–§5 (matroid axioms, filters/ultrafilter/rank, local bases, assembly of `Q`), the second half of §6, bibliography contents, the cited Bowler–Carmesin / Joó / Bowler–Geschke papers.
- **Theorem 1.1**: "In ZFC, there exist a countably infinite set E and two infinite matroids M₀,M₁ on E such that Mᵢ\* = Mᵢ on the same labelled ground set for i=0,1, and I₀∪I₁ ≠ E for every independent I₀ in M₀ and independent I₁ in M₁. The pair (M₀,M₁) has no packing/covering partition. Consequently, the infinite matroid packing/covering conjecture is false."
- **Corollary 1.2**: the same pair consists of partitional matroids and does not satisfy intersection; hence the unrestricted infinite Matroid Intersection Conjecture is false in ZFC; negative answer to Joó's Question 1.5. Proof cites Bowler–Carmesin Prop. 3.6 (intersection of (M,N) ⇔ packing/covering of (M,N\*)).
- §1 also claims the examples are neither finitary nor cofinitary (no nonempty finitary/cofinitary direct summand, shown in §6).
- **Corollary (§7, `cor:separate-covering-packing`)**: the separate Covering and Packing conjectures are false, *via Bowler–Carmesin's universal equivalences, without exhibiting witnessing families*.
- The paper's definition of packing/covering partition: partition E = P ⊔ C with S_i ⊆ P pairwise disjoint, cl_{M_i↾P}(S_i)=P, I_i independent in M_i.C (:= M_i/(E∖C) = ((M_i)\*↾C)\*), ⋃ I_i = C.

**O6 Mathlib at the pinned rev** (read in `Mathlib/Combinatorics/Matroid/{Basic,Closure,Dual}.lean` @ `d13f23b`): `Matroid α` is a ground set + `IsBase`/`Indep` with `exists_isBase`, `isBase_exchange`, and `maximality : ∀ X ⊆ E, ExistsMaximalSubsetProperty Indep X`; `Matroid.dual` via bases disjoint from independent sets; `Spanning M S` = `S ⊆ E ∧ closure S = E`.

**O7 Statement-level coverage in Lean of the paper's claims** (`grep`/read): `finitary` occurs in no file of `OAI/Combinatorics/InfiniteMatroid/`; `IsPartitional`, `IsUniform`, `HasIntersection`, `CoveringConjectureFor`, `PackingConjectureFor` occur only in the *Corollaries* challenge (`InfiniteMatroidCorollaries.lean`), not in `InfiniteMatroid.lean`.

---
## MACHINE-ENFORCED BINDINGS
(Enforced if and only if Comparator is run under its stated trust assumptions; **none has been run**, so none is currently *evidenced*.)
| Link | Mechanism | State |
|---|---|---|
| challenge theorem ↔ solution theorem (same statement, same constants it depends on) | Comparator compares exported kernel terms (`compareAt`) | N (not run) |
| solution proof checked by kernel; axioms ⊆ `permitted_axioms` | Lean kernel + Comparator axiom check | N |
| config → challenge/solution module names, theorem name | Comparator reads `InfiniteMatroid.json` | consistency checked by Stage A (S4/S5/S6); enforcement N |
| bytes frozen | sha256 in lock; Stage A | **demonstrated for provenance only**: `evidence/stage_a/stage_a_baseline.json` (83 checks pass); 12/12 one-byte mutations, deletion, injected patch, moved HEAD, and two forged-lock cases detected (`tamper_tests.json`); one *limit* case (T17: consistent forged lock) not detectable by design |
`definition_names` is empty: all definitions are ordinary (non-hole) definitions; whether Comparator compares them structurally through the theorem's dependency closure rather than by name is N (not read in Comparator's source).

---
## METADATA/PROSE BINDINGS
| Link | Where | What it actually is |
|---|---|---|
| family 185 → manuscript | `CONTENTS.md` | Markdown entry; 1 manuscript; hyperlink. Stage A S1 checks the strings exist. |
| manuscript → challenge file | `lean/docs/185.md` "Comparator links" | human text; relative links to `InfiniteMatroid.lean` and `InfiniteMatroidCorollaries.lean`; no theorem name, no hash. Stage A S2 checks the links exist. |
| manuscript ↔ `formalization.yaml` | **absent** | `main_results` entry has only `comparator_config`, `declaration`, `file`; `sources[]` lists the paper separately; `review.status: unchecked`, `automation: agent`. Stage A S3 checks yaml ↔ config only. |
| paper.pdf ↔ `build/*.tex` | **absent** | nothing ties the PDF bytes to the TeX sources (reproducible-build flags like `\pdfinfoomitdate` are in the preamble; a rebuild was not attempted: N). |
| docs scope text ↔ formal statement | prose | e.g. docs/185 says "constructs two self-dual partitional matroids … admit neither an independent covering nor a packing/covering partition … also refutes the intersection conjecture": the first Lean statement (`main`) covers only self-duality and the covering/packing failures; partitional and intersection are in the *adjacent* unit. |

---
## DERIVED
**D1 Correspondence of Theorem 1.1 to `main` (by reading; semantic equivalence NOT asserted).**
| Manuscript | Lean `main` | Relation |
|---|---|---|
| ∃ countably infinite set E | fixed concrete `E = ℤ × D`; `Countable E ∧ Infinite E` | Lean is a specific witness type; implies the existential. |
| two infinite matroids M₀,M₁ on E | `∃ M₀ M₁ : Matroid E, M₀.E = univ ∧ M₁.E = univ` | Mathlib `Matroid` has the BDKPW base-exchange + maximality-on-every-subset axioms (O6); equality with the paper's independence-axiom definition is a standard theorem, not checked here. |
| Mᵢ\* = Mᵢ on the same labelled ground set | `Mᵢ.dual = Mᵢ` | direct. Mathlib duality via bases (O6). |
| I₀∪I₁ ≠ E for all independent I₀, I₁ | same `∀ I₀ I₁, … ≠ Set.univ` | direct. |
| no packing/covering partition for (M₀,M₁) | `¬ HasPackingCovering M₀ M₁` | clause-by-clause transcription of the paper's definition for Θ={0,1}, with `M.C := (M.dual ↾ C).dual` matching `((M\*)↾C)\*` and `Spanning S` matching `cl(S)=P` inside `M↾P`. One extra explicit `M₁.E = M₀.E`. I find no mismatch; this is my reading, not a proof of equivalence. |
| "consequently the conjecture is false" | **not a Lean statement** | follows only if the Bowler–Carmesin conjecture (family-indexed, Θ arbitrary) is exactly "every family has such a partition", then a 2-element family is an instance. External paper not read. |
| "in ZFC" | Lean kernel with `propext`, `Quot.sound`, `Classical.choice` | Lean's logic (dependent type theory + these axioms) is not ZFC; passing from a Lean theorem to a ZFC theorem is the usual informal metatheoretic step, not machine-checked here. |

**D2 What `main` does *not* cover of the manuscript's headline claims:** (i) partitional (Cor. 1.2) ; (ii) failure of intersection (Cor. 1.2) ; (iii) answer to Joó's question ; (iv) not finitary / not cofinitary ; (v) §7 separate Covering/Packing corollary ; (vi) "this disproves the conjecture". Of these, (i),(ii),(v) have Lean statements only in the adjacent *Corollaries* unit (not frozen here); (iii),(iv),(vi) are not stated formally anywhere in the family's Lean (O7).

**D3 Lean accepts a proof of the *statement*, not the manuscript's proof.** The Lean module names (`Ideals`, `OrdinalRank`, `Interpolation`, `RankDescent`, `Columns`, …) suggest a development related to the paper's construction, but nothing binds individual Lean lemmas to paper sections, and a kernel-checked proof of `main` would remain valid even if the paper's own argument had a gap. Conversely, it would not verify any of the paper's prose reasoning. "Verifies the manuscript result" can therefore only mean "the manuscript's *stated theorem* is (a faithful reading of) a Lean-proved statement".

**D4 Inference ladder required before any sentence of the form "this verifies the manuscript result":**
1. Provenance: the checked bytes are the frozen upstream bytes (Stage A: demonstrated for bytes).
2. Lean build and Comparator acceptance under a stated environment (Stages B, C: not executed).
3. Rejection of controlled mutations (Stage D: not executed).
4. Mathlib `Matroid`/`dual`/`↾`/`Spanning` faithfully formalize the notions in the paper (human audit; D1 is a first pass).
5. `HasPackingCovering` ⇔ the paper's / Bowler–Carmesin's packing/covering partition for a two-element family (human audit).
6. Theorem 1.1's conjunction ⇔ `main` (D1 table; the "consequently…" sentence requires external-literature steps).
7. The Lean foundation → ZFC transfer.
8. Independence of the environment from the producer (profiles; Comparator unpinned upstream).
Steps 1 is demonstrated; 2–3 are executable-but-unexecuted; 4–8 are not machine-checkable by this pipeline. **P10 adjudication is where 4–8 are weighed; it is outside this repository's bootstrap.**

**D5 Binding strength summary.** Only the segment *challenge → solution → kernel* is machine-enforced (conditionally). The segments *catalogue → manuscript → docs → challenge* and *yaml → manuscript* are prose/metadata. Upstream offers no mechanism that fails when the prose and the Lean statement drift apart.

---
## NOT DEMONSTRATED
- Any Lean build, Comparator acceptance, kernel acceptance, or tamper rejection of this subject. Gates B, C, D: **NOT EXECUTED / ENVIRONMENT BLOCKED** (see below).
- The exact verifier implementation used upstream (`evidence/discovery/comparator_provenance.md`).
- That Comparator/lean4export at the P10 pins compile and run under `leanprover/lean4:v4.34.1`.
- That `paper.pdf` is the compilation of `build/*.tex`.
- That Mathlib's definitions at `d13f23b` match the paper's notions (D1 is my reading; Mathlib source read only for `Matroid`, `dual`, `Spanning`; `↾`/`closure` semantics not read).
- That the paper's proof (§§2–6) is correct; §§2–5 were not read.
- That the Bowler–Carmesin conjectures are exactly as paraphrased in the paper's introduction.
- Whether `lake update` is deterministic w.r.t. the 12 inherited branch-tracking pins.
- Any claim about novelty, priority, or the rest of the catalogue.

---
## OPEN RISKS
1. **Statement drift risk (high, unmitigated by upstream).** Docs/yaml/CONTENTS are prose; if a challenge were edited to something weaker, Comparator would still pass against the (equally edited) solution. Only the frozen hash + human audit of E5 catches that. Stage A T17 shows this limit explicitly.
2. **Trust in challenge definitions.** The statement's meaning rests on 4 challenge-local definitions (`D`, `E`, `contractOnto`, `HasPackingCovering`) plus Mathlib. A subtle mismatch with the paper (e.g. in `Spanning`/`↾`) would make `main` true but off-target; Comparator cannot detect that.
3. **Headline vs. unit mismatch.** The manuscript headlines include corollaries that sit in a *different* Comparator unit. A report that says "family 185 verified" from `InfiniteMatroid` alone would over-claim.
4. **Verifier identity.** Upstream's Comparator/lean4export/landrun revisions unrecoverable; the P10 profile is a new environment and must always be labelled as independent verification, never reproduction.
5. **Tool/toolchain skew.** No Comparator/lean4export revision targets v4.34.1; P10 pins use a toolchain override that is untested.
6. **Environment/mutability.** `lakefile.lean` executes code at configuration time; 23 patches (11 via config-time `run_cmd`, 12 only via `lake update`'s `post_update`); Mathlib cache and toolchain archive unpinned by hash (dependency_provenance.md).
7. **Order-of-operations hazard.** Compiling the solution outside the sandbox before Comparator violates Comparator's assumption 2; the harness uses separate workspaces and runs C first. Untested.
8. **Execution blockers on the intended machine.** See "Blockers" in `evidence/stage_bcd/` (disk, missing tools, non-root, network).
9. **Moving upstream.** `main` may change ("we will continue to update"); the pin protects the evidence, not future relevance.
