# Cycle 3 model protocol v0.1

## Model identity

Xiangji-CGIR v1 is a low-parameter structured probabilistic model with an optional chemistry-guided odor bridge. The parameter count is constrained by the available evidence: the public reference contains 91 formulas and 81 materials, including 30 singleton materials. A high-capacity neural generator is therefore not the v1 default.

## Two linked tasks

### T1: source-shifted partial-formula completion

Input consists of the formula title, work identifier and a deterministic masked subset of surviving material mentions. The model predicts the complete material set and relative aromatic composition. All title and method strings are stripped of ingredient-list text; the target formula text is never supplied as an input feature.

Primary evaluation uses the frozen two-work-held-out folds. Hong-source records remain quarantined from all model statistics and Cycle 3–4 evaluation; the holdout is not investigator-blinded because the records were handled during corpus construction. Metrics are computed both on the complete formula and on hidden components only.

### T2: odor-conditioned inverse formulation

Input consists of a 12-dimensional odor target and optional title. The 44 legacy recipes provide an auxiliary bridge between odor profiles and material compositions under family-blocked validation. These records lack adequate document provenance and therefore cannot support the primary cross-document claim.

The 30 lost-incense targets are application-only. They remain excluded from model selection, vocabulary construction, calibration and threshold tuning.

## Leakage controls

1. Material vocabulary, title features, frequency priors, source priors, hypergraph edges and ratio statistics are fitted from each training fold only.
2. Test formulas never contribute co-occurrence edges or title centroids.
3. Sealed reference IDs are removed before any Cycle 3 corpus statistic is computed.
4. Mask generation is deterministic from the record ID and registered seed. At least one component is observed and one remains hidden whenever a formula has two or more components.
5. Chemical profiles are frozen Cycle 2 evidence and may be used across folds because they are external material measurements, not test-formula labels.
6. A historical grade may inherit a base-material chemical profile only through an explicit proxy map and proxy indicator.

## Xiangji-CGIR v1 scoring model

For candidate material \(j\), context \(x\), source \(s\), observed material set \(O\), hypergraph kernel \(G\) and chemical kernel \(K\), the inclusion logit is

\[
\eta_j = \beta_0 + \beta_f\ell(p_j) + \beta_s[\ell(p_{j\mid s})-\ell(p_j)] +
\beta_t T_j(x) + \beta_g G_j(O) + \beta_c K_j(O) +
\beta_o Q_j(o) + \beta_r\mathbf 1[j\in O].
\]

Here \(T_j\) is title-to-material centroid similarity; \(G_j\) is training-fold directed conditional hypergraph affinity; \(K_j\) is profile-level chemical similarity; \(Q_j\) is odor-target similarity when available; and \(\ell\) is a clipped logit. Multiple observed-material edges are combined by an unweighted mean selected on development folds. Only global channel weights are learned, limiting variance in the small-data regime.

The inclusion decoder uses a Gaussian-prior generalized Bayesian logistic model. A Laplace approximation supplies coefficient uncertainty and posterior-predictive inclusion probabilities. Class-balanced fitting is corrected back to the natural candidate prevalence with a case-control prior-odds offset. Group DRO is evaluated as an optional source-robust objective; the locked primary model uses ERM because development selection did not favor Group DRO. Ablations remove title, graph, chemistry, source and group-DRO channels separately.

## Sparse probabilistic decoder

Ingredient count has a smoothed source-conditional categorical posterior rather than a fixed six-material rule. During masked evaluation it is conditioned on the exact registered deterministic masking mechanism; the posterior median is the Bayes action for absolute count error. Inclusion probabilities and the count posterior define a distribution over top-k sets. Ratio means are predicted from fold-specific global, source, title, graph and chemistry statistics. Positive concentration parameters define a Dirichlet posterior on the simplex. The API returns inclusion probabilities, count probabilities, posterior mean proportions, credible intervals and samples.

## Chemistry constraint

Chemical similarity is computed only for materials with source-backed molecular profiles or documented grade proxies. The v1 kernel combines profile-pair molecular fingerprint, physicochemical and odor-tag similarities and takes the maximum across profiles without pooling incompatible assays. Development results did not support using pairwise chemical similarity as a T1 co-occurrence reward, so the locked T1 model disables it. This is consistent with chemical similarity representing substitutability more naturally than complementarity.

For T2, predicted mixtures are passed through a frozen odor-forward bridge and a non-negative quadratic inverse decoder. Nested family-blocked validation chooses the strength of forward agreement and the blend of external chemical odor tags. The consistency term is disabled for T1 records that have no independent odor observation.

## Cycle 3 model-selection rule

Hyperparameters are chosen using development folds only. The primary criterion is hidden-component macro F1; ties are resolved by complete-set weighted Jaccard, then ratio Aitchison distance. A model advances only if it is not worse than frequency, source-prior, title-only and graph-only baselines on source-macro performance.

## Required diagnostics

- train/test vocabulary coverage by source;
- source-specific loss and group-DRO weights;
- estimated count-posterior calibration;
- inclusion Brier score and reliability bins;
- Dirichlet simplex validity and interval coverage;
- synthetic parameter and composition recovery;
- reduced-model Metropolis-Hastings versus Laplace predictive checks;
- ablations showing whether chemistry contributes measurable signal.
