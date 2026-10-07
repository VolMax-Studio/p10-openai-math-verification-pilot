#!/usr/bin/env python3
"""Stage C / B / D runner for profile p10-frozen-v1 on the minimal InfiniteMatroid workspace.

Usage:  p10_run.py snapshot|c|b|d  [--ws DIR]        (env: P10_TOOLS, P10_WS)
Every external command is logged verbatim (argv, stdout, stderr, exit status, elapsed) under evidence/stage_<x>/.
No wrapper, stub or cached verdict is ever treated as evidence: PASS comes only from the real tool's exit status.
Sources are read from git objects of the frozen upstream commit, never from a working copy.
"""
import hashlib, json, os, shutil, subprocess, sys, time, pathlib, shlex

REPO = pathlib.Path(__file__).resolve().parent.parent
FROZEN = "adc7f1241b42e322a6451854ab7e4b4c146bf78a"
UP = REPO / "upstream" / "openai-math"
LOCK = json.load(open(REPO / "subject.lock.json"))
TOOLS = pathlib.Path(os.environ.get("P10_TOOLS", REPO.parent / "p10-tools"))
WSROOT = pathlib.Path(os.environ.get("P10_WS", REPO.parent / "p10-ws"))
LEAN = "leanprover/lean4:v4.34.1"
CFG = "lean/ComparatorChallenges/InfiniteMatroid.json"
ENV = dict(os.environ, ELAN_HOME=str(TOOLS / "elan"),
           PATH=f"{TOOLS/'bin'}:{TOOLS/'elan'/'bin'}:{os.environ['PATH']}",
           COMPARATOR_LANDRUN=str(TOOLS / "bin" / "landrun"),
           COMPARATOR_LEAN4EXPORT=str(TOOLS / "bin" / "lean4export"))
_bus = pathlib.Path(f"/run/user/{os.getuid()}")
if (_bus / "bus").exists():  # session bus exists but a detached launcher may not export its address
    ENV.setdefault("XDG_RUNTIME_DIR", str(_bus))
    ENV.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path={_bus}/bus")


def sha(b): return hashlib.sha256(b).hexdigest()


def sh(argv, cwd=None, log=None, timeout=None, env=None):
    """Run argv, return dict(argv,rc,elapsed,stdout,stderr); append full record to log dir."""
    t = time.time()
    try:
        p = subprocess.run(argv, cwd=cwd, env=env or ENV, capture_output=True, timeout=timeout)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        rc, out, err = 124, e.stdout or b"", (e.stderr or b"") + b"\nTIMEOUT"
    r = dict(argv=argv, cwd=str(cwd) if cwd else None, rc=rc, elapsed_s=round(time.time() - t, 1),
             stdout=out.decode(errors="replace"), stderr=err.decode(errors="replace"))
    if log:
        log.mkdir(parents=True, exist_ok=True)
        n = len(list(log.glob("*.json")))
        (log / f"{n:03d}.json").write_text(json.dumps(r, indent=1))
    return r


def git_blob(path):
    return subprocess.check_output(["git", "-C", str(UP), "show", f"{FROZEN}:{path}"],
                                   env=dict(os.environ, GIT_NO_REPLACE_OBJECTS="1"))


def source_files():
    files = []
    for b in LOCK["binding_chain"]:
        if b["role"].startswith("Comparator") or b["role"].startswith("solution"):
            files += list(b["files_sha256"])
    files.append("lean/lean-toolchain")
    return sorted(set(files)), {**{k: v for b in LOCK["binding_chain"] for k, v in (b.get("files_sha256") or {}).items()},
                                **LOCK["environment_layer"]["files_sha256"]}


