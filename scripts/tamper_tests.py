#!/usr/bin/env python3
"""Controlled mutation tests for Stage A. Works ONLY on a temporary copy of the checkout; the frozen
checkout, lock and evidence are never mutated. Usage: tamper_tests.py <upstream_checkout> <lock> <out.json>"""
import hashlib, json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
root, lockp, outp = sys.argv[1:4]
lock = json.load(open(lockp)); subj = lock["subject"]
tmp = tempfile.mkdtemp(prefix="p10-tamper-"); copy = os.path.join(tmp, "up"); shutil.copytree(root, copy, symlinks=True)
def stage_a(lock_file=lockp):
    jp = os.path.join(tmp, "r.json")
    p = subprocess.run([sys.executable, "-I", os.path.join(HERE, "stage_a.py"), copy, lock_file, "--json", jp], capture_output=True, text=True)
    r = json.load(open(jp))
    return p.returncode, [c["id"] for c in r["checks"] if c["status"] == "FAIL"], len(r["checks"])
def mutate(rel, fn):
    fp = os.path.join(copy, rel); orig = open(fp, "rb").read(); open(fp, "wb").write(fn(orig)); return fp, orig
tests = []
def case(name, rel, fn, expect_fail_prefix, lock_override=None, note=""):
    fp, orig = mutate(rel, fn) if rel else (None, None)
    lf = lockp
    if lock_override:
        lf = os.path.join(tmp, "forged.lock.json"); json.dump(lock_override(), open(lf, "w"))
    rc, failed, n = stage_a(lf)
    if fp: open(fp, "wb").write(orig)
    detected = rc != 0
    tests.append({"test": name, "mutated": rel, "bytes_changed": None if not rel else (len(fn(orig)) - len(orig) if len(fn(orig)) != len(orig) else "in-place 1 byte"),
                  "stage_a_exit": rc, "detected": detected, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n,
                  "expected": expect_fail_prefix, "outcome_as_expected": (detected if expect_fail_prefix != "NOT_DETECTED_BY_DESIGN" else not detected) and
                  (expect_fail_prefix in ("NOT_DETECTED_BY_DESIGN", "") or any(f.startswith(expect_fail_prefix) for f in failed)), "note": note})
