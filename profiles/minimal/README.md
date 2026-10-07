# profiles/minimal — P10-authored workspace for InfiniteMatroid

Two files, both authored by P10 (this repository), neither an upstream artifact:
- `lakefile.toml` — declares Mathlib (same rev as upstream's manifest) and the two libraries needed (`OAI` limited to the
  InfiniteMatroid directory, `ComparatorChallenges` limited to the InfiniteMatroid challenge).
- `lake-manifest.json` — the 9 upstream manifest entries for `mathlib` and its 8 inherited packages, copied unchanged.

The distinction this encodes (a pilot result):
  OpenAI repository dependency universe: 30 direct + 12 inherited Lake packages, 23 compatibility patches.
  InfiniteMatroid verification dependency closure: local `OAI.Combinatorics.InfiniteMatroid.*` modules + Mathlib (+ Mathlib's own 8 packages).
Trust: `scripts/p10_run.py` (`profile_check()`, run at the start of every stage) checks that every manifest entry equals the
corresponding entry in the frozen upstream manifest and that the lakefile's Mathlib rev equals the manifest's; `verify_ws()` re-hashes
the workspace copies against these repository files after each run. These two files are NOT yet hashed into `subject.lock.json`
(Stage A does not cover them) — they are P10-controlled artifacts whose sha256 is recorded in each stage result. The lakefile is simple enough to read in full; Comparator's
assumption 1 (trustworthy lakefile) is therefore auditable by hand.
