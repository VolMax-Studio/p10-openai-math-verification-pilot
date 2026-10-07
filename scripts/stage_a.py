#!/usr/bin/env python3
"""Stage A: provenance of the ENTIRE frozen chain, with the frozen upstream Git commit as the root of trust.
Usage: stage_a.py <upstream_checkout> <subject.lock.json> [--json <out>]
Trust direction:  FROZEN COMMIT ID -> (recomputed) commit/tree/blob objects -> canonical bytes -> expected SHA-256
                  -> compared with subject.lock.json (a MANIFEST, never the authority) -> compared with the working copy.
Every object read from the local object store is re-hashed (SHA-1) and chained back to the commit id, so a doctored
.git/objects, a `git replace` ref, a forged lock and a forged working tree are all independent failure points.
Not derivable from the commit (separate trust roots): the FROZEN_COMMIT constant below / the ratifier's copy of this
repository's git history (it identifies which upstream commit is frozen); SHA-1 collision resistance of git object ids.
Exit: 0 all checks pass; 4 any check failed. PASS = provenance only.
"""
import hashlib, json, os, re, subprocess, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inspect_candidates import strip, families_from_text, yaml_from_text, IMPORT, NOISE

FROZEN_COMMIT = "adc7f1241b42e322a6451854ab7e4b4c146bf78a"
sha256 = lambda b: hashlib.sha256(b).hexdigest()

class GitRoot:
    """Canonical bytes of the frozen commit, with every object hash re-verified."""
    def __init__(self, repo, commit):
        self.repo, self.commit, self.cache = repo, commit, {}
        self.env = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1")      # ignore `git replace` refs
        t, body = self.obj(commit)
        if t != "commit": raise ValueError("not a commit")
        m = re.match(rb"tree ([0-9a-f]{40})\n", body)
        if not m: raise ValueError("commit has no tree line")
        self.tree = m.group(1).decode()
    def obj(self, sha):
        if sha in self.cache: return self.cache[sha]
        t = subprocess.run(["git", "-C", self.repo, "cat-file", "-t", sha], env=self.env, capture_output=True)
        if t.returncode: raise KeyError(sha)
        typ = t.stdout.decode().strip()
        b = subprocess.run(["git", "-C", self.repo, "cat-file", typ, sha], env=self.env, capture_output=True)
        if b.returncode: raise KeyError(sha)
        body = b.stdout
        if hashlib.sha1(f"{typ} {len(body)}\0".encode() + body).hexdigest() != sha:
            raise ValueError(f"object {sha} fails SHA-1 re-verification")
        self.cache[sha] = (typ, body); return typ, body
    def entries(self, tsha):
        typ, body = self.obj(tsha)
        if typ != "tree": raise ValueError("not a tree")
        out, i = {}, 0
        while i < len(body):
            sp = body.index(b" ", i); nul = body.index(b"\0", sp)
            out[body[sp + 1:nul].decode()] = (body[i:sp].decode(), body[nul + 1:nul + 21].hex()); i = nul + 21
        return out
    def lookup(self, path):
        """-> ('blob', bytes) | ('tree', sha) | None"""
        cur = self.tree
        parts = [x for x in path.split("/") if x]
        for k, part in enumerate(parts):
            e = self.entries(cur)
            if part not in e: return None
            mode, sha = e[part]
            if k == len(parts) - 1:
                return ("tree", sha) if mode == "40000" else ("blob", self.obj(sha)[1])
            if mode != "40000": return None
            cur = sha
        return ("tree", cur)
    def blob(self, path):
        r = self.lookup(path)
        return r[1] if r and r[0] == "blob" else None
    def walk(self, path):
        """all blob paths under a directory (canonical membership)"""
        r = self.lookup(path)
        if not r or r[0] != "tree": return []
        out = []
        def rec(tsha, pre):
            for name, (mode, sha) in sorted(self.entries(tsha).items()):
                if mode == "40000": rec(sha, pre + name + "/")
                else: out.append(pre + name)
        rec(r[1], path.rstrip("/") + "/"); return out

def canon_closure(g, root_mod):
    seen, ext, miss, stack = {}, set(), set(), [root_mod]
    while stack:
        m = stack.pop()
        if m in seen or m in ext or m in miss: continue
        data = g.blob("lean/" + m.replace(".", "/") + ".lean")
        if data is None:
            (miss if m.split(".")[0] in ("OAI", "ComparatorChallenges") else ext).add(m if m.split(".")[0] in ("OAI", "ComparatorChallenges") else m.split(".")[0]); continue
        t = data.decode(errors="replace"); seen[m] = t
        stack += [x for l in IMPORT.findall(t) for x in l.split()]
    return seen, sorted(ext - set(NOISE)), sorted(miss)

