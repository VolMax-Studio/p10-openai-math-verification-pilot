#!/usr/bin/env python3
"""Final local RC rerun of stages C, B, D with dependency integrity as a FAIL-CLOSED P10 gate.

Usage: p10_rc_run.py a|c|b|d [--ws DIR]        (env: P10_TOOLS, P10_WS; see p10_run.py)

Threat-model result carried over from the first RC pass (evidence/stage_dep/): Lake and Comparator accept a dependency
checkout with local source changes if those changes still compile. Dependency integrity is therefore a P10 gate:
  pre-check (before any Comparator/Lean command)  ->  FAIL stops the stage, the verifier is NOT executed
  execute                                         ->  real tool exit status
  post-check (same state, same digest)            ->  FAIL makes the stage FAIL even if the tool returned success
Workspaces derive from the frozen manifest; `lake update` is never run. Evidence goes to evidence/stage_rcfinal_<x>/;
earlier evidence directories are never touched.
"""
import hashlib, json, os, pathlib, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p10_run as R

REPO = R.REPO
CACHE_ID_FILE = REPO / "profiles" / "mathlib_cache_identity.json"
D4_FILE = "Mathlib/Combinatorics/Matroid/Closure.lean"   # defines Matroid.Spanning, inside the subject's import closure


def git(d, *a):
    return R.sh(["git", "-C", str(d), *a])["stdout"]


def dep_state(ws):
    """Exact dependency state of the workspace vs the frozen manifest. ok == every package clean and at its pin."""
    man = json.loads((ws / "lake-manifest.json").read_text())["packages"]
    pk = ws / ".lake" / "packages"
    rows, probs = [], []
    present = sorted(p.name for p in pk.iterdir()) if pk.exists() else []
    if present != sorted(e["name"] for e in man): probs.append(f"package set differs from manifest: {present}")
    for e in man:
        d = pk / e["name"]
        head = git(d, "rev-parse", "HEAD").strip(); tree = git(d, "rev-parse", "HEAD^{tree}").strip()
        tracked = [l for l in git(d, "status", "--porcelain", "--untracked-files=no").splitlines() if l.strip()]
        untracked = [l for l in git(d, "status", "--porcelain", "--untracked-files=all").splitlines() if l.startswith("??") and ".lake/" not in l]
        clean = head == e["rev"] and not tracked and not untracked
        rows.append({"name": e["name"], "manifest_rev": e["rev"], "head": head, "head_tree": tree, "clean": clean,
                     "modified_tracked": tracked[:5], "untracked_non_lake": untracked[:5]})
        if not clean: probs.append(f"{e['name']}: head==pin {head == e['rev']}, modified {tracked[:2]}, untracked {untracked[:2]}")
    digest = R.sha("\n".join(f"{r['name']} {r['manifest_rev']} {r['head']} {r['head_tree']} {r['clean']}" for r in sorted(rows, key=lambda r: r["name"])).encode())
    return {"ok": not probs, "problems": probs, "state_digest": digest, "packages": rows,
            "identity_definition": "per package: manifest rev, actual HEAD, HEAD^{tree}, clean = HEAD==pin and no modified tracked file and no untracked non-.lake file"}


def cache_identity(cdir):
    h = hashlib.sha256(); lines = []; total = 0
    for p in sorted(x for x in cdir.rglob("*") if x.is_file()):
        f = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""): f.update(chunk)
        lines.append(f"{p.relative_to(cdir)} {p.stat().st_size} {f.hexdigest()}"); total += p.stat().st_size
    digest = R.sha("\n".join(lines).encode())
    return {"files": len(lines), "bytes": total, "digest": digest, "listing": lines,
            "definition": "sha256 over sorted lines `relative_path size sha256(content)` of every file in the private MATHLIB_CACHE_DIR after `lake exe cache get`"}


