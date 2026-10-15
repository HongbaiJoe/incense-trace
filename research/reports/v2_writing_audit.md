# V2 writing and presentation audit

Date: 2026-09-09

## Argument

- The manuscript asks one question: which ingredient relations transfer to a historical work excluded from training?
- The primary claim is the directed conditional graph gain over global frequency.
- SSCL is reported as a tested source-aware extension. Its 0.0003 F1 difference from the direct graph is stated directly and is not presented as a performance advance.
- Missingness shift and nested calibration support the central source-transfer argument.
- Chemistry is confined to the 18-material ablation supported by the registry.

## Prose

- Abstract, Introduction, Results, Discussion, and Limitations were rewritten from the V1 draft.
- Binary AI constructions, self-congratulatory claims, repeated process labels, and unnecessary boundary reminders were removed.
- Limitations appear once in a dedicated section.
- Claims begin with the result or mechanism and are followed by the relevant number or design fact.

## Mathematical presentation

- The manuscript contains 22 numbered equation or aligned-equation environments.
- Model construction, posterior means, source pooling, baseline objectives, count prediction, mass closure, calibration, metrics, and exact inference are defined in the main text.
- Every notation-table entry in the first column is enclosed in explicit dollar-sign math mode.

## Tables and figures

- Seven three-rule tables appear in the main text.
- Four figures are generated directly from recorded experiment JSON.
- Each quantitative figure has CSV source data and PDF, SVG, TIFF, and PNG exports.
- The plotting source passes the Nature figure static preflight with 14 passes, no warnings, and no failures.

## Compilation

- Tectonic produces a 14-page A4 PDF.
- The final log contains no undefined citations, undefined references, overfull boxes, underfull boxes, or missing characters.
