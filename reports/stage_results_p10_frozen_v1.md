# Stage results — profile `p10-frozen-v1`, subject `InfiniteMatroid`

**No overall verdict is issued.** Four independent gate results follow. None of them is, or implies, `Verified`.
Local only: nothing was pushed, tagged, released, signed, or opened as a PR. Ivan remains the final ratifier.

Claims kept separate:

| claim | status |
|---|---|
| reproduce upstream's verification environment (`upstream-as-is`) | **NOT DEMONSTRATED** — upstream's exact verifier revisions are not recoverable (see `evidence/discovery/comparator_provenance.md`); not reconstructed |
| independently verify in a newly pinned environment (`p10-frozen-v1`) | gates below |

## Gate table (each reported on its own)

| gate | status | what it establishes | what it does not |
|---|---|---|---|
| A PROVENANCE | **PASS** (device and sandbox; 25/25 tamper tests as expected, run in the sandbox only) | the files under test are exactly the bytes of upstream commit `adc7f12…`; expected hashes are derived from that commit, not from the lock | nothing about mathematics |
| C COMPARATOR | **PASS** | Comparator (3 pinned tool commits, Lean v4.34.1) accepted `OAI.InfiniteMatroidCounterexample.main` from `OAI.Combinatorics.InfiniteMatroid.Main` against the sorry-challenge `ComparatorChallenges/InfiniteMatroid.lean`, axioms ⊆ {propext, Quot.sound, Classical.choice}, Lean default kernel accepted ("Your solution is okay!") | that the challenge statement formalizes Theorem 1.1 |
| B LEAN BUILD | **PASS** | fresh workspace, plain `lake build OAI ComparatorChallenges`: rc 0, no `sorry` in the solution closure, `#print axioms` = [propext, Classical.choice, Quot.sound] | same as C; shares the Mathlib cache download with C (see below) |
| D NEGATIVE CONTROLS | **PASS** with stated caveats | 4 mutations rejected by Comparator for the intended reason, 1 provenance mismatch caught by P10's own check, control PASS before and after | breadth: 5 mutations are not a mutation-testing campaign |

## Environment (identical for C, B, D unless noted)

