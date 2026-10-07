# CANDIDATE FOR RATIFICATION — P10 pilot, subject `InfiniteMatroid`

> **Superseded status note:** This was the candidate presented for ratification. Ratification was subsequently completed. The authoritative decision record is `RATIFICATION.md`.

**This is not `Verified`, not `Ratified`, and not a P10 verdict.** It is a frozen local evidence state offered to the ratifier (Ivan). Nothing has been pushed, tagged, released, signed, published or deployed.

- Candidate evidence commit: `1edd19c5a5694ff0e0a84ba43d9294849201cd42` (branch `claude/charming-noether-j0w6k4`, device repository; this document is committed on top of it and contains no new evidence).
- Upstream subject: `openai/math` commit `adc7f1241b42e322a6451854ab7e4b4c146bf78a`, family 185, `OAI.InfiniteMatroidCounterexample.main`.
- Profile: `p10-frozen-v1` (`profiles/verifier_profiles.json`, minimal workspace `profiles/minimal/`). Claim kept separate from `upstream-as-is`, which is NOT DEMONSTRATED (upstream's exact verifier revisions are unrecoverable).

## Gate results (final RC rerun; each reported independently)

| gate | status | evidence |
|---|---|---|
| A PROVENANCE | **PASS** — Stage A: 162 checks (CLOSURE 2, ENV 4, HASH 71, PROFILE 5, ROOT 73, STRUCT 7), tamper tests 30/30 as expected | `evidence/stage_rcfinal_a/` |
| C COMPARATOR | **PASS** — dependency pre PASS → Comparator rc 0 ("Your solution is okay!", 143.5 s) → dependency post PASS, identical state digest | `evidence/stage_rcfinal_c/` |
| B LEAN BUILD | **PASS** — dependency pre PASS → `lake build OAI ComparatorChallenges` rc 0 (106.4 s), no `sorry` in the solution closure, axioms {propext, Classical.choice, Quot.sound} → dependency post PASS, identical digest | `evidence/stage_rcfinal_b/` |
| D NEGATIVE CONTROLS | **PASS** (caveats below) | `evidence/stage_rcfinal_d/` |

Order executed: A → C → evidence committed → C workspace deleted → B (fresh workspace) → evidence committed → B workspace deleted → D (fresh workspace) → evidence committed → D workspace deleted. One large workspace at a time; `p10-ws/` is empty. Each of C/B/D cloned its dependencies from the frozen manifest (no `lake update`) and downloaded the Mathlib cache independently into its own private `MATHLIB_CACHE_DIR`.

### Dependency integrity is a P10 gate (fail-closed)
For C, B and D: `dep_state()` before any Comparator/Lean command (a FAIL stops the stage with the verifier NOT executed), and again after (a FAIL, or a changed digest, makes the stage FAIL even if the tool returned success). Recorded per package: manifest rev, actual HEAD, `HEAD^{tree}`, clean flag (no modified tracked file, no untracked non-`.lake` file), plus package-set equality with the manifest. State digest **`cd60aa529a2e8189…`** was identical in C, B and D, before and after every run.

Preserved RC finding (`evidence/stage_dep/`, earlier pass, untouched): *Lake/Comparator alone did not reject a harmless dirty Mathlib source mutation (comment appended to `Mathlib/Combinatorics/Matroid/Closure.lean`); a definition change was rejected only because Mathlib then failed to compile. P10 dependency verification is therefore required to bind execution to the frozen dependency state.*

### Stage D detail
Control PASS before (137.8 s) and after restore (28.8 s); state digest unchanged.
- D1 theorem mismatch → rejected: `Challenge and solution theorem statement do not match`.
- D2 `sorry` solution → rejected: `Illegal axiom detected: 'sorryAx'`.
- D3 nonexistent declaration → rejected **through a lean4export PANIC** (`Child exited with 134`), not a clean diagnostic.
- D5b injected illegal axiom (`p10_bad : False`) → rejected: `Illegal axiom detected: '…p10_bad'`.
- D4 dependency source mutation (Mathlib `Closure.lean`), D4b untracked `.lean` file injected into `batteries`, D4c `aesop` HEAD moved off its pin: P10 dependency pre-check **FAIL, Comparator NOT EXECUTED**, restore → clean. D4d workspace manifest rev altered: P10 profile check detected, restored. These are **P10-layer gate controls, not Comparator negative controls.**
- Earlier D evidence (`stage_d_run1/`, `stage_d/`) and the invalid first D5 (rejected by an elaboration error, not the axiom check) are kept unrewritten.

## Identities
- Tools (built from full SHAs, no source modified, `git status` clean): comparator `d03acab154d269c06e60e4de7e4cc85deebff94b` (binary sha256 `afa65e57a1770f59…`), lean4export `076e8e57707e813375e8f9da8bf989799ace9680` (`8c5d64ba68f4d3a6…`), landrun `811cfff51ceaf3d9843708aa6d22e9b84ccac8b4` (`0fbdfcb1bb379b50…`). None targets Lean 4.34.1 officially; all built and ran against it.
- Lean `4.34.1` (commit `5045d0056413266e57c625dcd7c365b10e377c52`); elan 4.2.4; Go 1.24.13 (used only to build landrun).
- Challenge `lean/ComparatorChallenges/InfiniteMatroid.lean` sha256 `802e9bf6…`, config `…InfiniteMatroid.json` `8d565944…`, solution `Main.lean` `4c47af8f…` (all re-checked after each run against the frozen blobs).
- Profile files hashed in the lock (`subject.lock.json#p10_profile`): `lakefile.toml` `2d1fcec6…`, `lake-manifest.json` `fc1c3ed8…`.
- **Lean toolchain payload:** `lean-4.34.1-linux.tar.zst` sha256 `47bf4bbd78f70c2e9670598ab7124d92b6efb7330ff33e5fbb4030f6fd72e4e4` equals the digest GitHub publishes for the asset; extracted-tree digest `a73f9239936ce77d625c3e9170c36029664ee431dcc8987ab1c0db1cc6d8c34a`, identical for the tarball and for the elan-installed toolchain. Stated precisely: *payload integrity is pinned; the same payload bytes were obtained from two sources and the installed tree equals the archive tree; reproducible build-from-source provenance of the Lean binaries is NOT demonstrated.*
- **Mathlib cache payload identity (frozen in `profiles/mathlib_cache_identity.json`):** 8908 files, 451433503 bytes, digest `51739e8da6b72d84…`. Observed first in C, then **matched by independent downloads in B and D**. This identifies the payload; it does **not** make the cache provider or the compiled artifacts trusted.

## Trusted base (stated, not reduced)
The Lean kernel and the Lean 4.34.1 binaries as released; Comparator, lean4export, landrun as built (not audited); Landlock/systemd sandboxing and Linux 7.0; the Mathlib cache provider and its compiled `.olean` content (**cached compiled artifact trust**, distinct from **dependency source integrity**, which P10 now checks: sources are git-pinned and verified clean; the compiled artifacts were not rebuilt from source); GitHub as the source of the pinned git revisions; the device and its hardware. Independent *execution* is demonstrated; independence from these components is not.

## Remaining boundary (not closed by any gate)
1. **Manuscript ↔ Lean:** `reports/manuscript_bridge_review_theorem_1_1.md` — 13 rows, sign-off block EMPTY, status NOT REVIEWED. Open rows: 3 (Mathlib matroid presentation vs BDKPW axioms), 9 (Mathlib `closure` vs manuscript `cl`), 11 ("in ZFC" vs Lean), 13 ("the conjecture is false" is not in `main`). Semantic equivalence: **Not Demonstrated**. Full manuscript correctness: **Not Demonstrated**.
2. `upstream-as-is` reproduction: **Not Demonstrated** (and not attempted).

## Known diagnostic caveats
- D3 is a crash-rejection (exporter PANIC).
- D1 edits the trusted challenge file; it shows statement binding, not resistance to a malicious challenge.
- `verify_deps` cannot see a *compiled-artifact* substitution inside the Mathlib cache (covered only by the payload digest and trust in the provider).
- Stages B/C/D share one machine and one network path; the Stage A tamper tests ran with the same scripts that are being tested.
- The first RC pass runs of B/C/D (`stage_b/`, `stage_c/`, `stage_d*/`) predate the dependency gate; they are retained as history and are superseded by `stage_rcfinal_*` for any claim.
- The sandbox copy of this repository is behind the device copy (lacks the evidence commits); the device repository is the record.

## Ratification would need (from Ivan, explicitly)
The exact claim to ratify, the reviewed bridge table, acceptance of the trusted-base statement above, and acceptance of this candidate commit (or a named later one). Suggested narrow claim, for the ratifier's edit only: *The frozen formal-verification path for `InfiniteMatroid` was independently executed under the `p10-frozen-v1` profile: provenance, Comparator, an independent Lean build, and negative controls passed, with dependency integrity enforced by P10 and the trusted base as stated; manuscript↔formal equivalence and full-manuscript correctness are not claimed.*
