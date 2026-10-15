# V2.5 data expansion result

## Decision

The 91-formula corpus can be increased immediately without weakening the gold evaluation set.

- 592 source-linked formula candidates are available.
- 296 contain a complete automatic aromatic-mass parse.
- 91 are reviewed gold formulas.
- 205 ratio-ready records remain outside the gold set.
- Genealogy filtering removes 59 records connected to gold families.
- 146 weak records in 100 new families remain eligible.
- The resulting model-facing union contains 237 records in 191 families.

## Training rule

Gold records receive weight 1. Weak record weight is the selected reliability value divided by the number of weak witnesses in its provisional family. The reliability grid is 0, 0.10, 0.25, 0.50, and 1.00. Every outer and inner fold removes weak records from the target transcription collection. The outer test set contains reviewed records only.

## Measured result

Gold-only SSCL reaches hidden F1 0.4263, weighted Jaccard 0.4716, and count MAE 1.1447. Gold-plus-weak SSCL reaches hidden F1 0.4254, weighted Jaccard 0.4704, and count MAE 1.0891. The paired work-level F1 change is -0.0009 with exact two-sided sign-flip p = 1.0. Weak evidence improves the formula-size prior and preserves ingredient ranking at the same aggregate level.

## Next expansion

Review the 146 weak records in this order:

1. families that introduce an out-of-vocabulary material into at least two collections;
2. families that create a second observation for a singleton material;
3. families with high source novelty and low parsing ambiguity;
4. families that reduce the variance of a high-use graph edge.

Completing this queue moves the reviewed corpus toward 237 formulas. Three additional public-domain collections at 80 to 120 accepted families each produce a 450 to 600 formula, ten-work benchmark.
