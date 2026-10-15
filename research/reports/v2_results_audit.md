# V2 results audit

Date: 2026-09-09

## Primary nested cross-work evaluation

The revised evaluation uses six outer leave-one-work-out folds. Hyperparameters are selected by inner leave-one-work-out validation within each outer training set. Each work is therefore absent from its model, vocabulary, edge estimates, and model selection scores.

| Model | Hidden precision | Hidden recall | Hidden F1 | Weighted Jaccard | Count MAE |
|---|---:|---:|---:|---:|---:|
| Frequency | 0.4323 | 0.3633 | 0.3782 | 0.4514 | 1.145 |
| Directed conditional graph | 0.4808 | 0.4134 | 0.4260 | 0.4699 | 1.145 |
| SSCL | 0.4802 | 0.4138 | 0.4263 | 0.4716 | 1.145 |
| EASE | 0.4793 | 0.4082 | 0.4229 | 0.4730 | 1.145 |
| SLIM-style elastic net | 0.4402 | 0.3713 | 0.3874 | 0.4545 | 1.145 |
| Personalized graph diffusion | 0.4672 | 0.3968 | 0.4119 | 0.4594 | 1.145 |

SSCL increased source-macro hidden F1 by 0.0481 over frequency. Five works improved and one tied. The exact two-sided six-block sign-flip p-value was 0.0625. The directed conditional graph produced F1 0.4260. SSCL exceeded it by 0.0003, with an exact paired p-value of 1.0. EASE achieved the highest weighted Jaccard, 0.4730, which was 0.0014 above SSCL.

## Interpretation locked for V2 writing

The cross-source signal is real enough to produce an absolute F1 gain near 0.05 over frequency under nested work-level evaluation. The source-stability penalty does not add a measurable gain over the direct conditional graph in the primary task. V2 will therefore claim a benchmark and evaluation contribution. SSCL remains a tested source-aware extension and is reported without calling its 0.0003 difference an advance.

The stricter two-work-held-out test retains the previous ranking scale: direct graph F1 0.3672, SSCL 0.3650, EASE 0.3625, and frequency 0.3386. This test is reported as a harder source-shift condition. It is not pooled with the six-work nested estimate.

## Observation-mechanism stress tests

At 50% observed context, the selected graph and SSCL methods remained above frequency under uniform, abundance-biased, prefix, and unknown-fraction conditions. The strongest method varied by mechanism. Directed graph led abundance-biased retention at F1 0.4295. EASE led prefix retention at 0.4812. SSCL led the unknown-fraction test at 0.4038.

At 75% observed context, hidden F1 did not increase monotonically because the hidden reference set became smaller and contained a different mix of materials. Frequency reached 0.3550 under abundance-biased retention and exceeded the structured models. Under prefix retention, SSCL reached 0.4619 versus 0.3951 for frequency. Under uniform unknown-fraction decoding, EASE reached 0.3107, SSCL 0.3055, directed graph 0.2923, and frequency 0.2567.

These results reject a single universal winner. They also show why fixed uniform masking was too narrow: model ordering changes when the missingness mechanism changes.

## Probability calibration

Nested logit calibration fitted one slope and intercept inside each outer fold. It reduced source-macro Brier score from 0.0427 to 0.0340, negative log likelihood from 0.1572 to 0.1262, and adaptive calibration error from 0.0579 to 0.0145.

The uncalibrated model issued 186 predictions above 0.8. Their mean probability was 0.839 and their empirical inclusion frequency was 0.608. Logit calibration left only two predictions above 0.8. This is the correct operational response to unsupported high confidence. The data do not support a precise claim about calibration within the remaining high-probability region.

## Chemistry and annotation

V2 retains the existing 18-material chemistry ablation as a bounded result: the tested pairwise kernel did not improve formula completion at its present coverage. No broader conclusion about molecular similarity follows. The paper also states that the single-curator corpus lacks an inter-annotator reliability estimate. Neither limitation is rewritten as a positive finding.

## Acceptance-gate decision

The original headline gate is only partly met. SSCL beats frequency across five works with one tie and stays within 0.01 weighted Jaccard of EASE. It does not produce a meaningful gain over the direct graph. V2 is therefore a source-shift benchmark paper with a source-stability extension, not a claim of a superior new learning architecture.