def prep(stage, ws):
    st = f"rcfinal_{stage}"; out = REPO / "evidence" / f"stage_{st}"
    if out.exists(): shutil.rmtree(out)
    cdir = R.WSROOT / f"cache-{stage}"
    if cdir.exists(): shutil.rmtree(cdir)
    cdir.mkdir(parents=True)
    R.ENV["MATHLIB_CACHE_DIR"] = str(cdir)
    res = {"stage": stage.upper(), "status": "NOT_EXECUTED", "steps": []}
    res["snapshot"] = R.snapshot(st, ws)
    res["snapshot"]["env"]["MATHLIB_CACHE_DIR"] = str(cdir)
    res["profile_check"] = R.profile_check()
    res["workspace_files_sha256"] = R.make_ws(ws)
    log = out / "logs"
    r = R.sh(["lake", "exe", "cache", "get"], cwd=ws, log=log, timeout=3600)
    res["steps"].append({k: r[k] for k in ("argv", "rc", "elapsed_s")})
    if r["rc"] != 0:
        res["status"] = "ENVIRONMENT_BLOCKED"; res["blocker"] = {"stderr_tail": r["stderr"][-1500:]}
        return res, log, cdir, st
    ci = cache_identity(cdir)
    (out / "mathlib_cache_listing.txt").write_text("\n".join(ci.pop("listing")) + "\n")
    res["mathlib_cache_identity"] = ci
    if CACHE_ID_FILE.exists():
        exp = json.loads(CACHE_ID_FILE.read_text())["digest"]
        res["mathlib_cache_identity"]["frozen_expected"] = exp; res["mathlib_cache_identity"]["matches_frozen"] = exp == ci["digest"]
    else:
        res["mathlib_cache_identity"]["matches_frozen"] = None
    return res, log, cdir, st


def summ(d):
    return {"ok": d["ok"], "state_digest": d["state_digest"], "problems": d["problems"], "packages": d["packages"]}


def guarded_comparator(ws, log):
    """pre-check -> (Comparator only if pre passes) -> post-check. Returns (record, raw result or None)."""
    pre = dep_state(ws); rec = {"deps_pre": summ(pre)}
    if not pre["ok"]:
        rec.update(executed=False, outcome="NOT_EXECUTED (P10 dependency pre-check FAIL)", ok=False); return rec, None
    r = R.comparator_run(ws, log)
    post = dep_state(ws)
    rec.update(executed=True, rc=r["rc"], elapsed_s=r["elapsed_s"], stdout_tail=r["stdout"][-1500:], stderr_tail=r["stderr"][-1200:],
               deps_post=summ(post), deps_unchanged=post["state_digest"] == pre["state_digest"])
    rec["ok"] = r["rc"] == 0 and post["ok"] and rec["deps_unchanged"]
    return rec, r


def write(res, st, name=None):
    out = REPO / "evidence" / f"stage_{st}"
    (out / (name or f"stage_{st}_result.json")).write_text(json.dumps(res, indent=1))
    print(f"{res['stage']}:", res["status"]); return res


def cache_gate(res):
    m = res["mathlib_cache_identity"].get("matches_frozen")
    return m is not False   # None = first observation (nothing frozen yet) is allowed; False = mismatch with the frozen digest fails


def stage_c(ws):
    res, log, cdir, st = prep("c", ws)
    if res["status"] == "ENVIRONMENT_BLOCKED": return write(res, st)
    rec, r = guarded_comparator(ws, log)
    res["comparator"] = rec; res["mismatched_sources_after"] = R.verify_ws(ws)
    res["status"] = "PASS" if rec["ok"] and not res["mismatched_sources_after"] and not res["profile_check"] and cache_gate(res) else "FAIL"
    return write(res, st)


