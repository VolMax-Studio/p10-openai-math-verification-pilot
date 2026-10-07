# P10 OpenAI Mathematics Verification Pilot

Independent formal verification of a frozen result from the OpenAI Mathematics catalogue.

## Ratified result

**VERIFIED**

This repository records an independent verification pilot over the frozen formal-verification path for:

`OAI.InfiniteMatroidCounterexample.main`

from OpenAI's Mathematics catalogue, family 185.

The ratified claim is deliberately narrow:

> The frozen formal-verification path for `OAI.InfiniteMatroidCounterexample.main` was independently executed under the separately frozen `p10-frozen-v1` environment. Provenance binding, Comparator verification, an independent Lean build, the recorded negative controls, and P10 dependency-integrity checks passed for the ratified evidence state.

This is **not** a claim that the full associated manuscript has been independently verified.

It is also **not** a reproduction of OpenAI's original verifier run.

---

## Verification gates

| Gate | Purpose | Result |
|---|---|---|
| A | Provenance binding | **PASS** |
| B | Independent Lean build | **PASS** |
| C | Comparator verification | **PASS** |
| D | Negative controls | **PASS** |
| Dependency integrity | Pre/post execution binding | **PASS** |

The formal solution was accepted through the independently pinned Comparator path and Lean kernel.

A separate fresh Lean build also completed successfully.

The selected solution closure contained no `sorry`.

Recorded axioms:

- `propext`
- `Classical.choice`
- `Quot.sound`

Negative controls demonstrated rejection of:

- a changed theorem statement;
- a solution containing `sorry`;
- an invalid declaration binding;
- a solution relying on an injected unauthorized axiom.

Dependency-source mutations were separately blocked by the P10 dependency-integrity gate before Comparator execution.

---

## Ratified evidence

Exact evidence commit:

```text
1edd19c5a5694ff0e0a84ba43d9294849201cd42
```

Evidence subtree:

```text
fd0bf4c81a82d7914f87c16544330aff5a349303
```

Human ratification commit:

```text
52ed6cd5181f3ca140708ebb63a3b48205b1e9af
```

Ratified merge/release root:

```text
3c4817a2ed4a3f5c46c803ffea0d64852b75720e
```

Signed release tag:

```text
v1.0.0
```

The authoritative scope, exclusions, trusted-base statement, and ratifier decision are recorded in [`RATIFICATION.md`](RATIFICATION.md).

Later documentation commits do not create new verification evidence unless explicitly stated.

---

## Upstream subject

Upstream repository:

`openai/math`

Frozen upstream commit:

```text
adc7f1241b42e322a6451854ab7e4b4c146bf78a
```

Selected family:

```text
185 — InfiniteMatroid
```

Primary declaration:

```text
OAI.InfiniteMatroidCounterexample.main
```

The frozen binding chain is:

```text
OpenAI catalogue / manuscript
        ↓
lean/docs/185.md
        ↓
formalization metadata
        ↓
ComparatorChallenges/InfiniteMatroid.lean
        ↓
InfiniteMatroid.json
        ↓
OAI.Combinatorics.InfiniteMatroid.Main
        ↓
OAI.InfiniteMatroidCounterexample.main
        ↓
Comparator / Lean kernel
```

The repository records which links are machine-enforced and which remain metadata or prose-level bindings.

---

## What was independently verified

For the frozen subject and `p10-frozen-v1` profile, the pilot establishes that:

1. checked subject bytes correspond to the frozen upstream Git objects;
2. dependency source state corresponds to the frozen dependency revisions;
3. challenge, configuration, and solution identities were re-checked against the frozen blobs after the relevant runs;
4. Comparator accepted the formal solution;
5. an independent Lean build accepted the selected solution closure;
6. the relevant execution stages began and ended with unchanged dependency state;
7. controlled invalid variants were rejected or blocked as documented;
8. the exact evidence state was frozen and human-ratified.

This is an **execution-level formal-verification claim**.

---

## What is not demonstrated

The ratification does **not** establish:

