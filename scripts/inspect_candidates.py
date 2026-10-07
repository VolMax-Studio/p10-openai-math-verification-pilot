#!/usr/bin/env python3
"""Read-only discovery over a checkout of openai/math. Stdlib only.

Usage: inspect_candidates.py <upstream_checkout> <out_dir> [--inventory]

Writes (all derived by this script from the checkout; nothing is hand-edited):
  <out_dir>/upstream_facts.json      commit, toolchain, dependency pins, counts
  <out_dir>/candidates.json          per-candidate binding chain + SHA-256 of every file
  <out_dir>/challenge_inventory.json (--inventory; needs the FULL checkout) all Comparator configs
"""
import hashlib, json, os, re, subprocess, sys, datetime

CANDIDATES = [  # config basename -> docs file; ORDER IS NOT A RANKING
    "AbhyankarSathaye", "FiniteCongruenceGraph", "InfiniteMatroid",
    "GrahamSpherical", "PlanarAndersonSpectrum",
]
IMPORT = re.compile(r"^\s*(?:public\s+)?import\s+(.+)$", re.M)
NOISE = ("Mathlib", "Init", "Lean", "Std", "Batteries", "Aesop", "Qq", "Lake")

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def git(root, *a):
    return subprocess.check_output(["git", "-C", root, *a], text=True).strip()

def strip(t):
    return re.sub(r"--.*", "", re.sub(r"/-.*?-/", "", t, flags=re.S))

class Tree:
    def __init__(self, root):
        self.root, self.lean, self.cache = root, os.path.join(root, "lean"), {}
    def mod(self, m):
        return os.path.join(self.lean, m.replace(".", "/") + ".lean")
    def closure(self, root_mod):
        seen, ext, missing, stack = {}, set(), set(), [root_mod]
        while stack:
            m = stack.pop()
            if m in seen or m in ext or m in missing:
                continue
            p = self.mod(m)
            if not os.path.exists(p):
                if m.split(".")[0] in ("OAI", "ComparatorChallenges"):
                    missing.add(m)
                else:
                    ext.add(m.split(".")[0])
                continue
            t = open(p, errors="replace").read()
            seen[m] = (p, t.count("\n") + 1, t)
            stack += [x for l in IMPORT.findall(t) for x in l.split()]
        return seen, sorted(ext - set(NOISE)), sorted(missing)

def config_docs(tree):
    """docs/NNN.md -> papers + Comparator links (the only manuscript<->challenge link found)."""
    out = {}
    d = os.path.join(tree.lean, "docs")
    for f in sorted(os.listdir(d)):
        if not f.endswith(".md"):
            continue
        t = open(os.path.join(d, f)).read()
        papers = re.findall(r"\]\(\.\./\.\./preprints/(.+?)/paper\.pdf\)", t)
        for c in re.findall(r"\]\(\.\./ComparatorChallenges/([^)]+)\.lean\)", t):
            out.setdefault(c, []).append({"docs": "lean/docs/" + f, "papers": papers})
    return out

def families(tree):
    return families_from_text(open(os.path.join(tree.root, "CONTENTS.md")).read())

def families_from_text(t):
    """CONTENTS.md: '**NNN. Title.** headline ([Lean](lean/docs/NNN.md))' followed by that family's manuscripts."""
    parts = re.split(r"^\*\*(\d{3})\. ", t, flags=re.M)
    out = {}
    for i in range(1, len(parts), 2):
        body = parts[i + 1]
        head = re.sub(r"\s+", " ", body.split("</td>")[0]).strip()
        out[parts[i]] = {"headline": head,
                         "manuscripts": sorted(set(re.findall(r"\]\(preprints/(.+?)/[^/)]+\.pdf\)", body))),
                         "lean_docs_link": f"lean/docs/{parts[i]}.md" in body}
    return out

def yaml_facts(tree):
    return yaml_from_text(open(os.path.join(tree.lean, "formalization.yaml")).read())

