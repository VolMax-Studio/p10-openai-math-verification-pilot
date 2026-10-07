# p10-openai-math-verification-pilot

This repository is an experimental P10 verification pilot over one result from the OpenAI Mathematics catalogue. Its purpose is not to re-prove the entire manuscript, but to establish a reproducible evidence chain showing exactly which formal claim was checked, under which toolchain and dependencies, against which upstream artifact, and what remains outside the verified boundary.

**Lean acceptance is evidence about a formal statement. It is not, by itself, evidence that every claim in the associated manuscript has been independently verified.**

## Status

Bootstrap only. No subject has been selected, nothing has been built, and no claim of independent verification is made.
`subject.lock.json` pins the upstream commit and records candidate file hashes; `selected_candidate` is `null`
until the ratifier (Ivan) chooses. `scripts/reproduce.sh` fails closed (exit 3) while no subject is selected.

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
| `candidate_results.md` | candidate pilot subjects with evidence (no selection made) |
| `subject.lock.json` | machine-readable provenance pin (selected subject currently `null`) |
| `scripts/` | `fetch_upstream.sh`, `inspect_candidates.sh`(+`.py`), `reproduce.sh`, `clean.sh` |
| `evidence/` | generated observations (`evidence/README.md`) |
| `reports/` | reserved for post-evidence reports |
| `upstream/` | pinned sparse checkout location (git-ignored) |

## Quick start (read-only)

```sh
scripts/fetch_upstream.sh        # pinned sparse fetch of openai/math
scripts/inspect_candidates.sh    # regenerate evidence/discovery/*.json
scripts/reproduce.sh             # fail-closed; currently exits 3 (no subject selected)
```

License: Apache-2.0 (same text as upstream's `LICENSE`; placeholder pending the owner's decision). Upstream content is not redistributed here.
