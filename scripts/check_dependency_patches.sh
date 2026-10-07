#!/usr/bin/env bash
# NETWORK. For each lean/patches/*-lean4341.patch: hash it, fetch the pinned dependency commit
# (blob:none, depth 1), and test `git apply --check`. Writes evidence/discovery/dependency_patch_check.tsv
# columns: package, sha256(patch), manifest_rev, fetched_head, apply_check, files_touched
set -uo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
L="${UPSTREAM_DIR:-$HERE/upstream/openai-math}/lean"
OUT="$HERE/evidence/discovery/dependency_patch_check.tsv"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
printf 'package\tpatch_sha256\tmanifest_rev\tfetched_head\tapply_check\tfiles_touched\n' > "$OUT"
python3 -I - "$L" > "$W/deps.tsv" <<'PY'
import json,sys,os
L=sys.argv[1]
for p in json.load(open(L+'/lake-manifest.json'))['packages']:
    n=p['name'].strip('«»')
    if os.path.exists(f'{L}/patches/{n}-lean4341.patch'): print(n,p['url'],p['rev'],sep='\t')
PY
while IFS=$'\t' read -r n url rev; do
  d="$W/$n"; patch="$L/patches/$n-lean4341.patch"; h=$(sha256sum "$patch" | cut -d' ' -f1)
  git init -q "$d"; git -C "$d" remote add origin "$url"
  if git -C "$d" fetch -q --filter=blob:none --depth 1 origin "$rev" 2>/dev/null && git -C "$d" checkout -q --detach FETCH_HEAD 2>/dev/null; then
    got=$(git -C "$d" rev-parse HEAD)
    git -C "$d" apply --check "$patch" 2>/dev/null && ap=APPLIES || ap=FAILS
    files=$(git -C "$d" apply --numstat "$patch" 2>/dev/null | wc -l)
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$n" "$h" "$rev" "$got" "$ap" "$files" >> "$OUT"
  else printf '%s\t%s\t%s\tFETCH_FAILED\t-\t-\n' "$n" "$h" "$rev" >> "$OUT"; fi
  rm -rf "$d"
done < "$W/deps.tsv"
echo "wrote $OUT ($(($(wc -l < "$OUT")-1)) packages)"
