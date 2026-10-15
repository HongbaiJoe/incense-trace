# Source acquisition and transcription protocol v0.1

## Corpus goal

Build a provenance-complete benchmark of at least 80 deduplicated formula families from at least five historical work groups, with a stretch goal of 120–200 families across eight work groups. Corpus growth stops only when source-level evaluation is statistically and historically defensible, not when a calendar day ends.

## Priority sources

| Work group | Digital witness | Candidate formula-bearing sections | Role |
|---|---|---|---|
| 洪氏《香谱》 | Chinese Wikisource 2026-09-01 multistream dump, *Siku Quanshu* transcription | 香之法 / formula sections | early independent work; training or held-out source |
| 《陈氏香谱》 | Chinese Wikisource 2026-09-01 multistream dump, *Siku Quanshu* transcription | 合香方 and named formulas | largest Song-period development source |
| 《香乘》 | Chinese Wikisource 2026-09-01 multistream dump, *Siku Quanshu* transcription | vols. 14–25 used in the current high-recall pass | later compilation; genealogy-aware training source |
| 《晦斋香谱》 | *香乘* vol. 23 witness | complete embedded work | held-out work group, grouped with copied parallels |
| 《墨娥小录香谱》 | *香乘* vol. 24 witness | complete embedded work | held-out work group |
| 《猎香新谱》 | *香乘* vol. 25 witness | complete embedded work | held-out work group |
| 《遵生八笺》 | one manually scoped Chinese Text Project chapter page (`ctp:ws360607`); scan verification pending | 燕閒清賞箋中卷, paragraphs 126–156 | independent Ming work; candidate confirmation source |
| 《居家必用事类全集》 / 《事林广记》 | public-domain scans or traceable transcription | household incense sections | external confirmation candidates |

The *香乘* preface explicitly reports copying complete earlier manuals and notes overlap among earlier sources. Volume labels alone therefore do not define independent samples. The benchmark tracks both `work_id` and `witness_id`, then groups cross-work duplicates into one `formula_family_id`.

The current Wikisource acquisition is reproducible from bounded byte ranges of the official dump; each preserved page records page ID, revision ID, stable revision URL and SHA-256. The CText page is intentionally not bulk mirrored. Eleven manually delimited spans may be retained in a local, git-ignored review artifact, but neither their transcription nor derived structured records enter the public v0.1 build. A page image or independently licensed edition and a redistribution review are required before a later release can include them.

## Record schema

Each record is stored losslessly before normalization:

```json
{
  "record_id": "stable-local-id",
  "work_id": "canonical-historical-work",
  "witness_id": "specific-edition-or-digital-witness",
  "volume": "卷十四",
  "page_or_folio": "stable page, image or paragraph locator",
  "source_url": "permalink",
  "formula_title_verbatim": "",
  "formula_text_verbatim": "",
  "material_mentions": [],
  "quantity_mentions": [],
  "process_mentions": [],
  "notes_verbatim": [],
  "rights": "public-domain/CC metadata",
  "transcription_status": "ocr|checked|double_checked"
}
```

Derived tables hold mention spans, normalized units, candidate canonical identities and composition values. Verbatim text is never overwritten.

## Extraction procedure

1. Download or permalink the page image and transcription; record access date, revision identifier and content hash.
2. Segment candidate formula titles and bodies using deterministic headings, quantity expressions and material lexicons.
3. Preserve every extraction span and parser version.
4. Manually inspect all evaluation records and at least 20% of training records against the page image or a second independent witness.
5. Double-check ambiguous characters, quantities and boundaries.
6. Mark absent or qualitative quantities as missing/interval-valued; never impute a point ratio into gold data.
7. Separate aromatic materials from binders, solvents, carriers, fuels and processing aids.
8. Record alternative botanical/material identities instead of forcing a single modern label.

## Formula genealogy and deduplication

Candidate duplicates are generated from normalized titles, ingredient-set Jaccard, quantity-ratio distance, character n-gram similarity and explicit attribution phrases. A curator assigns `formula_family_id` after comparing the witnesses. All related witnesses remain in one split group. Near-identical recipes copied from an earlier manual into *香乘* cannot supply both training and test examples.

## Quality gates

- 100% of evaluated formulas have stable locators and verbatim text.
- 100% of numerical gold labels can be recomputed from recorded quantities.
- No generated or model-inferred historical wording enters the corpus.
- At least two work groups are completely unseen during each primary evaluation fold.
- At least one sealed work group remains untouched until model and thresholds freeze.
- Inter-annotator agreement is reported for spans, canonical identities and formula-family grouping on the double-checked subset.
- A digital transcription with unresolved redistribution rights may support internal verification but is not exported as benchmark text.
