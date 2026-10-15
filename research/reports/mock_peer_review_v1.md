# Mock peer review v1

## Review setup

- **Input scope:** complete manuscript v1, supplementary information, five main figures, seven source tables, curated data and frozen Cycle 3–5 experiment artifacts.
- **Assessment boundary:** this review tests readiness for *npj Heritage Science*. It does not assume access to author identity, funding statements, laboratory measurements or independent annotations that are absent from the repository.
- **Shared claim:** a directed material co-formulation graph can complete partially observed historical Chinese incense formulas across held-out work groups, while source, title and pairwise chemical-similarity channels add no stable improvement.
- **Visible evidence:** 91 curated formulas from six work groups; ten two-work-held-out primary folds over five work groups and five masks; one six-formula confirmation work; ablations, negative controls, calibration, rarity analysis and reproducible code.
- **Missing materials affecting readiness:** independent curation agreement, modern set-completion baselines, explicit cross-work near-duplicate sensitivity, and completed author declarations.

## Reviewer 1

- **Emphasis:** technical soundness and statistical design.
- **Overall assessment:** The source-blocked design is stronger than a random formula split and the training-only graph construction closes the main leakage path. The present comparison set is too weak for the central computer-science claim, and the count posterior is demonstrably miscalibrated.
- **Who would be interested:** researchers in digital heritage, sparse multi-label prediction, recipe informatics and computational olfaction would use the benchmark design and provenance schema.
- **Major strengths:** work-level blocking, deterministic masks, formula-level averaging before source-level inference, a quarantined confirmation source, synthetic recovery and a semantic chemistry negative control.
- **Recommendation posture:** major revision before submission.

### R1-M1

- **Axis:** experimental design
- **Claim pointer:** the directed graph is the effective transferable model component.
- **Evidence pointer:** Results, A directed material graph carries the cross-document gain; Methods, Model selection baselines and negative controls.
- **Concern and resolution test:** Frequency, source, title and graph ablations do not represent competitive set-completion methods. Add at least one formula-nearest-neighbour baseline and one low-rank collaborative baseline. Lock their hyperparameters on development work splits, run the unchanged primary protocol and report every result.

### R1-M2

- **Axis:** statistical rigor
- **Claim pointer:** the model produces count and composition posteriors.
- **Evidence pointer:** Results, Posterior outputs are useful but high probabilities remain overconfident; reported 80% count coverage 64.2%.
- **Concern and resolution test:** Calling the count output a usable posterior requires either calibrated coverage or a direct failure label. Add training-only conformal recalibration for the count interval or remove any implication that its nominal level is reliable. Evaluate coverage and width under the same source-blocked protocol.

### R1-M3

- **Axis:** data resource quality
- **Claim pointer:** family-unique records and source blocking prevent textual and compositional leakage.
- **Evidence pointer:** Methods, Corpus construction and provenance; Supplementary Note 1; family audit artifact.
- **Concern and resolution test:** The manuscript does not quantify cross-work near-duplicates that survived family consolidation. Compute title and material-set similarity between each test formula and its training pool, rerun primary metrics after excluding high-similarity cases and release the flagged pairs.

### R1-m1

- **Axis:** reproducibility
- **Claim pointer:** the full pipeline is reproducible on a laptop.
- **Evidence pointer:** Methods, Software and computational profiling.
- **Concern and resolution test:** A timing result is useful, but a clean-environment command and machine-readable run report are still required. Execute the documented pipeline from a fresh environment and record commands, versions, hashes and exit status.

## Reviewer 2

- **Emphasis:** originality and scientific importance.
- **Overall assessment:** The paper asks an original heritage-informatics question and makes the valuable distinction between substitution similarity and historical complementarity. Its strongest contribution is the source-shifted task and evaluation protocol, not the logistic decoder itself.
- **Who would be interested:** heritage scientists working without surviving residues, historians of material culture and machine-learning researchers studying small, shifted, long-tailed data.
- **Major strengths:** a precise task definition, provenance at the record level, a direct comparison with residue-based smell reconstruction and an interpretable negative chemistry result.
- **Recommendation posture:** promising after the novelty claim and evidence hierarchy are tightened.

### R2-M1

- **Axis:** novelty and significance
- **Claim pointer:** Xiangji-CGIR makes four contributions, including a probabilistic graph decoder.
- **Evidence pointer:** final Introduction paragraph; Discussion paragraph on Bayesian multi-label learning.
- **Concern and resolution test:** The graph and Gaussian-prior logistic components are established methods. State the methodological novelty as their task-specific integration with masked count and composition inference under source shift. Demonstrate that the benchmark changes conclusions relative to random splitting or explain why no random-split comparison is needed.

### R2-M2

