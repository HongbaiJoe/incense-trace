# Probabilistic graph completion of historical Chinese incense formulas under source shift

**[Author name]**  
[Affiliation, city, country]  
[Corresponding email]

## Abstract

Historical incense books preserve formulas unevenly, while modern odor datasets describe molecules and rarely recipes. We formulate missing-ingredient recovery as source-shifted probabilistic set completion. Xiangji-CGIR combines a directed material graph with a Laplace-approximated inclusion model and explicit ingredient-count and composition uncertainty. We curated 91 family-unique Chinese incense formulas from six work groups. At 50% observed context, the graph reached source-macro hidden-component F1 0.365 versus 0.339 for frequency, 0.343 for formula k-nearest neighbours and 0.334 for PureSVD. Removing nine cross-work high-similarity formulas retained the graph advantage, 0.348 versus 0.322. Development-calibrated count intervals achieved 0.825 coverage at nominal 0.80. The full decoder reached F1 0.366, and confirmation on a quarantined work reached 0.577. An 18-material chemical kernel did not improve completion. Co-formulation structure transfers across texts; molecular similarity alone does not represent historical ingredient complementarity.

## Introduction

Smell can carry cultural meaning, but it leaves a fragmented archive. Heritage frameworks now treat historic odors as objects that can be identified, described and preserved [1]. The Odeuropa data model connects odor sources, emissions, experiences, places and historical language [2]. Analytical heritage science has also reconstructed the present smell of a surviving perfume residue by combining gas chromatography, olfactory detection and sensory validation [3]. Historical incense formulas pose a different computational problem. The material may no longer survive, and the books may preserve only a name, partial recipe, attributed source or literary description, with no measurable headspace sample.

Computational olfaction has learned useful mappings from molecular structure or mass spectra to perceptual descriptors [4-8]. Mixture models now predict descriptors for pairs of aroma chemicals [9], and inverse design can optimize modern essential-oil mixtures against a requested scent profile [10]. These systems start from molecules, spectra or controlled vocabulary. They do not recover a historical natural-material formula from incomplete evidence transmitted through different texts. Historical language processing addresses orthographic variation and sparse annotation [11], while recipe information extraction resolves ingredients and quantities from modern text [12]. Neither line of work supplies a source-shifted benchmark for historical formula completion. Nearest-neighbour retrieval and low-rank recommendation test whether a historical graph adds information beyond local formula analogy or latent co-occurrence [16,17]. Development-held-out interval expansion tests whether its count uncertainty transfers [18].

We define a formula as a sparse set of aromatic materials with relative dry-mass ratios. Given its title, source identifier and a known subset of ingredients, the task is to recover the hidden materials and their proportions. This setting tests a practical scholarly operation: completing a damaged or selectively transmitted formula from patterns learned in other works. It also exposes the central statistical difficulty. Incense vocabularies are long-tailed, formula sizes vary, and source traditions differ. A random record split would let near-identical textual and material conventions leak across training and test sets.

Xiangji-CGIR makes four contributions. First, it introduces a provenance-rich reference set of 91 family-unique formulas from six Chinese incense work groups, with stable source locators, canonical material identifiers and source-blocked splits. Second, it represents each formula as a hyperedge and converts training-only co-occurrence counts into a directed posterior-predictive material graph. Third, it couples that graph to a Laplace-approximated generalized Bayesian inclusion decoder, an empirical-Bayes ingredient-count distribution and a residual-scaled Dirichlet composition distribution. Fourth, it measures the contribution of chemistry through development ablations, an auxiliary inverse-odor task and shuffled material-chemistry assignments. Co-formulation structure transfers across historical works; title and source channels add no reliable gain beyond the graph, and pairwise chemical similarity does not improve completion.

## Related Work

This study joins three research lines that are usually evaluated separately. Computational olfaction predicts perceptual descriptors from molecular structure, spectra or controlled mixtures [4-10]. Historical-language and recipe-processing systems recover entities and quantities from text [11,12]. Multi-label learning and recommender systems recover missing labels from sparse co-occurrence structure [13,16,17]. Xiangji-CGIR uses chemical representations as an auditable evidence layer, but its primary output is a structured completion of natural-material formulas rather than a molecular odor prediction.

The closest statistical formulation is multi-label set completion under domain shift. Sparse Bayesian multi-label models use label correlations to regularize prediction [13], while WILDS formalizes evaluation when deployment domains differ from training environments [14]. Historical formula books create both problems at once: ingredients are correlated within a formula, and each work carries its own vocabulary, editing history and compositional conventions. We therefore treat each work as a domain and rebuild every prevalence, graph and text statistic inside the training fold.

Our uncertainty design also draws on two distinct traditions. The inclusion decoder uses a Laplace approximation around a regularized, class-weighted logistic optimum, whereas the total-count interval is recalibrated from work-held-out residuals using split-conformal logic [18]. Composition is evaluated in simplex geometry [19]. These components answer different questions—whether a material is present, how many materials remain, and how mass is distributed—and are assessed separately rather than collapsed into one confidence score.

## Problem Formulation and Dataset

### Corpus Construction and Provenance

We extracted formula candidates from public-domain Chinese incense texts and their Wikisource transcriptions. Each candidate stored the work and edition identifier, formula title, verbatim source span, stable revision URL, line locator, transcription hash, material mentions, quantity strings, process mentions and rights statement. The curation protocol separated aromatic materials from binders, liquids and processing aids. It converted historical mass expressions to qian on a relative basis, summed repeated mentions and normalized aromatic mass to one. Records with an unresolved aromatic quantity, list boundary or formula identity were excluded without imputation.

Canonicalization mapped material mentions to an ontology identifier while retaining the surface form and identity status. Grade terms for agarwood remained separate identifiers. Four contextually resolved characters carry explicit resolution records. Candidate families were compared by normalized title, material-set overlap, ratio pattern and source genealogy. One checked representative was retained per provisional family. The resulting version 0.1 reference set contains 91 formulas; 29 screened candidates were excluded. All transformations are executable and hash checked.

### Prediction Task and Observation Mechanism

For formula $i$, let $q_{ij}$ be the converted aromatic mass of material $j$, $S_i$ its material support and $M$ the training vocabulary size. Aromatic masses were closed to the simplex as

