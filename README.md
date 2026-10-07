# p10-openai-math-verification-pilot

This repository is an experimental P10 verification pilot over one result from the OpenAI Mathematics catalogue. Its purpose is not to re-prove the entire manuscript, but to establish a reproducible evidence chain showing exactly which formal claim was checked, under which toolchain and dependencies, against which upstream artifact, and what remains outside the verified boundary.

**Lean acceptance is evidence about a formal statement. It is not, by itself, evidence that every claim in the associated manuscript has been independently verified.**

## Status

Bootstrap only. **Subject selected by the ratifier (Ivan), 2026-10-07: `InfiniteMatroid`** (openai/math family 185),
frozen in `subject.lock.json` at upstream commit `adc7f1241b42e322a6451854ab7e4b4c146bf78a`.
Only **Gate A (provenance of bytes)** has been executed. Lean build, Comparator, and tamper-rejection gates are
implemented but **not executed** (environment blocked). **No verification verdict exists, and none is claimed.**
`scripts/reproduce.sh` reports each gate separately (PASS / FAIL / NOT EXECUTED / ENVIRONMENT BLOCKED); unexecuted
or blocked gates are never success.

Two profiles are kept apart (`profiles/README.md`): **UPSTREAM AS-IS** (what openai/math lets us reproduce) and
**P10 FROZEN PROFILE** (what P10 had to add so an independent claim is auditable). The difference is a finding.

## Non-goals

This pilot does **not**:

- assess all 722 manuscripts;
- claim independent verification before the evidence exists;
- replace mathematical peer review;
- replace Lean Comparator (it is used as one evidence-producing verifier, not reimplemented);
- make novelty or priority claims;
- issue a P10 verdict during bootstrap.

## Evidence chain (architecture)

```
OpenAI manuscript
       ↓
formalization mapping / bridge        (lean/docs/NNN.md, lean/formalization.yaml)
       ↓
Lean statement + solution             (ComparatorChallenges/X.lean  /  OAI/**/Y.lean)
       ↓
Comparator / Lean kernel evidence     (ComparatorChallenges/X.json)
       ↓
reproducibility + provenance evidence (pinned commit, SHA-256, toolchain, dependency pins)
       ↓
P10 adjudication layer                (NOT part of this repository's bootstrap)
```

Each arrow is a place where a gap can hide; the pilot's job is to measure them, not to assume them closed.

## Evidence discipline

Every factual observation about upstream is traceable to an exact path, an exact commit, a command output, or a hash.
Documents separate **OBSERVED**, **DERIVED**, and **NOT DEMONSTRATED**; speculative conclusions are not written as findings.

## Layout

| Path | Purpose |
|---|---|
| `SUBJECT.md` | what upstream is, what was observed about its verification architecture |
| `SCOPE.md` | what this pilot will and will not establish |
| `candidate_results.md` | the five candidates examined; selection recorded (InfiniteMatroid) |
| `subject.lock.json` | frozen binding chain: role, path, sha256, identifier, commit, enforcement kind per element |
| `profiles/` | UPSTREAM AS-IS vs P10 FROZEN PROFILE; verifier pins |
| `scripts/` | `fetch_upstream.sh`, `inspect_candidates.*`, `build_lock.py`, `stage_a.py`, `tamper_tests.py`, `gates.py`, `reproduce.sh`, `selftest_harness.sh`, `check_dependency_patches.sh`, `clean.sh` |
| `evidence/` | generated observations and gate results (`evidence/README.md`) |
| `reports/` | `infinite_matroid_binding.md`: what the machinery can and cannot establish |
| `upstream/` | pinned sparse checkout location (git-ignored) |

## Quick start (read-only)

```sh
scripts/fetch_upstream.sh        # pinned sparse fetch of openai/math
scripts/inspect_candidates.sh    # regenerate evidence/discovery/*.json
scripts/reproduce.sh             # gates A..E; today: A PASS (provenance only), B/C/D ENVIRONMENT_BLOCKED, exit 6
```

## License

Original code/documents here: Apache-2.0 (placeholder pending the owner's confirmation). **Upstream OpenAI, Lean,
Mathlib, Comparator and other third-party artifacts remain under their respective original licenses and are not
relicensed by this repository.** Upstream content is not redistributed here; see `NOTICE`.
