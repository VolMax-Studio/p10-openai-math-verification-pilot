# evidence/

Machine-generated or verbatim-captured observations. Nothing here is a verdict.

| Path | Produced by | Content |
|---|---|---|
| `discovery/upstream_facts.json` | `scripts/inspect_candidates.sh` | upstream commit, toolchain, 42 dependency pins, counts, yaml-vs-config mismatches, hashes of metadata files |
| `discovery/candidates.json` | same | for each of 5 candidates: config, declarations, docs/family bindings, import-closure stats, text scan, SHA-256 of every bound file |
| `discovery/challenge_inventory.json` | same, against a FULL checkout | closure size / external packages for all 405 Comparator configs |
| `discovery/environment_probe.txt` | captured by hand from command output | Comparator/lean4export/landrun heads, sandbox tooling/network observations |

Labels used across this repository: **OBSERVED** (traceable to path+commit, command output, or hash),
**DERIVED** (computed or inferred from OBSERVED items; method stated), **NOT DEMONSTRATED**.
`challenge_inventory.json` was generated from a full shallow clone at the pinned SHA (outside this repo);
`candidates.json` was verified byte-identical between the full and the sparse checkout.

| Path (added 2026-10-07, second pass) | Produced by | Content |
|---|---|---|
| `discovery/comparator_provenance.md` | hand-written from git queries | Comparator/lean4export/landrun timeline and pins |
| `discovery/dependency_provenance.md` | hand-written + scripts | pin consistency, patches, mutability, network inventory |
| `discovery/dependency_patch_check.tsv`, `dependency_table.md` | `scripts/check_dependency_patches.sh`, `render_dependency_table.py` | 23 patch hashes + `git apply --check` against pinned revs; 42-package table |
| `stage_a/stage_a_baseline.json` | `scripts/stage_a.py --json` | 83 provenance checks |
| `stage_a/tamper_tests.json` | `scripts/tamper_tests.py` | 19 mutation tests on a temporary copy |
| `stage_bcd/*.json` | `scripts/reproduce.sh` | real (non-stub) gate outcomes per host: ENVIRONMENT_BLOCKED with reasons |
