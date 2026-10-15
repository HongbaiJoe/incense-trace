# Mathematical completeness audit

Status: **PASS**

- Main-text numbered equations: 29
- Main-text figures: 6
- Main-text tables: 8
- Word equations: native OMML with all equation numbers present
- LaTeX equations: numbered environments with matching labels
- Styling checks: Times New Roman declared; no blue title styling or highlights

## Equation-to-code traceability

| Eq. | Manuscript label | Implementation file | Symbol or function | Audit |
|---:|---|---|---|---|
| 1 | `composition-closure` | `src/xiangji/normalization/build_curated_reference.py` | `close_composition` | verified |
| 2 | `mask-cardinality` | `src/xiangji/models/data.py` | `deterministic_observation_mask` | verified |
| 3 | `prevalence-priors` | `src/xiangji/models/cgir.py` | `XiangjiCGIR._fit_priors` | verified |
| 4 | `directed-graph` | `src/xiangji/representations/kernels.py` | `hypergraph_kernel` | verified |
| 5 | `graph-affinity` | `src/xiangji/representations/kernels.py` | `affinity_from_observed` | verified |
| 6 | `title-affinity` | `src/xiangji/models/cgir.py` | `TitleMaterialEncoder` | verified |
| 7 | `candidate-features` | `src/xiangji/models/cgir.py` | `XiangjiCGIR._feature_matrix` | verified |
| 8 | `logistic-model` | `src/xiangji/models/bayesian_logistic.py` | `LaplaceLogisticRegression` | verified |
| 9 | `map-objective` | `src/xiangji/models/bayesian_logistic.py` | `LaplaceLogisticRegression.fit` | verified |
| 10 | `laplace-posterior` | `src/xiangji/models/bayesian_logistic.py` | `LaplaceLogisticRegression.fit` | verified |
| 11 | `predictive-probability` | `src/xiangji/models/bayesian_logistic.py` | `LaplaceLogisticRegression.predict_proba` | verified |
| 12 | `count-priors` | `src/xiangji/models/cgir.py` | `XiangjiCGIR._fit_priors` | verified |
| 13 | `count-posterior` | `src/xiangji/models/cgir.py` | `XiangjiCGIR.count_posterior` | verified |
| 14 | `count-decision` | `src/xiangji/models/cgir.py` | `XiangjiCGIR.predict` | verified |
| 15 | `ratio-ridge` | `src/xiangji/models/cgir.py` | `XiangjiCGIR.fit` | verified |
| 16 | `ratio-closure` | `src/xiangji/models/cgir.py` | `XiangjiCGIR.predict` | verified |
| 17 | `dirichlet-composition` | `src/xiangji/models/cgir.py` | `XiangjiCGIR.predict` | verified |
| 18 | `mass-constraint` | `src/xiangji/evaluation/cycle6_stress_tests.py` | `mass_constrained_composition` | verified |
| 19 | `profile-similarities` | `src/xiangji/representations/kernels.py` | `build_chemical_kernel` | verified |
| 20 | `chemical-kernel` | `src/xiangji/representations/kernels.py` | `build_chemical_kernel` | verified |
| 21 | `knn-similarity` | `src/xiangji/evaluation/cycle6_stress_tests.py` | `CompletionBaseline._scores` | verified |
| 22 | `svd-baseline` | `src/xiangji/evaluation/cycle6_stress_tests.py` | `CompletionBaseline.fit` | verified |
| 23 | `set-metrics` | `src/xiangji/evaluation/partial_completion.py` | `f1_sets` | verified |
| 24 | `composition-metrics` | `src/xiangji/evaluation/partial_completion.py` | `composition_metrics` | verified |
| 25 | `aitchison-distance` | `src/xiangji/evaluation/partial_completion.py` | `composition_metrics` | verified |
| 26 | `calibration-metrics` | `src/xiangji/evaluation/primary.py` | `selected_calibration` | verified |
| 27 | `source-macro` | `src/xiangji/evaluation/primary.py` | `source_level_metrics` | verified |
| 28 | `sign-flip-test` | `src/xiangji/evaluation/primary.py` | `exact_sign_flip_pvalue` | verified |
| 29 | `count-conformal` | `src/xiangji/evaluation/cycle6_stress_tests.py` | `recalibrated_count_intervals` | verified |

## Scope of this audit

The check establishes structural parity and an implementation locus for every equation. Numerical correctness remains covered by the unit and release test suites; empirical claims remain covered by the manuscript evidence audit.
