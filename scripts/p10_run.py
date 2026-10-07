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
    d["env"] = {k: ENV.get(k, "") for k in ("ELAN_HOME", "COMPARATOR_LANDRUN", "COMPARATOR_LEAN4EXPORT", "LAKE_HOME", "LEAN_PATH", "LAKE_ARTIFACT_CACHE")}
    d["lsm"] = pathlib.Path("/sys/kernel/security/lsm").read_text().strip() if pathlib.Path("/sys/kernel/security/lsm").exists() else None
    d["network"] = {u: sh(["curl", "-4", "-sS", "-o", "/dev/null", "-m", "15", "-w", "%{http_code}", u])["stdout"]
                    for u in ("https://github.com", "https://releases.lean-lang.org", "https://lakecache.blob.core.windows.net")}
    d["frozen_head"] = sh(["git", "-C", str(UP), "rev-parse", "HEAD"])["stdout"].strip()
    out = REPO / "evidence" / f"stage_{stage}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "environment_snapshot.json").write_text(json.dumps(d, indent=1))
    return d


def make_ws(ws, extra=None):
    """Materialise the minimal workspace from frozen git blobs + P10 profile files; verify hashes vs lock."""
    if ws.exists(): shutil.rmtree(ws)
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


def stage_c(ws):
    out = REPO / "evidence" / "stage_c"; log = out / "logs"
    if log.exists(): shutil.rmtree(log)
    res = {"stage": "C", "status": "NOT_EXECUTED", "steps": []}
    res["snapshot"] = snapshot("c", ws)
    res["workspace_files_sha256"] = make_ws(ws)
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
        res["status"] = "PASS" if r["rc"] == 0 else "FAIL"
    (out / "stage_c_result.json").write_text(json.dumps(res, indent=1))
    print("C:", res["status"])
    return res


if __name__ == "__main__":
    cmd = sys.argv[1]
    ws = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[2] == "--ws" else WSROOT / cmd
    if cmd == "snapshot": print(json.dumps(snapshot("pre", ws), indent=1))
    elif cmd == "c": sys.exit(0 if stage_c(ws)["status"] == "PASS" else 4)
