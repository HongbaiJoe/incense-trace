# Xiangji-CGIR study protocol v0.1

Status: Cycle 1 protocol; frozen before development of the proposed model.

## Research question

Can a source-aware probabilistic model recover the ingredient set and relative composition of a historical Chinese incense formula from sparse historical language, while using molecular/odor information to constrain chemically implausible solutions and remaining calibrated under document shift?

## Prediction target

For each recipe, predict:

1. a sparse subset of canonical incense materials;
2. a composition vector on the probability simplex;
3. a ranked set of alternative formulas or a posterior sample set;
4. calibrated uncertainty for material inclusion and composition.

Process ingredients such as honey, fruit juice, charcoal and binders are modeled separately from odor-bearing materials. A material alias can map to more than one canonical identity; ambiguous mappings are latent variables rather than silently collapsed labels.

## Primary hypotheses

- H1: source-aware historical text representations improve ingredient-set recovery over frequency, BM25 and odor-vector baselines on document-held-out data.
- H2: marginalizing uncertain historical aliases improves cross-document performance and calibration relative to deterministic alias replacement.
- H3: a molecular/odor forward-consistency term improves weighted composition similarity without reducing material-set recall.
- H4: a recipe-hypergraph prior improves rare-material recovery and family extrapolation.
- H5: the complete model produces smaller valid candidate sets than uncalibrated probability thresholds at matched empirical coverage.

H2–H5 become contribution claims only if their preregistered ablations show consistent gains across document folds.

## Data contract

Every final-corpus record must contain: `record_id`, `work_id`, `edition_id`, `volume`, `page_or_folio`, `formula_title`, `verbatim_text`, `material_mentions`, `quantities`, `units`, `process_mentions`, `canonical_candidates`, `mapping_evidence`, `rights`, and `transcriber`.

Minimum dataset gate for the full-method paper:

- at least 80 deduplicated formula families;
- at least four independent works or independently transmitted source groups;
- document identifiers and stable locators for every evaluated record;
- a double-checked gold subset covering at least 20% of records;
- all source licenses or public-domain status documented.

The current 44-record corpus is a development corpus only because it has no document identifiers or locators.

## Leakage controls

Near-duplicate formulas are grouped before splitting using title normalization, material-set Jaccard similarity, quantity-pattern similarity and source genealogy. All versions of a formula family stay in one fold. Hyperparameters are selected inside the training documents only. Material statistics, family priors, alias priors and descriptor mappings are recomputed within each training fold.

Evaluation tiers:

1. frozen v2.4 hash split — reproducibility only;
2. leave-one-style-family-out — development stress test, never called cross-document;
3. leave-one-work-out — primary model-selection protocol;
4. sealed external works — confirmation after model freeze.

## Models

Mandatory baselines: global frequency, BM25 character retrieval, odor-space kNN, Ridge compositional regression, chemistry-only NNLS, and frozen Xiangji v2.4. Stronger baselines added after corpus expansion include calibrated gradient boosting, a text-only encoder, a chemistry-only encoder and a source-aware retrieval model.

Proposed model components:

- historical text encoder;
- latent alias resolver over candidate canonical materials;
- permutation-invariant molecular-set material encoder;
- recipe hypergraph prior;
- sparse ingredient-set decoder plus simplex-valued composition distribution;
- differentiable forward odor-consistency module;
- source-aware robust objective and post-hoc conformal candidate-set calibration.

## Outcomes

Primary outcomes:

- macro average precision for material inclusion;
- recall@k and micro/macro F1 for the material set;
- weighted Jaccard for composition;
- union-support ratio MAE.

Secondary outcomes:

- top-1 dominant-material accuracy;
- Brier score and expected calibration error per material;
- candidate-set empirical coverage and average size;
- per-work results and worst-work performance;
- rare-material recall;
- forward odor-space reconstruction error.

## Statistical analysis

All paired model comparisons use the same held-out records. Report document-cluster bootstrap 95% confidence intervals, paired bootstrap differences, and effect sizes. Multiple primary ablations are controlled with Holm correction. Results are summarized across random seeds only when stochastic training is present; data splits remain fixed. No p-value replaces effect magnitude or cross-document consistency.

## Required ablations and negative controls

- remove historical text;
- remove molecular/odor information;
- deterministic aliases instead of latent aliases;
- remove hypergraph prior;
- remove forward-consistency loss;
- remove source-robust objective;
- random material vectors as a negative chemical control;
- shuffled odor descriptors as a negative semantic control;
- random document labels to test whether source embeddings exploit artifacts.

## Freeze rule

The 30 lost-incense targets are never used for training, threshold selection or model selection. They are decoded only after the final external test is complete. Day 5 is a checkpoint: the submission candidate freezes only when all data, evaluation, calibration, ablation and reproducibility gates pass.