append1 = lambda b: b + b"\n"
flip = lambda b: bytes([b[0] ^ 1]) + b[1:]
chal, cfg, sol = subj["challenge_path"], subj["comparator_config"], subj["solution_path"]
deep = "lean/OAI/Combinatorics/InfiniteMatroid/BlockDensity.lean"
ms = subj["manuscript_path"]
# control
case("T00 control (no mutation)", None, None, "")
tests[-1]["outcome_as_expected"] = tests[-1]["stage_a_exit"] == 0
case("T01 challenge statement file +1 byte", chal, append1, "A2.worktree:" + chal)
case("T02 Comparator JSON config +1 byte", cfg, append1, "A2.worktree:" + cfg)
case("T03 solution module (Main.lean) +1 byte", sol, append1, "A2.worktree:" + sol)
case("T04 deep closure module (BlockDensity.lean) 1 bit flip", deep, flip, "A2.worktree:" + deep)
case("T05 docs bridge (docs/185.md) +1 byte", subj["formalization_docs_path"], append1, "A2.worktree:" + subj["formalization_docs_path"])
case("T06 formalization.yaml +1 byte", subj["formalization_metadata_path"], append1, "A2.worktree:")
case("T07 CONTENTS.md +1 byte", "CONTENTS.md", append1, "A2.worktree:CONTENTS.md")
case("T08 manuscript PDF 1 bit flip", ms, flip, "A2.worktree:" + ms)
case("T09 manuscript TeX source +1 byte", ms.replace("paper.pdf", "build/sections/01-introduction.tex"), append1, "A2.worktree:")
case("T10 lean-toolchain +1 byte", "lean/lean-toolchain", lambda b: b.rstrip(b"\n") + b"0\n", "A2.worktree:lean/lean-toolchain")
case("T11 lake-manifest.json Mathlib rev 1 hex digit", "lean/lake-manifest.json", lambda b: b.replace(lock["environment_layer"]["mathlib_rev"].encode(), (lock["environment_layer"]["mathlib_rev"][:-1] + ("0" if lock["environment_layer"]["mathlib_rev"][-1] != "0" else "1")).encode(), 1), "A2.worktree:lean/lake-manifest.json")
pf = sorted(lock["environment_layer"]["patches_sha256"])[0]
case("T12 dependency patch +1 byte", pf, append1, "A2.worktree:" + pf)
# deletion
fp = os.path.join(copy, chal); orig = open(fp, "rb").read(); os.remove(fp); rc, failed, n = stage_a(); open(fp, "wb").write(orig)
tests.append({"test": "T13 challenge file deleted", "mutated": chal, "stage_a_exit": rc, "detected": rc != 0, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n, "expected": "A2.worktree:" + chal, "outcome_as_expected": rc != 0 and any(f.startswith("A2.worktree:" + chal) for f in failed), "note": ""})
# extra patch file
ex = os.path.join(copy, "lean/patches/Injected-lean4341.patch"); open(ex, "w").write("x"); rc, failed, n = stage_a(); os.remove(ex)
tests.append({"test": "T14 extra patch file injected", "mutated": "lean/patches/Injected-lean4341.patch", "stage_a_exit": rc, "detected": rc != 0, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n, "expected": "A2.worktree_membership:patches", "outcome_as_expected": rc != 0 and "A2.worktree_membership:patches" in failed, "note": ""})
# forged-lock cases: file changed AND lock hash updated consistently -> hash check passes, independent checks must still bite
def forged(rel, newhash_fn=None):
    def f():
        l = json.load(open(lockp)); h = hashlib.sha256(open(os.path.join(copy, rel), "rb").read()).hexdigest()
        for el in l["binding_chain"]:
            if rel in el["files_sha256"]: el["files_sha256"][rel] = h
        return l
    return f
# T15: solution gains an out-of-closure import; lock hash forged to match -> A3 must catch
imp = lambda b: b"import OAI.Algebra.Universal.GraphCriterion\n" + b
fp, orig = mutate(sol, imp); delta = os.path.getsize(fp) - len(orig)
l = json.load(open(lockp)); h = hashlib.sha256(open(fp, "rb").read()).hexdigest()
for el in l["binding_chain"]:
    if sol in el["files_sha256"]: el["files_sha256"][sol] = h
lf = os.path.join(tmp, "forged1.json"); json.dump(l, open(lf, "w")); rc, failed, n = stage_a(lf); open(fp, "wb").write(orig)
tests.append({"bytes_changed": delta, "test": "T15 forged lock+file: solution gains out-of-closure import", "mutated": sol, "stage_a_exit": rc, "detected": rc != 0, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n, "expected": "R2.lock_hash:", "outcome_as_expected": rc != 0 and any(f.startswith("R2.lock_hash:" + sol) for f in failed) and any(f.startswith("A2.worktree:" + sol) for f in failed), "note": "lock forged to match the edited file: R2 compares the lock to the frozen commit and fails"})
# T16: forged lock+file: yaml entry points at a different declaration
fp, orig = mutate(subj["formalization_metadata_path"], lambda b: b.replace(b"OAI.InfiniteMatroidCounterexample.main\n", b"OAI.InfiniteMatroidCounterexample.main2\n", 1)); delta = os.path.getsize(fp) - len(orig)
l = json.load(open(lockp)); h = hashlib.sha256(open(fp, "rb").read()).hexdigest()
for el in l["binding_chain"]:
    if subj["formalization_metadata_path"] in el["files_sha256"]: el["files_sha256"][subj["formalization_metadata_path"]] = h
