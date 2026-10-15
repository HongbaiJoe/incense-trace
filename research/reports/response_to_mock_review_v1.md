# Response to mock peer review

## Summary of revision

The revision adds two competitive set-completion baselines, a cross-work near-duplicate sensitivity analysis, development-only count-interval calibration, mass-constrained ratio decoding, one deterministic case study, complete source-title mapping, live verification of all 38 references and a clean-environment reproduction run. Model parameters and the registered primary evaluation did not change.

## Reviewer 1

### R1-M1 competitive baselines

Resolved. Formula k-nearest neighbours and PureSVD use the same masks, count rule and source-blocked primary folds as Xiangji-CGIR. We selected k, similarity and SVD rank on the five development work splits. The graph reached hidden F1 0.379, versus 0.343 for formula k-nearest neighbours and 0.334 for PureSVD. Methods now specify both grids; Fig. 6a and Supplementary Table S10 report all primary scores.

### R1-M2 count calibration

Resolved. The original count interval covered 64.2% at nominal 80%. We computed interval nonconformity on 420 leave-one-work-out development predictions. The finite-sample 80% quantile was one material. Expanding the locked primary intervals by this amount raised coverage to 82.5%, with mean width increasing from 1.24 to 2.86. No primary label entered calibration. Fig. 6c and Supplementary Table S12 report coverage and width.

### R1-M3 cross-work near duplicates

Resolved. Nine formulas had aromatic material-set Jaccard at least 0.8 with a formula in another work group. Excluding them reduced graph F1 from 0.379 to 0.348 and frequency F1 from 0.338 to 0.322. The graph retained a 0.0259 work-level advantage. The released JSON names every flagged pair; Fig. 6b and Supplementary Table S11 summarize the result.

### R1-m1 clean reproduction

Resolved. A fresh copy installed the locked environment, regenerated Cycle 6, ran 112 tests and compared 14 deterministic outputs. Every command exited zero and every checked output matched byte for byte. The report records commands, versions and SHA-256 hashes.

## Reviewer 2

### R2-M1 novelty and split choice

Resolved in framing and comparison. The paper locates novelty in the task, source-shifted benchmark and integration of a directed training-only graph with count and composition inference. It does not present logistic regression, nearest-neighbour retrieval or low-rank factorization as new algorithms. We did not add a random formula split because it mixes formulas from each historical work across training and test data and estimates within-document interpolation. The paper claims transfer to unseen works. The two-work-held-out design is therefore the estimand, while the new formula-neighbour baseline and near-duplicate exclusion directly test memorization and local analogy within that design.

### R2-M2 chemistry scope

Resolved. Results now state the analytical coverage directly: 18 of 81 materials, 18 specimen profiles, 17 publications and 40 PubChem compounds. The abstract, Results and Discussion restrict the conclusion to the tested pairwise kernel. The forward agenda specifies directed functional roles, combustion products, volatility and nonlinear mixture interactions.

### R2-M3 curation reliability

Addressed without inventing agreement data. The data object remains a curated pilot reference set, not a gold standard. Methods state that one curator performed canonicalization, the released audit records all 120 decisions and seven gates, and Discussion names independent recuration as the next dataset experiment. A second-curator statistic requires another human annotation pass and remains the only scientific extension not present in this release.

### R2-m1 case study

Resolved. A fixed rule selected the seed-17 Hong formula closest to the six-formula median hidden F1. For *Yinxiang fa*, the model received six of eleven components, recovered three of five hidden materials, missed two and added two. Hidden F1 was 0.600 and mass-constrained weighted Jaccard was 0.483. Supplementary Table S8 reports every observed, recovered, missed and extra material.

## Reviewer 3

### R3-M1 case-level use

Resolved through the same complete case. The manuscript now shows how the ranked output narrows candidate ingredients and exposes failures on low-frequency components.

### R3-M2 count and weighted Jaccard explanation

Resolved. Results define weighted Jaccard as the fraction of total formula mass shared by reference and prediction. Methods state why count is separate: inclusion scores rank candidates but do not determine where the list should stop.

### R3-m1 calibration denominators

Resolved. Marker area remains tied to the square root of bin count, and Supplementary Table S6 supplies all ten bin counts, mean probabilities and empirical frequencies.

### R3-m2 source mapping

Resolved. Supplementary Table S9 maps each work identifier to its represented source pages. The machine-readable CSV retains Chinese titles; the portable PDF includes romanized titles and juan locators.

## Editorial state

The computational claims, experiments, bibliography and reproducibility package pass the release gate. Journal upload still requires author name, affiliation, corresponding email, funding or acknowledgement text, CRediT contributions and the competing-interest declaration.