def stage_b(ws):
    res, log, cdir, st = prep("b", ws)
    if res["status"] == "ENVIRONMENT_BLOCKED": return write(res, st)
    pre = dep_state(ws); res["deps_pre"] = summ(pre)
    if not pre["ok"]:
        res["status"] = "FAIL"; res["reason"] = "dependency pre-check FAIL; Lean not executed"; return write(res, st)
    b = R.sh(["lake", "build", "OAI", "ComparatorChallenges"], cwd=ws, log=log, timeout=7200)
    res["build"] = {k: b[k] for k in ("argv", "rc", "elapsed_s")}; res["build"]["stdout_tail"] = b["stdout"][-1200:]; res["build"]["stderr_tail"] = b["stderr"][-800:]
    sorry = [l for l in (b["stdout"] + b["stderr"]).splitlines() if "sorry" in l]
    res["sorry_warnings"] = sorry; res["sorry_in_solution_closure"] = [l for l in sorry if "OAI/" in l or "OAI." in l]
    probe = "import OAI.Combinatorics.InfiniteMatroid.Main\n#print axioms OAI.InfiniteMatroidCounterexample.main\n"
    (ws / "P10Probe.lean").write_text(probe); res["probe_sha256"] = R.sha(probe.encode())
    p = R.sh(["lake", "env", "lean", "P10Probe.lean"], cwd=ws, log=log, timeout=1800)
    res["axioms"] = {"rc": p["rc"], "stdout": p["stdout"].strip(), "stderr_tail": p["stderr"][-400:]}
    permitted = set(json.loads(R.git_blob(R.CFG))["permitted_axioms"])
    got = set(a.strip() for a in p["stdout"].split("[")[-1].split("]")[0].split(",")) if "depends on axioms" in p["stdout"] else None
    res["axioms_set"] = sorted(got) if got is not None else None
    post = dep_state(ws); res["deps_post"] = summ(post); res["deps_unchanged"] = post["state_digest"] == pre["state_digest"]
    res["mismatched_sources_after"] = R.verify_ws(ws)
    ok = (b["rc"] == 0 and p["rc"] == 0 and got is not None and got <= permitted and not res["sorry_in_solution_closure"] and post["ok"]
          and res["deps_unchanged"] and not res["mismatched_sources_after"] and not res["profile_check"] and cache_gate(res))
    res["status"] = "PASS" if ok else "FAIL"
    return write(res, st)


def stage_d(ws):
    res, log, cdir, st = prep("d", ws)
    if res["status"] == "ENVIRONMENT_BLOCKED": return write(res, st)
    c0, _ = guarded_comparator(ws, log); res["control_before"] = c0
    if not c0["ok"]:
        res["status"] = "FAIL"; res["reason"] = "control (unmodified) did not pass; mutations not interpretable"; return write(res, st)
    rows = []
    for mid, rel, desc, fn in R.MUTATIONS:                       # D1, D2, D3, D5b: P10-source / config mutations, dependency tree untouched
        fp = ws / rel; orig = fp.read_bytes(); new = fn(orig)
        if new == orig: rows.append({"id": mid, "status": "FAIL", "reason": "mutation was a no-op"}); continue
        fp.write_bytes(new); rec, r = guarded_comparator(ws, log); fp.write_bytes(orig)
        text = (r["stdout"] + r["stderr"]) if r else ""
        rows.append({"id": mid, "kind": "comparator negative control", "description": desc, "mutated_file": rel, "mutated_sha256": R.sha(new),
                     "restored_ok": R.sha(fp.read_bytes()) == R.sha(orig), "deps_pre_ok": rec["deps_pre"]["ok"], "executed": rec["executed"],
                     "comparator_rc": rec.get("rc"), "rejected": bool(rec["executed"] and rec["rc"] != 0), "deps_post_ok": rec.get("deps_post", {}).get("ok"),
                     "key_lines": [l for l in text.splitlines() if any(k in l.lower() for k in ("error", "sorry", "axiom", "mismatch", "not found", "panic", "exception"))][-8:]})
    # D4: P10-layer dependency-source controls. Expected: pre-check FAIL and Comparator NOT EXECUTED; after restore the clean control runs again.
    pkg = ws / ".lake" / "packages"; d4 = []
    def d4case(cid, desc, mutate, restore):
        mutate(); rec, r = guarded_comparator(ws, log); restore(); after = dep_state(ws)
        d4.append({"id": cid, "kind": "P10 dependency gate (NOT a Comparator negative control)", "description": desc,
                   "deps_pre_ok": rec["deps_pre"]["ok"], "deps_pre_problems": rec["deps_pre"]["problems"][:3], "comparator_executed": rec["executed"],
                   "gate_blocked_execution": (not rec["deps_pre"]["ok"]) and not rec["executed"], "restored_clean": after["ok"]})
    mf = pkg / "mathlib" / D4_FILE; o1 = mf.read_bytes()
    d4case("D4", f"dependency source mutated: comment appended to Mathlib `{D4_FILE}` (compiles; this is the M1 case Comparator accepted in the RC pass)",
           lambda: mf.write_bytes(o1 + b"\n-- p10 D4 mutation\n"), lambda: git(pkg / "mathlib", "checkout", "--", D4_FILE))
    inj = pkg / "batteries" / "Batteries" / "P10Injected.lean"
    d4case("D4b", "untracked .lean file injected into dependency `batteries`", lambda: inj.write_text("-- injected\n"), lambda: inj.unlink())
    pin = [e["rev"] for e in json.loads((ws / "lake-manifest.json").read_text())["packages"] if e["name"] == "aesop"][0]
    d4case("D4c", "dependency `aesop` HEAD moved off its pin by a local empty commit",
           lambda: git(pkg / "aesop", "-c", "user.name=p10", "-c", "user.email=p10@invalid", "commit", "-q", "--allow-empty", "-m", "p10 D4c"),
           lambda: git(pkg / "aesop", "reset", "-q", "--hard", pin))
    mm = ws / "lake-manifest.json"; om = mm.read_bytes()
    rev = b"d13f23b723b8a846827a245b89c10fc7d3f11612"; mm.write_bytes(om.replace(rev, rev[:-1] + b"3", 1))
    found = R.verify_ws(ws); mm.write_bytes(om)
    d4.append({"id": "D4d", "kind": "P10 profile hash check (workspace manifest rev altered by one hex digit)", "detected": "lake-manifest.json" in found, "findings": found, "restored_clean": not R.verify_ws(ws)})
    c1, _ = guarded_comparator(ws, log); res["control_after_restore"] = c1
    res["mutations"] = rows; res["dependency_gate_controls"] = d4
    ok = (all(r.get("rejected") and r.get("restored_ok") and r.get("deps_pre_ok") and r.get("deps_post_ok") for r in rows)
          and all((x.get("gate_blocked_execution") and x["restored_clean"]) if x["id"] != "D4d" else (x["detected"] and x["restored_clean"]) for x in d4)
          and c1["ok"] and not R.verify_ws(ws) and not res["profile_check"] and cache_gate(res))
    res["status"] = "PASS" if ok else "FAIL"
    res["caveats"] = ["D3 is rejected through a lean4export PANIC, not a clean diagnostic", "D1 edits the trusted challenge file: it shows statement binding, not resistance to a malicious challenge",
                      "D4/D4b/D4c/D4d test P10's gates; Comparator is deliberately not executed there", "a rejection counts only with key_lines showing the intended reason"]
    return write(res, st)


