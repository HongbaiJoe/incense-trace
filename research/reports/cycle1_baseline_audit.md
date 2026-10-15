# Cycle 1 baseline and reproducibility audit

Date: 2026-09-06

## Reproducibility result

The frozen Python generator reproduces `app/data/model_output.json` byte for byte. Both files have SHA-256 `c2ed4b14e6d2b1fa6f9597b65dd2d2b2340dafcdb317a2c2cb0086ee137989b9`. This establishes an exact starting point for all later comparisons.

## Dataset state

The development corpus contains 44 formulas, 25 catalogued materials, 20 observed materials, 12 curated odor dimensions and five semantic style families. Ingredient counts range from two to eight. Seven records carry a legacy `validation=true` flag.

None of the 44 records contains a document ID or page/folio locator. Consequently, a defensible cross-document experiment is not yet possible. The Cycle 1 family holdout tests extrapolation across semantic style labels only.

## Frozen hash split

| Model | Top-1 | Recall@6 | Weighted Jaccard | Ratio MAE | Micro-F1 | Macro-F1 | Macro AP |
|---|---:|---:|---:|---:|---:|---:|---:|
| Frequency | .545 | .594 | .283 | .155 | .453 | .112 | .303 |
| BM25 character retrieval | .636 | .602 | .292 | .155 | .453 | .193 | .542 |
| Odor kNN | .545 | .718 | .320 | .152 | .547 | .217 | .514 |
| Ridge composition | .545 | .844 | .357 | .150 | .623 | .229 | .585 |
| Chemistry-only NNLS | .091 | .392 | .098 | .228 | .309 | .174 | .556 |
| Frozen Xiangji v2.4 | .636 | .768 | .298 | .165 | .566 | .190 | .547 |

Ridge exceeds v2.4 on weighted Jaccard, ratio MAE, recall@6, micro-F1, macro-F1 and macro AP; v2.4 retains the higher top-1 score. The existing method therefore cannot serve as the paper's claimed algorithmic contribution.

## Leave-one-style-family-out

| Model | Top-1 | Recall@6 | Weighted Jaccard | Ratio MAE | Micro-F1 | Macro-F1 | Macro AP |
|---|---:|---:|---:|---:|---:|---:|---:|
| Frequency | .500 | .524 | .244 | .156 | .431 | .117 | .193 |
| BM25 character retrieval | .318 | .628 | **.296** | **.150** | .519 | .218 | .331 |
| Odor kNN | .341 | **.655** | .291 | .155 | **.545** | .201 | .313 |
| Ridge composition | .250 | .552 | .249 | .158 | .462 | .186 | .307 |
| Chemistry-only NNLS | .091 | .385 | .138 | .198 | .315 | **.220** | **.402** |

No baseline dominates every outcome. Text retrieval gives the best composition match; odor kNN gives the best set recall and micro-F1. Chemistry-only NNLS is a poor direct decoder but retains material-ranking signal, supporting its use as a regularizer or encoder rather than as the main inverse solver.

## Cycle 1 decisions

1. Replace the current hash split as the scientific evaluation protocol; retain it only for exact reproduction.
2. Make source acquisition and formula-family deduplication the immediate bottleneck.
3. Require the new model to beat BM25, odor kNN and Ridge under document-held-out evaluation, not merely the weak frequency prior.
4. Treat material-set recovery and composition recovery as linked but distinct tasks.
5. Model chemical information as a forward-consistency constraint with a learned residual, because a linear odor mixture alone is empirically insufficient.
6. Freeze the 30 target reconstructions until the final model and thresholds are locked.