$$[composition-closure] \mathbf{w}_i\in\Delta^{M-1},\qquad w_{ij}=\frac{q_{ij}}{\sum_{k\in S_i}q_{ik}},\qquad S_i=\{j:w_{ij}>0\}. $$

The model receives title $t_i$, work identifier $d_i$ and an observed subset $O_i\subset S_i$ with the original entries $\{w_{ij}:j\in O_i\}$. It predicts the hidden set $H_i=S_i\setminus O_i$, a complete material set $\widehat S_i$ and a composition $\widehat{\mathbf w}_i$.

We generated $O_i$ deterministically from a cryptographic hash of formula identifier, observation fraction and seed. For $K_i=|S_i|$, the retained count was

$$[mask-cardinality] r(K_i,f)=\min\{K_i-1,\max[1,\operatorname{round}(fK_i)]\},\qquad |O_i|=r(K_i,f). $$

Here $f\in\{0.25,0.50,0.75\}$. This rule guarantees at least one observed and one hidden in-vocabulary material. The registered primary fraction was 0.50. Five seeds, 17, 29, 43, 71 and 101, changed the observed subset but not the source splits.

### Source-Blocked Splits

The Hong work group and its six formulas were removed before vocabulary construction, prior estimation, feature scaling or model selection. Development used five leave-one-work-out folds. Primary evaluation used all ten unordered pairs of the five remaining work groups as test domains, with the other three groups as training data. Family identifiers were disjoint because the reference set contains one representative per checked family. Each test formula appears in four source-pair folds and five mask seeds. We first averaged repeated predictions for a formula, then averaged formulas within a work group, then averaged the five work groups. The historical work is the unit of primary inference.

[[TABLE:1]]

## Xiangji-CGIR Method

### Model Overview

Xiangji-CGIR separates formula completion into candidate inclusion, total ingredient count and composition. Figure 1 summarizes the training-only information flow and the source-blocked evaluation design.

[[FIGURE:1]]

### Directed Posterior-Predictive Material Graph

Each training formula defines a hyperedge over its aromatic materials. Among $N$ training formulas, let $c_a$ count formulas containing material $a$, $c_{ab}$ count formulas containing both $a$ and $b$, and $c_{dj}$ count material $j$ in the $N_d$ formulas from work $d$. Global and work-specific prevalence estimates were

$$[prevalence-priors] \pi_j=\frac{c_j+1/2}{N+1},\qquad \pi_{j\mid d}=\frac{c_{dj}+\lambda_s\pi_j}{N_d+\lambda_s},\qquad \lambda_s=5. $$

The directed posterior-predictive co-formulation edge was

$$[directed-graph] G_{ab}=\frac{c_{ab}+\alpha\pi_b}{c_a+\alpha},\qquad \alpha=2,\qquad G_{aa}=1. $$

For the locked arithmetic-mean reducer, graph affinity for candidate $j$ was

$$[graph-affinity] a^{(G)}_{ij}=\frac{1}{|O_i|}\sum_{a\in O_i}G_{aj}. $$

Direction matters because $G_{ab}$ generally differs from $G_{ba}$. During training, prevalence estimates and the graph for formula $i$ were rebuilt without that formula, preventing its target labels from contributing to its own features.

### Generalized Bayesian Inclusion Decoder

The title encoder mapped each title to an L2-normalized character 1- and 2-gram TF-IDF vector $\mathbf v(t)$. For candidate $j$, the normalized training-title centroid and its similarity to formula $i$ were

$$[title-affinity] \mathbf u_j=\frac{\sum_{r=1}^{N}y_{rj}\mathbf v(t_r)}{\left\|\sum_{r=1}^{N}y_{rj}\mathbf v(t_r)\right\|_2},\qquad a^{(T)}_{ij}=\mathbf v(t_i)^{\top}\mathbf u_j. $$

The active candidate feature vector in the locked decoder was

$$[candidate-features] g_{ij}=\operatorname{logit}\pi_{j\mid d_i}-\operatorname{logit}\pi_j,\qquad u_{ij}={\bf1}(j\in O_i),\qquad \mathbf x_{ij}=[\operatorname{logit}\pi_j,g_{ij},a^{(T)}_{ij},a^{(G)}_{ij},u_{ij},u_{ij}\log w_{ij}]^{\top}. $$

Training-fold means $\boldsymbol\mu_x$ and standard deviations $\mathbf s_x$ supplied elementwise standardization, $\mathbf z_{ij}=(\mathbf x_{ij}-\boldsymbol\mu_x)\oslash\mathbf s_x$. An odor-similarity slot was present in the software interface but identically zero because the primary formulas contain no independent odor target. Chemistry channels were disabled in the locked model after development selection. For a held-out work, $\pi_{j\mid d_i}$ defaults to $\pi_j$, so the source-deviation coordinate is exactly zero rather than using information from the test work.

Let $n$ index the $L_{\mathrm{tr}}$ formula-candidate training rows, $y_n\in\{0,1\}$ indicate material presence, and $\widetilde{\mathbf z}_n=[1,\mathbf z_n^{\top}]^{\top}$. The conditional inclusion model was

$$[logistic-model] p_n(\boldsymbol\theta)=\sigma(\widetilde{\mathbf z}_n^{\top}\boldsymbol\theta),\qquad \sigma(u)=\frac{1}{1+\exp(-u)}. $$

If $N_1$ and $N_0$ denote positive and negative candidate rows, class weights were $\omega_n=N/(2N_1)$ for $y_n=1$ and $\omega_n=N/(2N_0)$ otherwise. With intercept precision $10^{-6}$ and coefficient prior variance $C=3.0$, the generalized maximum-a-posteriori estimate minimized

$$[map-objective] \mathcal L(\boldsymbol\theta)=\sum_{n=1}^{L_{\mathrm{tr}}}\omega_n[\log(1+\exp\eta_n)-y_n\eta_n]+\frac{1}{2}\boldsymbol\theta^{\top}\boldsymbol\Lambda\boldsymbol\theta,\qquad \widehat{\boldsymbol\theta}=\arg\min_{\boldsymbol\theta}\mathcal L(\boldsymbol\theta),\quad \eta_n=\widetilde{\mathbf z}_n^{\top}\boldsymbol\theta. $$

