# Model card: Xiangji-CGIR v1

## Intended use

Xiangji-CGIR v1 ranks missing aromatic materials and estimates relative aromatic proportions for a partially observed historical incense formula. It is a research model for source-shifted reconstruction, not a chemical assay, a historical attribution engine, or a safety assessment.

## Primary input and output

Input comprises a formula title, an optional work identifier, and a subset of known aromatic materials with positive relative weights. Output comprises a posterior-predictive inclusion probability and 80% interval for every in-vocabulary material, a categorical posterior over total ingredient count, a selected material set, and a Dirichlet posterior over selected proportions.

## Training evidence

- 85 development formulas after quarantining the six Hong-source records from the 91-record reference. The quarantine is model-facing; researchers handled these records during corpus construction, so this is not an investigator-blinded holdout.
- 80 development materials, with 29 appearing only once.
- Five work groups in leave-one-work-out development folds.
- External material profiles are source-backed and frozen, but only a minority of historical materials have usable chemical profiles.

## Locked primary configuration

- Gaussian-prior generalized Bayesian logistic inclusion decoder; 10 global feature coefficients.
- Laplace coefficient posterior with case-control prior-odds calibration.
- Directed posterior-predictive material hypergraph; mean aggregation across observed materials.
- C = 3.0; ERM; three training masks per formula at 0.25, 0.50 and 0.75.
- Source-smoothed categorical count posterior and posterior-median decision.
- Ridge log-ratio mean and Dirichlet compositional posterior.
- Pairwise chemistry channel disabled for T1 by development selection.

## Development behavior

Across five registered mask seeds, source-macro hidden-component F1 is 0.3911 (SD 0.0081), weighted Jaccard 0.3982 (SD 0.0354), and vocabulary coverage 0.8780. The strongest graph baseline reaches hidden F1 0.3876; the paired mean difference is 0.0035 with a descriptive 95% t interval of -0.0040 to 0.0110. The gain is therefore weak and requires primary cross-source confirmation.

After case-control correction, hidden-candidate ECE is 0.0208 and vocabulary-level Brier score is 0.0352. Record-pooled count MAE is 0.988, mean signed error -0.631, and the central 80% count interval covers 72.6%. Conditional on selecting a true component, the nominal 80% ratio interval covers 91.6%, indicating conservative ratio uncertainty; only 66.7% of true components are selected.

## Auxiliary odor task

The 44-recipe legacy corpus supplies curated odor targets but inadequate document provenance. Under nested leave-one-family-out evaluation, odor kNN reaches weighted Jaccard 0.2913, compared with 0.2824 for the forward-consistent model, 0.2835 without chemical blending, and 0.2863 after shuffling chemical profiles. These results do not support a chemical-performance claim.

## Diagnostic evidence

On a reduced synthetic logistic problem, Laplace and Metropolis-Hastings posterior predictions differ by MAE 0.0016. On a synthetic formula-shift problem, the structured model reaches hidden F1 0.900 versus 0.497 for the frequency completion baseline. Synthetic success establishes implementation recovery under known structure; it does not estimate historical-domain performance.

## Known limitations

The corpus is small, sparse and source-imbalanced. Titles carry little independent signal. Historical ingredient aliases and preparation processes remain incompletely resolved. Relative proportions describe aromatic-only mass closure, not combustion-headspace abundance or perceptual mixture intensity. Unseen materials cannot be recovered as named labels. The residual-scaled Dirichlet ratio distribution is conservative and conditional on the selected set; the uncalibrated count posterior undercovers at its nominal level.
