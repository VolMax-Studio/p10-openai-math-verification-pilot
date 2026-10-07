# Verifier provenance: Comparator, lean4export, landrun

All facts **O** unless marked. Obtained 2026-10-07 by full (blob-less) clones of the three repositories and
`git log` / `git diff --stat` / `git show` on them (commands in `scripts/` are not needed; each is a plain git query).
Reference clock: openai/math commit `adc7f12…` = 2026-10-06T14:58:50-07:00 = **2026-10-06T21:58:50Z**.

## 1. Did upstream say which verifier revisions it used?  -> NO
- `lean/ComparatorChallenges/README.md` @ adc7f12: "Install `comparator`, `landrun`, and `lean4export`, and make them available on `PATH`." No repository URL, revision, tag, version, or binary hash.
- No `.github/`, no CI config, no submodule metadata, no lockfile or manifest entry for any of the three tools exists in the openai/math tree (`ls -a`, `git ls-tree`; the only references are the README line above, `lean/formalization.yaml` acknowledgements, `lean/lakefile.lean`'s name `ComparatorChallenges` lib, and `lean/docs/*.md` link text).
- `lean/lakefile.lean` / `lake-manifest.json` do not `require` comparator or lean4export.
- **Result:** `NOT DEMONSTRATED: exact verifier implementation used upstream.` External references (blog posts, release notes, commit messages outside this repo) were not searched; the repository itself is silent.

## 2. What the three public repositories look like around the upstream commit
| Tool | main HEAD at inspection | HEAD date | HEAD toolchain | Last commit that changed anything other than `lean-toolchain`/`lake-manifest.json`/tests |
|---|---|---|---|---|
| leanprover/comparator | `ca04cfc72b550331658ec314bf47685281bfd4bf` | 2026-10-06T16:25+02:00 (= 14:25Z, **before** openai/math's commit) | v4.35.0-rc4 | `2312244` 2026-08-30 "chore: more primitives" (git log with path excludes also lists the rc1/rc2 bump commits `9093852`, `32bd61d`, but `git diff d03acab HEAD --stat` shows only 2 files differ: `lake-manifest.json`, `lean-toolchain`) |
| leanprover/lean4export | `05d43a2bc773b40ecfdebb32294192a5ef756951` | 2026-10-06T16:08+02:00 (before) | v4.35.0-rc4 | `0c79a8b` 2026-08-25 "omit partial declarations unless exportUnsafe is true"; `git diff 076e8e5 HEAD --stat`: `Test.lean`, `lean-toolchain` only |
| Zouuup/landrun | `811cfff51ceaf3d9843708aa6d22e9b84ccac8b4` | 2026-07-23T13:23+01:00 (before; unchanged for 2.5 months) | n/a (Go) | `62823c0` 2026-07-22 (go-landlock v0.9.0); `ce85db1` 2026-07-23 funding; tag `v0.1.17` = `24c0e92`; `git diff v0.1.17 HEAD --stat`: tests, README, FUNDING.yml, `.gitignore`, 2 lines in `cmd/landrun/main.go` |

## 3. Lean-version timeline (O; `git log` on tags in leanprover/lean4, partial clone)
| Event | Time |
|---|---|
| Lean `v4.34.0` tag | 2026-09-14T13:35+02:00 |
| Comparator bump to `v4.34.0` = `d03acab154d2…` | 2026-09-14T16:24+02:00 |
| lean4export bump to `v4.34.0` = `076e8e57707e…` | 2026-09-14T16:12+02:00 |
| Lean `v4.35.0-rc1` | 2026-09-15T13:45+02:00 (Comparator `9093852` / lean4export `fd0d78e` follow the same day) |
| Lean `v4.34.1` tag | **2026-09-24T19:27+02:00** |
| Mathlib `d13f23b…` "chore: bump toolchain to v4.34.1" | 2026-09-24T22:34+02:00 |
| openai/math `adc7f12` (project toolchain v4.34.1, Mathlib `d13f23b`) | 2026-10-06T21:58Z |

**No Comparator or lean4export revision has `lean-toolchain` = `v4.34.1`.** The newest ones with a v4.34.x toolchain are `d03acab` / `076e8e5` (v4.34.0, valid only 2026-09-14 → 2026-09-15). Therefore, if upstream used `main` of either tool on 2026-10-06, they were on v4.35.0-rc4 while the project builds with v4.34.1; if upstream used v4.34.x-targeted tools they had to build them against a toolchain that the tool repos do not record for v4.34.1. Either way the exact binary is unrecoverable from public history (**N**).

## 4. Consequence for P10: two claims, kept apart
1. **Reproducing the upstream verification environment** — impossible to complete; upstream's verifier identity is `NOT DEMONSTRATED`. Profile `upstream-as-is` therefore has `executable_as_reproduction: false`.
2. **Independently verifying the same challenge with a newly pinned environment** — profile `p10-frozen-v1` (profiles/verifier_profiles.json):
   - Comparator `d03acab154d269c06e60e4de7e4cc85deebff94b` — the last revision before the rc-line whose `lean-toolchain` is a v4.34 release; its source equals HEAD's source (only toolchain/manifest differ), so the choice affects the Lean ABI, not Comparator logic (**O**, `git diff --stat`).
   - lean4export `076e8e57707e813375e8f9da8bf989799ace9680` — the revision Comparator `d03acab` itself pins in its `lake-manifest.json` (**O**).
   - landrun `811cfff51ceaf3d9843708aa6d22e9b84ccac8b4` — Comparator README says "compiled from the main branch"; main was unchanged since 2026-07-23 (before the upstream commit), so this is `main` at every date between 2026-07-23 and now (**O**).
   - Deviation: both Lean tools are built with `leanprover/lean4:v4.34.1` instead of their recorded v4.34.0. Whether they compile and run correctly under v4.34.1 is **N** (never attempted).
3. Selection rationale is a *choice*, not a recovery. It must be reported as such in any later result.

## 5. Trust assumptions of Comparator that this project cannot discharge by itself (O, README @ ca04cfc)
Challenge import closure and the lakefile are trustworthy; the Solution has never been compiled outside the sandbox in that workspace; `landrun` and `lean4export` correct; Lean kernel correct; not run as a privileged user; on Linux < 7.1 the `systemd-run … RestrictAddressFamilies=~AF_UNIX` guard is required (the README says the underlying landrun issue "will be fixed in Linux 7.1"; the user's workstation kernel is 7.0.0-34-generic, see environment_probe).