Here $\boldsymbol\Lambda=\operatorname{diag}(10^{-6},C^{-1},\ldots,C^{-1})$. At $\widehat{\boldsymbol\theta}$, the Laplace covariance and generalized posterior approximation were

$$[laplace-posterior] \boldsymbol\Sigma=\left[\widetilde{\mathbf Z}^{\top}\operatorname{diag}\{\omega_n\widehat p_n(1-\widehat p_n)\}\widetilde{\mathbf Z}+\boldsymbol\Lambda\right]^{+},\qquad \boldsymbol\theta\mid\mathcal D\approx\mathcal N(\widehat{\boldsymbol\theta},\boldsymbol\Sigma). $$

Class balancing changes the effective prior odds. The implementation restores the training-population odds with $\delta=\log(N_1/N_0)$ and uses the logistic-normal approximation

$$[predictive-probability] v_{ij}=\widetilde{\mathbf z}_{ij}^{\top}\boldsymbol\Sigma\widetilde{\mathbf z}_{ij},\qquad \widehat p_{ij}=\sigma\left(\frac{\widetilde{\mathbf z}_{ij}^{\top}\widehat{\boldsymbol\theta}+\delta}{\sqrt{1+\pi v_{ij}/8}}\right). $$

Central 80% parameter-induced probability intervals came from $B$ draws $\boldsymbol\theta^{(b)}\sim\mathcal N(\widehat{\boldsymbol\theta},\boldsymbol\Sigma)$ and $p_{ij}^{(b)}=\sigma(\widetilde{\mathbf z}_{ij}^{\top}\boldsymbol\theta^{(b)}+\delta)$. These intervals quantify coefficient uncertainty, not future Bernoulli outcomes. A separate 20,000-step Metropolis-Hastings check on a synthetic logistic problem produced mean absolute predictive difference 0.0016 from the Laplace implementation.

All global prevalence, source prevalence, title-centroid and graph features used leave-one-formula-out values for training examples. Observed materials were forced into the output set after prediction.

### Ingredient Count and Composition Uncertainty

We modeled ingredient count separately because inclusion probabilities rank materials but do not determine where the ranked list should stop. For support $k\in\{1,\ldots,K_{\max}\}$, global and work-shrunk count distributions were

$$[count-priors] p_0(k)=\frac{n_k+1/2}{N+K_{\max}/2},\qquad p_d(k)=\frac{n_{dk}+\lambda_k p_0(k)}{N_d+\lambda_k},\qquad \lambda_k=3. $$

Given $o=|O_i|$ and the registered fraction $f$, the exact deterministic-mask likelihood yields

$$[count-posterior] p(K_i=k\mid d_i,o,f)\propto p_{d_i}(k){\bf1}\{k\ge\max(1,o)\}{\bf1}\{r(k,f)=o\}. $$

For an unseen work, $p_{d_i}$ defaults to $p_0$. The selected formula size was the posterior median

$$[count-decision] \widehat K_i=\min\left\{k:\sum_{h=1}^{k}p(K_i=h\mid d_i,o,f)\ge\frac{1}{2}\right\}, $$

which is the Bayes action under absolute count loss. The top $\widehat K_i$ inclusion probabilities defined $\widehat S_i$, with observed materials forced into the ranking. This mask-conditioned count posterior is an evaluation model for known $f$; when the observation process is unknown, the software falls back to the unconditioned work or global count distribution.

For each present training material, ridge regression mapped the standardized candidate features to log composition. With $L_r$ positive training rows, target $\ell_n=\log w_n$ and penalty $\rho=1$, it solved

$$[ratio-ridge] \mathcal R(\mathbf b)=\sum_{n=1}^{L_r}(\ell_n-\widetilde{\mathbf z}_n^{\top}\mathbf b)^2+\rho\|\mathbf b\|_2^2,\qquad \widehat{\mathbf b}=\arg\min_{\mathbf b}\mathcal R(\mathbf b). $$

For the selected set $\widehat S_i$, exponentiation and closure supplied the compositional mean

$$[ratio-closure] r_{ij}=\exp(\widetilde{\mathbf z}_{ij}^{\top}\widehat{\mathbf b}),\qquad \mu_{ij}=\frac{r_{ij}}{\sum_{h\in\widehat S_i}r_{ih}},\quad j\in\widehat S_i. $$

If $s_r^2$ is the mean squared training residual on the log-ratio scale, the implementation sets $\kappa=\operatorname{clip}(1/\max[s_r^2,0.01],2,100)$ and $\alpha_{ij}=\max(\kappa\mu_{ij},10^{-3})$, then draws

$$[dirichlet-composition] \mathbf W_{i,\widehat S_i}\sim\operatorname{Dirichlet}(\boldsymbol\alpha_i). $$

The 10th and 90th marginal quantiles of 200 draws form central 80% intervals. This is a residual-scaled uncertainty distribution conditional on the selected set, not a fully Bayesian posterior for set and composition jointly. The registered primary weighted Jaccard used the unconstrained mean $\boldsymbol\mu_i$. A post-freeze reporting transform holds supplied ratios fixed and allocates the remaining mass over predicted hidden materials:

$$[mass-constraint] \widehat w^{(c)}_{ij}=\begin{cases}w_{ij},&j\in O_i,\\ \left(1-\sum_{a\in O_i}w_{ia}\right)\dfrac{\mu_{ij}}{\sum_{h\in\widehat S_i\setminus O_i}\mu_{ih}},&j\in\widehat S_i\setminus O_i,\\0,&\text{otherwise}.\end{cases} $$

This transform changes neither material ranking nor selection. It increased post-freeze source-macro weighted Jaccard from 0.387 to 0.427.

The original count interval used the 10th and 90th percentiles of the masked count posterior. We calibrated its width from the five leave-one-work-out development folds [18]. For each development prediction, nonconformity was the integer distance from the true count to the original interval, or zero when covered. The finite-sample 80% quantile over 420 development predictions was one material. We expanded both primary interval endpoints by that value, retaining at least one hidden component. Primary labels did not determine the expansion.

### Chemoinformatic Evidence Layer

