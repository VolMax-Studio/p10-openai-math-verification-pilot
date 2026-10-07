#!/usr/bin/env bash
# Read-only discovery over the pinned upstream checkout. Regenerates evidence/discovery/*.json
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
UP="${UPSTREAM_DIR:-$HERE/upstream/openai-math}"
[ -d "$UP/.git" ] || { echo "FAIL: no upstream checkout at $UP (run scripts/fetch_upstream.sh)" >&2; exit 2; }
EXTRA=()
[ -d "$UP/lean/OAI" ] && [ "$(find "$UP/lean/OAI" -maxdepth 1 | wc -l)" -gt 5 ] && EXTRA+=(--inventory)
exec python3 -I "$HERE/scripts/inspect_candidates.py" "$UP" "$HERE/evidence/discovery" "${EXTRA[@]}" "$@"