- semantic equivalence between the manuscript, including Theorem 1.1, and the Lean statement;
- correctness of the full manuscript or any unformalized claim;
- reproduction of OpenAI's exact original verifier environment;
- proof that OpenAI used the same Comparator, `lean4export`, or `landrun` revisions selected here;
- translation of the Lean theorem into, or proof of the result specifically in, ZFC;
- the manuscript-level conclusion that “the conjecture is false” as a separately verified claim;
- novelty or priority;
- correctness of adjacent formal units;
- correctness of the wider OpenAI Mathematics catalogue.

The manuscript-to-formal bridge remains separately documented in:

[`reports/manuscript_bridge_review_theorem_1_1.md`](reports/manuscript_bridge_review_theorem_1_1.md)

Its sign-off remains intentionally separate from the ratified execution-level claim.

---

## Trusted base

The verified claim relies on an explicit trusted base including:

- the Lean kernel and released Lean toolchain binaries;
- the frozen Mathlib cache payload and provider chain;
- the pinned Comparator build;
- the pinned `lean4export` build;
- the pinned `landrun` build;
- the Linux / Landlock / systemd sandboxing substrate;
- Git-hosted source objects and revisions;
- the execution device and hardware.

The Lean 4.34.1 archive was obtained from `releases.lean-lang.org`; its digest matched the digest published for the corresponding GitHub release asset, and the installed toolchain tree matched the verified archive.

This establishes payload integrity across those observations, not reproducible build-from-source provenance.

The Mathlib cache payload was independently downloaded in fresh verification workspaces and produced the same frozen payload identity.

> **Reproducible build-from-source provenance of the trusted binaries is not demonstrated.**

---

## Important diagnostic findings

### Dependency integrity is not delegated to Comparator

During RC testing, a harmless local Mathlib source modification that still compiled was accepted by Lake and Comparator, with only a dirty-repository warning.

The final P10 profile therefore treats dependency integrity as a separate fail-closed verification gate.

Final Stage B, C, and D executions enforce dependency verification before and after the relevant execution.

### Not every negative control fails cleanly

One invalid declaration-binding test was rejected through a `lean4export` PANIC / child-process failure rather than a clean structured Comparator diagnostic.

The D4-family dependency mutation tests are P10 dependency-integrity controls, not Comparator negative controls.

These distinctions are preserved in the evidence rather than normalized away.

---

## Verification profiles

Two concepts are deliberately kept separate.

### Upstream as-is

This asks what can be reconstructed from the public upstream repository itself.

The exact verifier revisions originally used by OpenAI were not recoverable from the public repository.

Therefore:

```text
Exact reproduction of OpenAI's original verifier environment:
NOT DEMONSTRATED
```

### `p10-frozen-v1`

This is a separately selected and frozen environment used to independently verify the same formal path.

Pinned verifier revisions:

```text
Comparator
d03acab154d269c06e60e4de7e4cc85deebff94b

lean4export
076e8e57707e813375e8f9da8bf989799ace9680

landrun
811cfff51ceaf3d9843708aa6d22e9b84ccac8b4
```

Project toolchain:

```text
Lean 4.34.1
```

See [`profiles/README.md`](profiles/README.md).

---

## About `subject.lock.json`

`subject.lock.json` was frozen before the final verification verdict and therefore retains its historical status field:

```text
SELECTED_SUBJECT_FROZEN__NO_VERDICT
```

That field describes the state of the subject lock when it was frozen.

**The lock is not the verdict carrier.**

The final human verdict and its exact scope are recorded in [`RATIFICATION.md`](RATIFICATION.md).

---

## Evidence discipline

Evidence is separated into:

- **OBSERVED**
- **DERIVED**
- **NOT DEMONSTRATED**

A failed or infrastructure-blocked attempt is preserved as such and is not retroactively converted into a PASS.

For example, an early Comparator attempt was blocked by the local session-bus environment. That attempt remains in the evidence history; only the later valid execution contributes to the ratified Comparator PASS.

The same principle applies to dependency mutations, negative controls, and diagnostic limitations.

---

## Repository map

