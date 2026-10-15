# Cycle 5 completion report

## Manuscript outcome

Cycle 5 converts the frozen model and evaluation into a complete first manuscript for *npj Heritage Science*. The article title contains 11 words and the unstructured abstract contains 144 words, within the journal limits. The manuscript follows the required Article order and includes Data availability, Code availability, Author contributions and Competing interests sections.

The paper makes one primary claim: a directed conditional co-formulation graph transfers missing-ingredient information across historical work groups. The source-macro hidden-component F1 is 0.3787 for graph-only and 0.3379 for global frequency. The full decoder reaches 0.3768 and does not improve on the graph. The chemistry experiments remain in the paper as a designed negative result: pairwise molecular similarity models substitution, whereas historical co-formulation depends on complementarity.

The Discussion contains one concentrated limitations paragraph. The rest of the article states results directly and separates observed evidence from proposed follow-up work.

## Evidence and bibliography

Thirty-five references are cited and all 35 appear in the reference list. Seventeen analytical publications supporting the material-chemistry layer are now cited as references 19–35. The automated audit rejects missing citations, uncited references, non-sequential numbering, duplicate BibTeX keys and unresolved bibliography fields.

The enriched bibliography changed `literature/references.bib` without altering curated formulas, molecular representations, splits, model parameters or experiment outputs. The Cycle 2 release manifest was regenerated so its byte counts and SHA-256 hash for the bibliography remain truthful. This is a metadata-only post-freeze change.

## Figures and tables

Five main figures and seven source tables are generated directly from frozen JSON results. Each figure is exported as editable PDF and 450 dpi PNG. The graphics use a color-vision-safe palette, redundant marker or line encodings where categories are compared, embedded TrueType fonts and panel labels compatible with the target journal.

The figure manifest records the generator, input files and SHA-256 hash of every output. Visual inspection confirmed that labels, legends and annotations remain inside their panels at submission resolution.

## Computational profile

On an Apple arm64 laptop, the locked decoder fit 85 formulas and 80 materials in a median 0.1145 s across 11 serial repetitions. One prediction with 200 posterior samples required a median 1.702 ms. These measurements exclude data loading and are stored with environment metadata and raw repetition times.

## Consistency audit

The manuscript registry binds 13 evidence artifacts to their hashes and tracks nine central claims to the exact paragraphs that express them. Twenty-six numerical facts are checked against their rendered manuscript values. The current audit reports:

- title words: 11
- abstract words: 144
- cited references: 35 of 35
- missing required sections: 0
- missing numerical anchors: 0
- CJK characters in the English manuscript: 0
- unresolved human-supplied fields: 4

The four remaining fields are author name, affiliation and email, acknowledgements or funding, author contributions and competing interests. They require verified author information and are intentionally excluded from automated completion.

## Verification

The complete test suite passes 99 tests. It covers data parsing and curation, source and family blocking, feature leakage, posterior inference, model selection, primary evaluation, robustness, confirmation, manuscript assets, bibliography integrity, claim-number consistency and release-hash verification.

## Decision

Cycle 5 is complete. The scientific result, article structure, bibliography, figures and supplementary information are frozen for external-style review. Cycle 6 will test reproducibility from a clean environment, simulate peer review, correct only verified defects and build the submission package.
