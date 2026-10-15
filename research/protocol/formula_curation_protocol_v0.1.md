# Formula curation protocol v0.1

## Target object

The supervised target is the **relative dry-mass composition of aromatic materials** in one historical burned- or fumigating-incense formula. Binders, solvents, fuels, combustion aids, pigments, mould-release agents, and preparation reagents are retained in the full transcription but excluded from the aromatic target vector. Historical grades remain separate entities when the witness distinguishes them.

## Unit of analysis

One record represents one formula family, not one transcription. Parallel witnesses and near-duplicate formulae are linked before splitting. A representative transcription is selected for modelling; the remaining witnesses are reserved for genealogy checks, transcription-robustness tests, and cross-document evaluation.

## Inclusion gates

A record enters the curated exact-composition reference set only when all gates pass:

1. **Boundary:** the span contains exactly one formula. Poems, commentary, adjacent recipes, and alternative recipes are not merged.
2. **Title:** the formula title is identifiable and not an ingredient line or section heading.
3. **Materials:** every aromatic ingredient in the selected formula is mapped to an ontology entity. Unresolved historical identity may remain unresolved, but the surface mention may not be silently dropped.
4. **Quantities:** every target aromatic has a mass-convertible quantity or a clearly shared equal-parts quantity. Counts, volumes, `少許`, `不拘多少`, unspecified premixes, and optional ingredients disqualify an exact target unless the ambiguous item is outside the aromatic target.
5. **Roles:** aromatic versus binder/carrier/fuel/additive roles agree with the source context.
6. **Scope:** the text describes incense that is burned or used for fumigation. Edible fragrance, cosmetic paste, flower storage, and decorative-only preparations are excluded.
7. **Genealogy:** the provisional family assignment has been checked against linked witnesses and close title/material neighbours; only one representative may enter a split.

Passing records use the source-derived aromatic mass vector, aggregated by ontology entity and closed to sum to one. No missing aromatic is imputed in the reference labels.

## Ambiguity policy

- Alternative additions such as `別一方加…` define a separate variant; they are not silently folded into the base formula.
- Optional components such as `不用亦可` prevent a single exact label unless variants are represented separately.
- Preparation-note materials are included only when the note explicitly gives an added amount and the material remains in the finished incense. Infusion media later discarded are annotated but not included in the target.
- A source conversion note may normalize an archaic unit only when the witness itself supplies the equivalence.
- Contextually resolved `SKchar` templates retain their template ID, proposed character, evidence, and scan-check status. Unresolved templates never receive guessed characters.

## Review process

Pass A checks the source span, title, component transcription, quantity assignment, roles, and scope against the preserved witness text. Pass B reruns deterministic consistency checks, examines linked family members, and verifies that normalized proportions reproduce the adjudicated components. These are two passes by the same analyst and are **not** reported as independent double annotation. A future independent reviewer may validate a stratified subset; agreement statistics will be reported only if that review occurs.

## Status vocabulary

- `included_reference`: all seven gates pass and the exact aromatic vector is reproducible.
- `excluded_reference`: at least one gate fails; structured reason codes are required.
- `requires_correction`: the record can become eligible after a documented boundary, title, material, quantity, role, or family correction.

The automatic parser output is never called gold. The publishable artifact is a versioned **curated reference set** with source locators, decision provenance, exclusions, and family-aware split identifiers.
