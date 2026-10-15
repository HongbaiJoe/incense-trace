# Manuscript outline v0

## Working title

Xiangji-CGIR: Source-aware probabilistic reconstruction of historical Chinese incense formulations with chemical consistency constraints

## Central claim under test

Historical formulation recovery is a low-resource, non-identifiable structured prediction problem. A model that jointly handles document provenance, uncertain material names, ingredient-set structure and chemical/odor consistency should generalize across texts better than retrieval, perceptual-regression and unconstrained decoding baselines.

## Abstract logic

1. Problem: formula descriptions survive unevenly, historical names drift, and multiple compositions can fit the same olfactory language.
2. Gap: existing odor ML predicts single-molecule or mixture perception, and recent inverse scent design starts from modern analytical/descriptor data; neither recovers historical natural-material formulas from source text under provenance shift.
3. Method: provenance-rich corpus plus latent lexical mapping, set-to-simplex probabilistic decoder, recipe hypergraph and molecular/odor forward-consistency loss.
4. Evaluation: formula-family groups, leave-one-work-out and sealed external works; material-set, composition, calibration and worst-source metrics.
5. Result sentence: written only after frozen confirmation.
6. Contribution: task/benchmark, method components supported by ablation, and calibrated candidate reconstructions.

## Main text

### 1. Introduction

- historical and computational problem;
- why point reconstruction is underdetermined;
- boundary against modern inverse scent creation;
- research questions and contribution statement.

### 2. Related work

- molecular structure–odor prediction;
- odor-mixture representations and inverse formulation;
- computational recipe understanding;
- historical NER/entity disambiguation;
- uncertainty and constrained structured prediction.

### 3. Data and benchmark

- source selection and rights;
- transcription and entity schema;
- unit normalization and process/material separation;
- canonical material ontology and ambiguity distributions;
- formula-family deduplication;
- document-held-out split and annotation reliability.

### 4. Method

- formal problem;
- historical text/source encoder;
- latent alias resolver;
- molecular-set ingredient representations;
- recipe hypergraph;
- sparse set and simplex composition decoder;
- nonlinear forward-consistency objective;
- source robustness and calibrated candidate sets;
- complexity analysis.

### 5. Experiments

- baselines and fixed tuning protocol;
- primary and secondary metrics;
- cross-document evaluation;
- ablations, negative controls and sensitivity tests;
- clustered bootstrap and multiplicity handling.

### 6. Results

- corpus and coverage;
- main benchmark table;
- source-level and rare-material results;
- calibration/coverage;
- ablations;
- error taxonomy;
- frozen application to 30 targets.

### 7. Discussion

- what chemical constraints contribute;
- historical ambiguity and non-identifiability;
- limitations of descriptor and combustion modeling;
- transfer to other historical formulations.

### 8. Methods availability and declarations

Data, code, ethics if human evaluation is later added, author contributions, competing interests and scientific contribution statement.

## Planned figures

1. Task definition and full information flow.
2. Corpus provenance, formula genealogy and split construction.
3. Xiangji-CGIR architecture.
4. Cross-document performance with cluster-bootstrap intervals.
5. Ablation and negative-control results.
6. Calibration, candidate-set coverage and selected target reconstructions.

## Planned tables

1. Corpus and source statistics.
2. Main cross-document benchmark.
3. Component ablations and statistical differences.
4. External test, robustness and calibration summary.
