# Cycle 2 completion report

Date: 2026-09-07
Decision: internal Cycle 2 gate passed; Cycle 3 may begin only in the next scheduled work period

## Gate results

| Requirement | Result | Evidence |
|---|---|---|
| Every model-ready formula has a stable source | Pass | 91/91 reference records contain revision URL, locator and source-text hash |
| At least 80 family-unique formulas | Pass | 91 included records, 91 unique family IDs |
| At least five work groups | Pass | Six included work groups |
| Exact labels are reproducible | Pass | All compositions recomputed from aromatic mass mentions and close to 1 |
| Near-duplicate leakage is controlled | Pass | Family-unique reference plus family/source-disjoint split assertions |
| Family decisions carry inspectable evidence | Pass | 91 family audits with member-level title, text, material and composition comparisons |
| Two sources unseen in primary evaluation | Pass | Ten frozen pair-held-out folds |
| Sealed external evaluation exists | Pass | Six Hong-source records excluded from all development folds |
| Chemical fields carry provenance | Pass | 18 profiles, 17 verified sources, statement-level locators and typed measurements |
| Multiple chemical representations exist | Pass | Odor-tag, molecular-set and physicochemical profile views |
| Missingness and proxies are explicit | Pass | Presence-only, unresolved identity, preparation context and conditional-vector status retained |
| Bounded literature evidence map exists | Pass | 11 method papers, 17 analytical studies, screening table, evidence matrix, novelty matrix and BibTeX |
| Automated rebuild succeeds | Pass | `make -C research cycle2-data`; 63 tests pass |

## What is frozen

1. Formula selection and exclusion decisions for v0.1.
2. Material ontology and contextual SKchar resolution table.
3. Compound vocabulary, PubChem records and RDKit feature settings.
4. Primary analytical evidence graph and profile-level representations.
5. Development, primary and sealed source-blocked indices.

## Deliberately open external gates

These items are not represented as completed and do not invalidate the internal data freeze:

- independent second-annotator review and agreement statistics;
- page-image verification for the four contextually resolved SKchar characters;
- redistribution clearance and scan verification for locally held CText-derived spans;
- expansion from six to eight independent work groups;
- fuller analytical coverage for unresolved historical grades and animal materials;
- full systematic-review database coverage requiring institutional Web of Science, Scopus or CNKI access.

They remain release-strengthening tasks and must be reported honestly in the manuscript. Cycle 3 may use only the frozen public-reference subset and may not infer missing chemistry as observed evidence.

## Cycle 3 handoff constraints

- Do not access the sealed Hong subset.
- Do not tune against the 30 lost-incense targets.
- Fit and select models only on the supplied development folds.
- Keep profile-level assay context; do not average incompatible measurements.
- Report source-macro metrics alongside pooled metrics because work sizes are unbalanced.
- Any curation correction increments the dataset version and invalidates dependent hashes.