- **Axis:** claim moderation
- **Claim pointer:** pairwise chemical resemblance did not encode historical co-formulation.
- **Evidence pointer:** Results, Chemistry tests separate similarity from co-formulation; chemical layer with 18 profiled materials.
- **Concern and resolution test:** The result rejects this kernel on this coverage, not chemistry-aware reconstruction broadly. Retain the present bounded wording throughout the abstract, Results and Discussion, and add the 18-of-81 representation coverage directly to the Results.

### R2-M3

- **Axis:** data resource quality
- **Claim pointer:** the dataset provides a provenance-rich reference set.
- **Evidence pointer:** Methods, Corpus construction and provenance; Data availability.
- **Concern and resolution test:** A single curator made canonical identity and formula-boundary decisions. Release a blinded second-annotator sample or quantify internal recuration stability on a fixed subset. Without this, the dataset is a strong pilot reference set rather than a validated gold standard.

### R2-m1

- **Axis:** scientific importance
- **Claim pointer:** the work supports historical-formulation research.
- **Evidence pointer:** closing Discussion paragraph.
- **Concern and resolution test:** Show one complete held-out reconstruction with observed ingredients, ranked candidates, probabilities, ratios and source formula. A concrete case will connect aggregate metrics to the scholarly operation the paper claims to support.

## Reviewer 3

- **Emphasis:** interdisciplinary reach and readability.
- **Overall assessment:** The manuscript is readable and avoids inflated heritage claims. Its applied meaning remains abstract because every result is aggregated. One case-level reconstruction and a clearer explanation of what a historian can do with the output would widen its audience.
- **Who would be interested:** digital-humanities readers, conservators, historians of scent, chemoinformatics researchers and curators building structured corpora from transmitted technical texts.
- **Major strengths:** concise abstract, clear separation between residue analysis and documentary completion, interpretable workflow figure and direct reporting of failures on rare materials.
- **Recommendation posture:** moderate revision for accessibility and use-case clarity.

### R3-M1

- **Axis:** interdisciplinary readership
- **Claim pointer:** the task represents a practical scholarly operation.
- **Evidence pointer:** Introduction, task-definition paragraph; Results contain only aggregate evaluations.
- **Concern and resolution test:** Add a case study that displays the input evidence, prediction, true hidden components and model errors. Explain how the ranking narrows archival search or experimental testing without treating it as proof of historical identity.

### R3-M2

- **Axis:** writing clarity
- **Claim pointer:** the count and composition posteriors define a complete ranked reconstruction.
- **Evidence pointer:** Figure 1; Methods, Ingredient count and composition posteriors.
- **Concern and resolution test:** Explain in one plain sentence why ingredient count is modeled separately from inclusion. Define weighted Jaccard at first use in Results or point readers to its interpretation.

### R3-m1

- **Axis:** figures and tables
- **Claim pointer:** Fig. 5a presents aggregate calibration under source shift.
- **Evidence pointer:** Figure 5a and its legend.
- **Concern and resolution test:** Add bin counts to the source table and keep marker-area encoding in the legend. The generated CSV already contains the required denominator.

### R3-m2

- **Axis:** readability
- **Claim pointer:** formula and work-group names identify source-specific performance.
- **Evidence pointer:** Figure 3 and Results source paragraph.
- **Concern and resolution test:** Provide a supplementary mapping from romanized work labels to Chinese titles, edition identifiers and dates represented in the source registry.

## Cross-review synthesis

- **Consensus strengths:** The reviewers agree that source blocking, provenance, explicit masking and the distinction between documentary completion and sensory reconstruction create a credible research contribution. All three view the directed graph as interpretable and the negative chemistry result as useful when bounded to the tested kernel.
- **Consensus technical risks:** Two reviewers identify data-validation evidence as incomplete. Two require a case-level reconstruction. The most serious single issue is the lack of competitive set-completion baselines. Count-interval undercoverage is a separate statistical defect.
- **Where emphasis differs:** Reviewer 1 prioritizes benchmark validity and uncertainty calibration. Reviewer 2 locates novelty in task design and evidence integration rather than algorithmic primitives. Reviewer 3 focuses on making aggregate results usable to heritage readers.
- **Broad-interest readout:** The work has a clear interdisciplinary audience inside computational heritage and chemoinformatics. Its evidence does not support a general olfactory-reconstruction claim, and the manuscript no longer needs one.
- **Priority order:** (1) add locked modern baselines; (2) run near-duplicate sensitivity; (3) recalibrate or relabel count intervals; (4) add a full case study; (5) obtain second-curator evidence; (6) complete author fields and a clean-environment release.

## Risk and unsupported claims

- A validated gold-standard corpus is unsupported until independent curation evidence exists.
- Chemistry-wide ineffectiveness is unsupported; the experiment covers one pairwise kernel and 18 profiled materials.
- Sensory or combustion equivalence is untested and should not appear as an achieved outcome.
- A fully submission-ready package remains blocked on four author-supplied declaration fields.
