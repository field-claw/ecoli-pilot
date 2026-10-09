# NOTICE — Third-Party Model Attribution

This repository redistributes a genome-scale metabolic model under the
BiGG Models / University of California, San Diego non-profit license.

## Model

| Field | Value |
|---|---|
| Model id | `iML1515` |
| Organism | *Escherichia coli* str. K-12 substr. MG1655 |
| Taxonomy | 511145 |
| Source | BiGG Models (`bigg.model:iML1515`) |
| File | `data/iML1515.json` |
| Reactions / Metabolites / Genes | 5883 / 1877 / 1516 |

The JSON is an enzyme-constrained variant (`eciML1515`) that carries an
`enzyme_constraint` table, but the FBA gate in this repository treats the model
as a standard constraint-based GEM (the enzyme constraint is not exercised).

## Required citation

Monk JM, Lloyd CJ, Brunk E, Mih N, Sastry A, King Z, Takeuchi R, Nomura W,
Zhang Z, Mori H, Feist AM, Palsson BO. **iML1515, a knowledgebase that computes
*Escherichia coli* traits.** *Nature Biotechnology.* 2017;35(10):904-908.
doi:10.1038/nbt.3956 (PubMed: 29020004).

BiGG Models database: King ZA, Lu JS, Drager A, et al. *Nucleic Acids Research.*
2016;44(D1):D515-D522. doi:10.1093/nar/gkv1049

## License

The model file is redistributed for educational, research and non-profit
purposes only under the UCSD non-profit license. **Commercial use is NOT
permitted** — contact `invent@ucsd.edu` for commercial licensing. The full
license text is in `THIRD_PARTY_LICENSES/BiGG_LICENSE.txt`. This notice must
accompany all copies.

## Code

The FBA engine (`src/ecoli_fba.py`) and verification gate (`verify.py`) are
original code released under the MIT license (`LICENSE`).
