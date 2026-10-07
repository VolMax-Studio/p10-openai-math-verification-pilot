#!/usr/bin/env python3
"""Stage B/C/D harness. Status vocabulary (never collapsed): PASS | FAIL | NOT_EXECUTED | ENVIRONMENT_BLOCKED.
NOT_EXECUTED and ENVIRONMENT_BLOCKED are NEVER success. Execution paths here have NOT been exercised against a
real Lean/Comparator install (none available when written); only preflight/blocking and a stub plumbing self-test
(scripts/selftest_harness.sh) have run. Treat the first real run as a debugging run, not as evidence, until reviewed.
Usage: gates.py <B|C|D> <upstream_checkout> <subject.lock.json> <profile> <results_dir>
"""
import json, os, platform, shutil, subprocess, sys, time, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from inspect_candidates import sha

def _find_lake():
    if os.environ.get("P10_LAKE"): return os.environ["P10_LAKE"]
    if shutil.which("lake"): return "lake"
    cand = os.path.join(os.path.expanduser("~"), ".elan", "bin", "lake")   # elan's default location; not always on a login shell's PATH
    return cand if os.path.exists(cand) else "lake"
LAKE = _find_lake()
MIN_DISK_GB = float(os.environ.get("P10_MIN_DISK_GB", "30"))   # per workspace; ESTIMATE, not measured; override as needed
WS_COUNT = int(os.environ.get("P10_WS_COUNT", "1"))            # reproduce.sh sets 2 for --stage all (separate B and C workspaces)
HOSTS = ["https://github.com", "https://cache.mathlib.org", "https://release.lean-lang.org"]

def sh(cmd, cwd=None, env=None, timeout=None):
    e = dict(os.environ); e.update(env or {})
    p = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr

def have(x): return shutil.which(x) is not None

def preflight(gate, profile, ws_root):
    """Return list of blockers (strings). Empty list == not blocked."""
    b = []
    if os.environ.get("P10_SELFTEST") == "1": return b   # STUB plumbing self-test only (scripts/selftest_harness.sh)
    if platform.system() != "Linux": b.append(f"platform {platform.system()} (Linux required: landrun/Landlock)")
    for t in ("git", "curl"):
        if not have(t): b.append(f"missing tool: {t}")
    if not have(LAKE) and not os.path.exists(LAKE): b.append(f"missing tool: {LAKE} (elan/lake)")
    free = shutil.disk_usage(os.path.dirname(ws_root) if os.path.isdir(os.path.dirname(ws_root)) else REPO).free / 2**30
    need = MIN_DISK_GB * WS_COUNT
    if free < need: b.append(f"disk free {free:.1f} GiB < required {need:.0f} GiB (estimate: P10_MIN_DISK_GB per workspace x P10_WS_COUNT)")
    for h in HOSTS:
        rc, _, _ = sh(["curl", "-sS", "-m", "15", "-o", "/dev/null", "-I", "-L", h])
        if rc != 0: b.append(f"network: cannot reach {h}")
    if gate in ("C", "D"):
        for k in ("COMPARATOR_BIN", "COMPARATOR_LEAN4EXPORT", "COMPARATOR_LANDRUN"):
            v = os.environ.get(k)
            if not v or not os.access(v, os.X_OK): b.append(f"missing/non-executable ${k}")
        rec = os.environ.get("P10_TOOLS_RECORD")
        if not rec or not os.path.exists(rec): b.append("missing $P10_TOOLS_RECORD (build record of comparator/lean4export/landrun at profile pins)")
        if not have("systemd-run"): b.append("missing tool: systemd-run (--user sandbox guard)")
        if hasattr(os, "geteuid") and os.geteuid() == 0: b.append("running as root (Comparator README assumption 6)")
    return b

def tools_record_ok(profile_json, profile):
    rec = json.load(open(os.environ["P10_TOOLS_RECORD"]))
    pins = profile_json[profile]
    want = {"comparator": pins["comparator"]["rev"], "lean4export": pins["lean4export"]["rev"], "landrun": pins["landrun"]["rev"]}
    bad = [k for k, v in want.items() if rec.get(k, {}).get("rev") != v]
    for k, env in (("comparator", "COMPARATOR_BIN"), ("lean4export", "COMPARATOR_LEAN4EXPORT"), ("landrun", "COMPARATOR_LANDRUN")):
        if rec.get(k, {}).get("binary_sha256") != sha(os.environ[env]): bad.append(f"{k}:binary_sha256")
    return bad

