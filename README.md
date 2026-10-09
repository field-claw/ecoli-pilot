# ecoli-pilot — Real *Escherichia coli* (iML1515) virtual-microbe pilot

A minimal, reproducible constraint-based FBA pilot for **bona-fide**
*Escherichia coli* K-12 MG1655. This is the genuine E. coli entry of the
VitaMind virtual-microbe series — it replaces the earlier mislabeled
`ecoli_pilot` (whose model turned out to be *Aspergillus niger*; see
`ijb1325-aniger-archive`).

## Model

| Field | Value |
|---|---|
| Model id | `iML1515` |
| Organism | *Escherichia coli* str. K-12 substr. MG1655 (taxonomy 511145) |
| Source | [BiGG Models](https://bigg.ucsd.edu/models/iML1515) |
| Reactions / Metabolites / Genes | 5883 / 1877 / 1516 |
| Default objective | `BIOMASS_Ec_iML1515_core_75p37M` |
| WT growth rate | ≈ **0.87 h⁻¹** (real per-hour rate) |

The enzyme-constrained JSON (`eciML1515`) also carries an `enzyme_constraint`
table, but this pilot treats the model as a standard GEM (the enzyme budget is
not exercised).

## What this pilot proves

- **Real FBA** with COBRApy — no mock, no fabricated numbers. Every figure is
  re-derived at runtime by `verify.py`.
- **Carbon guardrail** — close all carbon-containing exchange reactions and the
  LP becomes infeasible (growth collapses). This is the honest discriminator
  between a real heterotrophic GEM and a broken/skeleton model.
- **Species assertion** — the gate refuses to pass unless the model name is
  *E. coli*, the id is `iML1515`, and no foreign-organism identifiers
  (*Aspergillus*, *Saccharomyces*) are present. This guard exists because a
  model was once silently mislabeled as E. coli.

## Reproduce

```bash
pip install -r requirements.txt
python src/ecoli_fba.py          # print WT growth + carbon guardrail
python verify.py                 # run the 7-check fail-closed gate
```

`verify.py` must exit `0` (all checks PASS). It is fully self-contained and
uses only **relative paths**, so the repository is portable to any machine.

### Check catalogue

| Check | What it asserts |
|---|---|
| L0 | License files present + no absolute paths in source |
| L1 | Dimensions 5883 / 1877 / 1516 |
| L2 | WT FBA growth ≈ 0.87 h⁻¹ |
| L3 | Carbon guardrail: closing C-exchanges ⇒ LP infeasible |
| L4 | Species: *E. coli*, id `iML1515`, no foreign-organism ids |
| L5 | Objective biomass = `BIOMASS_Ec_iML1515_core_75p37M` |
| L6 | Growth is a real h⁻¹ rate (0.1 < v < 2.0) |

## License

- **Code** (`src/`, `verify.py`): MIT — see `LICENSE`.
- **Model** (`data/iML1515.json`): BiGG Models / UCSD non-profit license —
  educational, research and non-profit use only; **commercial use NOT
  permitted**. See `THIRD_PARTY_LICENSES/BiGG_LICENSE.txt` and `NOTICE.md`
  for the full terms and required citation (Monk *et al.*, Nat. Biotechnol.
  2017, doi:10.1038/nbt.3956).

## Series

Part of the VitaMind virtual-microbe series. Index and cross-links:
<https://github.com/field-claw/vitamind-virtual-microbe>
