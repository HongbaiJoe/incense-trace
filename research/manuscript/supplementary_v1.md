# Supplementary Information

## Probabilistic graph completion of historical Chinese incense formulas under source shift

### Supplementary Note 1 Data curation decisions

The reference target is the relative dry-mass composition of aromatic materials in one burned or fumigating formula. Honey, fruit juice, wine, charcoal and binders remain in the source record as process materials but do not enter the aromatic composition vector. Curation retained only formulas whose aromatic quantities could be converted without imputation. Every record contains the original material string, canonical candidate, identity status, historical quantity string, normalized qian value and source locator.

The curation manifest records 91 inclusions and 29 exclusions. Exclusion categories include missing aromatic quantities, incomplete extraction boundaries, prose without an executable formula and unresolved duplication. The family audit records title similarity, material overlap, ratio-pattern evidence and source genealogy for all retained candidates.

### Supplementary Note 2 Split construction

The development set contains 85 formulas from five work groups. Five leave-one-work-out folds supported hyperparameter selection. Ten primary folds held out each unordered pair of work groups. Six Hong-source formulas remained outside vocabulary construction, feature statistics, model fitting and primary evaluation until the confirmation run. Researchers had already handled these records during curation. The confirmation is model-quarantined; it is not investigator-blinded.

### Supplementary Note 3 Leakage controls

For every training formula, global prevalence, source prevalence, title-material centroids and the directed material graph excluded that formula. Hyperparameters were selected only from development leave-one-work-out results. The primary source-pair metrics did not change model parameters. The Hong confirmation ran after code and model configuration were frozen.

### Supplementary Note 4 Model selection

The grid crossed five Gaussian-prior variances, two training objectives and three graph reducers over five mask seeds. The selected full decoder used C = 3.0, empirical-risk minimization and arithmetic-mean graph affinity. Development source-macro hidden F1 was 0.3911 with standard deviation 0.0081 across seeds. The strongest development baseline, graph-only with C = 0.1 and eight group-DRO updates, reached 0.3876 with standard deviation 0.0116. The mean paired seed difference was 0.0035, with descriptive 95% t interval [−0.0040, 0.0110].

### Supplementary Note 5 Approximate Bayesian inference checks

The inclusion model uses a Gaussian coefficient prior and a Laplace posterior centered at the maximum a posteriori solution. A separate Metropolis-Hastings chain with 20,000 draws checked posterior predictive probabilities on a synthetic logistic problem. The mean absolute difference between Laplace and Monte Carlo predictive probabilities was 0.0016.

Synthetic structured formulas provided an implementation-level recovery test. The proposed decoder reached hidden-component F1 0.900 and weighted Jaccard 0.658; frequency reached 0.497 and 0.445, respectively. This test verifies that the code can recover signal generated with compatible structure. It is not part of the historical performance estimate.

### Supplementary Note 6 Chemical representations

The material evidence graph contains 18 profile records covering 18 ontology materials, 17 analytical publications and 40 PubChem compounds. Each profile retains specimen, taxon, plant part, preparation, analytical method and measurement basis. Presence-only compounds receive equal conditional weights within that profile and are never described as measured abundance.

The material kernel combines three views: weighted Morgan fingerprint bits, standardized physicochemical descriptors and controlled odor tags. Similarity weights are 0.50, 0.25 and 0.25. The main paper reports the negative development and auxiliary-task results because they determine the model's scientific interpretation.

### Supplementary Note 7 Metric definitions

For true hidden set H and predicted hidden set P,

$$[supp-precision] \operatorname{precision}=\frac{|H\cap P|}{|P|}. $$

$$[supp-recall] \operatorname{recall}=\frac{|H\cap P|}{|H|}. $$

$$[supp-f1] F_1=\frac{2\operatorname{precision}\operatorname{recall}}{\operatorname{precision}+\operatorname{recall}}. $$

For reference and predicted composition vectors **w** and ŵ, weighted Jaccard is

$$[supp-weighted-jaccard] J_w=\frac{\sum_j\min(w_j,\widehat w_j)}{\sum_j\max(w_j,\widehat w_j)}. $$

Expected calibration error uses ten equal-width probability bins and weights each absolute probability-frequency gap by bin count. The Brier score averages squared error over hidden in-vocabulary candidate decisions.