Targeted searches identified analytical studies for materials in the ontology [22-38]. Each accepted statement linked one specimen and preparation to an identified compound, analytical method, source locator and measurement type. Presence-only reports were not converted into abundance. Incompatible preparations and units remained separate profiles. PubChem identifiers anchored 40 compounds.

RDKit generated radius-2, 2,048-bit Morgan fingerprints [20] and ten physicochemical descriptors. For $B$-bin profile vectors $\mathbf f$, standardized physicochemical vectors $\mathbf r$ and controlled odor-tag vectors $\mathbf o$, we used

$$[profile-similarities] T(\mathbf f_p,\mathbf f_q)=\frac{\sum_{b=1}^{B}\min(f_{pb},f_{qb})}{\sum_{b=1}^{B}\max(f_{pb},f_{qb})},\qquad C_+(\mathbf a,\mathbf b)=\max\left(0,\frac{\mathbf a^{\top}\mathbf b}{\|\mathbf a\|_2\|\mathbf b\|_2}\right). $$

For materials $a$ and $b$ with compatible profile sets $\mathcal P_a$ and $\mathcal P_b$, the chemical kernel was

$$[chemical-kernel] \kappa(p,q)=0.50T(\mathbf f_p,\mathbf f_q)+0.25C_+(\mathbf r_p,\mathbf r_q)+0.25C_+(\mathbf o_p,\mathbf o_q),\qquad K^{(C)}_{ab}=\max_{p\in\mathcal P_a,q\in\mathcal P_b}\kappa(p,q). $$

Seven historically graded materials used an explicit parent-material proxy solely for representation coverage. When enabled, chemical affinity is the observed-mass-weighted kernel average. The locked primary model excludes this channel.

We tested the chemical kernel in two settings. Primary-task development compared chemistry-enabled and chemistry-disabled decoders. The auxiliary inverse-odor task mapped 12-dimensional curated odor profiles to compositions for 44 legacy formulas using nested leave-one-family-out validation. It compared odor k-nearest neighbors, forward-consistent decoding, removal of chemistry and permutation of material-chemistry assignments. The auxiliary data did not enter primary model selection.

## Experimental Design

### Model Selection, Ablations and Negative Controls

Development searched C ∈ {0.03, 0.1, 0.3, 1, 3}, empirical-risk versus eight-step group-distributionally robust optimization, and graph reducers {weighted mean, mean, maximum}. Selection maximized mean source-macro hidden F1, then weighted Jaccard, then minimized dimension-normalized Aitchison distance. The locked configuration used C = 3, empirical-risk minimization and mean graph reduction.

Baselines isolated global frequency, source prevalence, title similarity and graph affinity. Chemistry ablations tested molecular similarity directly. The auxiliary task added shuffled chemical assignments as a negative semantic control. Synthetic recovery verified that the structured model could identify known generative structure: hidden F1 was 0.900 for the structured decoder and 0.497 for frequency.

[[TABLE:2]]

### Competitive Set-Completion Baselines

Formula k-nearest neighbours compared the observed binary vector $\mathbf o_i$ with each training incidence vector $\mathbf y_r$ [16]. The selected cosine score was

$$[knn-similarity] s_{ir}=\frac{\mathbf o_i^{\top}\mathbf y_r}{\|\mathbf o_i\|_2\|\mathbf y_r\|_2},\qquad \widehat{\mathbf p}_i=\frac{\sum_{r\in\mathcal N_{10}(i)}s_{ir}\mathbf y_r}{\sum_{r\in\mathcal N_{10}(i)}s_{ir}}. $$

Similarity-weighted neighbour compositions supplied ratios. PureSVD factorized the training incidence matrix $\mathbf Y=\mathbf U\boldsymbol\Sigma\mathbf V^{\top}$ and scored candidates by

$$[svd-baseline] \widehat{\mathbf p}_i=\mathbf o_i\mathbf V_{2}\mathbf V_{2}^{\top}+0.05\boldsymbol\pi. $$

Development search selected cosine similarity with ten neighbours from $k\in\{1,3,5,10\}$ and SVD rank two from $\{2,4,8,16,32\}$. Both baselines used the same deterministic masks, training-only count rule, fixed observed ratios and source-blocked evaluation. Their configurations were locked on leave-one-work-out development results before primary scores were computed.

### Cross-Work Similarity Sensitivity and Case Selection

For every development formula, we computed the maximum aromatic material-set Jaccard against formulas from other work groups. The sensitivity analysis removed a formula when this value was at least 0.8, then repeated formula-level and work-level aggregation on the stored primary predictions. This rule removed nine formulas and did not refit any model.

The case study used the Hong confirmation run at the registered seed 17. We selected the formula whose hidden F1 was closest to the median of the six confirmation formulas, breaking ties by reference identifier. The rule selected *Yinxiang fa*. The table reports every observed, recovered, missed and extra material under this fixed rule.

### Evaluation Metrics and Statistical Analysis

Let $H_i=S_i\setminus O_i$ and $P_i=\widehat S_i\setminus O_i$. Hidden-component precision, recall and F1 were

$$[set-metrics] \operatorname{Prec}_i=\frac{|H_i\cap P_i|}{|P_i|},\qquad \operatorname{Rec}_i=\frac{|H_i\cap P_i|}{|H_i|},\qquad F_{1i}=\frac{2\operatorname{Prec}_i\operatorname{Rec}_i}{\operatorname{Prec}_i+\operatorname{Rec}_i}. $$

For union support $U_i=S_i\cup\widehat S_i$, weighted Jaccard and union-support ratio error were

$$[composition-metrics] J_{wi}=\frac{\sum_{j\in U_i}\min(w_{ij},\widehat w_{ij})}{\sum_{j\in U_i}\max(w_{ij},\widehat w_{ij})},\qquad E_{Ui}=\frac{1}{|U_i|}\sum_{j\in U_i}|w_{ij}-\widehat w_{ij}|. $$

After adding $\epsilon=10^{-6}$ on $U_i$ and re-closing both vectors, the implementation reports the dimension-normalized Aitchison distance [19]

