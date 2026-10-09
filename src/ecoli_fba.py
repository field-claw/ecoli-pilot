#!/usr/bin/env python3
"""Real FBA engine for the E. coli (iML1515) virtual-microbe pilot.

This module is a self-contained, reproducible constraint-based FBA runner.
It deliberately uses ONLY relative paths so that the whole repository is
portable (no hardcoded absolute paths on any machine).

Model: iML1515 (Escherichia coli str. K-12 substr. MG1655)
  - Source: BiGG Models (bigg.model:iML1515, taxonomy 511145)
  - 5883 reactions / 1877 metabolites / 1516 genes
  - Default objective: BIOMASS_Ec_iML1515_core_75p37M
  - WT growth rate ~0.87 h^-1

All numeric results printed here are computed by COBRApy at runtime; nothing
is hard-coded as a "result". The verify.py gate re-derives the same numbers
independently and asserts them.

Usage:
    python src/ecoli_fba.py            # print WT growth + carbon guardrail
    python src/ecoli_fba.py --quiet    # minimal output (exit code only)
"""
from __future__ import annotations

import argparse
import os
import sys

import cobra

# ----- path resolution (relative, portable) ---------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
MODEL_PATH = os.path.join(REPO_ROOT, "data", "iML1515.json")

# Expected organism identity (anti-mislabel guard; see verify.py L4).
EXPECTED_ORGANISM = "Escherichia coli"
EXPECTED_MODEL_ID = "iML1515"
EXPECTED_BIOMASS = "BIOMASS_Ec_iML1515_core_75p37M"


def load_model(path: str = MODEL_PATH):
    return cobra.io.load_json_model(path)


def wt_growth(model) -> float:
    """Maximize the default biomass objective; return growth rate (h^-1)."""
    sol = model.optimize()
    if sol.status != "optimal":
        raise RuntimeError(f"WT FBA not optimal: status={sol.status}")
    return float(sol.objective_value)


def _met_has_carbon(met) -> bool:
    formula = getattr(met, "formula", None) or ""
    return "C" in formula


def carbon_guardrail(model):
    """Close every carbon-containing exchange reaction, then re-optimize.

    A genuine heterotrophic GEM must become infeasible (growth collapses) when
    all carbon sources are removed. Returns (n_closed, status, value).
    """
    m = model.copy()
    closed = 0
    for r in m.reactions:
        if not r.id.startswith("EX_"):
            continue
        mets = list(r.metabolites.keys())
        if not mets:
            continue
        if _met_has_carbon(mets[0]):
            r.lower_bound = 0.0
            r.upper_bound = 0.0
            closed += 1
    sol = m.optimize()
    return closed, sol.status, float(sol.objective_value)


def assert_organism(model) -> None:
    """Fail-closed guard: refuse to run if the model is not E. coli."""
    name = (model.name or "").lower()
    mid = (model.id or "").lower()
    if EXPECTED_ORGANISM.lower() not in name:
        raise RuntimeError(
            f"Organism mismatch: expected '{EXPECTED_ORGANISM}' but model.name="
            f"'{model.name}' (id='{model.id}'). Refusing to proceed."
        )
    if EXPECTED_MODEL_ID.lower() not in mid:
        raise RuntimeError(
            f"Model id mismatch: expected '{EXPECTED_MODEL_ID}' but got '{model.id}'."
        )
    # Reverse contamination check: the iJB1325 incident proved a model can be
    # silently mislabeled. Scan reaction/metabolite/gene ids+names for foreign
    # organisms.
    foreign = ("aspergillus", "saccharomyces", "niger", "cerevisiae")
    hits = []
    for r in model.reactions:
        blob = f"{r.id} {getattr(r, 'name', '') or ''}".lower()
        if any(f in blob for f in foreign):
            hits.append(r.id)
    for g in model.genes:
        blob = f"{g.id} {getattr(g, 'name', '') or ''}".lower()
        if any(f in blob for f in foreign):
            hits.append(g.id)
    if hits:
        raise RuntimeError(
            f"Foreign-organism identifiers detected ({len(hits)}): {hits[:10]}"
        )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="E. coli (iML1515) real FBA runner")
    ap.add_argument("--quiet", action="store_true", help="minimal output")
    args = ap.parse_args(argv)

    model = load_model()
    assert_organism(model)

    growth = wt_growth(model)
    closed, status, val = carbon_guardrail(model)
    guard_ok = status != "optimal"

    if not args.quiet:
        print(f"model        : {model.id} — {model.name}")
        print(f"dimensions   : {len(model.reactions)} rxn / "
              f"{len(model.metabolites)} met / {len(model.genes)} gene")
        print(f"biomass obj  : {EXPECTED_BIOMASS}")
        print(f"WT growth    : {growth:.6f} h^-1")
        print(f"carbon guard : closed {closed} C-exchanges -> "
              f"status={status} (crash={guard_ok})")
        print("RESULT       : " + ("PASS" if guard_ok else "FAIL"))

    return 0 if guard_ok else 1


if __name__ == "__main__":
    sys.exit(main())