def stage_a():
    st = "rcfinal_a"; out = REPO / "evidence" / f"stage_{st}"
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    r = R.sh([sys.executable, "-I", str(REPO / "scripts/stage_a.py"), str(R.UP), str(REPO / "subject.lock.json"), "--json", str(out / "stage_a_result.json")])
    (out / "stage_a_stdout.txt").write_text(r["stdout"] + r["stderr"])
    t = R.sh([sys.executable, "-I", str(REPO / "scripts/tamper_tests.py"), str(R.UP), str(REPO / "subject.lock.json"), str(out / "tamper_tests.json")])
    (out / "tamper_stdout.txt").write_text(t["stdout"][-3000:] + t["stderr"][-500:])
    res = {"stage": "A", "status": "PASS" if r["rc"] == 0 and t["rc"] == 0 else "FAIL", "stage_a_last_line": r["stdout"].strip().splitlines()[-1:], "tamper_last_line": t["stdout"].strip().splitlines()[-1:]}
    return write(res, st, "summary.json")


def freeze_cache_identity(src):
    """Write profiles/mathlib_cache_identity.json from a finished stage result (done once, after C; B and D must then match)."""
    ci = json.loads(pathlib.Path(src).read_text())["mathlib_cache_identity"]
    CACHE_ID_FILE.write_text(json.dumps({"digest": ci["digest"], "files": ci["files"], "bytes": ci["bytes"], "definition": ci["definition"],
                                         "source": "first observation, stage C of the final RC rerun; B and D downloaded independently and must match",
                                         "trust": "identifies the downloaded payload; does NOT make the Mathlib cache provider or its contents trusted"}, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    ws = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[2] == "--ws" else R.WSROOT / cmd
    if cmd == "a": sys.exit(0 if stage_a()["status"] == "PASS" else 4)
    elif cmd == "freeze-cache": freeze_cache_identity(sys.argv[2])
    else: sys.exit(0 if {"c": stage_c, "b": stage_b, "d": stage_d}[cmd](ws)["status"] == "PASS" else 4)