### Supplementary Note 8 Reproducibility commands

From the `research` directory:

```bash
uv sync --all-groups
make cycle2-data
uv run python -m xiangji.freeze_cycle3
uv run python -m xiangji.freeze_cycle4
make cycle5-manuscript
make verify-references
make export-submission
make export-latex
make clean-reproduction
make cycle6-release
```

The release manifests bind source data, configuration, experiment and report files by SHA-256. Raw primary and confirmation records are stored as deterministic gzip archives with modification time fixed to zero.

### Supplementary Note 9 Competitive baselines and post-freeze analyses

Formula k-nearest neighbours and PureSVD were added after the primary decoder was frozen. Their configuration grids used only the five development work splits. Formula k-nearest neighbours selected ten cosine neighbours; PureSVD selected rank two. The unchanged primary folds then provided their first source-pair results.

The cross-work similarity analysis flagged nine formulas whose aromatic material sets reached Jaccard 0.8 against another work group. Removing them lowered every model's score but preserved the graph-frequency ordering. The released table lists all reference pairs and similarities.

The original 80% count interval covered 72.6% of the 420 work-held-out development predictions. Integer distance from the interval supplied the nonconformity score. The finite-sample 80% quantile was one material, which expanded the primary interval from 64.2% to 82.5% coverage. Its mean width increased from 1.24 to 2.86 materials.

### Supplementary Note 10 Case-level reconstruction

The case rule selected the seed-17 Hong formula closest to the median hidden F1 across that run. It selected 印香法 (*Yinxiang fa*), with six observed and five hidden reference materials. Three hidden materials were recovered, two were missed and two extra materials were selected. Supplementary Table S8 gives the complete input, prediction and reference composition. The output holds observed ratios fixed and allocates the remaining mass across predicted hidden materials.

### Supplementary Note 11 Training-only estimators and explored robust objective

All candidate statistics for a training formula were recomputed without that formula. If $y_{ij}$ indicates whether formula $i$ contains material $j$, the leave-one-formula-out global prevalence used in its training rows was

$$[supp-loo-prevalence] \pi_j^{(-i)}=\frac{c_j-y_{ij}+1/2}{N}. $$

The title centroid and directed graph used the same exclusion. This prevents the candidate label for formula $i$ from appearing in its own predictors.

Group-distributionally robust optimization was explored during development but was not selected for the locked full decoder. For work weights $q_d^{(t)}$, work-level log loss $L_d(\boldsymbol\theta_t)$ and step size $\eta=0.2$, the implemented update was

$$[supp-group-dro] q_d^{(t+1)}=\frac{q_d^{(t)}\exp\{\eta L_d(\boldsymbol\theta_t)\}}{\sum_{h=1}^{D}q_h^{(t)}\exp\{\eta L_h(\boldsymbol\theta_t)\}}. $$

Each optimization iteration weighted a candidate row from work $d$ by $q_d^{(t)}/n_d$ before class balancing. The selected full decoder used zero group-DRO updates, so its final objective is Equation 9 of the main manuscript.

### Supplementary Tables

- Table S1: `tables/table1_corpus_by_source.csv`
- Table S2: `tables/table2_primary_models.csv`
- Table S3: `tables/table3_source_metrics.csv`
- Table S4: `tables/table4_context_sensitivity.csv`
- Table S5: `tables/table5_rarity_recall.csv`
- Table S6: `tables/table6_reliability_bins.csv`
- Table S7: `tables/table7_hong_confirmation.csv`
- Table S8: `tables/table8_case_study.csv`
- Table S9: `tables/table9_source_mapping.csv`
- Table S10: `tables/table10_competitive_baselines.csv`
- Table S11: `tables/table11_near_duplicate_sensitivity.csv`
- Table S12: `tables/table12_count_recalibration.csv`

The analytical-literature screening log is released as `literature/screening.csv`.

### Supplementary Data and software inventory

The data sheet, curation protocol, source-acquisition protocol, model protocol, model card, frozen configuration, development diagnostics, primary evaluation, robustness analysis, Hong confirmation, computational profile, figure source tables and release manifests are versioned in the repository. File hashes appear in the cycle release manifests and figure manifest.
