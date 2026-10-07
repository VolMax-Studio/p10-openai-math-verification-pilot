#!/usr/bin/env bash
# Fail-closed reproduction harness. Each stage reports separately; there is NO aggregate PASS.
# Exit codes: 0 only if every REQUESTED stage ran and passed; 2 = precondition/usage; 3 = no subject
# selected; 4 = stage failed; 5 = stage not implemented (treated as failure, never as skip).
# Usage: reproduce.sh [--stage A|B|C|D|E|all] [--candidate NAME]   (--candidate = dry run, NOT a selection)
set -uo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
LOCK="$HERE/subject.lock.json"
UP="${UPSTREAM_DIR:-$HERE/upstream/openai-math}"
STAGE=all; CAND=""; DRY=0
while [ $# -gt 0 ]; do case "$1" in
  --stage) STAGE="$2"; shift 2;; --candidate) CAND="$2"; DRY=1; shift 2;; *) echo "usage" >&2; exit 2;; esac; done
[ -f "$LOCK" ] || { echo "FAIL(2): missing subject.lock.json" >&2; exit 2; }
py() { python3 -I -c "$@"; }
SEL="$(py "import json;print(json.load(open('$LOCK'))['selected_candidate'] or '')")"
[ -n "$CAND" ] && SEL="$CAND"
coverage_boundary() {
cat <<'B'
== E. COVERAGE BOUNDARY (stated unconditionally; no stage above can widen it) ==
This execution does NOT establish:
  - that every mathematical statement in the manuscript is formalized;
  - that the formal theorem is semantically equivalent to the full informal manuscript claim;
  - that unformalized arguments are correct;
  - novelty or priority;
  - correctness of the rest of the openai/math catalogue;
  - any P10 verdict (adjudication is outside this repository's bootstrap).
Lean acceptance is evidence about a formal statement, not about the whole manuscript.
B
}
if [ -z "$SEL" ]; then
  echo "A. provenance binding : NOT RUN - no subject selected (selected_candidate is null)"
  echo "B. lean build         : NOT RUN"; echo "C. comparator         : NOT RUN"; echo "D. tamper rejection   : NOT RUN"
  coverage_boundary
  echo "RESULT: FAIL-CLOSED (3) - nothing was verified." >&2; exit 3
fi
rc=0
stage_A() {
  echo "== A. PROVENANCE BINDING (subject=$SEL$([ $DRY = 1 ] && echo ", dry run")) =="
  [ -d "$UP/.git" ] || { echo "A: FAIL no upstream checkout (scripts/fetch_upstream.sh)"; return 4; }
  py "
import json,hashlib,subprocess,sys,os
lock=json.load(open('$LOCK')); up='$UP'; sel='$SEL'
head=subprocess.check_output(['git','-C',up,'rev-parse','HEAD'],text=True).strip()
if head!=lock['upstream']['commit']: print('A: FAIL HEAD',head,'!= lock',lock['upstream']['commit']); sys.exit(4)
files=lock['candidates'][sel]['files_sha256']; bad=0
for p,h in sorted(files.items()):
    fp=os.path.join(up,p)
    if not os.path.isfile(fp): print('A: MISSING',p); bad+=1; continue
    if hashlib.sha256(open(fp,'rb').read()).hexdigest()!=h: print('A: MISMATCH',p); bad+=1
print('A:',len(files),'files checked,',bad,'bad'); sys.exit(4 if bad else 0)
"
}
want() { [ "$STAGE" = all ] || [ "$STAGE" = "$1" ]; }
unimpl() { echo "== $1 == NOT IMPLEMENTED (counted as failure, not skip)"; return 5; }
if want A; then stage_A; r=$?; [ $r -ne 0 ] && rc=$r; fi
if want B; then unimpl "B. LEAN BUILD"; r=$?; [ $rc -eq 0 ] && rc=$r; fi
if want C; then unimpl "C. COMPARATOR VERIFICATION"; r=$?; [ $rc -eq 0 ] && rc=$r; fi
if want D; then unimpl "D. TAMPER REJECTION"; r=$?; [ $rc -eq 0 ] && rc=$r; fi
want E && coverage_boundary
[ $DRY = 1 ] && echo "NOTE: --candidate is a harness dry run, not a subject selection."
echo "exit=$rc (0 required for every requested stage; per-stage lines above are the result)"
exit $rc
