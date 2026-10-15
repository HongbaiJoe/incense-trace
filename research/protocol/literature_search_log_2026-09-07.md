# Targeted analytical-literature search log

Search date: 2026-09-07  
Purpose: construct the first source-backed material-to-compound evidence layer for the chemical regularizer. This is a targeted evidence search, not yet the systematic review used to position the final paper.

## Eligibility rule

A profile was eligible only when all of the following were available:

1. a primary analytical study of a material represented in the historical ontology;
2. a named taxon or explicitly reported material family, sampled plant or animal part, and preparation/extraction context;
3. an analytical method and a statement-level locator (table, results subsection or abstract);
4. a resolvable DOI or PMID whose title could be checked against Crossref or Europe PMC;
5. molecular identities that could be mapped to the versioned PubChem vocabulary.

Numeric abundance was transcribed only from the primary study. Peak-area percentages, calibrated concentrations and mere presence are distinct measurement types. Non-detects and traces were not converted to zero. Values from different specimens, origins or extraction methods were stored as observed intervals rather than pooled means.

## Discovery queries

Europe PMC REST was queried with `format=json`, `resultType=core`, and `pageSize=10` or `20`. Targeted terms included combinations of:

- `agarwood Aquilaria essential oil GC-MS chemical composition`;
- `Santalum album heartwood essential oil GC-MS alpha-santalol`;
- `Boswellia sacra oil GC-MS composition`;
- `Syzygium aromaticum buds essential oil GC-MS composition`;
- `Cinnamomum cassia stem essential oil GC-MS`;
- `Cyperus rotundus rhizome essential oil GC-MS`;
- `Pogostemon cablin Nardostachys jatamansi ten essential oils GC-MS`;
- `Angelica dahurica root aroma-active GC-MS/O`;
- `Saussurea costus roots volatile constituents GC-MS`;
- `natural borneol chemical profiles GC-MS`;
- `Moschus berezovskii musk chemical composition GC-MS`;
- `Scrophularia ningpoensis root chemical constituents`;
- `Glycyrrhiza glabra root volatiles steam distillation SPME chemometrics`;
- `Liquidambar orientalis styrax oil GC-MS`;
- `Foeniculum vulgare seed essential oil GC-MS`;
- `Cinnamomum camphora stem bark essential oil GC-MS`;
- `Rheum palmatum rhizome volatile components GC-MS`.

Exact-record retrieval then used `PMCID:<identifier>`, `EXT_ID:<PMID>` or a DOI query. Crossref metadata were retrieved through `https://api.crossref.org/works/<percent-encoded-doi>`. Open full text, when available, was read through Europe PMC JATS XML; an author-hosted full text was used for the licorice Table 1. Publisher abstracts were used only when the abstract itself contained the analytical result.

The reproducible metadata command is:

```bash
make -C research literature-metadata
```

It writes the normalized Crossref/Europe PMC snapshot and flags title or year disagreements. The networked metadata refresh is kept separate from the offline corpus and feature build.

## Included analytical sources

| Material profile | Primary identifier | Evidence locator |
|---|---|---|
| *Aquilaria crassna* agarwood oil | `10.14233/ajchem.2020.22177` | publisher abstract |
| *Santalum album* heartwood oil | `10.1007/s13205-019-1758-9` | Table 2; Results paragraph 33 |
| *Boswellia sacra* oils | `10.3390/antibiotics9040195` | Table 2 |
| *Syzygium aromaticum* buds | `10.1155/2021/9940591` | Table 1 |
| *Cinnamomum cassia* stem oil | `10.1155/2018/7405736` | Table 1, EOCc column |
| *Cyperus rotundus* rhizome oil | `10.1038/srep45231` | Table 1, present-result column |
| Patchouli and spikenard commercial oils | `10.1016/j.biopen.2017.04.001` | Table 1; Essential-oils methods |
| *Angelica dahurica* roots | `10.3390/molecules24234352` | Table 3 |
| *Saussurea costus* roots | `10.4103/0974-8490.112424` | abstract; Results and Discussion |
| Natural borneol drug material | `10.3390/molecules22091446` | Table 1, NB column; Methods 4.1-4.2 |
| *Moschus berezovskii* secretion | `10.1038/srep18975` | Table 1; Musk chemical composition |
| *Scrophularia ningpoensis* root | `PMID:25857160` | indexed Methods and Results abstract |
| *Glycyrrhiza glabra* roots | `10.1111/j.1750-3841.2012.02927.x` | Table 1; plant-material methods |
| Asian styrax gum oil | `10.1002/ffj.1370` | publisher abstract |
| *Foeniculum vulgare* seed oils | `10.1002/fsn3.4593` | Table 1; Results 3.1 |
| *Cinnamomum camphora* stem-bark oil | `10.3390/ijms17111836` | Table 1, EB column; Results 2.1 |
| *Rheum palmatum* rhizome oil | `10.1002/(SICI)1099-1026(199601)11:1<57::AID-FFJ549>3.0.CO;2-K` | publisher abstract |

## Exclusions and unresolved cases

- `10.3389/fnut.2026.1764021` was not used because many GC-MS identities lacked retention-index confirmation or complete identifiers suitable for the current evidence schema.
- Review tables were discovery aids only; no review-derived abundance was entered.
- The public `song-incense-database` repository was excluded because it has no standard license and contains model-inferred formula records.
- 零陵香、茅香、甲香、金颜香 and several historical grades remain without modern chemical profiles because their material identity is unresolved or the studied modern specimen cannot yet be linked defensibly.
- A modern profile describes a particular specimen/preparation, not every chemotype, historical grade or combustion product of the named material.

## Verification outputs

- `data/sources/literature/crossref_europepmc_2026-09-07.json`: provider metadata and record-level comparisons;
- `reports/reference_verification_v0.1.md`: title/year audit;
- `data/curated/material_compound_evidence_v0.1.json`: statement-level analytical evidence;
- `reports/material_chemistry_audit_v0.1.json`: schema validation and corpus coverage.

