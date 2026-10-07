#!/usr/bin/env python3
"""Generate subject.lock.json for the SELECTED subject from the pinned upstream checkout. Stdlib only.
Usage: build_lock.py <upstream_checkout> <lock_out>
The selection itself is recorded as an explicit decision input (SELECTION below), not inferred.
"""
import hashlib, json, os, re, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inspect_candidates import Tree, sha, git, config_docs, families, yaml_facts

SELECTION = {"candidate": "InfiniteMatroid", "decided_by": "Ivan (ratifier)",
             "decision_date": "2026-10-07",
             "basis": "explicit instruction to the working session; candidate table in candidate_results.md; not a verification verdict"}
FAMILY = "185"
CFG = "lean/ComparatorChallenges/InfiniteMatroid"
PINNED_COMMIT = "adc7f1241b42e322a6451854ab7e4b4c146bf78a"
ENV_FILES = ["lean/lean-toolchain", "lean/lakefile.lean", "lean/lake-manifest.json"]

def digest(files):
    return hashlib.sha256("".join(f"{p} {h}\n" for p, h in sorted(files.items())).encode()).hexdigest()

def main():
    root, out = sys.argv[1], sys.argv[2]
    t = Tree(root)
    head = git(root, "rev-parse", "HEAD")
    assert head == PINNED_COMMIT, f"HEAD {head} != pin {PINNED_COMMIT}"
    cfg = json.load(open(os.path.join(root, CFG + ".json")))
    assert len(cfg["theorem_names"]) == 1
    decl = cfg["theorem_names"][0]
    sol_mod = cfg["solution_module"]
    sol_path = "lean/" + sol_mod.replace(".", "/") + ".lean"
    closure, ext, miss = t.closure(sol_mod)
    assert not ext and not miss, (ext, miss)
    closure_files = {os.path.relpath(p, root): sha(p) for (p, _, _) in closure.values()}
    docs = config_docs(t)["InfiniteMatroid"]
    assert len(docs) == 1 and docs[0]["docs"] == f"lean/docs/{FAMILY}.md"
    paper = docs[0]["papers"][0]
    fam = families(t)[FAMILY]
    assert fam["manuscripts"] == [paper]
    ms_dir = f"preprints/{paper}"
    ms_files = {}
    for dp, _, fs in sorted(os.walk(os.path.join(root, ms_dir))):
        for f in sorted(fs):
            full = os.path.join(dp, f); ms_files[os.path.relpath(full, root)] = sha(full)
    yf = yaml_facts(t)
    yentry = [m for m in yf["main_results"] if os.path.basename(m["comparator_config"]) == "InfiniteMatroid.json"]
    assert len(yentry) == 1
    patches = {os.path.relpath(os.path.join(dp, f), root): sha(os.path.join(dp, f))
               for dp, _, fs in os.walk(os.path.join(root, "lean/patches")) for f in sorted(fs) if f.endswith(".patch")}
    env_files = {p: sha(os.path.join(root, p)) for p in ENV_FILES}
    manifest = json.load(open(os.path.join(root, "lean/lake-manifest.json")))
    deps = {p["name"].strip("«»"): {"url": p["url"], "rev": p["rev"], "inherited": p["inherited"], "inputRev": p["inputRev"]}
            for p in manifest["packages"]}
    prev = {}
    if os.path.exists(out):
        prev = json.load(open(out)).get("upstream", {})
    retrieved = prev.get("retrieved_utc") or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    S = lambda p: {p: sha(os.path.join(root, p))}
    chain = [
      {"id": "E1", "role": "catalogue entry (family headline + manuscript list + link to docs bridge)",
       "path": "CONTENTS.md", "files_sha256": S("CONTENTS.md"), "identifier": f"family {FAMILY}",
       "source_commit": head, "enforcement": "PROSE_METADATA_ONLY",
       "detail": "Markdown entry '**185. ...** ([Lean](lean/docs/185.md))' followed by one manuscript link. Hyperlink only; no hash, no declaration name."},
      {"id": "E2", "role": "manuscript (informal claim source; TeX sources + PDF)",
       "path": ms_dir, "files_sha256": ms_files, "identifier": "TeX labels thm:main, cor:intersection, cor:separate-covering-packing (sections/01-introduction.tex, 07-consequences.tex)",
       "source_commit": head, "enforcement": "NONE",
       "detail": "Informal text. Nothing in upstream machine-checks that paper.pdf corresponds to build/*.tex or that either corresponds to any Lean declaration."},
      {"id": "E3", "role": "formalization bridge document (scope prose + links to paper and challenge)",
       "path": f"lean/docs/{FAMILY}.md", "files_sha256": S(f"lean/docs/{FAMILY}.md"), "identifier": "Comparator links table",
       "source_commit": head, "enforcement": "PROSE_METADATA_ONLY",
       "detail": "Human-written scope text. Links InfiniteMatroid.lean and InfiniteMatroidCorollaries.lean to one paper by relative hyperlinks. No hashes, no declaration names."},
      {"id": "E4", "role": "formalization catalogue metadata (machine-readable)",
       "path": "lean/formalization.yaml", "files_sha256": S("lean/formalization.yaml"),
       "identifier": {"main_results_entry": yentry[0], "sources_entry_id": f"../{ms_dir}/paper.pdf"},
       "source_commit": head, "enforcement": "METADATA_ONLY_UNLINKED",
       "detail": "main_results entry binds comparator_config+declaration+file but carries no manuscript/source field; sources[] lists the paper separately. review.status=unchecked."},
      {"id": "E5", "role": "Comparator challenge statement (sorry'd theorem + local definitions)",
       "path": CFG + ".lean", "files_sha256": S(CFG + ".lean"), "identifier": decl,
       "source_commit": head, "enforcement": "MACHINE_ENFORCED_CONDITIONAL",
       "detail": "Comparator checks solution proves the same statement as this challenge (given its trust assumptions). NOT EXECUTED here."},
      {"id": "E6", "role": "Comparator configuration", "path": CFG + ".json", "files_sha256": S(CFG + ".json"),
       "identifier": {"challenge_module": cfg["challenge_module"], "solution_module": sol_mod, "theorem_names": cfg["theorem_names"],
                      "definition_names": cfg.get("definition_names"), "permitted_axioms": cfg["permitted_axioms"], "enable_nanoda": cfg.get("enable_nanoda")},
       "source_commit": head, "enforcement": "MACHINE_ENFORCED_CONDITIONAL",
       "detail": "Consumed by Comparator. Binds challenge_module -> solution_module -> theorem_names."},
      {"id": "E7", "role": "solution module and complete local import closure", "path": sol_path, "files_sha256": closure_files,
       "identifier": {"solution_module": sol_mod, "closure_modules": sorted(closure), "closure_digest_sha256": digest(closure_files)},
       "source_commit": head, "enforcement": "MACHINE_ENFORCED_CONDITIONAL",
       "detail": "Elaborated and kernel-checked by Lean when built. External (non-local) imports: Mathlib only (scan). NOT EXECUTED here."},
      {"id": "E8", "role": "primary declaration", "path": sol_path, "files_sha256": {}, "identifier": decl,
       "source_commit": head, "enforcement": "MACHINE_ENFORCED_CONDITIONAL",
       "detail": "Comparator: same statement as challenge, axioms subset of permitted_axioms, kernel accepted."},
      {"id": "E9", "role": "Lean kernel acceptance evidence", "path": None, "files_sha256": {}, "identifier": None,
       "source_commit": None, "enforcement": "NOT_EXECUTED", "detail": "No build or Comparator run has happened in any environment recorded in this repository."},
    ]
    lock = {
      "schema": "p10-subject-lock/1",
      "status": "SELECTED_SUBJECT_FROZEN__NO_VERDICT",
      "selection": SELECTION,
      "upstream": {"repository": "https://github.com/openai/math", "commit": head, "commit_date": git(root, "log", "-1", "--format=%cI"), "retrieved_utc": retrieved},
      "selected_candidate": SELECTION["candidate"],
      "subject": {"manuscript_family": FAMILY, "manuscript_path": ms_dir + "/paper.pdf", "manuscript_sources_path": ms_dir + "/build/",
                  "formalization_metadata_path": "lean/formalization.yaml", "formalization_docs_path": f"lean/docs/{FAMILY}.md",
                  "challenge_path": CFG + ".lean", "solution_path": sol_path, "primary_declaration": decl, "comparator_config": CFG + ".json"},
      "binding_chain": chain,
      "adjacent_not_in_subject": {
        "note": "Same family; separate Comparator unit carrying the partitional/intersection and separate covering/packing corollaries. Recorded, NOT frozen as part of this subject.",
        "config": "lean/ComparatorChallenges/InfiniteMatroidCorollaries.json",
        "files_sha256": {p: sha(os.path.join(root, p)) for p in ("lean/ComparatorChallenges/InfiniteMatroidCorollaries.json", "lean/ComparatorChallenges/InfiniteMatroidCorollaries.lean")}},
      "environment_layer": {
        "toolchain": {"lean": open(os.path.join(root, "lean/lean-toolchain")).read().strip(), "source": "lean/lean-toolchain"},
        "files_sha256": env_files,
        "patches_sha256": patches,
        "patches_digest_sha256": digest(patches),
        "dependency_pins": deps,
        "mathlib_rev": deps["mathlib"]["rev"],
        "mathlib_rev_note": "d13f23b7 is 'chore: bump toolchain to v4.34.1' (2026-09-24T22:34+02:00); its own lake-manifest pins match the 8 inherited Mathlib deps in upstream's manifest (evidence/discovery/dependency_provenance.md)"},
      "p10_profile": {
        "note": "P10-AUTHORED files (not upstream artifacts) used to build the InfiniteMatroid closure without the 30-package upstream lakefile. Stage A (P1-P4) checks their hashes and derives their meaning from the frozen upstream manifest.",
        "files_sha256": {p: hashlib.sha256(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), p), "rb").read()).hexdigest() for p in ("profiles/minimal/lakefile.toml", "profiles/minimal/lake-manifest.json")}},
      "verifier_tooling": {"upstream_as_is": {"comparator": None, "lean4export": None, "landrun": None,
                               "status": "NOT DEMONSTRATED: exact verifier implementation used upstream (no revision recoverable; see evidence/discovery/comparator_provenance.md)"},
                           "p10_frozen_profile": "profiles/verifier_profiles.json#p10-frozen-v1"},
      "upstream_file_sha256": {p: sha(os.path.join(root, p)) for p in ("README.md", "lean/ComparatorChallenges/README.md", "lean/docs/185.md")},
    }
    json.dump(lock, open(out, "w"), indent=1, sort_keys=False)
    print("lock written", out, "chain", len(chain), "closure", len(closure_files), "patches", len(patches))

main()