def yaml_from_text(t):
    mr = re.findall(r"- comparator_config: (\S+)\n\s+declaration: (\S+)\n\s+file: (\S+)", t)
    return {
        "yaml_version": re.search(r'^version: "(.*)"', t, re.M).group(1),
        "sources_count": len(re.findall(r"^  - title:", t, re.M)),
        "main_results_count": len(mr),
        "main_results": [{"comparator_config": a, "declaration": b, "file": c} for a, b, c in mr],
        "review_status": re.search(r"^review:\n\s+status: (\S+)", t, re.M).group(1),
        "automation": re.findall(r"method: (\S+)", t.split("automation:")[1]),
        "scope": re.search(r'scope: "(.*)"', t).group(1),
    }

def main():
    root, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    tree = Tree(root)
    sha1 = git(root, "rev-parse", "HEAD")
    manifest = json.load(open(os.path.join(tree.lean, "lake-manifest.json")))
    yf = yaml_facts(tree)
    docs = config_docs(tree)
    fams = families(tree)
    mism = []
    for m in yf["main_results"]:
        cp = os.path.join(root, "lean", m["comparator_config"])
        if not os.path.exists(cp):
            mism.append({"config": m["comparator_config"], "issue": "config missing"}); continue
        c = json.load(open(cp))
        if m["declaration"] not in c["theorem_names"]:
            mism.append({"config": m["comparator_config"], "issue": "yaml declaration not in config theorem_names", "yaml": m["declaration"]})
        if c["solution_module"].replace(".", "/") + ".lean" != m["file"]:
            mism.append({"config": m["comparator_config"], "issue": "yaml file != config solution_module path", "yaml": m["file"], "config_module": c["solution_module"]})
    cfg_files = sorted(f for f in os.listdir(os.path.join(tree.lean, "ComparatorChallenges")) if f.endswith(".json"))
    facts = {
        "upstream": "https://github.com/openai/math",
        "commit": sha1,
        "commit_date": git(root, "log", "-1", "--format=%cI"),
        "commit_count_in_checkout": git(root, "rev-list", "--count", "HEAD"),
        "lean_toolchain": open(os.path.join(tree.lean, "lean-toolchain")).read().strip(),
        "dependencies": [{"name": p["name"].strip("«»"), "url": p["url"], "rev": p["rev"], "inherited": p["inherited"]} for p in manifest["packages"]],
        "comparator_configs": len(cfg_files),
        "formalization_yaml": {k: v for k, v in yf.items() if k != "main_results"},
        "yaml_vs_config_mismatches": mism,
        "yaml_main_results_have_source_field": bool(re.search(r"main_results:(?:.|\n)*?(source|paper|manuscript)", open(os.path.join(tree.lean, "formalization.yaml")).read().split("main_results:")[1].split("automation:")[0])),
        "families_in_contents": len(fams),
        "manuscripts_in_contents": len({m for f in fams.values() for m in f["manuscripts"]}),
        "configs_referenced_by_yaml_main_results": len({os.path.basename(m["comparator_config"]) for m in yf["main_results"]}),
        "docs_files": len([f for f in os.listdir(os.path.join(tree.lean, "docs")) if f.endswith(".md")]),
        "configs_linked_from_docs": len(docs),
        "sha256": {p: sha(os.path.join(root, p)) for p in (
            "README.md", "CONTENTS.md", "lean/lean-toolchain", "lean/lakefile.lean",
            "lean/lake-manifest.json", "lean/formalization.yaml", "lean/ComparatorChallenges/README.md")},
    }
    json.dump(facts, open(os.path.join(out, "upstream_facts.json"), "w"), indent=1)

    cands = {}
    for n in CANDIDATES:
        cfgp = f"lean/ComparatorChallenges/{n}.json"
        cfg = json.load(open(os.path.join(root, cfgp)))
        sol, ext, miss = tree.closure(cfg["solution_module"])
        _, cext, cmiss = tree.closure(cfg["challenge_module"])
        ymatch = [m for m in yf["main_results"] if os.path.basename(m["comparator_config"]) == n + ".json"]
        files = {cfgp: sha(os.path.join(root, cfgp)),
                 f"lean/ComparatorChallenges/{n}.lean": sha(os.path.join(root, f"lean/ComparatorChallenges/{n}.lean")),
                 "lean/formalization.yaml": facts["sha256"]["lean/formalization.yaml"]}
        d = docs.get(n, [])
        papers = sorted({p for e in d for p in e["papers"]})
        for e in d:
            files[e["docs"]] = sha(os.path.join(root, e["docs"]))
        for p in papers:
            for sub in ("paper.pdf", "README.md"):
                files[f"preprints/{p}/{sub}"] = sha(os.path.join(root, "preprints", p, sub))
            b = os.path.join(root, "preprints", p, "build")
            for dp, _, fs in sorted(os.walk(b)):
                for f in sorted(fs):
                    full = os.path.join(dp, f)
                    files[os.path.relpath(full, root)] = sha(full)
        for m, (p, _, _) in sorted(sol.items()):
            files[os.path.relpath(p, root)] = sha(p)
        body = [strip(t) for (_, _, t) in sol.values()]
        scan = {k: sum(len(re.findall(pat, b, re.M)) for b in body) for k, pat in {
            "sorry": r"\bsorry\b", "axiom_decl": r"^\s*axiom\b", "native_decide": r"native_decide",
            "unsafe": r"\bunsafe\b", "extern_or_implemented_by": r"implemented_by|@\[extern",
            "set_option": r"set_option", "run_cmd_elab_macro_initialize": r"run_cmd|^\s*elab |^\s*macro |^\s*initialize"}.items()}
        cands[n] = {
            "config": cfgp, "challenge_module": cfg["challenge_module"], "solution_module": cfg["solution_module"],
            "theorem_names": cfg["theorem_names"], "definition_names": cfg.get("definition_names", []),
            "permitted_axioms": cfg["permitted_axioms"], "enable_nanoda": cfg.get("enable_nanoda"),
            "yaml_main_results_entry": ymatch, "docs": d, "manuscripts": papers,
            "solution_closure_modules": len(sol), "solution_closure_lines": sum(l for (_, l, _) in sol.values()),
            "external_packages_in_closure": ext, "unresolved_local_modules": miss,
            "challenge_external_packages": cext, "challenge_unresolved": cmiss,
            "closure_text_scan_comments_stripped": scan,
            "families": {fn: {**fams[fn], "docs_linked_manuscripts_in_family": [p for p in papers if p in fams[fn]["manuscripts"]],
                              "docs_linked_manuscripts_not_in_family": [p for p in papers if p not in fams[fn]["manuscripts"]]}
                         for fn in sorted({e["docs"][-6:-3] for e in d}) if fn in fams},
            "files_sha256": files,
        }
    json.dump(cands, open(os.path.join(out, "candidates.json"), "w"), indent=1)

    if "--inventory" in sys.argv:
        inv = []
        for f in cfg_files:
            cfg = json.load(open(os.path.join(tree.lean, "ComparatorChallenges", f)))
            sol, ext, miss = tree.closure(cfg["solution_module"])
            _, cext, _ = tree.closure(cfg["challenge_module"])
            n = f[:-5]
            inv.append({"config": f, "solution_module": cfg["solution_module"], "theorems": len(cfg["theorem_names"]),
                        "closure_modules": len(sol), "closure_lines": sum(l for (_, l, _) in sol.values()),
                        "external_packages": ext, "unresolved_local": miss, "challenge_external": cext,
                        "docs": [e["docs"] for e in docs.get(n, [])], "papers": sorted({p for e in docs.get(n, []) for p in e["papers"]}),
                        "in_yaml_main_results": any(os.path.basename(m["comparator_config"]) == f for m in yf["main_results"])})
        json.dump(inv, open(os.path.join(out, "challenge_inventory.json"), "w"), indent=1)

    print("ok", sha1)

if __name__ == "__main__":
    main()
