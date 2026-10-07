# SCOPE

## In scope (target, once a subject is selected)
Demonstrate **separately**, never as one aggregate PASS:

| Stage | Question | Status |
|---|---|---|
| A. Provenance binding | Do the exact frozen files (whole binding chain) match the lock; do closure and metadata cross-checks hold? | **executed: PASS (provenance only)**; tamper tests 25/25 as expected; expected hashes derived from the frozen git commit (lock is a manifest, not the authority) (`evidence/stage_a/`) |
| B. Lean build | Does the selected solution build under the frozen toolchain/dependencies? | implemented (never run to success); ENVIRONMENT BLOCKED here |
| C. Comparator verification | Does Comparator accept the solution for the intended challenge/config? | implemented (never run to success); ENVIRONMENT BLOCKED |
| D. Tamper rejection | Does at least one controlled mutation of theorem/solution/binding fail Comparator? (4 mutations defined; Stage-A byte-tamper is separate) | implemented (never run to success); NOT EXECUTED |
| E. Coverage boundary | What does this execution NOT establish? | printed unconditionally by `reproduce.sh` |

Gate statuses are PASS / FAIL / NOT EXECUTED / ENVIRONMENT BLOCKED. The last two are never success and `reproduce.sh` never prints a verification verdict.

## Out of scope / not established by anything in this repository
- that every statement in the manuscript is formalized;
- semantic equivalence of the formal theorem and the informal manuscript claim;
- correctness of unformalized arguments;
- novelty or priority;
- correctness of the rest of the 722-manuscript / 372-family catalogue;
- any P10 verdict, ratification, signature, tag, or release (Ivan is the sole ratifier and release authority).

## Trust model note (OBSERVED, from the Comparator README at ca04cfc)
Comparator guarantees only: the solution proves the *same statement as the Challenge*, uses no axioms beyond
`permitted_axioms`, and is accepted by the Lean kernel -- *given* that the Challenge's import closure and the
lakefile are trustworthy, no adversarial file was previously compiled, `landrun`/`lean4export` are correct,
and the kernel is correct. Whether the Challenge statement faithfully encodes the manuscript is outside
Comparator by construction.
