#!/usr/bin/env bash
# Fail-closed reproduction harness. Every gate reports separately; there is NO aggregate PASS and NO verdict.
# Gate status: PASS | FAIL | NOT_EXECUTED | ENVIRONMENT_BLOCKED   (the last two are never success)
# Exit: 0 only if every REQUESTED gate is PASS; else 4 (any FAIL) > 6 (any ENVIRONMENT_BLOCKED) > 5 (any NOT_EXECUTED).
# Usage: reproduce.sh [--stage A|B|C|D|E|all] [--profile p10-frozen-v1|upstream-as-is]
# Execution order for 'all' is A, C, B, D (Comparator README assumption 2: do not compile the solution outside
# the sandbox before Comparator has run in that workspace; B and C therefore use separate workspaces).
set -uo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
LOCK="$HERE/subject.lock.json"; UP="${UPSTREAM_DIR:-$HERE/upstream/openai-math}"
STAGE=all; PROFILE=p10-frozen-v1
while [ $# -gt 0 ]; do case "$1" in --stage) STAGE="$2"; shift 2;; --profile) PROFILE="$2"; shift 2;; *) echo "usage: see header" >&2; exit 2;; esac; done
[ -f "$LOCK" ] || { echo "FAIL(2): missing subject.lock.json" >&2; exit 2; }
SEL="$(python3 -I -c "import json;print(json.load(open('$LOCK'))['selected_candidate'] or '')")"
RD="$HERE/work/results/$PROFILE"; mkdir -p "$RD"
declare -A ST
want() { [ "$STAGE" = all ] || [ "$STAGE" = "$1" ]; }
boundary() { cat <<'B'
== E. COVERAGE BOUNDARY (unconditional; no gate above can widen it) ==
This execution does NOT establish:
  - that every mathematical statement in the manuscript is formalized (the formal main theorem is one Lean statement;
    see reports/infinite_matroid_binding.md for what it does and does not cover);
  - that the formal theorem is semantically equivalent to the informal manuscript claim;
  - that unformalized arguments (including cited external results) are correct;
  - novelty or priority;
  - correctness of the rest of the openai/math catalogue;
  - fidelity of Mathlib's definitions (Matroid, Spanning, ...) to the mathematical notions they are used for;
  - any P10 verdict. Adjudication is outside this repository's bootstrap; Ivan is the ratifier.
Lean acceptance is evidence about a formal statement, not about the whole manuscript.
B
}
if [ -z "$SEL" ]; then echo "no subject selected: FAIL-CLOSED (3)"; boundary; exit 3; fi
echo "subject=$SEL profile=$PROFILE lock=$(sha256sum "$LOCK" | cut -c1-12)"
gate_py() { python3 -I "$HERE/scripts/gates.py" "$1" "$UP" "$LOCK" "$PROFILE" "$RD"; ST[$1]=$?; }
if want A; then
  echo "== A. PROVENANCE BINDING (provenance only) =="
  python3 -I "$HERE/scripts/stage_a.py" "$UP" "$LOCK" --json "$RD/A.json"; ST[A]=$?
fi
for g in C B D; do want $g && { echo "== $g. $( [ $g = B ] && echo 'LEAN BUILD' || { [ $g = C ] && echo 'COMPARATOR VERIFICATION' || echo 'TAMPER REJECTION'; } ) =="; gate_py $g; }; done
want E && boundary
echo "---- summary (no aggregate verdict) ----"
worst=0; label() { case "$1" in 0) echo PASS;; 4) echo FAIL;; 5) echo NOT_EXECUTED;; 6) echo ENVIRONMENT_BLOCKED;; *) echo "ERROR($1)";; esac; }
for g in A B C D; do [ -n "${ST[$g]+x}" ] && { echo "  $g: $(label ${ST[$g]})"; r=${ST[$g]}; case $r in 4) worst=4;; 6) [ $worst -ne 4 ] && worst=6;; 5) [ $worst -eq 0 ] && worst=5;; 0) ;; *) worst=4;; esac; }; done
echo "  VERIFICATION VERDICT: UNAVAILABLE (this script issues none; unexecuted/blocked gates are not success)"
exit $worst
