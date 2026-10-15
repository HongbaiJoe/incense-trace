# External dataset audit: `song-incense-database`

Audit date: 2026-09-06  
Repository snapshot: commit `a0b99f1`  
Claimed scale: 378 formulas from eight texts

## Decision

**Excluded from model training, validation and external testing.** It may be used only as a title/source lead list whose entries must be independently located in a primary edition.

## Evidence

1. The repository has no standard license file or SPDX license. Its README says that curated data and translations are available for scholarly and educational use, but does not define redistribution, modification or model-training permissions.
2. The extraction scripts explicitly query `deepseek-v4-flash` “from model knowledge” rather than parsing supplied primary-text pages.
3. The extraction prompt states that, if original wording is unavailable, the model may infer a plausible conventional Song-period formula and mark it as inferred.
4. The repository's own validation report flags 141 of 279 inspected records. Numerous records are explicitly marked “model-inferred,” “requires checking against the original,” or “possibly incomplete.”
5. The source-structure files state that they reconstruct book structures from model memory and warn that the results may be incomplete or uncertain.
6. The public discussion identifies mistranslations, conflation of traditional medical “flavor” labels with odor, and procedures that require source-level checking.

## Scientific implication

Using these JSON records as gold data would train and test on generated claims rather than historical formulas. It would also create circular evaluation if a language model later appeared anywhere in the proposed pipeline. The only admissible use is candidate discovery followed by exact transcription from a public-domain scan or traceable scholarly edition.

## Verification rule for any recovered lead

A lead enters the corpus only when a curator records a stable page/folio locator, verbatim source text, edition metadata, extraction span, normalized quantities, unresolved readings and a second-pass check. If a formula appears in multiple works, those witnesses share a formula-family identifier and cannot be split across train and test.
