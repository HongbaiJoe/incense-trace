# V2 scientific design lock

Date: 2026-09-09

## Research question

Which ingredient relations remain useful when a historical incense formula is completed from work groups that differ from the target work?

## Primary estimand

The primary estimand is the unweighted mean across all six work groups of the within-work mean hidden-component F1 difference between the selected V2 method and direct global frequency at 50% observed context. Each work is held out once. Hyperparameters are selected by leave-one-work-out validation inside the remaining five works. Repeated masks are averaged before the work mean.

## Core method

The candidate method is the source-stable conditional-lift graph (SSCL). For each training work, it estimates a smoothed conditional probability of candidate material (b) given observed material (a). It subtracts the work-specific marginal log odds of (b), pools these conditional lifts with exposure weights, and penalizes between-work dispersion. A high edge score therefore requires conditional association that is supported by training observations and is not confined to one source.

The tunable terms are the beta-prior strength, heterogeneity penalty, observed-edge reducer, and marginal-prior coefficient. Inner leave-one-work-out folds select them independently for each outer test work.

## Comparator families

1. Direct global frequency.
2. Directed posterior-predictive graph.
3. Formula k-nearest neighbours.
4. PureSVD.
5. EASE with a zero diagonal.
6. Non-negative elastic-net item-item regression as a SLIM-style comparator.
7. Personalized graph diffusion.
8. The V1 Laplace-logistic decoder as a historical comparator.

## Observation mechanisms

- Uniform: deterministic sampling from the in-vocabulary ingredients.
- Abundance: higher-mass ingredients are preferentially retained by seeded weighted sampling.
- Prefix: the first ingredients in the source list are retained, which simulates a surviving list prefix.
- Unknown fraction: the observed set is generated at a sampled fraction, but the decoder uses the unconditioned count distribution.

Uniform 50% remains the primary task. All other combinations are secondary stress tests.

## Composition decision

Observed mass fractions remain fixed. The model allocates the unobserved mass among selected hidden materials. SSCL uses a development-selected mixture of training-neighbour ratios and prevalence-weighted ratios. Weighted Jaccard is secondary to hidden F1 and must be reported with it.

## Calibration

One scalar temperature rescales candidate logits. A separate temperature is fitted to inner work-held-out predictions inside each outer fold. Calibration is summarized first within formula and work, then across works. Brier score, adaptive calibration error, and the empirical inclusion frequency above probability 0.8 are reported.

## Inference

The historical work group is the independent block. The paper reports the paired work differences, their mean, and the exact two-sided sign-flip distribution. Six outer blocks still produce a coarse exact distribution. The manuscript reports estimates and their direction across works, not a result manufactured from repeated masks.

## Headline acceptance gate

SSCL becomes the main method only if all conditions hold on the primary evaluation:

- source-macro hidden F1 exceeds direct frequency;
- source-macro hidden F1 exceeds the strongest development-selected comparator;
- at least five of six work-level F1 differences versus frequency are positive;
- mass-constrained weighted Jaccard is no more than 0.01 below the best comparator.

If the gate fails, V2 is written as a benchmark study and the empirically strongest simpler method becomes the main result.

## Fixed evidence boundaries

The corpus contains 91 formulas, 81 canonical aromatic materials, and six work groups. One curator performed canonicalization. The chemistry registry contains 18 material profiles. The project contains no controlled-burn, headspace, or sensory measurements. V2 cannot use those absent observations as evidence.
