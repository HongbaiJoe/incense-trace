# Xiangji V3 figure contract

## Scope

V3 preserves every numerical result and the full V2.5 manuscript text. Seven figures are redrawn into an independent `research/figures/v3` directory. V2.5 source files and artwork remain unchanged.

## Visual system

- Backend: Python and Matplotlib.
- Final width: 180 mm, white background, editable SVG and PDF, 600 dpi TIFF and PNG.
- Typography: Arial-compatible sans serif; 8 pt base text, 7.25 pt minimum at final size, 9.5 pt panel titles, and 10 pt panel letters.
- Palette: charcoal for frequency/reference, deep teal for the directed graph, cinnabar for SSCL, sage for EASE, plum for SLIM, and ochre for PPR or gold evidence.
- Legends: placed above or outside plotting regions. No legend may cover a data mark, label, interval, or bar.
- Diagrams: square-cornered or lightly rounded modules, single-direction arrows with visible endpoints, and no decorative icons.

## Figure contracts

1. **Data scale.** The evidence pipeline yields 237 model-facing records while retaining 91 reviewed formulas for evaluation. Panel a shows the exact union logic; panel b shows collection composition; panel c shows work-level weak-supervision effects.
2. **Reference corpus.** Six work groups form an imbalanced and long-tailed 91-formula benchmark. Panels show work counts, formula size, and material frequency.
3. **Model and evaluation design.** Partial-formula completion, nested work-blocked selection, and source-stable lift form one ordered computational pipeline. Every arrow represents a data or evaluation dependency.
4. **Primary performance.** Structured models improve source-macro completion relative to frequency, with heterogeneous work-level effects. Legends sit in reserved top margins.
5. **Missingness.** Model ordering depends on the observation mechanism and retained fraction. One shared legend applies to all panels.
6. **Calibration.** Nested logit calibration improves probability errors and removes unsupported high scores. Legends remain outside panels a and b.
7. **Stress tests.** Competitive baselines, duplicate removal, and interval recalibration support distinct robustness claims. Legends occupy reserved top margins.

## Integrity

All figures read the frozen V2/V2.5 experiment JSON and curated reference files. No observations, work blocks, masks, models, bins, or baselines are removed or resampled during the visual revision.