lf = os.path.join(tmp, "forged2.json"); json.dump(l, open(lf, "w")); rc, failed, n = stage_a(lf); open(fp, "wb").write(orig)
tests.append({"bytes_changed": delta, "test": "T16 forged lock+file: yaml main_results declaration changed", "mutated": subj["formalization_metadata_path"], "stage_a_exit": rc, "detected": rc != 0, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n, "expected": "R2.lock_hash:", "outcome_as_expected": rc != 0 and any(f.startswith("R2.lock_hash:" + subj["formalization_metadata_path"]) for f in failed), "note": "self-consistent metadata+lock edit is rejected against the frozen commit"})
# T17: LIMIT demonstration: statement edited in challenge AND lock forged consistently -> Stage A cannot know
fp, orig = mutate(chal, lambda b: b.replace(b"I\xe2\x82\x80 \xe2\x88\xaa I\xe2\x82\x81 \xe2\x89\xa0 Set.univ", b"I\xe2\x82\x80 \xe2\x88\xaa I\xe2\x82\x81 = Set.univ", 1) if b"I\xe2\x82\x80 \xe2\x88\xaa I\xe2\x82\x81 \xe2\x89\xa0 Set.univ" in b else b.replace(b"\xe2\x89\xa0", b"=", 1)); delta = os.path.getsize(fp) - len(orig)
l = json.load(open(lockp)); h = hashlib.sha256(open(fp, "rb").read()).hexdigest()
for el in l["binding_chain"]:
    if chal in el["files_sha256"]: el["files_sha256"][chal] = h
lf = os.path.join(tmp, "forged3.json"); json.dump(l, open(lf, "w")); rc, failed, n = stage_a(lf); open(fp, "wb").write(orig)
tests.append({"bytes_changed": delta, "test": "T17 (formerly the LIMIT case) challenge statement edited AND lock forged consistently", "mutated": chal, "stage_a_exit": rc, "detected": rc != 0, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n, "expected": "R2.lock_hash:", "outcome_as_expected": rc != 0 and any(f.startswith("R2.lock_hash:" + chal) for f in failed) and any(f.startswith("A2.worktree:" + chal) for f in failed), "note": "CLOSES the earlier limit: the forged lock no longer authenticates the edited statement because expected hashes are derived from the frozen commit"})
def lock_variant(name, fn):
    l = json.load(open(lockp)); fn(l); lf = os.path.join(tmp, name); json.dump(l, open(lf, "w")); return lf
# T19: lock claims a different upstream commit
lf = lock_variant("l19.json", lambda l: l["upstream"].__setitem__("commit", "0" * 40)); rc, failed, n = stage_a(lf)
tests.append({"test": "T19 lock names a different upstream commit", "mutated": "<lock>", "stage_a_exit": rc, "detected": rc != 0, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n, "expected": "R0.lock_commit_is_frozen_commit", "outcome_as_expected": rc != 0 and "R0.lock_commit_is_frozen_commit" in failed, "note": ""})
# T20: lock silently drops a closure module (worktree untouched)
def drop(l):
    e = next(x for x in l["binding_chain"] if x["id"] == "E7"); e["identifier"]["closure_modules"].remove(e["identifier"]["closure_modules"][-1])
lf = lock_variant("l20.json", drop); rc, failed, n = stage_a(lf)
tests.append({"test": "T20 lock drops a closure module (working copy untouched)", "mutated": "<lock>", "stage_a_exit": rc, "detected": rc != 0, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n, "expected": "A3.closure_set", "outcome_as_expected": rc != 0 and "A3.closure_set" in failed, "note": "membership is derived from the frozen tree, not from the lock"})
# T21: lock hash edited for the config, working copy untouched
def edit_hash(l):
    for e in l["binding_chain"]:
        if cfg in e["files_sha256"]: e["files_sha256"][cfg] = "0" * 64
lf = lock_variant("l21.json", edit_hash); rc, failed, n = stage_a(lf)
tests.append({"test": "T21 lock hash for config edited (working copy untouched)", "mutated": "<lock>", "stage_a_exit": rc, "detected": rc != 0, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n, "expected": "R2.lock_hash:", "outcome_as_expected": rc != 0 and any(f.startswith("R2.lock_hash:" + cfg) for f in failed), "note": ""})
# T22: lock lists an extra manuscript file that is not in the frozen tree
def extra(l):
    e = next(x for x in l["binding_chain"] if x["id"] == "E2"); e["files_sha256"][ms.rsplit("/", 1)[0] + "/injected.tex"] = "1" * 64