$$[aitchison-distance] d_{Ai}=\frac{\|\operatorname{clr}(\mathbf w_i^{\epsilon})-\operatorname{clr}(\widehat{\mathbf w}_i^{\epsilon})\|_2}{\sqrt{|U_i|}},\qquad \operatorname{clr}(\mathbf x)=\log\mathbf x-\frac{1}{|U_i|}\sum_{j\in U_i}\log x_j. $$

For hidden in-vocabulary candidate decisions, the Brier score and ten-bin expected calibration error were

$$[calibration-metrics] \operatorname{Brier}=\frac{1}{L}\sum_{n=1}^{L}(p_n-y_n)^2,\qquad \operatorname{ECE}=\sum_{b=1}^{10}\frac{|B_b|}{L}\left|\overline p_b-\overline y_b\right|. $$

We also recorded absolute count error and vocabulary coverage.

Repeated appearances of formula $i$ across source-pair folds and mask seeds formed a set $A_i$. Metrics were averaged first within formula, then within work, and finally across the $D=5$ primary works:

$$[source-macro] \overline m_i=\frac{1}{|A_i|}\sum_{a\in A_i}m_{ia},\qquad \overline m_d=\frac{1}{|I_d|}\sum_{i\in I_d}\overline m_i,\qquad m_{\mathrm{macro}}=\frac{1}{D}\sum_{d=1}^{D}\overline m_d. $$

Primary comparisons used paired work-level F1 differences $\Delta_d$. Alongside the mean difference and a descriptive t interval, we report a 20,000-draw work-group percentile bootstrap interval and the exact two-sided sign-flip p-value

$$[sign-flip-test] T(\mathbf s)=\left|D^{-1}\sum_{d=1}^{D}s_d\Delta_d\right|,\qquad p_{\mathrm{flip}}=2^{-D}\sum_{\mathbf s\in\{-1,1\}^{D}}{\bf1}\{T(\mathbf s)\ge T(\mathbf 1)\}. $$

Five blocks restrict this p-value to a coarse grid, so the analysis emphasizes effect magnitude and direction across sources. Calibration pools repeated source-pair folds and mask seeds and is descriptive. No primary model parameter changed after the primary results were computed.

The original count interval $[L_i,U_i]$ was recalibrated only from $n=420$ work-held-out development predictions. For nonconformity $a_i=\max(L_i-K_i,K_i-U_i,0)$, the radius was

$$[count-conformal] q=\operatorname{Quantile}_{\lceil(n+1)0.8\rceil/n}^{\mathrm{higher}}(a_1,\ldots,a_n),\qquad [L_i^{(c)},U_i^{(c)}]=[\max(|O_i|+1,L_i-q),U_i+q]. $$

The resulting $q=1$ was applied unchanged to primary intervals; primary labels did not determine it.

### Software and Computational Profiling

The reference implementation uses Python 3.11 or later, NumPy, SciPy, scikit-learn [21], pandas and RDKit. Every data freeze stores SHA-256 hashes for inputs and outputs. The automated test suite covers parsing, curation, family blocking, source splits, feature leakage, posterior inference, model selection, primary evaluation, robustness, confirmation and manuscript asset generation. Computational timing used Python 3.14.6 and NumPy 2.5.2 on macOS 14.5 arm64. Eleven serial repetitions excluded data-loading time and used 200 posterior samples per prediction.

## Results

### A source-blocked benchmark exposes material and document sparsity

The curation pipeline screened 120 candidate formulas and retained 91 with complete aromatic quantities. Each retained record links a verbatim transcription to a stable revision URL and locator. The six work groups contributed 38, 29, 10, 6, 6 and 2 formulas, respectively (Fig. 2a; Table 3). The corpus contains 81 canonical aromatic materials. Formula size ranges from 2 to 17 materials, with a median of 6 and a mean of 6.85 (Fig. 2b). Thirty materials occur in one formula, while four materials appear in more than 40 formulas. This frequency profile makes rare-material recovery a defining part of the task, not a peripheral edge case.

Six formulas attributed to the Hong Xiangpu work group were removed before any model-facing statistic was constructed. The other 85 formulas from five work groups contain 80 materials and formed development and primary evaluation data. Ten primary folds held out every pair of work groups and trained on the remaining three. This design tests transfer to documents whose lexical and compositional habits are absent from training. Eighty-four formulas remained evaluable with at least two in-vocabulary components; one Huizhai formula did not.

[[TABLE:3]]

[[FIGURE:2]]

### A directed material graph carries the cross-document gain

At the registered 50% observation fraction, the global-frequency baseline reached source-macro hidden-component F1 0.339 and weighted Jaccard 0.379. Weighted Jaccard measures the fraction of total formula mass shared by the reference and prediction. The directed graph reached F1 0.365 and weighted Jaccard 0.388. The locked full decoder reached F1 0.366 and weighted Jaccard 0.387 (Fig. 3; Tables 4 and 5). Its mean work-level F1 difference from frequency was 0.0278. Four of five work groups improved; the source-bootstrap interval was [0.0079, 0.0473], while the exact five-block sign-flip test gave p = 0.125. Five independent work groups produce a coarse exact p-value grid, so the effect magnitude and cross-source pattern are the informative quantities.

The full decoder and graph-only scores were nearly identical. Their mean work-level F1 difference was 0.0010, the source-bootstrap interval was [−0.0072, 0.0100], and the exact sign-flip p-value was 0.875. Title similarity and source prevalence therefore did not add stable information after the observed ingredients reached the conditional graph. The graph is the effective model component.

Transfer varied by source. The full decoder reached hidden F1 0.443 on Liexiang Xinpu, 0.396 on Chen Xiangpu, 0.392 on the Xiangcheng compilation, 0.392 on Xiaolu Xiangpu and 0.210 on Huizhai Xiangpu (Fig. 3a; Table 5). Weighted Jaccard ranged from 0.324 to 0.446. Reporting only the pooled mean would conceal this document effect.

After freezing the decoder, we added two competitive set-completion baselines with configurations selected on the five development work splits. Formula k-nearest neighbours reached primary hidden F1 0.343 and PureSVD reached 0.334, compared with 0.365 for the directed graph (Fig. 4a; Table 4). The graph exceeded formula k-nearest neighbours by 0.0223 F1 and PureSVD by 0.0311 at the work level. Formula k-nearest neighbours produced the highest weighted Jaccard, 0.443, because it fixed supplied ratios and interpolated neighbour compositions. Applying the same mass constraint to the full decoder increased weighted Jaccard from 0.387 to 0.427 without changing its selected materials.