def run(repo, lock_path):
    lock = json.load(open(lock_path)); res = []
    def chk(cid, group, ok, msg=""): res.append({"id": cid, "group": group, "status": "PASS" if ok else "FAIL", "detail": msg})
    # R0: root of trust
    chk("R0.lock_commit_is_frozen_commit", "ROOT", lock["upstream"]["commit"] == FROZEN_COMMIT, f"lock={lock['upstream']['commit']} frozen={FROZEN_COMMIT}")
    try:
        g = GitRoot(repo, FROZEN_COMMIT); chk("R0.commit_object_reverified", "ROOT", True, f"tree={g.tree}")
    except Exception as e:
        chk("R0.commit_object_reverified", "ROOT", False, repr(e)); return res
    try: head = subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True).strip()
    except Exception as e: head = f"ERR {e}"
    chk("A1.worktree_HEAD", "HASH", head == FROZEN_COMMIT, f"HEAD={head}")
    # R2/A2: every locked file: lock hash == canonical hash == working-copy hash
    expected = {}
    for el in lock["binding_chain"]:
        for p, h in el["files_sha256"].items(): expected[p] = h
    expected.update(lock["environment_layer"]["files_sha256"]); expected.update(lock["environment_layer"]["patches_sha256"])
    for p, h in sorted(expected.items()):
        cb = g.blob(p)
        if cb is None: chk(f"R2.lock_hash:{p}", "ROOT", False, "path absent from frozen commit"); continue
        c = sha256(cb)
        chk(f"R2.lock_hash:{p}", "ROOT", c == h, "" if c == h else f"lock {h} != canonical(commit) {c}")
        fp = os.path.join(repo, p)
        if not os.path.isfile(fp): chk(f"A2.worktree:{p}", "HASH", False, "missing"); continue
        w = sha256(open(fp, "rb").read()); chk(f"A2.worktree:{p}", "HASH", w == c, "" if w == c else f"working copy {w} != canonical {c}")
    # membership derived from the frozen tree
    subj = lock["subject"]; ms_dir = subj["manuscript_path"].rsplit("/", 1)[0]
    canon_ms = {p for p in g.walk(ms_dir)}
    lock_ms = set(next(e for e in lock["binding_chain"] if e["id"] == "E2")["files_sha256"])
    chk("R3.manuscript_membership", "ROOT", canon_ms == lock_ms, f"extra_in_lock={sorted(lock_ms-canon_ms)[:3]} missing_in_lock={sorted(canon_ms-lock_ms)[:3]}")
    canon_patches = {p for p in g.walk("lean/patches") if p.endswith(".patch")}
    chk("R3.patch_membership", "ROOT", canon_patches == set(lock["environment_layer"]["patches_sha256"]), f"{len(canon_patches)} canonical vs {len(lock['environment_layer']['patches_sha256'])} locked")
    # working-copy membership (extra untracked files in the directories the subject depends on)
    def wt_files(d):
        base = os.path.join(repo, d); out = set()
        for dp, _, fs in os.walk(base):
            for f in fs: out.add(os.path.relpath(os.path.join(dp, f), repo))
        return out
    chk("A2.worktree_membership:manuscript_dir", "HASH", wt_files(ms_dir) == canon_ms, f"extra={sorted(wt_files(ms_dir)-canon_ms)[:3]} missing={sorted(canon_ms-wt_files(ms_dir))[:3]}")
    wp = {p for p in wt_files("lean/patches") if p.endswith(".patch")}
    chk("A2.worktree_membership:patches", "HASH", wp == canon_patches, f"extra={sorted(wp-canon_patches)[:3]} missing={sorted(canon_patches-wp)[:3]}")
    # closure and config from canonical bytes
    cfg = None
    try:
        cfg = json.loads(g.blob(subj["comparator_config"])); solmod = cfg["solution_module"]
        closure, ext, miss = canon_closure(g, solmod)
        locked = next(e for e in lock["binding_chain"] if e["id"] == "E7")["identifier"]["closure_modules"]
        chk("A3.closure_set", "CLOSURE", sorted(closure) == locked, f"canonical {len(closure)} vs locked {len(locked)}; extra={sorted(set(closure)-set(locked))} missing={sorted(set(locked)-set(closure))}")
        lockfiles = set(next(e for e in lock["binding_chain"] if e["id"] == "E7")["files_sha256"])
        chk("R3.closure_files_membership", "ROOT", lockfiles == {"lean/" + m.replace(".", "/") + ".lean" for m in closure}, "")
        chk("A3.closure_external_imports_none", "CLOSURE", not ext and not miss, f"external={ext} unresolved_local={miss}")
    except Exception as e:
        closure = {}; chk("A3.closure_set", "CLOSURE", False, f"cannot compute: {e!r}")
    # structural (prose/metadata) bindings, evaluated on CANONICAL bytes
    txt = lambda p: (g.blob(p) or b"").decode(errors="replace")
    try:
        fam = families_from_text(txt("CONTENTS.md"))[subj["manuscript_family"]]; ms = ms_dir.split("/")[1]
        chk("S1.catalogue->docs+manuscript", "STRUCT", fam["lean_docs_link"] and fam["manuscripts"] == [ms], f"{fam['lean_docs_link']} {fam['manuscripts']}")
    except Exception as e: chk("S1.catalogue->docs+manuscript", "STRUCT", False, repr(e))
    try:
        d = txt(subj["formalization_docs_path"]); cname = os.path.basename(subj["challenge_path"])
        chk("S2.docs->manuscript+challenge", "STRUCT", f"preprints/{ms_dir.split('/')[1]}/paper.pdf" in d.replace("../../", "") and f"../ComparatorChallenges/{cname})" in d, "")
    except Exception as e: chk("S2.docs->manuscript+challenge", "STRUCT", False, repr(e))
    try:
        yf = yaml_from_text(txt(subj["formalization_metadata_path"])); cn = os.path.basename(subj["comparator_config"])
        ent = [m for m in yf["main_results"] if os.path.basename(m["comparator_config"]) == cn]
        chk("S3.yaml_main_results==config", "STRUCT", len(ent) == 1 and ent[0]["declaration"] == subj["primary_declaration"] and ent[0]["file"] == subj["solution_path"][len("lean/"):], f"{ent}")
    except Exception as e: chk("S3.yaml_main_results==config", "STRUCT", False, repr(e))
    if cfg:
        chal_rel = "lean/" + cfg["challenge_module"].replace(".", "/") + ".lean"; sol_rel = "lean/" + cfg["solution_module"].replace(".", "/") + ".lean"
        chk("S4.config_paths+decl", "STRUCT", chal_rel == subj["challenge_path"] and sol_rel == subj["solution_path"] and cfg["theorem_names"] == [subj["primary_declaration"]] and set(cfg["permitted_axioms"]) <= {"propext", "Quot.sound", "Classical.choice"}, f"{chal_rel} {sol_rel} {cfg['theorem_names']}")
        def info(path):
            raw = g.blob(path)
            if raw is None: return None
            t = strip(raw.decode(errors="replace")); ns = re.findall(r"^\s*namespace\s+(\S+)", t, re.M)
            m = re.search(r"theorem\s+main\b(.*?)(?=\n(?:end|theorem|namespace)\b|\Z)", t, re.S)
            return {"ns": ns, "has_main": bool(m), "sorry": bool(m and re.search(r"\bsorry\b", m.group(1))), "file_sorry": bool(re.search(r"\bsorry\b", t))}
        ci, si = info(subj["challenge_path"]), info(subj["solution_path"]); leaf = subj["primary_declaration"].rsplit(".", 1)[0].split(".")[-1]
        chk("S5.challenge_declares_main_with_sorry", "STRUCT", bool(ci) and ci["has_main"] and ci["sorry"] and ci["ns"][:2] == ["OAI", leaf], f"{ci}")
        chk("S6.solution_declares_main_without_sorry", "STRUCT", bool(si) and si["has_main"] and not si["sorry"] and not si["file_sorry"] and leaf in si["ns"], f"{si}")
        bad = [m for m, t in closure.items() if re.search(r"\bsorry\b", strip(t))]
        chk("S6b.closure_has_no_sorry_token", "STRUCT", not bad, f"{bad}")
    # environment layer, from canonical bytes
    env = lock["environment_layer"]
    try:
        tc = txt("lean/lean-toolchain").strip(); man = json.loads(g.blob("lean/lake-manifest.json"))
        mrev = {p["name"].strip("«»"): p["rev"] for p in man["packages"]}
        req = {n.strip("«»"): r for n, r in re.findall(r'require\s+(\S+)\s+from\s+git\s+"[^"]+"\s+@\s+"([0-9a-f]{40})"', txt("lean/lakefile.lean"))}
        chk("E1.toolchain", "ENV", tc == env["toolchain"]["lean"], tc)
        chk("E2.mathlib_rev", "ENV", mrev.get("mathlib") == env["mathlib_rev"] == req.get("mathlib"), "")
        chk("E3.lakefile_requires==manifest", "ENV", all(mrev.get(n) == r for n, r in req.items()) and len(req) == 30, f"{len(req)} direct requires")
        chk("E4.manifest_pins==lock", "ENV", mrev == {n: v["rev"] for n, v in env["dependency_pins"].items()}, "")
    except Exception as e: chk("E*.environment", "ENV", False, repr(e))
    return res

def main():
    repo, lockp = sys.argv[1], sys.argv[2]
    res = run(repo, lockp); bad = [r for r in res if r["status"] == "FAIL"]; by = {}
    for r in res: by.setdefault(r["group"], [0, 0]); by[r["group"]][0 if r["status"] == "PASS" else 1] += 1
    for r in bad: print(f"  FAIL {r['id']}: {r['detail'][:200]}")
    print("A: " + ", ".join(f"{g}: {p} pass/{f} fail" for g, (p, f) in sorted(by.items())) + f"  => {'FAIL' if bad else 'PASS (provenance only)'}")
    if "--json" in sys.argv:
        json.dump({"stage": "A", "status": "FAIL" if bad else "PASS", "scope": "provenance only", "root_of_trust": FROZEN_COMMIT, "checks": res}, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
    sys.exit(4 if bad else 0)

if __name__ == "__main__":
    main()
