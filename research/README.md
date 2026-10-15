# Incense Trace research

The current V5 models, website export, and reproduction commands are described in [the repository overview](../README.md) and [V5 reproduction guide](submission/v5/REPRODUCE.md). The sections below preserve the historical development checkpoints, including their original dataset sizes; they are not a description of the current release alone.

## Historical checkpoints

This directory is isolated from the production website. It freezes the v2.4 generator, audits its data, and provides comparable baselines before any new model is introduced.

```bash
make -C research cycle1
```

Current evaluation labels are curated 12-dimensional odor descriptors. The 44 recipes do not yet carry document IDs or locators, so leave-one-family-out results are reported as style-family extrapolation—not cross-document validation.

## Cycle 2 data checkpoint

The research branch now also contains provenance-preserving snapshots from the 2026-09-01 Chinese Wikisource dump:

- *Xiangcheng* formula-bearing volumes 14–25;
- the two-volume *Xiangpu* traditionally attributed to Hong Chu;
- the four-volume *Chen shi xiangpu* attributed to Chen Jing.

Each snapshot records the dump byte range, SHA-256 checksum, page and revision IDs, stable revision URL, raw wikitext, rights and attribution. Run the deterministic downstream pipeline with:

```bash
make -C research cycle2-data
```

The generated 592 public-build formula records remain high-recall candidates. `ratio_ready_automatic` means only that the parser found a complete within-formula mass basis; it is not a curated-label flag. Formula-genealogy edges are retrieval candidates rather than claims of textual descent.

The Cycle 2 release adds `Xiangji Formula Reference v0.1`: 91 family-unique, revision-addressable formula records from six historical work groups. Each included record passed seven documented gates for boundary, title, materials, quantities, roles, use scope and genealogy assignment. All aromatic-only proportions are recomputed from preserved source quantities; no missing amount is imputed. The complete 120-record decision log—including 29 structured exclusions—is retained in the audit artifact. This is a two-pass review by one analyst, not independent double annotation.

```bash
make -C research curation-preflight
make -C research curated-reference
```

The compound layer stores 40 resolved PubChem structures and a pinned RDKit 2026.3.3 representation (Morgan radius 2, 2,048 bits plus molecular descriptors). Vocabulary tags do not establish that a compound occurs in a material. The first analytical evidence graph contains 18 material profiles from 17 primary studies; each edge retains its measurement type, specimen context, preparation and source locator.

Profile-level material features are frozen in three separate views: controlled odor-tag weights, molecular-set fingerprints and physicochemical descriptors. They are conditional on the compounds reported by each study; the pipeline does not pool incompatible assays or treat an incomplete GC-MS table as a complete material composition.

Source-blocked indices provide five leave-one-work-out development folds, ten primary folds with two unseen work groups, and a six-record sealed source. The bounded Cycle 2 evidence map contains 11 method papers and 17 primary analytical sources. It is explicitly not presented as a completed PRISMA review because comprehensive database hit counts were not retained.

Refresh and audit bibliographic metadata separately from the offline data build:

```bash
make -C research literature-metadata
```

## Cycle 3 model checkpoint

Cycle 3 defines two linked tasks. The primary task completes a deterministically masked historical formula under held-out-work shift. The auxiliary task maps a 12-dimensional odor profile to a composition in the provenance-limited 44-recipe legacy corpus.

```bash
make -C research cycle3-model
```

The locked primary model is selected only from five development leave-one-work-out folds and five registered mask seeds. The Hong source is quarantined from model statistics and the two-work primary folds remain unused; this is not an investigator-blinded holdout because researchers handled the Hong records during corpus construction. The model uses a directed conditional material hypergraph, a 10-parameter Gaussian-prior generalized Bayesian inclusion decoder with Laplace uncertainty, a source-smoothed count posterior, and a Dirichlet compositional posterior. Case-control prior-odds correction is applied after class-balanced fitting.

The chemistry channel is not forced into the primary model: pairwise chemical similarity did not improve development completion. In the auxiliary odor task, nested family-blocked testing likewise did not show a stable chemistry advantage over odor kNN. Both negative results are retained as part of the scientific record.

## Cycle 4 cross-source evaluation

Cycle 4 runs the frozen model on all ten two-work-held-out folds, performs source-block inference and context sensitivity, and then tests six Hong-source formulas that remained outside all model statistics.

```bash
make -C research cycle4-evaluate
```

The directed graph improves hidden-component recovery over frequency. The locked full model matches the graph ablation, so the added title and source channels do not support a separate performance claim. Inclusion probabilities remain calibrated under source shift. Ingredient count and rare-material recovery remain the main errors.

### Rights and citation

- Historical works are public domain; the Wikisource transcription is distributed under CC BY-SA 4.0. See each source manifest for revision-level attribution.
- CText-derived review candidates and transcription-bearing intermediates are excluded from the public build while scan verification and redistribution review remain open.
- PubChem records retain CID, endpoint outputs and access date. Consult the source records and [PubChem PUG REST documentation](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest).
