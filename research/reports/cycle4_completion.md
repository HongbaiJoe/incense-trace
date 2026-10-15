# Cycle 4 completion report

## Primary result

The frozen model completed all ten two-work-held-out folds at five mask seeds. It reached source-pair macro hidden-component F1 0.3768, weighted Jaccard 0.3898 and vocabulary coverage 0.8781 at 50% observed context.

The directed graph produced almost all of the predictive gain. Graph-only reached hidden F1 0.3787, while frequency reached 0.3379. At the work-group level, the full model exceeded frequency by 0.0278 hidden F1. Four of five work groups improved. The descriptive t interval was [-0.0046, 0.0602], the source bootstrap interval was [0.0079, 0.0473], and the exact two-sided sign-flip p-value was 0.125.

The full model matched graph-only. Their work-group difference was 0.0010, with a descriptive t interval of [-0.0126, 0.0147] and exact p = 0.875. This result rejects the planned claim that title and source features add reliable value beyond the conditional graph. The paper will identify the graph as the effective component.

## Source results

| Held-out work | Hidden F1 | Weighted Jaccard |
|---|---:|---:|
| Chen xiangpu compilation | 0.3959 | 0.3821 |
| Huizhai xiangpu | 0.2098 | 0.3241 |
| Liexiang xinpu | 0.4430 | 0.3773 |
| Xiaolu xiangpu | 0.3917 | 0.4458 |
| Xiangcheng unresolved compilation | 0.3919 | 0.4064 |

The Huizhai source transferred poorly. The source range is wide enough to make a single pooled score misleading, so the manuscript will report the table with the macro estimate.

## Context sensitivity

| Observed formula fraction | Frequency hidden F1 | Graph hidden F1 | Full hidden F1 |
|---:|---:|---:|---:|
| 0.25 | 0.3882 | 0.4078 | 0.3995 |
| 0.50 | 0.3379 | 0.3787 | 0.3768 |
| 0.75 | 0.2373 | 0.2621 | 0.2626 |

Hidden-component F1 falls at 75% context because only a small, difficult residual set remains. At 25% context, graph-only beat the full model in all five works by a mean 0.0076. The exact sign-flip test reached its five-block minimum of 0.0625. Extra title and source features hurt when context is sparse.

## Calibration and cardinality

The selected model retained probability calibration under the primary shift: hidden-candidate Brier score was 0.0429 and ECE was 0.0236. Ingredient count remained biased downward. The mean signed error was -0.883 ingredients, count MAE was 1.190, and the nominal 80% count interval covered 64.2%. The ratio interval stayed conservative, with 91.2% coverage conditional on selecting the true component.

## Error structure

Training frequency set the practical recovery limit:

| Training frequency | Hidden recall |
|---|---:|
| 5 or more | 0.5730 |
| 2 to 4 | 0.0559 |
| 1 | 0.0234 |
| 0, out of vocabulary | 0.0000 |

The model overpredicted sandalwood, borneol, musk, agarwood and clove. The most frequent misses included scrophularia root, spikenard, zhan-grade agarwood, frankincense and clove. Mean prediction-set Jaccard across mask seeds was 0.6442.

Materials with external chemical profiles had hidden recall 0.4826; materials without profiles had recall 0.0921. Training frequency confounds that comparison, so it does not establish a chemical effect. The locked T1 model did not use chemical similarity.

## Hong-source confirmation

The final six Hong formulas remained outside every model statistic until this confirmation run. Researchers had processed the formulas during curation, so the test was model-quarantined rather than investigator-blinded.

The locked model reached hidden F1 0.5767, graph-only 0.5583 and frequency 0.4689. Weighted Jaccard values were 0.4676, 0.4560 and 0.4195. Vocabulary coverage reached 0.9833. The formulas belong to one work group, so this result measures transfer to one source and does not add an independent source-level significance test.

## Decision

Cycle 4 supports three claims:

1. A directed conditional material graph improves cross-work formula completion over global frequency.
2. Title, source-prior and pairwise chemical-similarity channels do not improve the graph consistently.
3. The model produces calibrated inclusion probabilities but underestimates ingredient count and rarely recovers low-frequency materials.

The model remains frozen. Cycle 5 will write the paper around these results and will not search for a more favorable metric or subset.
