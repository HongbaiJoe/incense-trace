# Xiangji V2.5 completion record

Date: 2026-09-09

## Delivered manuscript

- LaTeX source: `research/submission/latex/xiangji_source_stable_v2_5.tex`
- Compiled PDF: `research/submission/latex/xiangji_source_stable_v2_5.pdf`
- Length and structure: 24 A4 pages, 29 equation or align environments, 13 tables, 7 figures, and 34 unique citation keys.

## Data and model upgrade

- 592 source-linked discovery candidates.
- 296 ratio-ready candidate formulas.
- 91 reviewed gold formulas retained for evaluation.
- 146 genealogy-filtered weak records from 100 new families.
- 237 model-facing records across 191 families.
- Family-normalized weak supervision with nested selection of the reliability weight and collection-blocked outer testing.

Gold-plus-weak SSCL obtains hidden F1 0.4254, weighted Jaccard 0.4704, and count MAE 1.0891. The corresponding gold-only values are 0.4263, 0.4716, and 1.1447. The added records improve count estimation and preserve ingredient-recovery performance.

## Verification

- Test suite: 137 passed.
- Cross-reference audit: 49 unique labels, 11 referenced labels, zero missing references, zero duplicate labels.
- Language scan: zero matches for the specified defensive and binary AI-style phrases.
- Figure preflight: 14 passes, zero warnings, zero failures; SVG/PDF vector output and 600 dpi TIFF output are present.
- Compiled PDF: 24 pages, A4, with no substantive LaTeX, bibliography, undefined-reference, overfull-box, or underfull-box warnings in the final log.
- Visual review: all 24 pages inspected for clipping, blank pages, table overflow, caption placement, and figure legibility.

## Review coverage

Every item from the two teacher reviews is mapped to a manuscript location in `research/reports/v2_5_teacher_comment_matrix.md`. The second-curator agreement study and formula-linked chemical or sensory validation remain defined next experiments because their outcomes require new human annotation or physical measurements.