| Path | Purpose |
|---|---|
| [`RATIFICATION.md`](RATIFICATION.md) | signed human ratification scope and exclusions |
| [`SUBJECT.md`](SUBJECT.md) | subject-selection and upstream discovery record |
| [`SCOPE.md`](SCOPE.md) | original pilot scope; contains historical pre-execution status |
| [`subject.lock.json`](subject.lock.json) | frozen subject/binding metadata; not a verdict carrier |
| [`profiles/`](profiles/) | frozen verifier and dependency profiles |
| [`evidence/stage_rcfinal_a/`](evidence/stage_rcfinal_a/) | final provenance evidence |
| [`evidence/stage_rcfinal_b/`](evidence/stage_rcfinal_b/) | final independent Lean-build evidence |
| [`evidence/stage_rcfinal_c/`](evidence/stage_rcfinal_c/) | final Comparator evidence |
| [`evidence/stage_rcfinal_d/`](evidence/stage_rcfinal_d/) | final negative-control evidence |
| [`evidence/stage_dep/`](evidence/stage_dep/) | dependency mutation experiments |
| [`evidence/tools/`](evidence/tools/) | toolchain and verifier build records |
| [`reports/infinite_matroid_binding.md`](reports/infinite_matroid_binding.md) | historical pre-execution binding analysis |
| [`reports/manuscript_bridge_review_theorem_1_1.md`](reports/manuscript_bridge_review_theorem_1_1.md) | manuscript ↔ Lean bridge review |
| [`reports/stage_results_p10_frozen_v1.md`](reports/stage_results_p10_frozen_v1.md) | execution history and RC results |
| [`scripts/p10_rc_run.py`](scripts/p10_rc_run.py) | final RC execution harness |
| [`scripts/install_tools.sh`](scripts/install_tools.sh) | pinned verifier-tool installation/build helper |

---

## Inspect the ratified release

```bash
git clone https://github.com/VolMax-Studio/p10-openai-math-verification-pilot.git
cd p10-openai-math-verification-pilot
git checkout v1.0.0
```

Read the ratification record:

```bash
cat RATIFICATION.md
```

Verify the signed tag using an allowed-signers configuration containing the ratifier public key:

```bash
git -c gpg.format=ssh \
    -c gpg.ssh.allowedSignersFile=/path/to/allowed_signers \
    verify-tag v1.0.0
```

---

## Re-run the final verification path

The original `scripts/reproduce.sh` and `scripts/gates.py` belong to the earlier bootstrap harness and do **not** reproduce the final ratified RC workflow.

They are retained for provenance and should be treated as **legacy**.

The final execution path uses:

```text
scripts/install_tools.sh
scripts/p10_rc_run.py
```

Prepare the pinned verification tools according to the repository profile and local environment requirements.

The installer uses `P10_TOOLS` as the private tool prefix.

The final runner uses `P10_WS` for disposable workspaces.

The ratified stage order was:

```text
A → C → B → D
```

with fresh/disposable workspaces and dependency integrity checks around the relevant executions.

The runner exposes the individual stages:

```bash
python scripts/p10_rc_run.py a
python scripts/p10_rc_run.py c
python scripts/p10_rc_run.py b
python scripts/p10_rc_run.py d
```

Consult:

- [`profiles/README.md`](profiles/README.md)
- [`scripts/install_tools.sh`](scripts/install_tools.sh)
- [`scripts/p10_rc_run.py`](scripts/p10_rc_run.py)
- [`reports/stage_results_p10_frozen_v1.md`](reports/stage_results_p10_frozen_v1.md)

before attempting a clean rerun.

A rerun requires the declared Lean/tool environment, Linux sandboxing prerequisites, network access for frozen dependencies/cache retrieval, and sufficient local storage.

A new execution is a new observation; it does not modify the already-ratified `v1.0.0` evidence state.

---

## Release

Ratified release:

[`v1.0.0`](https://github.com/VolMax-Studio/p10-openai-math-verification-pilot/releases/tag/v1.0.0)

---

## Attribution

The OpenAI Mathematics catalogue, associated manuscripts, and upstream formal artifacts are OpenAI's work.

VolMax Studio Lab performed this independent verification pilot over a frozen public upstream subject.

This project is independent and does not imply affiliation with, endorsement by, or verification on behalf of OpenAI.

---

## License

Original VolMax code and documentation in this repository are licensed under Apache-2.0.

Upstream OpenAI, Lean, Mathlib, Comparator, and other third-party artifacts remain under their respective original licenses and are not relicensed by this repository.

See [`NOTICE`](NOTICE).
