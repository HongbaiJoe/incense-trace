# Cycle 3 completion report

## Outcome

Cycle 3 converts the Cycle 2 corpus into a leakage-controlled, uncertainty-producing research model and locks its primary configuration before cross-source evaluation. The development gate passes numerically, but the improvement over the strongest graph baseline is small and statistically unresolved. Chemistry does not yet provide measurable predictive value; that negative result is retained.

## Task definition

The 91 reference formulas list their ingredients but do not contain independent odor observations. Supplying the formula text as input would therefore reveal the target. The primary task (T1) instead uses title, work context and a deterministic masked subset of materials to predict the complete aromatic set and proportions. The six Hong-source records are removed before vocabulary or statistic construction. Researchers handled them during corpus construction, so they are model-quarantined rather than investigator-blinded. The 30 lost-incense targets remain application-only.

The auxiliary task (T2) uses the 44 legacy recipes with 12-dimensional curated odor profiles. It is evaluated by nested leave-one-family-out validation and is not used for the primary historical-source claim.

## Model changes completed

1. Removed training-record self-influence from title centroids, global prevalence, source prevalence and hypergraph construction.
2. Replaced symmetric co-occurrence with a directed, smoothed posterior-predictive conditional graph.
3. Conditioned ingredient count on the exact deterministic masking rule and used the posterior median for absolute count loss.
4. Replaced point-estimate logistic regression with a Gaussian-prior generalized Bayesian decoder and Laplace posterior.
5. Corrected class-balanced probabilities with the case-control prior odds.
6. Added inclusion intervals, categorical count uncertainty, Dirichlet ratio intervals and posterior samples.
7. Added T2 nested validation, chemical ablation and shuffled-chemical semantic control.
8. Added synthetic composition recovery and an independent Laplace-versus-MH check.

## Development selection

The full grid contains five seeds, five values of C, ERM versus eight-step Group DRO, and three graph reducers. Selection maximizes source-macro hidden-component F1, then weighted Jaccard, then minimizes Aitchison distance.

The locked model is `full_no_chemistry`, C = 3.0, ERM, mean graph reducer. Across seeds it achieves hidden F1 0.3911 ± 0.0081 and weighted Jaccard 0.3982 ± 0.0354. The strongest baseline is graph-only, C = 0.1, Group DRO, mean reducer, with hidden F1 0.3876 ± 0.0116. Paired seed differences average 0.0035; the descriptive 95% t interval is [-0.0040, 0.0110]. Cycle 4 must therefore treat superiority as unconfirmed.

The best chemistry-enabled T1 variant reaches hidden F1 0.3905, slightly below the locked non-chemistry variant. Chemical similarity is not used as a co-occurrence reward in the primary lock.

## Calibration and inference checks

- Hidden-candidate ECE: 0.0208 after prior-odds correction.
- Inclusion Brier score: 0.0352.
- Record-pooled count MAE: 0.988; mean bias: -0.631 ingredients.
- Central 80% count interval coverage: 72.6%.
- Conditional 80% ratio interval coverage: 91.6%; conservative.
- True-component selection rate: 66.7%.
- Laplace versus 20,000-draw MH predictive MAE: 0.0016.
- Synthetic hidden-component F1: 0.900 structured versus 0.497 frequency.
- Synthetic weighted Jaccard: 0.658 structured versus 0.445 frequency.

## Auxiliary odor inverse result

The repaired ID bridge recovers legacy odor vectors for 25/25 materials and external chemical odor views for 14/25. Nested family-blocked pooled weighted Jaccard is 0.2913 for odor kNN, 0.2824 for the proposed forward-consistent model, 0.2835 without chemistry and 0.2863 under shuffled chemistry. Chemical semantics do not beat the negative control, so no chemistry-accuracy claim advances from T2.

## Locked boundary for Cycle 4

Cycle 4 may evaluate the frozen two-work-held-out primary folds using `xiangji_cgir_v1_locked.json`. It may not change channels, C, training objective, graph reducer, count decision or masking mechanism after seeing those results. The Hong source remains quarantined from model statistics and evaluation. Any later change creates a new model version and requires a new untouched evaluation source.

## Primary artifacts

- `configs/model/xiangji_cgir_v1_locked.json`
- `experiments/cycle3_model_selection.json`
- `experiments/cycle3_development_diagnostics.json`
- `experiments/cycle3_odor_inverse_nested.json`
- `experiments/cycle3_inference_diagnostics.json`
- `protocol/cycle3_model_protocol_v0.1.md`
- `reports/model_card_xiangji_cgir_v1.md`
