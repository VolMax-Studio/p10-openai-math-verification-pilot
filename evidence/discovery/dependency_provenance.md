# Dependency mutability and network surface

All **O** unless marked. Source: `lean/lakefile.lean`, `lean/lake-manifest.json`, `lean/patches/`, `lean/README.md`,
`lean/ComparatorChallenges/README.md` at adc7f12; Mathlib/doc-gen4 manifests at their pinned revs; `dependency_table.md`;
`dependency_patch_check.tsv`.

## 1. What is pinned
- 30 direct `require … from git "<url>" @ "<40-hex sha>"` in `lakefile.lean`; all 30 equal the `rev` in `lake-manifest.json` (`stage_a.py` E3). All direct `inputRev == rev` (no branch names).
- 12 **inherited** packages (not in `lakefile.lean`) carry branch-name `inputRev`s: batteries/main, aesop/master, Qq/master, proofwidgets/main, importGraph/main, LeanSearchClient/main, plausible/main, Cli/v4.34.0, leansqlite/main, UnicodeBasic/main, BibtexQuery/master, MD4Lean/main. Their `rev`s are pinned in the manifest.
- **Cross-check (new):** the 8 inherited packages `batteries, aesop, Qq, proofwidgets, importGraph, LeanSearchClient, plausible, Cli` have *exactly* the revs in Mathlib `d13f23b`'s own `lake-manifest.json`; the other 4 (`leansqlite, UnicodeBasic, BibtexQuery, MD4Lean`) have exactly the revs in doc-gen4 `953c899`'s manifest. So the committed manifest is internally consistent with its dependencies' own manifests (no drift detected at this commit).
- Mathlib `d13f23b…` is "chore: bump toolchain to v4.34.1" (2026-09-24T22:34+02:00); its `lean-toolchain` is `leanprover/lean4:v4.34.1`, equal to upstream's.

## 2. Patches
- 23 files `lean/patches/<pkg>-lean4341.patch` (sha256 of each in `dependency_table.md` and in the lock). All 23 apply cleanly (`git apply --check`) to a fresh checkout of their pinned manifest rev (23/23 APPLIES, `dependency_patch_check.tsv`). Touched-file counts range 2–158.
- `patches/README.md`: "Run `lake update` from `lean/` to fetch dependencies and apply the patches."
- **Two distinct application mechanisms in `lakefile.lean`:**
  1. `run_cmd` (executes at *configuration time on every lakefile elaboration*, before dependency resolution) — for 11 `lana-agents` packages (`iut, tate-curves-theta, genl, heights, pi1, orbicurve-cores, oka, tempered-fundamental-groups, elliptic-curves, formal-schemes, belyi`): if `.lake/packages/<n>` is absent it `git clone --no-checkout <url>`, checks out the pinned rev, `git apply`s the patch, renames into place.
  2. `post_update` hook — for 12 packages (`fixed-point-theorems, PrimeNumberTheoremAnd, Zeta3Irrational, rellich-kondrachov, carleson, StrongPNT, AbsorptionCutoff, AINTLIB, ClassFieldTheory, schoenflies-lean, SphereEversion, gromov`): applies the patch **only when `lake update` runs**.
  - **D:** a plain `lake build` from the committed manifest does not apply the second group's patches; the "patched" state upstream describes exists only after `lake update`. Reproducing upstream's documented path therefore requires `lake update`; a manifest-only path is a *different* tree for those 12 packages. (Not exercised; reasoned from the lakefile text.)
  - None of the 23 patched packages is in the import closure of the InfiniteMatroid solution (closure imports: local modules + Mathlib only).
- The lakefile comment: "Declare shared dependencies last: Lake resolves later requirements first. These pins override the older versions in the upstream packages' manifests." — i.e. the root lakefile's pin order is load-bearing for resolution.

## 3. Configuration-time code execution and `lake update`
- `lakefile.lean` runs arbitrary Lean (`run_cmd`, `post_update`) with git/filesystem effects during configuration. Comparator's README requires the lakefile to be trustworthy (assumption 1).
- `lake update` re-resolves; for direct deps the pins are SHA-exact. For the 12 inherited, **N:** whether Lake would re-resolve them from branch tips or from the dependencies' manifests was not tested (Mathlib's lakefile `require`s `batteries @ git "main"`, so a tip-following resolution would drift; the observed equality above shows only that the committed manifest *is* the dependency-manifest state today).
- **Frozen-profile rule (p10-frozen-v1):** never run `lake update`; build from the committed manifest; after the build assert (a) `lake-manifest.json` byte-identical, (b) each `.lake/packages/<n>` HEAD == manifest rev (`gates.py: manifest_invariant`). Any change → FAIL (fail closed). Not exercised.

## 4. Network fetches a clean reproduction needs (frozen profile; every one is a mutable-world touchpoint)
| # | Purpose | Endpoint(s) | Pinned by | Residual risk |
|---|---|---|---|---|
| N1 | upstream tree | `https://github.com/openai/math` | commit sha1 (git content-addressed) | none beyond sha1 |
| N2 | Lean toolchain v4.34.1 | `release.lean-lang.org` (elan metadata), `github.com/leanprover/lean4/releases/download/v4.34.1/…` (observed: 302 → 200 for the linux tarball) | tag name only; **no hash recorded** | mutable release asset; record sha256 on first fetch |
| N3 | 42 Lake packages (30 direct + 12 inherited) | the git URLs in `dependency_table.md` (github.com only) | sha1 revs in manifest | git sha1; repos could vanish |
| N4 | config-time clones (11 packages) | same URLs as N3 (done by `run_cmd`) | lakefile sha | same |
| N5 | Mathlib build cache | `https://cache.mathlib.org`, `https://lakecache.blob.core.windows.net/mathlib4` (+ `github.com/leanprover-community/static-curl` releases for a curl binary) — URLs from `Cache/Infra.lean`, `Cache/IO.lean` at Mathlib d13f23b | **content hash in cache key from source hash; cache payload trusted** | Comparator README: acceptable only if the cache is trusted. Untrusted option: build Mathlib from source (hours; disk) |
| N6 | verifier tool sources | github.com/leanprover/comparator, /lean4export, /Zouuup/landrun (+ lean4export via Comparator's manifest) | profile pins | git sha1 |
| N7 | landrun Go modules | Go module proxy (`go.mod`: go-landlock v0.9.0, urfave/cli v3.6.2; Go ≥ 1.24) | `go.sum` | proxy/checksum DB |
| N8 | Lean build of tools | none beyond N2/N3 | | |
Observed in the authoring sandbox (proxy-mediated): github.com git/HTTPS reachable; `release.lean-lang.org` and `cache.mathlib.org` NOT reachable; Azure cache host not reached.

## 5. Can a frozen build be obtained from {exact upstream commit, committed manifest, exact dependency commits, exact patch bytes, no implicit upgrades}?
- **Yes in principle for the sources:** every input in N1, N3 is content-addressed; patch bytes are hashed and pinned in `subject.lock.json`.
- **Not yet for the toolchain binaries and the Mathlib cache** (N2, N5): no hash is pinned by upstream; P10 can record hashes on first fetch but cannot prove what upstream used.
- **Fail-closed behaviour implemented:** Stage A (hashes + closure + structure), the manifest invariant in Stage B/C. **Not implemented / not demonstrated:** hash-pinning of the Lean toolchain archive and the cache payload; offline mode.
- A smaller P10 workspace (Mathlib and its own 8 inherited pins only, without the other 29 direct requires and without run_cmd/post_update) would shrink the surface to N1–N2, N5, N6 — but it is a *different lakefile*, so it must be reported as a P10 deviation. Not built.
