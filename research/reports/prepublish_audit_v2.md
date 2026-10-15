# Prepublication audit v2

## Content

- Core claim matches the experiment: the training-only directed co-formulation graph transfers across held-out historical works.
- Competitive comparison now includes frequency, formula k-nearest neighbours and PureSVD.
- Post-freeze analyses cover near duplicates, count calibration, mass conservation and one complete reconstruction.
- Chemistry claims remain specific to an 18-material pairwise kernel.
- The single-curator status is explicit; the corpus is called a reference set rather than a gold standard.

Result: pass.

## Structure and clarity

- Title is 11 words and contains no punctuation.
- Abstract is 139 words and unstructured.
- Introduction has no subheadings; Results and Methods use informative subheadings; Discussion has none.
- Weighted Jaccard and separate count modeling receive plain-language explanations.
- One complete case links aggregate scores to a historical formula.

Result: pass.

## Statistics and provenance

- Hyperparameters use development work splits only.
- Primary evaluation holds out every pair of five work groups and aggregates at formula, work and source-macro levels.
- Exact sign-flip inference uses five work blocks; bootstrap intervals use work groups.
- Count recalibration uses 420 development predictions and never reads primary labels.
- Thirteen manuscript claims map to 16 hashed source artifacts.

Result: pass.

## Bibliography

- All 38 numbered references are cited.
- Live Crossref, Europe PMC or primary-page verification passed 38 of 38 records.
- The audit corrected reference 7 to the title registered for DOI 10.1149/1945-7111/ac33e0.
- Two online-first versus issue-year differences preserve reference identity.

Result: pass.

## Reproduction and files

- The local suite passes 112 tests.
- A fresh locked environment passes the same 112 tests.
- Fourteen regenerated outputs match byte for byte, including the editable Figure 6 SVG.
- Main DOCX/PDF render to 18 pages; supplementary DOCX/PDF render to 15 pages.
- The LaTeX manuscript and supplement compile without errors to 17 pages each using Tectonic 0.17.0.
- Main figures follow the Nature artwork specifications: 180 mm-class layouts, standard sans-serif text, Type 42 PDF fonts, editable SVG text, RGB colour and redundant marker or line encodings.
- Supplementary tables use three-rule formatting without vertical rules in Word and LaTeX.
- Every Word-rendered and LaTeX-rendered page was visually inspected. Page numbering, tables, equations, figures and portable source labels are intact.

Result: pass.

## Submission gate

The scientific and technical package is ready for author completion. Six human-supplied fields remain: author name, affiliation, corresponding email, funding or acknowledgements, CRediT contributions and competing interests. The manuscript highlights these fields in the DOCX. They must be completed before upload.