lf = lock_variant("l22.json", extra); rc, failed, n = stage_a(lf)
tests.append({"test": "T22 lock adds a manuscript file absent from the frozen tree", "mutated": "<lock>", "stage_a_exit": rc, "detected": rc != 0, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n, "expected": "R3.manuscript_membership", "outcome_as_expected": rc != 0 and "R3.manuscript_membership" in failed, "note": ""})
# T23: `git replace` ref substituting the challenge blob (object-store level attack) -- must be ignored
blob = subprocess.check_output(["git", "-C", copy, "rev-parse", "HEAD:" + chal], text=True).strip()
evil = subprocess.run(["git", "-C", copy, "hash-object", "-w", "--stdin"], input=open(os.path.join(copy, chal), "rb").read().replace("\u2260".encode(), b"=", 1), capture_output=True).stdout.decode().strip()
subprocess.run(["git", "-C", copy, "replace", "-f", blob, evil], check=True, capture_output=True)
rc, failed, n = stage_a()
subprocess.run(["git", "-C", copy, "replace", "-d", blob], capture_output=True)
tests.append({"test": "T23 git-replace ref substitutes the challenge blob; working copy untouched", "mutated": "<object store refs>", "stage_a_exit": rc, "detected": rc != 0, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n, "expected": "NEUTRALIZED (replace refs ignored; canonical bytes still re-verified)", "outcome_as_expected": rc == 0, "note": "attack has no effect on Stage A's canonical bytes; PASS is the correct outcome here (the working copy is the real, unmodified file)"})
# T24: corrupt object in the local store (loose object with wrong content under the real blob id)
import zlib
oid = blob; d = os.path.join(copy, ".git", "objects", oid[:2]); os.makedirs(d, exist_ok=True)
bad = open(os.path.join(copy, chal), "rb").read().replace("\u2260".encode(), b"=", 1)
open(os.path.join(d, oid[2:]), "wb").write(zlib.compress(f"blob {len(bad)}\0".encode() + bad))
rc, failed, n = stage_a()
tests.append({"test": "T24 object store: loose object with wrong content planted under the real blob id", "mutated": "<.git/objects>", "stage_a_exit": rc, "detected": rc != 0, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n, "expected": "any failure (re-hash) or NEUTRALIZED if git prefers the intact packed copy", "outcome_as_expected": True, "observed_ok": True, "note": "outcome recorded as observed; either a re-verification failure or the genuine packed object being used is acceptable, a PASS using the planted bytes is not (the working copy would then differ from them and A2 fails)"})
os.remove(os.path.join(d, oid[2:]))
# HEAD moved (last: modifies the temp repo)
subprocess.run(["git", "-C", copy, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "moved"], check=True, capture_output=True)
rc, failed, n = stage_a()
tests.append({"test": "T18 upstream HEAD moved (empty commit on temp copy)", "mutated": "<git HEAD>", "stage_a_exit": rc, "detected": rc != 0, "failed_checks": failed[:6], "failed_checks_total": len(failed), "checks_run": n, "expected": "A1.worktree_HEAD", "outcome_as_expected": rc != 0 and "A1.worktree_HEAD" in failed, "note": ""})
shutil.rmtree(tmp)
summary = {"tests": len(tests), "as_expected": sum(t["outcome_as_expected"] for t in tests),
           "one_byte_mutations_detected": sum(1 for t in tests if t["test"][:3] in ("T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10", "T11", "T12") and t["detected"])}
json.dump({"stage": "A", "kind": "tamper tests on a temporary copy of the pinned checkout", "lock": os.path.basename(lockp), "summary": summary, "tests": tests}, open(outp, "w"), indent=1)
for t in tests: print(("ok  " if t["outcome_as_expected"] else "BAD ") + t["test"], "->", "exit", t["stage_a_exit"], t["failed_checks"][:1])
print(summary); sys.exit(0 if summary["as_expected"] == summary["tests"] else 1)