Nine formulas had aromatic material-set Jaccard at least 0.8 with a formula from another work group. Removing all nine reduced graph F1 to 0.348 and frequency F1 to 0.322; the graph retained a 0.0259 work-level advantage (Fig. 4b). High-similarity transmission therefore raises absolute performance but does not account for the graph-frequency ordering.

[[TABLE:4]]

[[TABLE:5]]

[[FIGURE:3]]

[[FIGURE:4]]

### Context amount changes the residual task

When 25% of a formula was observed, graph-only reached hidden F1 0.391, compared with 0.381 for frequency and 0.383 for the full decoder. At 50%, the values were 0.365, 0.339 and 0.366. At 75%, they were 0.245, 0.232 and 0.244 (Fig. 5a; Table 6). Every value uses the same formula-first, work-second and equal-work macro aggregation as the primary analysis. Hidden F1 falls as the observed fraction rises because the remaining labels form a smaller and harder residual set. At the sparsest 25% context, graph-only beat the full decoder in all five work groups. The full model's extra channels dilute the strongest signal when little context is available.

Training frequency set a sharp recovery frontier. Hidden-material recall was 0.573 for materials appearing in at least five training formulas, 0.056 for those appearing two to four times, 0.023 for singletons and zero for out-of-vocabulary materials (Fig. 5b). The model most often overpredicted sandalwood, borneol, musk, agarwood and clove. Frequent misses included scrophularia root, spikenard, zhan-grade agarwood, frankincense and clove. Across five deterministic masks, the mean Jaccard similarity between predicted sets was 0.644. The error profile points to data coverage, not decoder depth, as the present performance ceiling.

[[TABLE:6]]

[[FIGURE:5]]

### Uncertainty outputs are informative but high probabilities remain overconfident

Across 95,210 hidden candidate decisions, the locked decoder produced a Brier score of 0.0429 and expected calibration error of 0.0236 [15]. Those aggregate values are dominated by the large low-probability class. The reliability curve shows close agreement below probability 0.3 and increasing overconfidence above 0.4; the highest bin had mean probability 0.931 and empirical inclusion frequency 0.565 (Fig. 6a; Table 7).

The formula-size posterior underestimated total ingredient count by 0.883 materials on average. Its mean absolute error was 1.190, and the nominal central 80% interval covered 64.2% of true counts. Work-held-out development residuals set a one-material expansion without accessing primary labels. The expanded interval covered 82.5% in primary evaluation, while mean width increased from 1.24 to 2.86 materials (Fig. 4c; Table 7). Conditional on both the selected set and correct material selection, the central 80% interval from the residual-scaled Dirichlet distribution covered 91.2% of reference ratios. The selected set contained 63.1% of all true components. Inclusion probabilities were accurate at low scores, count uncertainty required calibration and ratio intervals were conservative after correct selection.

[[TABLE:7]]

[[FIGURE:6]]

### Chemistry tests separate similarity from co-formulation

Ratio estimation uses compositional-data geometry [19], compounds use radius-2, 2,048-bit Morgan fingerprints [20], and the implementation uses scikit-learn [21]. The chemical evidence layer links 18 of 81 materials to 18 specimen-level analytical profiles drawn from 17 publications [22-38] and 40 PubChem compounds. Each profile retains taxon, plant part, preparation, analytical method and measurement basis. The model also includes physicochemical descriptors and controlled odor tags. A pairwise kernel combines fingerprint Tanimoto similarity, positive physicochemical cosine similarity and positive odor-tag cosine similarity.

The best chemistry-enabled primary-task variant reached development F1 0.3905, compared with 0.3911 for the selected non-chemistry variant. Chemistry was therefore disabled before primary evaluation. The auxiliary odor-to-formula task used 44 legacy formulas and nested leave-one-family-out validation. Odor k-nearest neighbors reached pooled weighted Jaccard 0.2913. The forward-consistent model reached 0.2824, its no-chemistry ablation 0.2835 and shuffled chemistry 0.2863. Pairwise chemical resemblance did not encode historical co-formulation. Similar materials can substitute for one another, while formulas often combine chemically dissimilar materials for contrast, volatility control or processing behavior.

### Quarantined-source confirmation reproduces the ranking

After the model and analysis code were frozen, all 85 development formulas were used to predict the six Hong-source formulas. At 50% observed context, frequency reached hidden F1 0.469, graph-only 0.558 and the full decoder 0.577 (Fig. 6b). Weighted Jaccard values were 0.420, 0.456 and 0.468. The full decoder exceeded frequency by 0.108 F1 across the six formulas. These records share one work group, so they confirm transfer to a new source without adding a sixth independent block to the primary inference.

A fixed case-selection rule chose the seed-17 confirmation formula closest to the six-formula median hidden F1. For *Yinxiang fa*, six of eleven reference materials were observed. The decoder recovered zhan-grade agarwood, borneol and sandalwood; it missed frankincense and licorice and added clove and linglingxiang. Ingredient count was exact, hidden F1 was 0.600 and mass-constrained weighted Jaccard was 0.483 (Table 8). This case shows the intended use of the ranking and its current failure mode: common structural partners are recoverable, while low-frequency components remain difficult.

[[TABLE:8]]

### The complete model runs on ordinary hardware

Training the locked decoder on all 85 development formulas and 80 materials took a median 0.115 s across 11 serial repetitions on an Apple arm64 system. A prediction with 200 posterior samples took 1.70 ms. The interquartile ranges were 5.28 ms for fitting and 0.14 ms for prediction. The conditional graph uses dense O(NM²) construction in the reference implementation, although sparse hyperedge accumulation reduces this to O(Σᵢ|Sᵢ|²). With D decoder features and R training masks, logistic fitting uses RNM candidate rows and O(RNMD) work per objective evaluation. The small-data design keeps the full pipeline reproducible on a laptop.

## Discussion

