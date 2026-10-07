#!/usr/bin/env bash
# Remove fetched upstream and build products. Never touches evidence/ or reports/.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
rm -rf "$HERE/upstream/openai-math" "$HERE/work"
echo "cleaned"
