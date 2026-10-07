# SUBJECT

Upstream: `https://github.com/openai/math`, commit `adc7f1241b42e322a6451854ab7e4b4c146bf78a`
(commit date 2026-10-06T14:58:50-07:00, subject line "Initial commit"; history depth not examined).
Retrieved 2026-10-07 (UTC). Selected result: **none** (see `candidate_results.md`).

Labels: **O** = OBSERVED (path @ commit, command output, or hash), **D** = DERIVED (method stated), **N** = NOT DEMONSTRATED.
Machine-readable backing: `evidence/discovery/*.json`.

## 1. What upstream contains
- **O** `README.md`: 722 manuscripts in 372 families; "results at different stages of verification. Not all have accompanying Lean formalizations"; "Some of the unformalized results could have issues."
- **O** `CONTENTS.md` parsed by `scripts/inspect_candidates.py`: 372 families, 722 distinct manuscript directories (matches README).
- **O** `preprints/<Title-Date>/{paper.pdf,README.md,build/}`: manuscripts; `build/` holds TeX sources.
- **O** `lean/`: one Lake package `OAI`, 121,734 `.lean` files under `lean/OAI` (full clone), `ComparatorChallenges/` with 405 `*.json` configs + 405 `*.lean` challenge files, `docs/` (235 files), `patches/` (23 `*-lean4341.patch`).

## 2. Toolchain and dependencies (all O, `lean/`)
- `lean-toolchain`: `leanprover/lean4:v4.34.1`; lakefile `fixedToolchain := true`, `autoImplicit false`.
- `lakefile.lean`: 30 direct `require ... @ "<40-hex sha>"`; `lake-manifest.json`: 42 packages (12 inherited). Mathlib pinned at `d13f23b723b8a846827a245b89c10fc7d3f11612`. 11 dependencies are from the `lana-agents` GitHub org.
- **O** `lakefile.lean` contains `run_cmd` (git clone + `git apply` of compatibility patches into `.lake/packages/` *at configuration time*) and a `post_update` hook applying further patches. Lake therefore executes upstream code with network/git/filesystem effects before any build.

## 3. Verification architecture as documented
- **O** `lean/ComparatorChallenges/README.md`: install `comparator`, `landrun`, `lean4export` on `PATH`; then `lake update; lake exe cache get; lake env comparator ComparatorChallenges/<X>.json`. **No versions or commits of comparator/landrun/lean4export are given anywhere in the repository** (grep over non-`OAI`/non-`preprints` files).
- **O** Config schema (`ComparatorChallenges/X.json`): `challenge_module`, `solution_module`, `theorem_names[]`, `definition_names[]` (optional), `permitted_axioms[]` (all 405 permit only `propext`, `Quot.sound`, `Classical.choice`), `enable_nanoda` (absent in 2 configs, `true` in 1 [`ArtinParabolicIntersections`], `false` in 402), and one config (`SymmetricMahlerEquality`) has an extra `solution_imports` key. Challenge `X.lean` states the theorem with `sorry`; the solution module lives in `OAI/**`.
- **O** `lean/formalization.yaml` (v0.4): `sources` (162 papers, by `id: ../preprints/.../paper.pdf`), `related_formalizations`, `status.main_results` (185 entries, each only `{comparator_config, declaration, file}`), `automation.methods: [agent]`, `review.status: unchecked`, `status.scope: "Partial progress."`.
- **O** `lean/docs/NNN.md` (235 files): prose "Scope" + "Comparator links" table linking `../ComparatorChallenges/*.lean` and the paper PDF(s). All 405 configs are linked from some docs file; 218 distinct manuscripts are linked.

## 4. Binding chain, and where each link is (not) machine-checkable
| Link | Mechanism | Strength |
|---|---|---|
| family -> manuscripts | `CONTENTS.md` ("[Lean](lean/docs/NNN.md)") | O: prose + hyperlink; no hash |
| manuscript -> challenge statement | `lean/docs/NNN.md` links (paper path, challenge `.lean` path) | O: hyperlinks in prose; no hash, no declaration name |
| manuscript -> `formalization.yaml` | **none**: `main_results` entries carry no source/manuscript field (`yaml_main_results_have_source_field=false`) | O: absent |
| challenge -> solution -> theorem | `X.json` (`challenge_module`, `solution_module`, `theorem_names`) | O: machine-readable |
| yaml -> config | `comparator_config` + `declaration` + `file` | O: consistent except 23 entries whose `file` differs from the config's `solution_module` path (`upstream_facts.json: yaml_vs_config_mismatches`) |
| config coverage | 178 of 405 configs referenced by `main_results`; 227 are not | O |
| statement -> informal claim | docs "Scope" prose written by upstream | O: prose; faithfulness N |

D: the only machine-checkable part of the chain is challenge -> solution -> kernel. Everything upstream of the challenge statement is human-readable prose written by the producer, and `review.status` is `unchecked`.

## 5. Comparator and tooling (O, see `evidence/discovery/environment_probe.txt`)
- Comparator HEAD `ca04cfc72b550331658ec314bf47685281bfd4bf`, lean4export HEAD `05d43a2bc773b40ecfdebb32294192a5ef756951`, landrun HEAD `811cfff51ceaf3d9843708aa6d22e9b84ccac8b4`. Comparator and lean4export default branches target `v4.35.0-rc4`; the project targets `v4.34.1`. N: which revisions are compatible with v4.34.1.
- N: whether `definition_names: []` / absent is sufficient for the definitions inside each challenge (Comparator's `compareAt` receives the targets and `definitionNames`; its exact semantics for non-hole definitions were not read in this bootstrap).

## 6. Hermeticity blockers (O unless marked)
1. Comparator/lean4export/landrun unpinned upstream; version skew with project toolchain (above).
2. `lakefile.lean` executes patch-and-clone logic at configuration time; Comparator's own trust assumption 1 requires the lakefile to be trustworthy.
3. 23 third-party compatibility patches applied to dependency checkouts (patched code != the pinned dependency commits).
4. README instructs `lake update`, not a build against the committed manifest; D: may re-resolve; N: whether it can drift from `lake-manifest.json`.
5. Mathlib build artifacts come from an external cache (`lake exe cache get`); Comparator permits this only if the cache is trusted.
6. Comparator needs `landrun` (Landlock) and `systemd-run --user`; N: availability in the target environment.
7. Upstream is a moving target ("We will continue to update"); the pin is a single SHA.
8. This sandbox has no Lean/elan; Mathlib cache and release.lean-lang.org were not reachable. **Nothing was built.**
