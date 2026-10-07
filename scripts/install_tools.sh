#!/usr/bin/env bash
# Build the three p10-frozen-v1 verifier tools in a P10-private prefix. Records every step; never edits tool source.
# Usage: P10_TOOLS=/abs/dir scripts/install_tools.sh   (no root; ~/.elan is NOT touched)
set -u
T="${P10_TOOLS:?set P10_TOOLS}"; mkdir -p "$T"/{dl,src,logs,bin}; L="$T/logs"
export ELAN_HOME="$T/elan" GOPATH="$T/gopath" GOCACHE="$T/gocache"
export PATH="$T/go/bin:$ELAN_HOME/bin:$PATH"
ELAN_URL=https://github.com/leanprover/elan/releases/download/v4.2.4/elan-x86_64-unknown-linux-gnu.tar.gz
ELAN_SHA=42b94d4244e8353142c456ec0e4ca6528fd898a6c604d4059f494e706e431f63
GOV=go1.24.13
LEAN=leanprover/lean4:v4.34.1
run(){ n=$1; shift; echo "### $n: $*" >>"$L/commands.txt"; t0=$(date +%s); "$@" >"$L/$n.out" 2>"$L/$n.err"; rc=$?; echo "rc=$rc elapsed=$(( $(date +%s)-t0 ))s" >>"$L/commands.txt"; echo "$n rc=$rc"; return $rc; }
step_elan(){ cd "$T/dl"; [ -f elan.tgz ] || curl -fsSL -o elan.tgz "$ELAN_URL"; echo "$ELAN_SHA  elan.tgz" | sha256sum -c - || return 1
  tar xzf elan.tgz && ./elan-init -y --no-modify-path --default-toolchain none; }
step_go(){ cd "$T/dl"; sha=$(curl -fsSL "https://go.dev/dl/?mode=json&include=all" | python3 -I -c "
import json,sys
for r in json.load(sys.stdin):
  if r['version']=='$GOV':
    for f in r['files']:
      if f['filename']=='$GOV.linux-amd64.tar.gz': print(f['sha256'])")
  [ -n "$sha" ] || return 1; echo "$sha" >go.sha256; curl -fsSL -o go.tgz "https://go.dev/dl/$GOV.linux-amd64.tar.gz"
  echo "$sha  go.tgz" | sha256sum -c - && tar xzf go.tgz -C "$T"; }
clone(){ d=$1; u=$2; sha=$3; [ -d "$T/src/$d" ] || git clone -q "$u" "$T/src/$d"; git -C "$T/src/$d" checkout -q --detach "$sha" && [ "$(git -C "$T/src/$d" rev-parse HEAD)" = "$sha" ]; }
step_landrun(){  clone landrun https://github.com/Zouuup/landrun.git 811cfff51ceaf3d9843708aa6d22e9b84ccac8b4 && cd "$T/src/landrun" && go build -o "$T/bin/landrun" ./cmd/landrun; }
step_lean(){ elan toolchain install "$LEAN"; }
step_l4e(){ clone lean4export https://github.com/leanprover/lean4export.git 076e8e57707e813375e8f9da8bf989799ace9680 && cd "$T/src/lean4export" && lake +"$LEAN" build && cp .lake/build/bin/lean4export "$T/bin/"; }
step_cmp(){ clone comparator https://github.com/leanprover/comparator.git d03acab154d269c06e60e4de7e4cc85deebff94b && cd "$T/src/comparator" && lake +"$LEAN" build && cp .lake/build/bin/comparator "$T/bin/"; }
echo 1000 >/proc/self/oom_score_adj 2>/dev/null; renice -n 15 $$ >/dev/null 2>&1
for s in elan go landrun lean l4e cmp; do
  [ -f "$L/DONE.$s" ] && continue
  run $s step_$s || { echo "BLOCKED at $s; see $L/$s.err"; exit 3; }
  touch "$L/DONE.$s"
done
echo ALL_TOOLS_BUILT