def prepare(root, lock, ws):
    """Materialize a workspace from the pinned checkout. Hash-verifies every copied file against the lock."""
    if os.path.exists(ws): shutil.rmtree(ws)
    L = os.path.join(ws, "lean"); os.makedirs(L)
    subj = lock["subject"]
    exp = {}
    for el in lock["binding_chain"]:
        exp.update({p: h for p, h in el["files_sha256"].items() if p.startswith("lean/")})
    exp.update(lock["environment_layer"]["files_sha256"]); exp.update(lock["environment_layer"]["patches_sha256"])
    exp[subj["comparator_config"]] = exp.get(subj["comparator_config"])
    for rel, h in exp.items():
        dst = os.path.join(ws, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(root, rel), dst)
        if h and sha(dst) != h: raise RuntimeError(f"hash mismatch while preparing {rel}")
    return L

def run_lake(cmd, L, log):
    t0 = time.time(); rc, out, err = sh([LAKE] + cmd, cwd=L)
    open(log, "a").write(f"$ lake {' '.join(cmd)}\n[exit {rc}] {time.time()-t0:.0f}s\n--stdout--\n{out}\n--stderr--\n{err}\n")
    return rc, out + err

def manifest_invariant(L, orig_sha, lock):
    bad = []
    if sha(os.path.join(L, "lake-manifest.json")) != orig_sha: bad.append("lake-manifest.json changed during run")
    pk = os.path.join(L, ".lake", "packages")
    for n, d in lock["environment_layer"]["dependency_pins"].items():
        pd = os.path.join(pk, n)
        if os.path.isdir(pd):
            rc, o, _ = sh(["git", "-C", pd, "rev-parse", "HEAD"])
            if rc == 0 and o.strip() != d["rev"]: bad.append(f"{n}: HEAD {o.strip()[:12]} != manifest {d['rev'][:12]}")
    return bad

def gate_B(root, lock, profile, rd):
    ws = os.path.join(REPO, "work", profile, "build"); log = os.path.join(rd, "B.log"); res = {"gate": "B", "profile": profile}
    blockers = preflight("B", profile, ws)
    if blockers: return {**res, "status": "ENVIRONMENT_BLOCKED", "blockers": blockers}
    if os.environ.get("P10_PREFLIGHT_ONLY"): return {**res, "status": "NOT_EXECUTED", "reason": "preflight only (P10_PREFLIGHT_ONLY set); environment NOT blocked"}
    L = prepare(root, lock, ws); man = sha(os.path.join(L, "lake-manifest.json"))
    target = lock["subject"]["solution_path"][len("lean/"):-len(".lean")].replace("/", ".")
    steps = ([["update"]] if profile == "upstream-as-is" else []) + [["exe", "cache", "get"], ["build", target]]
    for s in steps:
        rc, out = run_lake(s, L, log)
        if rc != 0: return {**res, "status": "FAIL", "failed_step": " ".join(s), "log": log}
    drift = manifest_invariant(L, man, lock)
    if profile == "upstream-as-is": return {**res, "status": "PASS", "observed_dependency_drift": drift, "note": "PASS = build exit 0; drift recorded as observation", "log": log}
    if drift: return {**res, "status": "FAIL", "reason": "implicit dependency change under frozen profile", "drift": drift, "log": log}
    if "declaration uses 'sorry'" in out or "declaration uses `sorry`" in out: return {**res, "status": "FAIL", "reason": "sorry reported", "log": log}
    return {**res, "status": "PASS", "scope": "plain Lean build of the solution module only; not Comparator", "log": log}

def comparator_cmd(L, cfg_rel):
    path = os.pathsep.join([os.path.dirname(os.environ["COMPARATOR_LANDRUN"]), os.path.dirname(os.environ["COMPARATOR_LEAN4EXPORT"]), os.environ.get("PATH", "")])
    inner = f'{LAKE} env "{os.environ["COMPARATOR_BIN"]}" "{cfg_rel}"'
    if os.environ.get("P10_SELFTEST") == "1": return ["bash", "-c", f'cd "{L}" && {inner}']
    return ["systemd-run", "--user", "--wait", "--pipe", "--collect", "--property=RestrictAddressFamilies=~AF_UNIX",
            "-E", f"PATH={path}", "-E", f"COMPARATOR_LANDRUN={os.environ['COMPARATOR_LANDRUN']}", "-E", f"COMPARATOR_LEAN4EXPORT={os.environ['COMPARATOR_LEAN4EXPORT']}",
            f"--working-directory={L}", "bash", "-c", inner]

