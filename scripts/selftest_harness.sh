#!/usr/bin/env bash
# STUB PLUMBING SELF-TEST. Uses fake `lake` and a fake `comparator` to exercise gates B/C/D control flow only.
# It proves NOTHING about Lean, Comparator, or the subject. Results are written under work/ (git-ignored), never to evidence/.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
cat > "$T/lake" <<'S'
#!/usr/bin/env bash
case "$1" in env) shift; exec "$@";; exe|build|update) echo "stub lake $*"; exit 0;; *) exit 1;; esac
S
cat > "$T/comparator" <<'S'
#!/usr/bin/env python3
import json,re,sys
cfg=json.load(open(sys.argv[1])); sol=open("OAI/Combinatorics/InfiniteMatroid/Main.lean").read(); ch=open("ComparatorChallenges/InfiniteMatroid.lean").read()
def stmt(t,n): m=re.search(r"theorem\s+"+re.escape(n)+r"\b(.*?):=\s*by",t,re.S); return m.group(1).strip() if m else None
n=cfg["theorem_names"][0].split(".")[-1]
a,b=stmt(ch,n),stmt(sol,n)
if a is None or b is None: sys.exit("theorem not found")
if a!=b: sys.exit("statement mismatch")
if re.search(r"\bsorry\b",re.sub(r"--.*","",sol)) or re.search(r"^\s*axiom\b",sol,re.M): sys.exit("axiom/sorry")
S
printf '#!/bin/sh\nexit 0\n' > "$T/landrun"; cp "$T/landrun" "$T/lean4export"; chmod +x "$T"/*
python3 -I - "$T" "$HERE/profiles/verifier_profiles.json" <<'PY' 
import hashlib,json,sys
T,pp=sys.argv[1:3]; p=json.load(open(pp))["p10-frozen-v1"]
h=lambda f: hashlib.sha256(open(f"{T}/{f}","rb").read()).hexdigest()
json.dump({"comparator":{"rev":p["comparator"]["rev"],"binary_sha256":h("comparator")},"lean4export":{"rev":p["lean4export"]["rev"],"binary_sha256":h("lean4export")},"landrun":{"rev":p["landrun"]["rev"],"binary_sha256":h("landrun")}},open(f"{T}/rec.json","w"))
PY
### STUB SELFTEST (plumbing only; not evidence) ###"
P10_SELFTEST=1 P10_LAKE="$T/lake" COMPARATOR_BIN="$T/comparator" COMPARATOR_LEAN4EXPORT="$T/lean4export" COMPARATOR_LANDRUN="$T/landrun" P10_TOOLS_RECORD="$T/rec.json" \
  "$HERE/scripts/reproduce.sh" --stage all | grep -v '^  - \|^This execution\|^Lean acceptance' || true

rm -rf "$HERE/work/results/p10-frozen-v1" "$HERE/work/p10-frozen-v1"