Historical formula completion is tractable when partial ingredients survive and related source traditions provide repeated material structure. The directed graph improved hidden-component F1 over frequency across four of five work groups, exceeded formula-neighbour and low-rank baselines, survived removal of nine high-similarity formulas and reproduced its ordering on the Hong confirmation source. Conditional co-formulation is the transferable signal. Generic text features and the tested chemical kernel added no stable gain.

The model's strongest feature is also its simplest. For every observed material, the graph estimates a smoothed conditional distribution over candidate partners using training formulas only. Averaging these directed conditionals captures asymmetric recipe logic. Musk may strongly predict a common base material even when the reverse conditional is weaker. Bayesian multi-label models have previously exploited label co-occurrence under sparse supervision [13]; Xiangji places that principle inside a document-held-out historical benchmark and joins it to explicit formula-size and composition uncertainty models. The source-blocked protocol follows the machine-learning requirement that deployment domains remain outside training data [14]. Each historical work defines a domain in this study.

The negative chemistry result sharpens the theory. Molecular odor models [4-8] and blend predictors [9] learn perceptual similarity or descriptor response. Historical ingredient pairing is a complementarity relation. A sandalwood base and a volatile top note may be valuable together because they differ in molecular composition and evaporation behavior. The symmetric kernel collapses substitution and complementarity into one number. A stronger chemistry-aware model should represent directed functional roles and interactions: base versus modifier, volatility ordering, combustion products, odor thresholds and nonlinear mixture suppression. It should train against new formula sources or physical measurements, leaving the present confirmation work untouched.

The task also differs from two adjacent forms of olfactory reconstruction. GC-MS/O can recover odor-active compounds when a physical residue survives [3]. Descriptor-to-mixture optimization can design a modern scent that matches a requested profile [10]. Xiangji completes a recorded material formula from documentary structure. Its output is a candidate formula completion; sensory identity requires analytical and panel validation. The task is computationally testable because known formulas can be masked and transferred across sources.

## Limitations

The corpus has five primary source blocks, one confirmation block and a long tail of materials supported by one or two formulas. One curator performed the current canonicalization; independent recuration is needed to measure label stability. The model has no combustion or sensory measurements, and the evaluated task assumes that part of the ingredient set is known. A second release should add independently annotated work groups, controlled burn-headspace profiles and ranked expert judgments. Those additions would support full text-to-candidate reconstruction while preserving the current benchmark.

## Conclusion

This study establishes a computational baseline for historical-formulation research. It provides the dataset structure, leakage controls, uncertainty decomposition and negative controls needed to compare stronger models. Across source shift, learned recipe relations carry usable information, while chemical similarity must be modeled as interaction before it can guide historical ingredient pairing.

## Data availability

The curated formula reference, source locators, source-blocked splits, material ontology, compound-evidence registry, frozen experiment outputs and figure source tables are included in the project repository at https://github.com/HongbaiJoe/xiangji-incense-reconstruction-lab on the `research/xiangji-cgir-paper` branch. Historical transcriptions remain subject to their recorded source terms; the dataset stores revision URLs and rights metadata for each record.

## Code availability

Model, evaluation, figure-generation and audit code is available in the same repository and branch. The repository includes a locked environment, deterministic seeds, Make targets and automated tests. An archival DOI will be added before journal submission.

## Acknowledgements

[Add verified funding and acknowledgements, or state that the work received no specific funding.]

## Author contributions

[Insert author initials and verified CRediT contributions before submission.]

## Competing interests

