#!/usr/bin/env python3
"""Stage A: provenance binding of the ENTIRE frozen chain. Stdlib only. Read-only on the checkout.
Usage: stage_a.py <upstream_checkout> <subject.lock.json> [--json <out>]
Exit: 0 all checks pass; 4 any check failed. PASS here means ONLY: the bytes and the metadata bindings are
exactly what the lock froze. It says nothing about Lean acceptance or manuscript correspondence.
Groups: HASH (cryptographic), CLOSURE (recomputed imports), STRUCT (prose/metadata consistency, string-level), ENV.
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inspect_candidates import Tree, sha, git, strip, families, yaml_facts

def run(root, lock_path):
    lock = json.load(open(lock_path)); res = []
    def chk(cid, group, ok, msg=""):
        res.append({"id": cid, "group": group, "status": "PASS" if ok else "FAIL", "detail": msg})
    t = Tree(root)
    # A1 commit
    try:
        head = git(root, "rev-parse", "HEAD")
    except Exception as e:
        head = f"ERR {e}"
    chk("A1.commit", "HASH", head == lock["upstream"]["commit"], f"HEAD={head} lock={lock['upstream']['commit']}")
    # A2 file hashes: every chain element + environment layer
    expected = {}
    for el in lock["binding_chain"]:
        for p, h in el["files_sha256"].items():
            expected[p] = h
    for p, h in lock["environment_layer"]["files_sha256"].items(): expected[p] = h
    for p, h in lock["environment_layer"]["patches_sha256"].items(): expected[p] = h
    for p, h in sorted(expected.items()):
        fp = os.path.join(root, p)
        if not os.path.isfile(fp):
            chk(f"A2.hash:{p}", "HASH", False, "missing"); continue
        got = sha(fp); chk(f"A2.hash:{p}", "HASH", got == h, "" if got == h else f"sha256 {got} != locked {h}")
    # A3 closure
    subj = lock["subject"]; cfgp = os.path.join(root, subj["comparator_config"])
    try:
        cfg = json.load(open(cfgp)); solmod = cfg["solution_module"]
        closure, ext, miss = t.closure(solmod)
        locked = next(e for e in lock["binding_chain"] if e["id"] == "E7")["identifier"]["closure_modules"]
        chk("A3.closure_set", "CLOSURE", sorted(closure) == locked, f"recomputed {len(closure)} vs locked {len(locked)}; extra={sorted(set(closure)-set(locked))} missing={sorted(set(locked)-set(closure))}")
        chk("A3.closure_external_imports_none", "CLOSURE", not ext and not miss, f"external={ext} unresolved_local={miss}")
    except Exception as e:
        cfg = None; closure = {}
        chk("A3.closure_set", "CLOSURE", False, f"cannot compute: {e!r}")
    # A4 structural / prose-metadata bindings
    try:
        fam = families(t)[subj["manuscript_family"]]
        ms = subj["manuscript_path"].split("/")[1]
        chk("S1.catalogue->docs+manuscript", "STRUCT", fam["lean_docs_link"] and fam["manuscripts"] == [ms], f"lean_docs_link={fam['lean_docs_link']} manuscripts={fam['manuscripts']}")
    except Exception as e: chk("S1.catalogue->docs+manuscript", "STRUCT", False, repr(e))
    try:
        d = open(os.path.join(root, subj["formalization_docs_path"])).read()
        cname = os.path.basename(subj["challenge_path"])
        chk("S2.docs->manuscript+challenge", "STRUCT", f"preprints/{subj['manuscript_path'].split('/')[1]}/paper.pdf" in d.replace("../../", "") and f"../ComparatorChallenges/{cname})" in d, "docs links paper and challenge .lean")
    except Exception as e: chk("S2.docs->manuscript+challenge", "STRUCT", False, repr(e))
    try:
        yf = yaml_facts(t); cn = os.path.basename(subj["comparator_config"])
        ent = [m for m in yf["main_results"] if os.path.basename(m["comparator_config"]) == cn]
        sol_rel = subj["solution_path"][len("lean/"):]
        chk("S3.yaml_main_results==config", "STRUCT", len(ent) == 1 and ent[0]["declaration"] == subj["primary_declaration"] and ent[0]["file"] == sol_rel, f"entry={ent}")
    except Exception as e: chk("S3.yaml_main_results==config", "STRUCT", False, repr(e))
    if cfg:
        chal_rel = "lean/" + cfg["challenge_module"].replace(".", "/") + ".lean"
        sol_rel2 = "lean/" + cfg["solution_module"].replace(".", "/") + ".lean"
        chk("S4.config_paths+decl", "STRUCT", chal_rel == subj["challenge_path"] and sol_rel2 == subj["solution_path"] and cfg["theorem_names"] == [subj["primary_declaration"]] and set(cfg["permitted_axioms"]) <= {"propext", "Quot.sound", "Classical.choice"}, f"challenge={chal_rel} solution={sol_rel2} theorems={cfg['theorem_names']} axioms={cfg['permitted_axioms']}")
        def decl_info(path):
            try: txt = strip(open(os.path.join(root, path)).read())
            except OSError: return None
            ns = re.findall(r"^\s*namespace\s+(\S+)", txt, re.M)
            m = re.search(r"theorem\s+main\b(.*?)(?=\n(?:end|theorem|namespace)\b|\Z)", txt, re.S)
            return {"ns": ns, "has_main": bool(m), "sorry": bool(m and re.search(r"\bsorry\b", m.group(1))), "file_sorry": bool(re.search(r"\bsorry\b", txt))}
        ci, si = decl_info(subj["challenge_path"]), decl_info(subj["solution_path"])
        full = subj["primary_declaration"]
        want_ns = full.rsplit(".", 1)[0]
        leaf_ns = want_ns.split(".")[-1]
        okc = bool(ci) and ci["has_main"] and ci["sorry"] and ci["ns"][:2] == ["OAI", leaf_ns]
        chk("S5.challenge_declares_main_with_sorry", "STRUCT", okc, f"{ci}")
        oks = bool(si) and si["has_main"] and not si["sorry"] and not si["file_sorry"] and leaf_ns in si["ns"]
        chk("S6.solution_declares_main_without_sorry", "STRUCT", oks, f"{si}")
        sorry_any = [m for m, (_, _, tx) in closure.items() if re.search(r"\bsorry\b", strip(tx))]
        chk("S6b.closure_has_no_sorry_token", "STRUCT", not sorry_any, f"files={sorry_any}")
    # A5 environment layer (string-level)
    env = lock["environment_layer"]
    try:
        tc = open(os.path.join(root, "lean/lean-toolchain")).read().strip()
        man = json.load(open(os.path.join(root, "lean/lake-manifest.json")))
        mrev = {p["name"].strip("«»"): p["rev"] for p in man["packages"]}
        lf = open(os.path.join(root, "lean/lakefile.lean")).read()
        req = {n.strip("«»"): r for n, r in re.findall(r'require\s+(\S+)\s+from\s+git\s+"[^"]+"\s+@\s+"([0-9a-f]{40})"', lf)}
        chk("E1.toolchain", "ENV", tc == env["toolchain"]["lean"], tc)
        chk("E2.mathlib_rev", "ENV", mrev.get("mathlib") == env["mathlib_rev"] == req.get("mathlib"), f"manifest={mrev.get('mathlib')} lakefile={req.get('mathlib')} lock={env['mathlib_rev']}")
        chk("E3.lakefile_requires==manifest", "ENV", all(mrev.get(n) == r for n, r in req.items()) and len(req) == 30, f"{len(req)} direct requires")
        chk("E4.manifest_pins==lock", "ENV", {n: mrev[n] for n in mrev} == {n: v["rev"] for n, v in env["dependency_pins"].items()}, "")
        pdir = os.path.join(root, "lean/patches")
        have = sorted("lean/patches/" + f for f in os.listdir(pdir) if f.endswith(".patch"))
        chk("E5.patch_set", "ENV", have == sorted(env["patches_sha256"]), f"{len(have)} patch files on disk vs {len(env['patches_sha256'])} locked")
    except Exception as e:
        chk("E*.environment", "ENV", False, repr(e))
    return res

def main():
    root, lockp = sys.argv[1], sys.argv[2]
    res = run(root, lockp)
    bad = [r for r in res if r["status"] == "FAIL"]
    by = {}
    for r in res: by.setdefault(r["group"], [0, 0]); by[r["group"]][0 if r["status"] == "PASS" else 1] += 1
    for r in bad: print(f"  FAIL {r['id']}: {r['detail'][:200]}")
    print("A: " + ", ".join(f"{g}: {p} pass/{f} fail" for g, (p, f) in sorted(by.items())) + f"  => {'FAIL' if bad else 'PASS (provenance only)'}")
    if "--json" in sys.argv:
        json.dump({"stage": "A", "status": "FAIL" if bad else "PASS", "scope": "provenance only", "checks": res}, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
    sys.exit(4 if bad else 0)

if __name__ == "__main__":
    main()
