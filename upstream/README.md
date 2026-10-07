# upstream/

Holds the **pinned, read-only, sparse** checkout of `https://github.com/openai/math`
at `upstream/openai-math/` (git-ignored; never vendored into this repository).

    scripts/fetch_upstream.sh          # pinned sparse fetch; verifies HEAD == PIN, exits non-zero otherwise
    FULL=1 scripts/fetch_upstream.sh   # whole tree (~3 GB, ~133k files); only needed for --inventory

Pin: `adc7f1241b42e322a6451854ab7e4b4c146bf78a` (see `subject.lock.json`).
The sparse checkout contains the metadata, Comparator configs, docs, and the Lean/manuscript
directories of the five candidates in `candidate_results.md` only.
Never edit files in the checkout; `scripts/reproduce.sh` stage A detects any divergence by SHA-256.