def gate_C(root, lock, profile, rd, ws=None, ret_ws=False):
    ws = ws or os.path.join(REPO, "work", profile, "comparator"); log = os.path.join(rd, "C.log"); res = {"gate": "C", "profile": profile}
    profiles = json.load(open(os.path.join(REPO, "profiles", "verifier_profiles.json")))
    if profile == "upstream-as-is":
        return {**res, "status": "NOT_EXECUTED", "reason": "upstream-as-is has no recoverable verifier revisions; this gate cannot be a reproduction"}
    blockers = preflight("C", profile, ws)
    if not blockers:
        bad = tools_record_ok(profiles, profile)
        if bad: blockers += [f"tools record mismatch: {bad}"]
    if blockers: return {**res, "status": "ENVIRONMENT_BLOCKED", "blockers": blockers}
    if os.environ.get("P10_PREFLIGHT_ONLY"): return {**res, "status": "NOT_EXECUTED", "reason": "preflight only (P10_PREFLIGHT_ONLY set); environment NOT blocked"}
    L = prepare(root, lock, ws); man = sha(os.path.join(L, "lake-manifest.json"))
    for s in (["exe", "cache", "get"],):
        rc, _ = run_lake(s, L, log)
        if rc != 0: return {**res, "status": "FAIL", "failed_step": " ".join(s), "log": log}
    cfg = lock["subject"]["comparator_config"][len("lean/"):]
    rc, o, e = sh(comparator_cmd(L, cfg)); open(log, "a").write(f"$ comparator {cfg}\n[exit {rc}]\n{o}\n{e}\n")
    drift = manifest_invariant(L, man, lock)
    out = {**res, "status": "PASS" if rc == 0 and not drift else "FAIL", "comparator_exit": rc, "drift": drift, "log": log,
           "scope": "Comparator: same statement as challenge, permitted axioms only, kernel accepted -- for the formal statement only"}
    if ret_ws: out["_ws"] = L
    return out

MUTATIONS = [  # (id, relative file, description, transform(bytes)->bytes)
    ("D1", "ComparatorChallenges/InfiniteMatroid.lean", "challenge statement weakened/changed (first '≠' -> '=')", lambda b: b.replace("≠".encode(), b"=", 1)),
    ("D2", "OAI/Combinatorics/InfiniteMatroid/Main.lean", "solution proof replaced by sorry", lambda b: b[: b.index(b":= by", b.index(b"theorem main"))] + b":= by\n  sorry\n\nend InfiniteMatroidCounterexample\nend\n\nend OAI\n"),
    ("D3", "ComparatorChallenges/InfiniteMatroid.json", "config theorem_names points to nonexistent declaration", lambda b: b.replace(b"InfiniteMatroidCounterexample.main", b"InfiniteMatroidCounterexample.nonexistent", 1)),
    ("D4", "OAI/Combinatorics/InfiniteMatroid/Main.lean", "extra axiom injected and used (axiom outside permitted set)", lambda b: b.replace(b"theorem main", b"axiom p10_bad : False\n\ntheorem main", 1).replace(b":= by\n  obtain", b":= by\n  exact p10_bad.elim\n  obtain", 1)),
]

def gate_D(root, lock, profile, rd):
    res = {"gate": "D", "profile": profile}
    c = gate_C(root, lock, profile, rd, ret_ws=True)
    if c["status"] != "PASS": return {**res, "status": "NOT_EXECUTED" if c["status"] != "ENVIRONMENT_BLOCKED" else "ENVIRONMENT_BLOCKED", "reason": f"control gate C is {c['status']}", "blockers": c.get("blockers")}
    L = c["_ws"]; cfg = lock["subject"]["comparator_config"][len("lean/"):]; rows = []
    for mid, rel, desc, fn in MUTATIONS:
        fp = os.path.join(L, rel); orig = open(fp, "rb").read(); open(fp, "wb").write(fn(orig))
        if open(fp, "rb").read() == orig: open(fp, "wb").write(orig); rows.append({"id": mid, "status": "FAIL", "reason": "mutation was a no-op"}); continue
        rc, o, e = sh(comparator_cmd(L, cfg)); open(fp, "wb").write(orig)
        rows.append({"id": mid, "description": desc, "comparator_exit": rc, "rejected": rc != 0, "stderr_tail": (o + e)[-400:]})
    rc, _, _ = sh(comparator_cmd(L, cfg))
    ok = all(r.get("rejected") for r in rows) and rc == 0
    return {**res, "status": "PASS" if ok else "FAIL", "mutations": rows, "control_after_restore_exit": rc,
            "caveat": "a rejection is only meaningful if the control passes before AND after; stderr must be read to confirm the rejection reason is the intended one, not infrastructure"}

def main():
    gate, root, lockp, profile, rd = sys.argv[1:6]
    os.makedirs(rd, exist_ok=True); lock = json.load(open(lockp))
    r = {"B": gate_B, "C": gate_C, "D": gate_D}[gate](root, lock, profile, rd); r.pop("_ws", None)
    json.dump(r, open(os.path.join(rd, f"{gate}.json"), "w"), indent=1)
    print(f"{gate}: {r['status']}" + (f"  blockers: {r['blockers']}" if r.get("blockers") else "") + (f"  ({r.get('reason')})" if r.get("reason") else ""))
    sys.exit({"PASS": 0, "FAIL": 4, "NOT_EXECUTED": 5, "ENVIRONMENT_BLOCKED": 6}[r["status"]])

if __name__ == "__main__":
    main()
