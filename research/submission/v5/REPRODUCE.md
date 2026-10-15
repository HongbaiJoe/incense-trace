# Reproduce V5

Run commands from the extracted `research` directory. Python 3.11+ and `uv` are required. `uv.lock` is included. No paid AI API is needed for training or inference.

```sh
uv sync --frozen
uv run pytest -q
uv run python -m xiangji.evaluation.v5_upgrade --audit
uv run python -m xiangji.evaluation.v5_pairing_audit
uv run python -m xiangji.evaluation.v5_upgrade
uv run python -m xiangji.evaluation.v5_weak_fixed_masks
uv run python submission/v5/build_manuscript.py
uv run python submission/v5/export_figures.py
```

The two full nested searches take considerably longer than unit tests. Experiment JSON and per-query prediction archives are provided so readers can inspect all results without rerunning training. V5 treats the existing benchmark as the prior study; nested tuning protects each current outer fold, but this is not a newly preregistered experiment.

## Files

- `data/`: archived texts, extracted records, provenance, splits, chemistry assets and curated compositions.
- `src/xiangji/models/source_stable_graph.py`: SSCL and directed-graph baseline.
- `src/xiangji/models/posterior_stable_graph.py`: exact moments, noise decomposition, unknown-retention decoder and composition projection.
- `experiments/v5_upgrade.json`: selections and per-work results for four model conditions.
- `experiments/v5_predictions.json.gz`: visible inputs and predictions for every evaluated V5 query.
- `experiments/v5_weak_fixed_masks.json`: complete nested weak-weight selection with fixed inputs.
- `reports/v5_data_audit.json`: the five data questions.
- `submission/v5/reconcile_weak.py`: exact sign-flip interval breakpoints and manuscript result replacement.
- `submission/v5/editable_figures/`: vector figure PDFs, editable TikZ and exact plotted coordinates. CSV series order follows each figure's source; categorical labels remain strings.

## Build the manuscript

Use a current TeX Live installation (XeLaTeX) or Tectonic. From `submission/v5`:

```sh
tectonic xiangji_v5.tex --keep-logs
```

The publisher class is included unchanged. Only the EPS logo include is redirected to the accompanying vector PDF for engine compatibility. All main figures are editable TikZ; none are generative illustrations. The file called `original_v4` is a preserved input, not the version to submit.

## Website

The website at the repository root includes a frozen exported model, 91 source-linked formulas, eight Python reference fixtures, a TypeScript engine, server-side validation and D1 schema migrations. From the repository root:

```sh
npm ci
npx tsc --noEmit
npm run test:engine
npm run dev
```

The optional browser QA scripts use Playwright Chromium; install Playwright and its browser separately. API tests use local fake identities exclusively. Production uses the hosting provider's trusted user identity; local integration-test fake identities must never be sent to production. Visitor database contents are excluded from this source release.

Model records saved by website visitors do not automatically become benchmark labels. Historical texts retain their source-specific rights; see each record's stable revision URL. Components and images retain separate licenses in the website source.
