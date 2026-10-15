# Cycle 2 data checkpoint

Date: 2026-09-07
Status: frozen internal Cycle 2 corpus and representation release

## Frozen outputs

- 592 public-build provenance-preserving high-recall formula candidates: 332 from *Xiangcheng*, 16 from *Hong shi Xiangpu*, and 244 from *Chen shi Xiangpu*. Eleven locally reviewed *Zunsheng bajian* candidates are excluded from git and every public downstream artifact.
- 296 automatically ratio-ready candidates. This parser flag is never used as a curated label.
- 121 genealogy-retrieval edges, 415 provisional families, and 99 multi-member families after rejecting same-title/zero-material-overlap links.
- A 120-record, family-deduplicated review batch spanning six provisional work groups.
- `Xiangji Formula Reference v0.1`: 91 included exact-composition formula families from six work groups; 29 exclusions retain seven-gate decisions and structured reasons.
- Included formulas contain 2–17 aromatic components (mean 6.85). Every composition is recomputed from recorded source quantities and closes to one.
- Five leave-one-work-out development folds and ten primary folds holding out two works simultaneously. Six Hong-source records are sealed and absent from every development fold.
- 40 PubChem-resolved compounds with pinned RDKit 2026.3.3 molecular descriptors and Morgan fingerprints.
- 18 source-located material profiles from 17 primary analytical studies: 38 numeric component edges and four presence-only edges. Coverage is 65.24% of aromatic-material mentions in the automatic ratio-ready pool.
- Three profile-level material representations: controlled odor-tag weights, molecular-set fingerprints, and physicochemical descriptor vectors. Profiles remain separated by specimen, preparation and assay.
- Crossref/Europe PMC metadata verification for all 17 analytical sources: all titles match after normalization; two online-first/issue-year differences remain explicitly annotated.
- 63 automated tests passing after a clean one-command rebuild.

## Frozen hashes

| Artifact | SHA-256 |
|---|---|
| Curation batch | `89909d380a9c93340be3e17a38b0140b2e303c007a5800d258f29183548a25ed` |
| Curation manifest | `61c3a2e7709022fab10bb0ec666568f0c24fe9cdf1d09357a0d3838e75db688a` |
| Formula reference | `476e9078c4fe6b22cd1aa5e367461d68b6c6c99a0ef45e1a5de90e98900d15be` |
| Formula audit | `f9ad6a1b697efee6e6f749a4636c39c2a53da3514f6a0dedcb332b9c88e056bf` |

The formula-reference hash is expected to change only if its manifest hash field or reviewed content changes. The batch hash is the hard input lock used by the builder.

## Scientific consequences

1. Random recipe splitting is prohibited: copied or lightly edited formulae would leak across train and test.
2. The 91 formulas are a curated reference set, not historical ground truth. Review consisted of two passes by one analyst plus deterministic checks; independent agreement has not been measured.
3. Material chemical profiles are conditional observations, not timeless identities. Peak area, calibrated concentration and presence evidence remain different measurement types.
4. CText-derived transcription and structured records remain local-only and are excluded from the public v0.1 pipeline pending scan and redistribution review.
5. The sealed Hong-source subset may not be opened for model selection, threshold tuning or error-driven architecture changes.

## Reproduction

```bash
make -C research cycle2-data
```

Expected terminal state: 592 candidates, 296 automatically ratio-ready, 121 genealogy edges, 91 included reference families, 18 material profiles, 10 primary two-source folds, and 63 passing tests.
