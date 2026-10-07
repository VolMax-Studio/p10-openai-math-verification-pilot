#!/usr/bin/env bash
# Read-only, pinned, sparse fetch of openai/math into upstream/openai-math (git-ignored).
# Never vendors upstream into this repository. Verifies the resulting HEAD == PIN.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
REPO="https://github.com/openai/math"
PIN="adc7f1241b42e322a6451854ab7e4b4c146bf78a"       # observed 2026-10-07; see evidence/discovery/
DEST="$HERE/upstream/openai-math"
# Candidate subject directories (see candidate_results.md). ORDER IS NOT A RANKING.
PATHS=(
  /README.md /CONTENTS.md
  /lean/README.md /lean/lakefile.lean /lean/lake-manifest.json /lean/lean-toolchain
  /lean/formalization.yaml /lean/OAI.lean /lean/ComparatorChallenges/ /lean/docs/ /lean/patches/
  /lean/OAI/AlgebraicGeometry/AbhyankarSathaye/ /lean/OAI/Algebra/Universal/
  /lean/OAI/Combinatorics/InfiniteMatroid/ /lean/OAI/Combinatorics/SphericalRamsey/
  /lean/OAI/MathematicalPhysics/PlanarAnderson/
  "/preprints/An-explicit-noncoordinate-polynomial-with-affine-three-space-zero-fibre-September-24-2026/"
  "/preprints/Finite-Congruence-Lattices-Characterization-and-Undecidability-September-24-2026/"
  "/preprints/A-Counterexample-to-the-Infinite-Matroid-Packing-Covering-Conjecture-September-24-2026/"
  "/preprints/A-classification-of-finite-Euclidean-Ramsey-configurations-September-23-2026/"
  "/preprints/Pure-Point-Spectrum-for-the-Two-Dimensional-Anderson-Model-at-Every-Positive-Disorder-September-23-2026/"
)
[ "${FULL:-0}" = 1 ] && PATHS=("/*")   # FULL=1: whole tree (~3 GB, 130k files) for --inventory
if [ ! -d "$DEST/.git" ]; then
  mkdir -p "$DEST"; git -C "$DEST" init -q
  git -C "$DEST" remote add origin "$REPO"
fi
git -C "$DEST" config extensions.partialClone origin
git -C "$DEST" sparse-checkout init --no-cone
printf '%s\n' "${PATHS[@]}" | git -C "$DEST" sparse-checkout set --no-cone --stdin
git -C "$DEST" fetch -q --filter=blob:none origin "$PIN"
git -C "$DEST" checkout -q --detach "$PIN"
GOT="$(git -C "$DEST" rev-parse HEAD)"
[ "$GOT" = "$PIN" ] || { echo "FAIL: HEAD $GOT != pin $PIN" >&2; exit 1; }
echo "OK upstream at $GOT ($DEST)"
