# Profiles: UPSTREAM AS-IS vs P10 FROZEN PROFILE

The pilot keeps two columns on purpose. We do not repair upstream; we record what upstream permits us to
reproduce and what P10 had to add so that an independent claim is auditable. The difference is itself a result.

| Aspect | UPSTREAM AS-IS (what openai/math gives) | P10 FROZEN PROFILE `p10-frozen-v1` (what P10 adds) |
|---|---|---|
| Claim type | reproduction of upstream's documented procedure | independent verification of the same challenge in a newly pinned environment |
| Upstream tree | a branch/commit of a moving repo ("will continue to update") | exact commit `adc7f12…`, sparse pinned fetch, SHA-256 for every bound file |
| Manuscript → statement binding | prose (`CONTENTS.md`, `docs/185.md`), yaml without manuscript field | same bytes frozen; relation audited by hand in `reports/infinite_matroid_binding.md`; still not machine-enforced |
| Challenge → solution binding | `X.json` consumed by Comparator | same, plus Stage A recomputes config/closure/declaration consistency |
| Lean toolchain | `lean-toolchain` = v4.34.1 (elan fetch, no archive hash) | same version; archive hash to be recorded on first fetch (not yet) |
| Dependencies | `lake update` (README); 12 patches applied only by `post_update`; 11 by config-time `run_cmd` | `lake update` forbidden; committed manifest; manifest + `.lake/packages` HEADs asserted unchanged; 23 patch hashes pinned; 23/23 shown to apply to pinned revs |
| Comparator / lean4export / landrun | "on PATH", unpinned, revisions unrecoverable | Comparator `d03acab`, lean4export `076e8e5`, landrun `811cfff` (+ toolchain override to v4.34.1 — untested) |
| Mathlib cache | `lake exe cache get`, trusted | same trust unless built from source; trust stated, not hidden |
| Gate separation | one command, one outcome | A provenance / B build / C Comparator / D tamper / E boundary, each with PASS · FAIL · NOT EXECUTED · ENVIRONMENT BLOCKED |
| Sandbox ordering | not specified | C before any unsandboxed compile of the solution; B in a separate workspace (Comparator assumption 2) |
| Network | implicit | enumerated in `evidence/discovery/dependency_provenance.md` §4 |

Machine-readable pins: `profiles/verifier_profiles.json`. Neither profile has been executed.
`upstream-as-is` is marked `executable_as_reproduction: false` because its verifier identity is `NOT DEMONSTRATED`.
