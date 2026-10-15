# Model card: Xiangji baseline suite v0

## Purpose

This suite measures how much predictive signal is available from ingredient frequency, historical wording, curated odor targets and the material odor matrix before training Xiangji-CGIR. It is a scientific control, not a deployment model.

## Inputs and outputs

Input records contain a formula title, short description, semantic family and a curated 12-dimensional odor target. Output is a 25-material score vector, normalized and truncated to six predicted materials for set/composition metrics.

## Components

- Frequency prior: training-set average composition.
- BM25 character retrieval: Chinese character unigram/bigram retrieval, followed by weighted neighbor composition.
- Odor kNN: distance-weighted regression from the 12-dimensional target.
- Ridge: regularized multi-output composition regression.
- Chemistry NNLS: nonnegative inversion of the fixed material-by-odor matrix.
- Xiangji v2.4: frozen website generator, evaluated only on its original hash split.

## Evaluation

The original hash split reproduces v2.4 but has no historical-source interpretation. Leave-one-style-family-out supplies a harder development stress test. Neither is a valid cross-document test because source metadata are absent.

## Limitations

- only 44 formulas and 20 observed materials;
- descriptor targets were curated, not measured;
- five style families are imbalanced and are not textual-source groups;
- historical synonyms and uncertain botanical identities are collapsed;
- linear odor vectors do not represent combustion or nonlinear perceptual interactions;
- no calibrated uncertainty or external validation.

## Intended use

Use these models to set minimum performance requirements, diagnose leakage and test whether proposed components add information. Do not use them to claim a historically authentic or chemically unique reconstruction.
