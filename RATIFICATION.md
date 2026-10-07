# P10 ratification record — `InfiniteMatroid`

**Status: RATIFIED — VERIFIED**

Prepared locally on `2026-10-07T17:13:55+02:00`. This file is a decision record for the sole ratifier, Ivan. Its presence does not itself ratify, sign, tag, release, publish, or assign a broader P10 verdict to the subject.

## Objects presented for ratification

- Repository: `VolMax-Studio/p10-openai-math-verification-pilot`
- Branch at preparation: `claude/charming-noether-j0w6k4`
- Exact evidence commit: `1edd19c5a5694ff0e0a84ba43d9294849201cd42`
- Evidence commit tree: `23b8fc9c62783dfd8d4cd03332a11aa674435499`
- Documentation commit: `c0d27d41f65642541b3052046aa4a3addaf1efb0`
- Documentation commit tree: `d199ecc9ee013db30cfc2044789810247f30b447`
- Upstream subject: `openai/math` commit `adc7f1241b42e322a6451854ab7e4b4c146bf78a`, family 185, declaration `OAI.InfiniteMatroidCounterexample.main`
- Verification profile: `p10-frozen-v1`

The evidence subtree at both presented commits resolves to the same Git tree:

```text
fd0bf4c81a82d7914f87c16544330aff5a349303
```

`git diff --exit-code 1edd19c5a5694ff0e0a84ba43d9294849201cd42 c0d27d41f65642541b3052046aa4a3addaf1efb0 -- evidence/` returned `0`. The only changes from the evidence commit through the documentation commit are the addition of `reports/CANDIDATE_FOR_RATIFICATION.md` and documentation changes to `reports/manuscript_bridge_review_theorem_1_1.md`; no evidence file changed.

## Exact narrow claim offered to Ivan

> The frozen formal-verification path for `OAI.InfiniteMatroidCounterexample.main` was independently executed under the `p10-frozen-v1` profile at evidence commit `1edd19c5a5694ff0e0a84ba43d9294849201cd42`: provenance binding, Comparator verification, an independent Lean build, and the recorded negative controls passed, with P10 dependency-integrity checks enforced before and after the relevant execution and with the trusted base and caveats stated in `reports/CANDIDATE_FOR_RATIFICATION.md`. This ratification is limited to that recorded formal-verification execution and its frozen evidence.

This is the whole claim. No manuscript-level or broader mathematical claim is incorporated by reference.

## Findings supporting the narrow claim

### OBSERVED

- Git resolves both named SHAs as commits. The evidence commit is an ancestor of the documentation commit.
- `evidence/stage_rcfinal_a/summary.json` records Gate A `PASS`: 162 checks passed and 30/30 tamper tests behaved as expected.
- `evidence/stage_rcfinal_c/stage_rcfinal_c_result.json` records Gate C `PASS`: Comparator returned `0`, the Lean default kernel accepted the solution, and the output states `Your solution is okay!`; dependency checks before and after were both clean with identical state digest `cd60aa529a2e818969c79f4f51616f8d5b797f579b8e9ce2b2ab049253036a11`.
- `evidence/stage_rcfinal_b/stage_rcfinal_b_result.json` records Gate B `PASS`: `lake build OAI ComparatorChallenges` returned `0`, the solution closure contained no `sorry`, the reported axioms were `{propext, Classical.choice, Quot.sound}`, and dependency state was clean and unchanged.
- `evidence/stage_rcfinal_d/stage_rcfinal_d_result.json` records Gate D `PASS`: the clean control passed before and after restoration; four Comparator mutations were rejected; three dependency mutations were blocked before Comparator execution; and the altered manifest was detected.
- `git fsck --full --no-progress` returned `0`. It also reported an unrelated dangling commit, `bc3f6265e1b649ce1ca539cc14fce993527aec5c`, which is not one of the presented objects.
- Both presented commits are unsigned (`%G? = N`; `git verify-commit` returned `1`). No ratification signature currently exists on them.

### DERIVED

- Because both presented commits resolve `evidence/` to the identical tree object, the later pinned-source documentation did not alter the evidence offered for ratification.
- The recorded gate results support only the narrow execution claim above, subject to the stated trusted base and diagnostic caveats. They do not close the manuscript-to-Lean semantic bridge.

## Explicit exclusions — NOT DEMONSTRATED / outside scope

Ratification of the narrow claim must not be quoted or interpreted as demonstrating any of the following:

1. semantic equivalence between the manuscript, including Theorem 1.1, and the Lean statement;
2. correctness of the full manuscript or of any unformalized claim;
3. reproduction of OpenAI's exact original/upstream verifier environment;
4. translation of the Lean result into, or proof of the result "in ZFC";
5. the manuscript-level conclusion that "the conjecture is false";
6. novelty, priority, correctness of adjacent formal units, or correctness of the wider OpenAI mathematics catalogue.

Rows 3 and 9 of `reports/manuscript_bridge_review_theorem_1_1.md` retain explicit representation/closure assumptions. Rows 11 and 13 remain outside the ratified claim. The bridge sign-off block remains empty and is not required for this deliberately Lean-formal, execution-only claim.

## Trusted base and caveats accepted only for this claim

The claim inherits the trusted base and caveats in `reports/CANDIDATE_FOR_RATIFICATION.md`, including the Lean kernel and released Lean binaries; unaudited Comparator, `lean4export`, and `landrun`; Landlock/systemd/Linux; the Mathlib cache provider and compiled artifacts; GitHub as source of pinned revisions; and the execution device/hardware. In particular, D3 is a crash-rejection, D1 tests statement binding rather than a malicious challenge, compiled-cache substitution is not excluded by source checks alone, and B/C/D were run on one machine and network path.

## Signing configuration inspected, not changed

- Git identity: `VolMax-Studio <volmax.core@gmail.com>`
- Git signing format: `ssh`
- Allowed-signers file: `/home/volmax-studio/.config/git/p10_allowed_signers`
- `user.signingkey`: not configured
- automatic commit signing: not configured
- automatic tag signing: not configured
- Ivan P10 human-ratification public-key fingerprint: `SHA256:5aVclA4mSj525gNohpxgBArgTo8qWvUbftMsGUs2TLw`
- Ivan P10 offline human-ratification 2026 public-key fingerprint: `SHA256:ZWS4wWm51TGadLbTpc4IqscRiMsk1ZjEx0hUaE+2iNc`

Both Ivan fingerprints are represented in the allowed-signers file for `volmax.core@gmail.com`. The newer offline key is present locally as `~/.ssh/id_ed25519_ivan_p10_ratification_2026`; this preparation did not access its private contents or invoke it.

## Ivan's explicit decision

Ivan must edit this section himself before any signed ratification commit is created.

- [x] **RATIFY** exactly the narrow claim quoted above, with all exclusions, trusted-base statements, and caveats preserved.
- [ ] **DO NOT RATIFY.**

```text
ratifier: Ivan Nestorov
decision timestamp (ISO 8601): 2026-10-07T17:21:40+02:00
notes / exceptions (none unless stated): none
signing-key fingerprint: SHA256:ZWS4wWm51TGadLbTpc4IqscRiMsk1ZjEx0hUaE+2iNc
```

Ivan selected RATIFY. This record becomes effective only through the verified SSH-signed ratification commit containing this exact file. Tagging, pushing, releasing, and publishing are separate later actions and are not authorized by this record.
