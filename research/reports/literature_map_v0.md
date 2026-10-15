# Literature map and novelty boundary v0

Search date: 2026-09-06. Initial queries covered inverse scent design, odor-mixture prediction, molecular structure–odor learning, historical entity resolution, recipe information extraction and conformal multilabel prediction. This is a seed map; Cycle 2 expands it into a screened, deduplicated review with a query log and citation graph.

## Closest prior art

| Work | Input → output | Main method | Consequence for Xiangji-CGIR |
|---|---|---|---|
| Aleixandre, Prasetyawan & Nakamoto (2024), *Automatic scent creation by cheminformatics method* | desired odor descriptors → essential-oil component ratios | mass spectra, NMF odor components, DNN forward model, gradient search, sensory test | Directly establishes descriptor-to-mixture inverse design. Xiangji cannot claim that task as new. |
| Sisson et al. (2025), *Deep Learning for Odor Prediction on Aroma-Chemical Blends* | two molecular graphs → blend descriptors | permutation-invariant GNN variants | Establishes nonlinear blend prediction and mixture embeddings, but not historical-text-conditioned inverse recovery. |
| Lee et al. (2023), *A Principal Odor Map Unifies Diverse Tasks in Olfactory Perception* | molecular graph → perceptual embedding/descriptors | message-passing GNN and prospective panel validation | Supplies a defensible molecular odor representation; does not solve multi-material historical formula inference. |
| Hamel et al. (2024), *Pyrfume* | heterogeneous olfactory datasets → unified archive | standardized data model and curation | Candidate source for material/molecule/descriptor evidence; provenance and license must be preserved per archive. |
| Gutiérrez et al. (2018) | molecular features → natural-language odor descriptions | semantic and psychophysical prediction | Motivates explicit descriptor semantics and exposes label heterogeneity. |
| Sorbi, Moccozet & Marchand-Maillet (2026) | low-resource historical text → entities | weakly supervised historical NER | Supports dictionary/weak-supervision extraction, while emphasizing noisy and incomplete distant labels. |
| Contrastive Entity Coreference and Disambiguation for Historical Texts (2024) | historical mentions → linked/cross-document entities | bi-encoder retrieval, hard negatives, coreference | Supports treating historical material names as retrieval/disambiguation variables rather than fixed string replacements. |
| Goel et al. (2024), *Deep Learning Based Named Entity Recognition Models for Recipes* | recipe phrases → ingredient, quantity, unit and state entities | supervised NER plus augmented annotations | Provides extraction baselines, though modern food recipes differ strongly from literary Chinese incense formulas. |
| Tyagi & Guo (2023) | multilabel scores → prediction sets | split conformal inference with hierarchical testing | Supports uncertainty sets for candidate ingredients; exchangeability assumptions must be reconciled with document shift. |

## Novelty boundary

The defensible paper is not “AI generates an incense recipe from an odor description.” That has close prior art. The candidate contribution is a new low-resource structured-inference problem and method:

> infer a sparse, simplex-valued historical formulation from incomplete literary evidence while marginalizing historical-name ambiguity, constraining candidates with molecular/odor structure, and evaluating under source shift.

Four candidate contributions are retained for testing:

1. **Task and benchmark:** provenance-preserving historical formula recovery with formula-family and document-held-out splits.
2. **Latent lexical inference:** probabilistic canonicalization of historically unstable material names, learned jointly or marginalized during formula prediction.
3. **Chemistry-guided structured decoder:** a permutation-invariant ingredient-set decoder coupled to a composition distribution and a nonlinear forward-odor consistency term.
4. **Set-valued reconstruction:** calibrated alternative formulas that expose non-identifiability rather than returning one unsupported point estimate.

Claims 2–4 survive only if source-held-out ablation studies show material gains. If they do not, the paper pivots to a dataset/benchmark contribution with strong baselines.

## Formal problem statement

Let historical text and metadata be \(x,s\); canonical materials be \(m=1,\ldots,M\); ambiguous mention assignments be latent \(z\); selected ingredients be \(S\); and mixture weights \(w\in\Delta^{M-1}\). Molecular and odor evidence defines material representations \(C\), while a historical recipe hypergraph is \(G\). The target is

\[
p(S,w,z\mid x,s,C,G) \propto p_\theta(S,w\mid x,s,z,C,G)\,p(z\mid x,s)\,\exp[-\lambda d(F_C(w),\hat{o}(x))].
\]

Here \(F_C\) is a learned or hybrid chemical-to-odor forward model and \(\hat{o}(x)\) is the descriptor distribution supported by the historical passage. The energy term narrows chemically inconsistent solutions but does not assert that odor mixtures are linearly additive.

## Sources verified in this seed map

- Aleixandre, M., Prasetyawan, D. & Nakamoto, T. Scientific Reports 14, 31284 (2024). DOI: 10.1038/s41598-024-82654-7.
- Sisson, L. et al. ACS Omega (2025). DOI: 10.1021/acsomega.4c07078.
- Lee, B. K. et al. Science 381, 999–1006 (2023). DOI: 10.1126/science.ade4401.
- Hamel, E. A. et al. Scientific Data 11, 1220 (2024). DOI: 10.1038/s41597-024-04051-z.
- Gutiérrez, E. D. et al. Nature Communications 9, 4979 (2018). DOI: 10.1038/s41467-018-07439-9.
- Keller, A. et al. Science 355, 820–826 (2017). DOI: 10.1126/science.aal2014.
- Debnath, T., Prasetyawan, D. & Nakamoto, T. Journal of The Electrochemical Society 168, 117505 (2021). DOI: 10.1149/1945-7111/ac33e0.
- Thomas-Danguin, T. et al. Frontiers in Psychology 5, 504 (2014). DOI: 10.3389/fpsyg.2014.00504.
- Sorbi, M., Moccozet, L. & Marchand-Maillet, S. SIGHUM/LaTeCH-CLfL 2026, 48–65 (2026).
- Goel, M. et al. LREC-COLING 2024, paper 406 (2024).
- Tyagi, C. & Guo, W. PMLR 204, 488–512 (2023).
