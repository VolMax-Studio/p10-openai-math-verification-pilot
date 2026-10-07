#!/usr/bin/env python3
"""RC hardening 2: dependency-SOURCE mutation controls (disposable workspace only).

Question: if a file of the pinned Mathlib checkout inside the workspace is altered (not just the manifest string),
(a) does P10's dependency check see it, and (b) what do Lake/Comparator do? (b) is recorded, never assumed.
Comparator trusts the import closure; it is NOT expected to notice a consistently mutated Mathlib. The control that is
expected to bite is verify_deps(): every package checkout must be at its manifest rev with no modified tracked file.
Usage: p10_dep_mutation.py [--ws DIR]
"""
import json, os, pathlib, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p10_run as R

TARGET = "Mathlib/Combinatorics/Matroid/Closure.lean"   # defines Matroid.Spanning, imported by the subject's closure
MUT = [
    ("M1", "comment-only change appended to the Mathlib file defining `Matroid.Spanning` (still compiles)",
     lambda b: b + b"\n-- p10 dependency mutation M1\n"),
    ("M2", "definition change in that file: `Spanning.closure_eq` weakened from `=` to `⊆`",
     lambda b: b.replace("closure_eq : M.closure S = M.E".encode(), "closure_eq : M.closure S ⊆ M.E".encode(), 1)),
]


def verify_deps(ws):
    """Each package in the workspace manifest must be checked out at its pinned rev with no modified tracked file."""
    probs = []
    for e in json.loads((ws / "lake-manifest.json").read_text())["packages"]:
        d = ws / ".lake" / "packages" / e["name"]
        head = R.sh(["git", "-C", str(d), "rev-parse", "HEAD"])["stdout"].strip()
        if head != e["rev"]: probs.append(f"{e['name']}: HEAD {head[:12]} != pin {e['rev'][:12]}")
        st = R.sh(["git", "-C", str(d), "status", "--porcelain", "--untracked-files=no"])["stdout"].strip()
        if st: probs.append(f"{e['name']}: modified tracked files: {st.splitlines()[:3]}")
    return probs


def main(ws):
    res, log = R.prepare("dep", ws)
    if res["status"] == "ENVIRONMENT_BLOCKED": return R.finish(res, "dep")
    res["baseline_verify_deps"] = verify_deps(ws)
    c0 = R.comparator_run(ws, log)
    res["control_before"] = {"rc": c0["rc"], "elapsed_s": c0["elapsed_s"], "last_line": c0["stdout"].strip().splitlines()[-1:]}
    if res["baseline_verify_deps"] or c0["rc"] != 0:
        res["status"] = "FAIL"; res["reason"] = "baseline not clean / control failed"; return R.finish(res, "dep")
    fp = ws / ".lake" / "packages" / "mathlib" / TARGET
    orig = fp.read_bytes(); rows = []
    for mid, desc, fn in MUT:
        new = fn(orig)
        if new == orig: rows.append({"id": mid, "status": "FAIL", "reason": "mutation was a no-op"}); continue
        fp.write_bytes(new)
        found = verify_deps(ws)                      # P10's check, before anything is built
        r = R.comparator_run(ws, log)                # what the verifier does with the mutated dependency (observation)
        R.sh(["git", "-C", str(ws / ".lake/packages/mathlib"), "checkout", "--", TARGET])
        rows.append({"id": mid, "description": desc, "file": TARGET, "mutated_sha256": R.sha(new),
                     "verify_deps_detected": bool(found), "verify_deps_findings": found,
                     "comparator_rc": r["rc"], "comparator_elapsed_s": r["elapsed_s"],
                     "comparator_outcome": "ACCEPTED" if r["rc"] == 0 else "REJECTED",
                     "comparator_key_lines": [l for l in (r["stdout"] + r["stderr"]).splitlines() if any(k in l.lower() for k in ("error", "okay", "illegal", "mismatch"))][-8:],
                     "restored_clean": not verify_deps(ws) and R.sha(fp.read_bytes()) == R.sha(orig)})
    c1 = R.comparator_run(ws, log)
    res["control_after_restore"] = {"rc": c1["rc"], "elapsed_s": c1["elapsed_s"], "last_line": c1["stdout"].strip().splitlines()[-1:], "verify_deps": verify_deps(ws)}
    res["mutations"] = rows
    res["status"] = "PASS" if rows and all(r.get("verify_deps_detected") and r.get("restored_clean") for r in rows) and c1["rc"] == 0 and not res["control_after_restore"]["verify_deps"] else "FAIL"
    res["interpretation"] = ("PASS here means only: P10's verify_deps() detects a modified dependency checkout and the control passes before/after. "
                             "If comparator_outcome is ACCEPTED for a mutation, Comparator itself does NOT guard the dependency source; that guarantee comes solely from the git pin + verify_deps().")
    return R.finish(res, "dep")


if __name__ == "__main__":
    ws = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--ws" else R.WSROOT / "dep"
    sys.exit(0 if main(ws)["status"] == "PASS" else 4)
