# V2.5 figure contract

## Figure 1: corpus expansion and weak supervision

Core conclusion: the extraction pipeline increases model-facing evidence from 91 reviewed formulas to 237 records while keeping the 91-formula gold set as the sole evaluation target.

Figure archetype: quantitative grid with a schematic-led first panel.

Target output: general computer-science and cheminformatics manuscript, 180 mm width, editable SVG and PDF, 600 dpi TIFF.

Panel map:

- a: candidate-to-model evidence flow, 592 candidates to 296 ratio-ready records to 91 gold plus 146 leakage-eligible weak records.
- b: collection composition at discovery, ratio-ready, gold, and weak-eligible stages.
- c: paired work-level hidden F1 for gold-only and weak-augmented SSCL.

Evidence hierarchy: panel a establishes scale; panel b shows source balance; panel c tests whether added weak labels improve transfer.

Statistics: work means over five masks; six paired historical work groups; exact sign-flip result belongs in the legend and text.

Source data: frozen structured-candidate file, curated reference file, and nested weak-supervision result.

Integrity: no records are omitted for plotting beyond the stated genealogy and source-isolation filters; all counts are read from repository artifacts.

Primary risk: readers may equate weak records with reviewed formulas. The graphic uses separate labels and colors for gold and weak evidence.
