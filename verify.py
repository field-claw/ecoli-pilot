#!/usr/bin/env python3
"""Fail-closed verification gate for the E. coli (iML1515) pilot.

Re-derives every number from the model at runtime — nothing is hard-coded as a
"passing result". This gate exists precisely because the iJB1325 model was once
silently mislabeled as E. coli; checks L4/L6 are the anti-recurrence guards.

Checks
------
L0  License presence + NO absolute paths in source (portability / reproducibility)
L1  Model dimensions: 5883 rxn / 1877 met / 1516 gene
L2  WT FBA growth ~0.87 h^-1 (real per-hour rate, not a model-unit artifact)
L3  Carbon guardrail: closing all carbon exchanges makes LP infeasible (growth crash)
L4  Species assertion: name==E. coli, id==iML1515, NO foreign-organism identifiers
L5  Biomass identity: default objective == BIOMASS_Ec_iML1515_core_75p37M
L6  Growth-unit sanity: 0.1 < growth < 2.0 h^-1 (distinguishes h^-1 from model units)

Run:  python verify.py
Exit: 0 if all pass, 1 otherwise.
"""
from __future__ import annotations

import os
import re
import sys

import cobra

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "data", "iML1515.json")

EXPECTED = dict(
    id="iML1515",
    name_substr="Escherichia coli",
    rxn=5883,
    met=1877,
    gene=1516,
    biomass="BIOMASS_Ec_iML1515_core_75p37M",
)
# foreign organisms that must NEVER appear in an E. coli model
FOREIGN = ("aspergillus", "saccharomyces", "niger", "cerevisiae")


def _check(name, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    line = f"[{mark}] {name}" + (f" — {detail}" if detail else "")
    print(line)
    return ok


def _has_carbon(met) -> bool:
    return "C" in (getattr(met, "formula", None) or "")


def main() -> int:
    results = []

    # ---- L0: license files present + no absolute paths in source ------------
    lic_ok = os.path.isfile(os.path.join(HERE, "LICENSE"))
    tp_ok = os.path.isfile(
        os.path.join(HERE, "THIRD_PARTY_LICENSES", "BiGG_LICENSE.txt")
    )
    notice_ok = os.path.isfile(os.path.join(HERE, "NOTICE.md"))
    abs_paths = []
    for root, _dirs, files in os.walk(os.path.join(HERE, "src")):
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(root, f)
            with open(p, encoding="utf-8") as fh:
                txt = fh.read()
            for m in re.finditer(r'["\']([A-Za-z]:[\\/][^"\']+|/[a-zA-Z][^"\']+)', txt):
                # ignore http(s) urls and relative paths
                tok = m.group(1)
                if tok.startswith("http"):
                    continue
                abs_paths.append((f, tok))
    l0 = _check("L0 license+portability",
                lic_ok and tp_ok and notice_ok and not abs_paths,
                f"LICENSE={lic_ok} BiGG={tp_ok} NOTICE={notice_ok} "
                f"abs_paths={abs_paths}")
    results.append(l0)

    # ---- load model ---------------------------------------------------------
    model = cobra.io.load_json_model(MODEL_PATH)

    # ---- L1: dimensions -----------------------------------------------------
    l1 = _check("L1 dimensions",
                len(model.reactions) == EXPECTED["rxn"]
                and len(model.metabolites) == EXPECTED["met"]
                and len(model.genes) == EXPECTED["gene"],
                f"{len(model.reactions)}/{len(model.metabolites)}/"
                f"{len(model.genes)} (expect 5883/1877/1516)")
    results.append(l1)

    # ---- L2: WT growth ------------------------------------------------------
    sol = model.optimize()
    growth = float(sol.objective_value) if sol.status == "optimal" else None
    l2 = _check("L2 WT growth ~0.87 h^-1",
                growth is not None and abs(growth - 0.8698) < 0.05,
                f"growth={growth:.6f} status={sol.status}")
    results.append(l2)

    # ---- L3: carbon guardrail ----------------------------------------------
    m2 = model.copy()
    closed = 0
    for r in m2.reactions:
        if not r.id.startswith("EX_"):
            continue
        mets = list(r.metabolites.keys())
        if mets and _has_carbon(mets[0]):
            r.lower_bound = 0.0
            r.upper_bound = 0.0
            closed += 1
    sol2 = m2.optimize()
    guard_ok = sol2.status != "optimal"
    l3 = _check("L3 carbon guardrail (growth must crash)",
                guard_ok,
                f"closed={closed} C-exchanges -> status={sol2.status}")
    results.append(l3)

    # ---- L4: species assertion (anti-mislabel) ------------------------------
    name_l = (model.name or "").lower()
    id_l = (model.id or "").lower()
    name_ok = EXPECTED["name_substr"].lower() in name_l
    id_ok = EXPECTED["id"].lower() in id_l
    foreign_hits = []
    for r in model.reactions:
        blob = f"{r.id} {getattr(r, 'name', '') or ''}".lower()
        if any(f in blob for f in FOREIGN):
            foreign_hits.append(r.id)
    for g in model.genes:
        blob = f"{g.id} {getattr(g, 'name', '') or ''}".lower()
        if any(f in blob for f in FOREIGN):
            foreign_hits.append(g.id)
    l4 = _check("L4 species assertion (E. coli, no foreign ids)",
                name_ok and id_ok and not foreign_hits,
                f"name='{model.name}' id='{model.id}' "
                f"foreign_hits={len(foreign_hits)}")
    results.append(l4)

    # ---- L5: biomass identity ----------------------------------------------
    obj_rxn = None
    for r in model.reactions:
        if abs(r.objective_coefficient) > 0:
            obj_rxn = r.id
            break
    l5 = _check("L5 biomass identity",
                obj_rxn == EXPECTED["biomass"],
                f"objective={obj_rxn} (expect {EXPECTED['biomass']})")
    results.append(l5)

    # ---- L6: growth-unit sanity (h^-1, not model units) ---------------------
    l6 = _check("L6 growth-unit sanity (0.1 < h^-1 < 2.0)",
                growth is not None and 0.1 < growth < 2.0,
                f"growth={growth:.6f}")
    results.append(l6)

    total = len(results)
    passed = sum(results)
    print("-" * 60)
    print(f"verify: {passed}/{total} checks passed")
    print("OVERALL: " + ("PASS" if passed == total else "FAIL"))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