[Insert the authors' verified competing-interest declaration before submission.]

## References

1. Bembibre, C. & Strlič, M. Smell of heritage: a framework for the identification, analysis and archival of historic odours. *Herit. Sci.* **5**, 2 (2017). https://doi.org/10.1186/s40494-016-0114-1
2. Lisena, P. *et al.* Capturing the semantics of smell: the Odeuropa data model for olfactory heritage information. In *The Semantic Web* 387-405 (Springer, 2022). https://doi.org/10.1007/978-3-031-06981-9_23
3. Paolin, E. *et al.* A systematic approach to the scientific reproduction of historical smells: case study of a 20th-century perfume flask. *npj Herit. Sci.* (2026). https://doi.org/10.1038/s40494-026-02699-x
4. Lee, B. K. *et al.* A principal odor map unifies diverse tasks in olfactory perception. *Science* **381**, 999-1006 (2023). https://doi.org/10.1126/science.ade4401
5. Gutiérrez, E. D., Dhurandhar, A., Keller, A., Meyer, P. & Cecchi, G. A. Predicting natural language descriptions of mono-molecular odorants. *Nat. Commun.* **9**, 4979 (2018). https://doi.org/10.1038/s41467-018-07439-9
6. Keller, A. *et al.* Predicting human olfactory perception from chemical features of odor molecules. *Science* **355**, 820-826 (2017). https://doi.org/10.1126/science.aal2014
7. Debnath, T., Prasetyawan, D. & Nakamoto, T. Predicting odor perception of mixed scent from mass spectrometry. *J. Electrochem. Soc.* **168**, 117505 (2021). https://doi.org/10.1149/1945-7111/ac33e0
8. Hamel, E. A. *et al.* Pyrfume: a window to the world's olfactory data. *Sci. Data* **11**, 1220 (2024). https://doi.org/10.1038/s41597-024-04051-z
9. Sisson, L., Barsainyan, A. A., Sharma, M. & Kumar, R. Deep learning for odor prediction on aroma-chemical blends. *ACS Omega* **10**, 8980-8992 (2025). https://doi.org/10.1021/acsomega.4c07078
10. Aleixandre, M., Prasetyawan, D. & Nakamoto, T. Automatic scent creation by cheminformatics method. *Sci. Rep.* **14**, 31284 (2024). https://doi.org/10.1038/s41598-024-82654-7
11. Sorbi, M., Moccozet, L. & Marchand-Maillet, S. Weakly supervised named entity recognition for historical texts. In *Proceedings of the 10th Joint SIGHUM Workshop* 48-65 (ACL, 2026). https://doi.org/10.18653/v1/2026.latechclfl-1.6
12. Goel, M. *et al.* Deep learning based named entity recognition models for recipes. In *Proceedings of LREC-COLING 2024* 4542-4554 (ELRA and ICCL, 2024).
13. Zhao, H., Rai, P., Du, L. & Buntine, W. Bayesian multi-label learning with sparse features and labels, and label co-occurrences. *Proc. Mach. Learn. Res.* **84**, 1943-1951 (2018).
14. Koh, P. W. *et al.* WILDS: a benchmark of in-the-wild distribution shifts. *Proc. Mach. Learn. Res.* **139**, 5637-5664 (2021).
15. Guo, C., Pleiss, G., Sun, Y. & Weinberger, K. Q. On calibration of modern neural networks. *Proc. Mach. Learn. Res.* **70**, 1321-1330 (2017).
16. Cover, T. M. & Hart, P. E. Nearest neighbor pattern classification. *IEEE Trans. Inf. Theory* **13**, 21-27 (1967). https://doi.org/10.1109/TIT.1967.1053964
17. Cremonesi, P., Koren, Y. & Turrin, R. Performance of recommender algorithms on top-N recommendation tasks. In *Proceedings of the Fourth ACM Conference on Recommender Systems* 39-46 (ACM, 2010). https://doi.org/10.1145/1864708.1864721
18. Angelopoulos, A. N. & Bates, S. Conformal prediction: a gentle introduction. *Found. Trends Mach. Learn.* **16**, 494-591 (2023). https://doi.org/10.1561/2200000101
19. Aitchison, J. The statistical analysis of compositional data. *J. R. Stat. Soc. B* **44**, 139-160 (1982). https://doi.org/10.1111/j.2517-6161.1982.tb01195.x
20. Rogers, D. & Hahn, M. Extended-connectivity fingerprints. *J. Chem. Inf. Model.* **50**, 742-754 (2010). https://doi.org/10.1021/ci100050t
21. Pedregosa, F. *et al.* Scikit-learn: machine learning in Python. *J. Mach. Learn. Res.* **12**, 2825-2830 (2011).
22. Ngan, T. T. K. *et al.* Chemical components of agarwood (*Aquilaria crassna*) essential oils grown in various regions of Asia. *Asian J. Chem.* **32**, 36-40 (2020). https://doi.org/10.14233/ajchem.2020.22177
23. Fatima, T. *et al.* Assessment of morphological and genetic variability through genic microsatellite markers for essential oil in sandalwood (*Santalum album* L.). *3 Biotech* **9**, 252 (2019). https://doi.org/10.1007/s13205-019-1758-9
24. Di Stefano, V., Schillaci, D., Cusimano, M. G., Rishan, M. & Rashan, L. In vitro antimicrobial activity of frankincense oils from *Boswellia sacra* grown in different locations of the Dhofar region. *Antibiotics* **9**, 195 (2020). https://doi.org/10.3390/antibiotics9040195
25. Ben Hassine, D. *et al.* Clove buds essential oil: the impact of grinding on the chemical composition and its biological activities involved in consumer health security. *BioMed Res. Int.* **2021**, 9940591 (2021). https://doi.org/10.1155/2021/9940591
26. Firmino, D. F. *et al.* Antibacterial and antibiofilm activities of *Cinnamomum* sp. essential oil and cinnamaldehyde. *Sci. World J.* **2018**, 7405736 (2018). https://doi.org/10.1155/2018/7405736
27. Hu, Q.-P., Cao, X.-M., Hao, D.-L. & Zhang, L.-L. Chemical composition and biological activities of *Cyperus rotundus* rhizome essential oil. *Sci. Rep.* **7**, 45231 (2017). https://doi.org/10.1038/srep45231
28. Han, X., Beaumont, C. & Stevens, N. Chemical composition analysis and in vitro biological activities of ten essential oils in human skin cells. *Biochim. Open* **5**, 1-7 (2017). https://doi.org/10.1016/j.biopen.2017.04.001
29. Hu, D. *et al.* Comparison and identification of the aroma-active compounds in the root of *Angelica dahurica*. *Molecules* **24**, 4352 (2019). https://doi.org/10.3390/molecules24234352
30. Andola, H. C., Lohani, H., Chauhan, N., Gwari, G. & Bhandari, U. Volatile constituents of *Saussurea costus* roots cultivated in the Uttarakhand Himalayas. *Pharmacogn. Res.* **5**, 179 (2013). https://doi.org/10.4103/0974-8490.112424
31. Zou, L. *et al.* Comparison of chemical profiles between synthetic borneol and natural borneol. *Molecules* **22**, 1446 (2017). https://doi.org/10.3390/molecules22091446
32. Li, D. *et al.* The musk chemical composition and microbiota of Chinese forest musk deer males. *Sci. Rep.* **6**, 18975 (2016). https://doi.org/10.1038/srep18975
33. Xue, G. Q. *et al.* Chemical constituents of *Scrophularia ningpoensis* root. *Zhong Yao Cai* **37**, 1597-1599 (2014). https://pubmed.ncbi.nlm.nih.gov/25857160/
34. Farag, M. A. & Wessjohann, L. A. Volatiles profiling in medicinal licorice roots using steam distillation and solid-phase microextraction coupled to chemometrics. *J. Food Sci.* **77** (2012). https://doi.org/10.1111/j.1750-3841.2012.02927.x
35. Fernandez, X. *et al.* Chemical composition of the essential oils from Turkish and Honduras *Styrax*. *Flavour Fragr. J.* **20**, 70-73 (2005). https://doi.org/10.1002/ffj.1370
36. Raza, M. H. *et al.* Comparative study of *Foeniculum vulgare* seed oils obtained by three distillation methods. *Food Sci. Nutr.* **12**, 10535-10549 (2024). https://doi.org/10.1002/fsn3.4593
37. Guo, S. *et al.* The chemical composition of essential oils from *Cinnamomum camphora*. *Int. J. Mol. Sci.* **17**, 1836 (2016). https://doi.org/10.3390/ijms17111836
38. Miyazawa, M., Minamino, Y. & Kameoka, H. Volatile components of the rhizomes of *Rheum palmatum* L. *Flavour Fragr. J.* **11**, 57-60 (1996). https://doi.org/10.1002/(SICI)1099-1026(199601)11:1%3C57::AID-FFJ549%3E3.0.CO;2-K
