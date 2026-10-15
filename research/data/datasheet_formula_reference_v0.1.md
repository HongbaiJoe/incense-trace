# Datasheet: Xiangji Formula Reference v0.1

## Motivation and intended use

This dataset supports research on structured extraction and source-shifted inverse reconstruction of historical Chinese incense formulas. Its supervised target is the relative dry mass of aromatic materials in a source-attested burned or fumigating formula. It is suitable for family- and source-blocked computational experiments. It is not evidence that a predicted formula is the unique historical original, nor a safety guide for combustion or human exposure.

## Composition

The release contains 91 records from six work groups. Each record includes a stable source locator, verbatim Wikisource span, source-text hash, normalized material mentions, raw quantities, material roles, a family identifier, the aromatic mass vector, its closed composition and curation metadata. Twenty-nine reviewed exclusions remain in `reports/formula_reference_audit_v0.1.json`.

Work distribution:

| Work group | Records |
|---|---:|
| Chen shi Xiangpu compilation | 38 |
| Hong shi Xiangpu attributed | 6 |
| Huizhai Xiangpu embedded in Xiangcheng | 10 |
| Liexiang Xinpu embedded in Xiangcheng | 6 |
| Moe Xiaolu Xiangpu embedded in Xiangcheng | 2 |
| Xiangcheng compilation, embedded source unresolved | 29 |

## Collection and provenance

Wikisource pages were reconstructed from bounded byte ranges of the official 2026-09-01 Chinese Wikisource multistream dump. Page ID, revision ID, stable revision URL and SHA-256 are recorded in source manifests. Historical texts are public domain; Wikisource transcription reuse is attributed under CC BY-SA 4.0. CText candidates were reviewed internally but are absent from the public structured build and release.

## Curation

The 120-record batch was selected after deterministic high-recall extraction, mass-basis parsing and provisional genealogy clustering. Inclusion required seven checks: formula boundary, title, material coverage, quantity completeness, role assignment, burned/fumigating scope and family assignment. No missing aromatic amount was imputed. The review was performed in two passes by one analyst and checked by executable invariants; it is not independent double annotation.

## Known limitations

- Several historical material identities remain at family, grade or unresolved-entity level.
- Work labels embedded in compilations are provisional where the source boundary cannot yet be established.
- The corpus is small and unbalanced; the Moe Xiaolu group has only two eligible records.
- A stable textual recipe does not prove actual historical preparation, sensory outcome or complete transmission history.
- Independent scan verification and second-reviewer agreement are future release upgrades.

## Splits

`source_blocked_splits_v0.1.json` supplies five development leave-one-work-out folds, ten primary two-unseen-work folds and one sealed Hong-source set. Record-level random splits are intentionally absent. Formula families are disjoint by construction.

## Maintenance and versioning

Version 0.1 is frozen by batch, manifest, reference and code hashes. Corrections require a new manifest entry, a regenerated audit and a version increment. Excluded spans are retained so later textual or identity corrections remain traceable.