def snapshot(stage, ws):
    d = {"stage": stage, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "uname": os.uname().release, "uid": os.getuid(), "ws": str(ws)}
    g = lambda *a: sh(list(a))["stdout"].strip() + sh(list(a))["stderr"].strip()
    st = shutil.disk_usage(WSROOT if WSROOT.exists() else WSROOT.parent)
    d["disk_free_gib"] = round(st.free / 2**30, 1)
    d["mem"] = g("free", "-m")
    d["lean"] = g("lean", "+" + LEAN, "--version")
    d["lake"] = g("lake", "+" + LEAN, "--version")
    d["tool_commits"] = {n: sh(["git", "-C", str(TOOLS / "src" / n), "rev-parse", "HEAD"])["stdout"].strip()
                         for n in ("comparator", "lean4export", "landrun")}
    d["tool_binary_sha256"] = {n: sha((TOOLS / "bin" / n).read_bytes()) for n in ("comparator", "lean4export", "landrun")}
    d["env"] = {k: ENV.get(k, "") for k in ("ELAN_HOME", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS", "COMPARATOR_LANDRUN", "COMPARATOR_LEAN4EXPORT", "LAKE_HOME", "LEAN_PATH", "LAKE_ARTIFACT_CACHE")}
    d["lsm"] = pathlib.Path("/sys/kernel/security/lsm").read_text().strip() if pathlib.Path("/sys/kernel/security/lsm").exists() else None
    d["network"] = {u: sh(["curl", "-4", "-sS", "-o", "/dev/null", "-m", "15", "-w", "%{http_code}", u])["stdout"]
                    for u in ("https://github.com", "https://releases.lean-lang.org", "https://lakecache.blob.core.windows.net")}
    d["frozen_head"] = sh(["git", "-C", str(UP), "rev-parse", "HEAD"])["stdout"].strip()
    out = REPO / "evidence" / f"stage_{stage}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "environment_snapshot.json").write_text(json.dumps(d, indent=1))
    return d


def make_ws(ws, reuse=False):
    """Materialise the minimal workspace from frozen git blobs + P10 profile files; verify hashes vs lock."""
    if ws.exists():
        if reuse:  # keep only .lake (cloned deps + cache); every source file is rewritten and re-hashed below
            for x in ws.iterdir():
                if x.name != ".lake": shutil.rmtree(x) if x.is_dir() else x.unlink()
        else: shutil.rmtree(ws)
    files, want = source_files()
    rec = {}
    for f in files:
        b = git_blob(f)
        assert sha(b) == want[f], f"hash mismatch vs lock: {f}"
        dst = ws / f.removeprefix("lean/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b)
        rec[f] = sha(b)
    for n in ("lakefile.toml", "lake-manifest.json"):
        b = (REPO / "profiles" / "minimal" / n).read_bytes()
        (ws / n).write_bytes(b)
        rec["P10:" + n] = sha(b)
    # config path inside workspace: ComparatorChallenges/InfiniteMatroid.json
    (ws / "lean-toolchain").write_text(LEAN + "\n")
    return rec


def comparator_cmd(ws):
    inner = f"lake env {shlex.quote(str(TOOLS/'bin'/'comparator'))} ComparatorChallenges/InfiniteMatroid.json"
    guard = os.uname().release.split(".")
    use_guard = (int(guard[0]), int(guard[1])) < (7, 1)
    base = ["bash", "-c", f"cd {shlex.quote(str(ws))} && {inner}"]
    if not use_guard: return base, False
    return ["systemd-run", "--user", "--wait", "--pipe", "--collect", "--property=RestrictAddressFamilies=~AF_UNIX",
            "-E", f"PATH={ENV['PATH']}", "-E", f"ELAN_HOME={ENV['ELAN_HOME']}",
            "-E", f"COMPARATOR_LANDRUN={ENV['COMPARATOR_LANDRUN']}", "-E", f"COMPARATOR_LEAN4EXPORT={ENV['COMPARATOR_LEAN4EXPORT']}",
            "--working-directory", str(ws), "--"] + base, True


def stage_c(ws, reuse=False):
    out = REPO / "evidence" / "stage_c"; log = out / "logs"
    if log.exists(): shutil.rmtree(log)
    res = {"stage": "C", "status": "NOT_EXECUTED", "steps": []}
    res["snapshot"] = snapshot("c", ws)
    res["workspace_files_sha256"] = make_ws(ws, reuse)
    for argv, to in ((["lake", "exe", "cache", "get"], 3600),):
        r = sh(argv, cwd=ws, log=log, timeout=to)
        res["steps"].append({k: r[k] for k in ("argv", "rc", "elapsed_s")})
        if r["rc"] != 0:
            res["status"] = "ENVIRONMENT_BLOCKED"; res["blocker"] = {"step": argv, "stderr_tail": r["stderr"][-1500:], "stdout_tail": r["stdout"][-800:]}
            break
    else:
        argv, guarded = comparator_cmd(ws)
        res["systemd_guard"] = guarded
        r = sh(argv, cwd=ws, log=log, timeout=7200)
        res["comparator"] = {k: r[k] for k in ("argv", "rc", "elapsed_s")}
        res["comparator"]["stdout_tail"] = r["stdout"][-2000:]; res["comparator"]["stderr_tail"] = r["stderr"][-2000:]
        launch_failed = guarded and r["rc"] != 0 and "Failed to connect to bus" in r["stderr"]
        res["status"] = "PASS" if r["rc"] == 0 else ("ENVIRONMENT_BLOCKED" if launch_failed else "FAIL")
        if launch_failed: res["blocker"] = {"step": argv[:1], "stderr_tail": r["stderr"][-500:], "note": "comparator never started"}
    (out / "stage_c_result.json").write_text(json.dumps(res, indent=1))
    print("C:", res["status"])
    return res


def profile_sums():
    return {n: sha((REPO / "profiles" / "minimal" / n).read_bytes()) for n in ("lakefile.toml", "lake-manifest.json")}


def profile_check():
    """P10-authored minimal profile vs the frozen upstream manifest: every entry byte-equal (as JSON), lakefile rev == manifest mathlib rev,
    and the mathlib rev equals the lock's recorded mathlib rev. Returns list of problems (empty = consistent)."""
    up = {p["name"]: p for p in json.loads(git_blob("lean/lake-manifest.json"))["packages"]}
    mine = json.loads((REPO / "profiles/minimal/lake-manifest.json").read_text())
    probs = [f"entry differs from frozen upstream manifest: {e['name']}" for e in mine["packages"] if up.get(e["name"]) != e]
    lf = (REPO / "profiles/minimal/lakefile.toml").read_text()
    m = [e for e in mine["packages"] if e["name"] == "mathlib"][0]["rev"]
    if f'rev = "{m}"' not in lf: probs.append("lakefile mathlib rev != manifest mathlib rev")
    if m != LOCK["environment_layer"].get("mathlib_rev", m): probs.append("manifest mathlib rev != lock mathlib_rev")
    return probs


def verify_ws(ws):
    """Workspace sources must still equal the frozen blobs / P10 profile files. Returns list of mismatching paths."""
    files, want = source_files()
    bad = [f for f in files if sha((ws / f.removeprefix("lean/")).read_bytes()) != want[f]]
    bad += [n for n, h in profile_sums().items() if sha((ws / n).read_bytes()) != h]
    return bad


def prepare(stage, ws, reuse=False):
    res = {"stage": stage.upper(), "status": "NOT_EXECUTED", "steps": []}
    res["snapshot"] = snapshot(stage, ws)
    res["profile_check"] = profile_check()
    res["workspace_files_sha256"] = make_ws(ws, reuse)
    log = REPO / "evidence" / f"stage_{stage}" / "logs"
    if log.exists(): shutil.rmtree(log)
    r = sh(["lake", "exe", "cache", "get"], cwd=ws, log=log, timeout=3600)
    res["steps"].append({k: r[k] for k in ("argv", "rc", "elapsed_s")})
    if r["rc"] != 0:
        res["status"] = "ENVIRONMENT_BLOCKED"
        res["blocker"] = {"step": r["argv"], "stderr_tail": r["stderr"][-1500:]}
    return res, log


def finish(res, stage, suffix=""):
    out = REPO / "evidence" / f"stage_{stage}"
    (out / f"stage_{stage}{suffix}_result.json").write_text(json.dumps(res, indent=1))
    print(f"{stage.upper()}:", res["status"])
    return res


def stage_b(ws):
    res, log = prepare("b", ws)
    if res["status"] == "ENVIRONMENT_BLOCKED": return finish(res, "b")
    b = sh(["lake", "build", "OAI", "ComparatorChallenges"], cwd=ws, log=log, timeout=7200)
    res["build"] = {k: b[k] for k in ("argv", "rc", "elapsed_s")}
    res["build"]["stdout_tail"] = b["stdout"][-1500:]; res["build"]["stderr_tail"] = b["stderr"][-1500:]
    sorry_lines = [l for l in (b["stdout"] + b["stderr"]).splitlines() if "sorry" in l]
    res["sorry_warnings"] = sorry_lines
    res["sorry_in_solution_closure"] = [l for l in sorry_lines if "OAI/" in l or "OAI." in l]
    probe = "import OAI.Combinatorics.InfiniteMatroid.Main\n#print axioms OAI.InfiniteMatroidCounterexample.main\n"
    (ws / "P10Probe.lean").write_text(probe)
    res["probe_sha256"] = sha(probe.encode())
    p = sh(["lake", "env", "lean", "P10Probe.lean"], cwd=ws, log=log, timeout=1800)
    res["axioms"] = {"rc": p["rc"], "stdout": p["stdout"].strip(), "stderr_tail": p["stderr"][-500:]}
    permitted = set(json.loads(git_blob(CFG))["permitted_axioms"])
    got = set(a.strip() for a in p["stdout"].split("[")[-1].split("]")[0].split(",")) if "depends on axioms" in p["stdout"] else None
    res["axioms_set"] = sorted(got) if got is not None else None
    res["mismatched_sources"] = verify_ws(ws)
    ok = b["rc"] == 0 and p["rc"] == 0 and got is not None and got <= permitted and not res["sorry_in_solution_closure"] and not res["mismatched_sources"]
    res["status"] = "PASS" if ok else "FAIL"
    return finish(res, "b")


MUTATIONS = [  # (id, file under ws, description, transform(bytes)->bytes)
    ("D1", "ComparatorChallenges/InfiniteMatroid.lean", "modified theorem statement in the challenge (first '≠' -> '=')",
     lambda b: b.replace("≠".encode(), b"=", 1)),
    ("D2", "OAI/Combinatorics/InfiniteMatroid/Main.lean", "modified solution: proof of `main` replaced by sorry",
     lambda b: b[: b.index(b":= by", b.index(b"theorem main"))] + b":= by\n  sorry\n\nend InfiniteMatroidCounterexample\nend\n\nend OAI\n"),
    ("D3", "ComparatorChallenges/InfiniteMatroid.json", "incorrect challenge<->solution binding: config names a declaration the solution does not have",
     lambda b: b.replace(b"InfiniteMatroidCounterexample.main", b"InfiniteMatroidCounterexample.nonexistent", 1)),
    ("D5b", "OAI/Combinatorics/InfiniteMatroid/Main.lean", "solution proves `main` from an injected axiom `p10_bad : False` (axiom outside the permitted set; elaborates cleanly)",
     lambda b: b.replace(b"theorem main", b"axiom p10_bad : False\n\ntheorem main", 1)[: b.replace(b"theorem main", b"axiom p10_bad : False\n\ntheorem main", 1).index(b":= by", b.replace(b"theorem main", b"axiom p10_bad : False\n\ntheorem main", 1).index(b"theorem main"))] + b":= by\n  exact p10_bad.elim\n\nend InfiniteMatroidCounterexample\nend\n\nend OAI\n"),
]


def comparator_run(ws, log):
    argv, _ = comparator_cmd(ws)
    r = sh(argv, cwd=ws, log=log, timeout=7200)
    return r


def _rerun(res, rows, ws, log):
    c1 = comparator_run(ws, log)
    res["control_after_restore"] = {"rc": c1["rc"], "elapsed_s": c1["elapsed_s"], "last_line": c1["stdout"].strip().splitlines()[-1:], "mismatched_sources": verify_ws(ws)}
    res["mutations"] = rows
    res["status"] = "PASS" if all(r.get("rejected") and not r.get("bus_failure") and r.get("restored_ok") for r in rows) and c1["rc"] == 0 and not res["control_after_restore"]["mismatched_sources"] else "FAIL"
    return res


def stage_d(ws, reuse=False, only=None):
    res, log = prepare("d", ws, reuse)
    if res["status"] == "ENVIRONMENT_BLOCKED": return finish(res, "d")
    c0 = comparator_run(ws, log)
    res["control_before"] = {"rc": c0["rc"], "elapsed_s": c0["elapsed_s"], "last_line": c0["stdout"].strip().splitlines()[-1:] }
    if c0["rc"] != 0:
        res["status"] = "FAIL"; res["reason"] = "control (unmodified) run did not pass; mutations not interpretable"
        return finish(res, "d")
    rows = []
    for mid, rel, desc, fn in [m for m in MUTATIONS if not only or m[0] in only]:
        fp = ws / rel; orig = fp.read_bytes(); new = fn(orig)
        if new == orig:
            rows.append({"id": mid, "status": "FAIL", "reason": "mutation was a no-op"}); continue
        fp.write_bytes(new)
        r = comparator_run(ws, log)
        fp.write_bytes(orig)
        text = r["stdout"] + r["stderr"]
        keys = [l for l in text.splitlines() if any(k in l.lower() for k in ("error", "sorry", "axiom", "mismatch", "not found", "does not", "differ", "okay", "accepts", "rejected", "unknown"))]
        rows.append({"id": mid, "description": desc, "mutated_file": rel, "mutated_sha256": sha(new), "restored_ok": sha(fp.read_bytes()) == sha(orig),
                     "comparator_rc": r["rc"], "rejected": r["rc"] != 0, "elapsed_s": r["elapsed_s"], "key_lines": keys[-12:],
                     "bus_failure": "Failed to connect to bus" in r["stderr"]})
    if only: return finish(_rerun(res, rows, ws, log), "d", suffix="_rerun_" + "_".join(only))
    # D4: provenance mismatch of the dependency pin (P10's own check, not Comparator): flip one hex digit of Mathlib's rev in the manifest copy
    mf = ws / "lake-manifest.json"; orig = mf.read_bytes(); rev = b"d13f23b723b8a846827a245b89c10fc7d3f11612"
    mf.write_bytes(orig.replace(rev, b"d13f23b723b8a846827a245b89c10fc7d3f11613", 1))
    rows.append({"id": "D4", "description": "dependency provenance mismatch: Mathlib rev in the workspace manifest altered by one hex digit; P10 profile check (verify_ws) must detect it. Tests P10's check, NOT Comparator/Lake.",
                 "detected_mismatches": verify_ws(ws), "rejected": "lake-manifest.json" in verify_ws(ws)})
    mf.write_bytes(orig)
    c1 = comparator_run(ws, log)
    res["control_after_restore"] = {"rc": c1["rc"], "elapsed_s": c1["elapsed_s"], "last_line": c1["stdout"].strip().splitlines()[-1:], "mismatched_sources": verify_ws(ws)}
    res["mutations"] = rows
    ok = all(r.get("rejected") and not r.get("bus_failure") and r.get("restored_ok", True) for r in rows) and c1["rc"] == 0 and not res["control_after_restore"]["mismatched_sources"]
    res["status"] = "PASS" if ok else "FAIL"
    res["caveat"] = "a rejection counts only if the control passes before and after AND the key_lines show the intended reason (read them; rc != 0 alone is not sufficient)"
    return finish(res, "d")


if __name__ == "__main__":
    cmd = sys.argv[1]
    ws = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[2] == "--ws" else WSROOT / cmd
    if cmd == "snapshot": print(json.dumps(snapshot("pre", ws), indent=1))
    elif cmd == "b": sys.exit(0 if stage_b(ws)["status"] == "PASS" else 4)
    elif cmd == "d":
        only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
        sys.exit(0 if stage_d(ws, "--reuse" in sys.argv, only)["status"] == "PASS" else 4)
    elif cmd == "c": sys.exit(0 if stage_c(ws, "--reuse" in sys.argv)["status"] == "PASS" else 4)