- Device: HP, Linux 7.0.0-34 (< 7.1, so the README's `systemd-run … RestrictAddressFamilies=~AF_UNIX` guard was used), uid 1000, Landlock present in LSM list.
- Lean `4.34.1` (commit `5045d0056413266e57c625dcd7c365b10e377c52`), Lake 5.0.0; elan 4.2.4 (archive sha256 `42b94d42…1f63`), Go 1.24.13 (sha256 `1fc94b57…d730`, fetched from go.dev's published list).
- Tool commits (full SHAs, `git status` clean after build, **no tool source modified, no compatibility patch needed**):
  - comparator `d03acab154d269c06e60e4de7e4cc85deebff94b`, binary sha256 `afa65e57…e4a2`
  - lean4export `076e8e57707e813375e8f9da8bf989799ace9680`, binary sha256 `8c5d64ba…ddd1`
  - landrun `811cfff51ceaf3d9843708aa6d22e9b84ccac8b4`, binary sha256 `0fbdfcb1…e4a`
  All three built against Lean v4.34.1 although none of them targets it officially (they are the v4.34.0-toolchain revisions). Build logs and exact commands: `evidence/tools/`.
- Private prefix `p10-tools/` (own `ELAN_HOME`); `~/.elan` (a dangling symlink to an unrelated project) was not touched.
- Challenge / solution / config identity (from frozen git objects; hashes re-checked in each stage result):
  - challenge `lean/ComparatorChallenges/InfiniteMatroid.lean` sha256 `802e9bf6…ae3a7`
  - config `lean/ComparatorChallenges/InfiniteMatroid.json` sha256 `8d565944…3b82`
  - solution `lean/OAI/Combinatorics/InfiniteMatroid/Main.lean` sha256 `4c47af8f…b25b` (+ closure, hashed in `subject.lock.json`)
- Network: needed for git clones of Mathlib and 8 packages (manifest pins), the Mathlib cache, the elan toolchain download. IPv6 was unreachable and DNS flaked once (landrun's first `go build` and elan's first download failed; both recorded in `evidence/tools/logs/*attempt1.err` and succeeded on retry without any change).

## Disk / resource observations

- Free space on `/`: 37 GiB at start, 33 GiB after all stages. A full workspace is ≈ 7.7–7.9 GiB (cloned packages ≈ 1 GiB + unpacked Mathlib oleans), plus ≈ 0.9 GiB shared cache in `~/.cache/mathlib`, plus ≈ 4.5 GiB `p10-tools` in total (elan toolchain, Go, clones, build output).
- Order executed: A → C → evidence committed → C workspace deleted → B (fresh workspace, fresh clone) → evidence committed → B workspace deleted → D (fresh workspace) → deleted. At most one workspace existed at any time. `p10-ws/` is empty now.
- Mathlib cache was downloaded for C; B and D re-ran `lake exe cache get` and received the same files from `~/.cache/mathlib` (a download cache, not a build tree). **B did not reuse C's build outputs**, but B is not independent of the Mathlib cache provider. Cache contents are trusted per Comparator README ("running `lake exe cache get` is acceptable if you trust the cache").
- Memory was tight on the machine (≈ 1–9 GiB available, swap in use) because of the user's other applications; runs used `nice`; no OOM occurred.
- Wall time (device): C comparator run 134 s; B build 103 s (+158 s cache); D control ≈ 129 s, each mutated run 25–60 s.

## Dependency scope

- OpenAI repository dependency universe: 30 direct + 12 inherited Lake packages (42 manifest entries), 23 compatibility patches.
- InfiniteMatroid verification dependency closure: local `OAI.Combinatorics.InfiniteMatroid.*` modules + Mathlib (and Mathlib's own 8 packages). **Demonstrated, not assumed:** Stage A (A3) shows no external import outside Mathlib in the closure; stages B/C/D then built and checked it in a workspace that contains only those 9 manifest entries (`profiles/minimal/`). No `lake update`; Mathlib rev `d13f23b723b8a846827a245b89c10fc7d3f11612` checked out by Lake from the manifest pin in all three workspaces.
- The two P10-authored files (`profiles/minimal/lakefile.toml`, `lake-manifest.json`) are **not yet hashed into `subject.lock.json`**; their sha256 is recorded per stage. Stages B and C ran with `lakefile.toml` sha256 `fcccc85f…2023` (identical manifest `fc1c3ed8…8eb4`); afterwards one comment line in the lakefile was edited (it wrongly said "checked by Stage A R4"), giving sha256 `2d1fcec6…9f9a`, which the D rerun used. The change is a comment only; it is recorded here rather than hidden. `profile_check()` (manifest entries == frozen upstream entries; lakefile rev == manifest rev == lock rev) passes.

## Stage D detail

Control before: PASS (rc 0, 129 s). Control after restoring every file and re-hashing: PASS (rc 0).

| id | mutation (disposable workspace only) | Comparator rc | reason, from the tool's own output |
|---|---|---|---|
| D1 | challenge theorem statement changed (`≠` → `=`) | 1 | `Challenge and solution theorem statement do not match: 'OAI.InfiniteMatroidCounterexample.main'` |
| D2 | solution: proof of `main` replaced by `sorry` | 1 | `Illegal axiom detected: 'sorryAx'` |
| D3 | challenge↔solution binding: config names a declaration the solution lacks | 1 | lean4export `PANIC … Constant OAI.InfiniteMatroidCounterexample.nonexistent not found in environment` — rejected, but by a crash of the exporter, not by a clean diagnostic |
| D5 v1 | injected axiom, edit left the proof malformed | 1 | `error: … No goals to be solved` — **not a valid axiom test**: rejected by an elaboration error. Kept in `evidence/stage_d_run1/`, superseded |
| D5b | solution proves `main` from injected `axiom p10_bad : False` (elaborates) | 1 | `Illegal axiom detected: 'OAI.InfiniteMatroidCounterexample.p10_bad'` (separate rerun, `evidence/stage_d/`, with its own control after) |
| D4 | Mathlib rev in the workspace manifest altered by one hex digit | n/a | detected by **P10's** `verify_ws()` (hash vs repository profile). This tests P10's check, not Lake or Comparator; Lake was not asked what it would do with a mismatched manifest. |

Honest limits: D1 modifies the *trusted* challenge file, which is exactly why a mismatch is reported; it demonstrates the statement-binding check, not resistance to a malicious challenge. No mutation tested a dependency-source change (e.g. a modified Mathlib file) — that is covered only by trusting the git pin and the cache.

## What the gates still leave open (the remaining epistemic boundary)

Everything above concerns **Lean `main`** — i.e. the statement of `OAI.InfiniteMatroidCounterexample.main`:
`E` countable and infinite, matroids `M₀ M₁` on `E` with `E = univ`, both self-dual (`M.dual = M`), no pair of independent sets covering `univ` (`I₀ ∪ I₁ ≠ univ`), and `¬ HasPackingCovering M₀ M₁` where `HasPackingCovering` is defined locally in the challenge file via `contractOnto`, `Spanning`, `Indep` from Mathlib (`d13f23b…`).

It is **not** shown here that this is a faithful formalization of the manuscript's **Theorem 1.1** (informal claim, `preprints/…/`). By my reading of the abstract, §1, §7 and the first half of §6 (§2–5 not read) the clause-by-clause textual match is plausible, but it is a reading, not a proof. Specifically *not* in `main`: partitional matroids, the intersection corollaries (they live in the adjacent `InfiniteMatroidCorollaries` unit, not in the subject), "not finitary", Joó's question, the sentence "the conjecture is false", and the step from Lean's foundations to ZFC. The bridge files (`formalization.yaml`, `lean/docs/185.md`, `CONTENTS.md`) are prose/metadata, not machine-enforced. Closing this gap is a human/expert review task for the ratifier; no gate here does it.

Other boundaries: the Lean kernel, Landlock/systemd sandboxing, the Mathlib cache provider, GitHub, and Lean `4.34.1` binaries (downloaded, not built from source, and not hash-pinned by P10) are in the trusted base; the three tools were not built or tested by their authors against 4.34.1.

## Evidence index (this repository, device copy)

`evidence/tools/` (pre-install snapshot, `tool_record.txt`, commands, logs incl. failed first attempts) · `evidence/stage_c_attempt1_bus_unreachable/` (Comparator never started: no session-bus variables in the detached launcher; first misclassified as FAIL, runner fixed to report ENVIRONMENT_BLOCKED, nothing about the solution was learned or compiled) · `evidence/stage_c/` · `evidence/stage_b/` · `evidence/stage_d_run1/` · `evidence/stage_d/` (rerun D5b, `profile_check_posthoc.json`, `disk_after_all_stages.txt`). Each stage dir holds `environment_snapshot.json`, `logs/NNN.json` (argv, rc, elapsed, full stdout/stderr per command) and the result JSON.
