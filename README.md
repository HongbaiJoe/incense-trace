# Incense Trace · 香迹

**Historical incense formula reconstruction from source texts, ingredient relationships, and compositional models.**

香迹把古籍中的香方整理成可追溯的数据，根据残方中已知的香材与份量，推断可能缺失的材料和比例。本仓库包含网站、Python 模型、原始文献快照、实验结果和测试，供研究者检查与复现。

## Contents

- **Website:** 91 source-linked formulas, partial-formula reconstruction, supporting recipes, and a method overview. A separate legacy interface explores odor descriptions.
- **Models:** source-stable conditional lift (SSCL), posterior log-odds pooling, ingredient-count inference, and constrained composition projection, alongside comparison methods.
- **Data:** 592 extracted candidates, 296 ratio-ready records, 91 curated formulas across six work groups, and 146 separately evaluated weak-label records. These are overlapping stages of one corpus, not independent datasets.
- **Evaluation:** source-blocked splits, nested parameter selection, calibration, weak-supervision experiments, and query-level predictions.

The main model completes partially known ingredient lists. Odor-description retrieval is a separate task. Predicted compositions are candidates for historical investigation; experimental burning and sensory validation are not included.

## Repository map

| Path | Contents |
| --- | --- |
| `app/`, `components/`, `public/` | Website, images, fonts, downloadable paper |
| `app/research-engine.ts` | Browser inference |
| `app/data/research-model.json` | Frozen fitted graph and parameters |
| `db/`, `drizzle/`, `app/api/` | Storage schema, migrations, and API |
| `research/src/xiangji/` | Parsing, normalization, modeling, evaluation, export |
| `research/data/` | Source snapshots, provenance, formulas, chemical features |
| `research/experiments/` | Selections, metrics, prediction archives |
| `research/tests/` | Python tests |
| `research/submission/v5/` | Current paper source and editable figures |

## Website

Requires Node.js 22.13+.

```sh
npm ci
npm run dev
```

Open the local address printed by the development server.

```sh
npm test
npm run test:engine
```

The application uses React, Vinext, and Cloudflare D1. Saved-record APIs depend on a trusted hosting gateway for identity. This is a source release, not a Vercel migration: browsing and inference use bundled data, while authenticated storage requires configured D1 tables and a trusted gateway. See [runtime notes](docs/RUNTIME.md).

## Research

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```sh
cd research
uv sync --locked --group dev
uv run --locked pytest -q
```

Inspect data accounting and rerun V5 evaluation:

```sh
uv run python -m xiangji.evaluation.v5_upgrade --audit
uv run python -m xiangji.evaluation.v5_pairing_audit
uv run python -m xiangji.evaluation.v5_upgrade
uv run python -m xiangji.evaluation.v5_weak_fixed_masks
```

Nested searches take longer than unit tests. Saved outputs allow inspection without retraining. Historical release tests can regenerate reports; use a disposable checkout when comparing archived hashes.

Fit and export the operational model:

```sh
uv run python -m xiangji.export_web_model ../app/data
```

The browser consistency test compares eight Python reference predictions with TypeScript inference. See [reproduction instructions](research/submission/v5/REPRODUCE.md) and [release verification](docs/VERIFICATION.md).

## Sources and rights

Records preserve stable source links, original quantities, and normalization decisions. Wikisource transcriptions retain attribution and CC BY-SA terms; chemical snapshots retain PubChem identifiers and query metadata. A CText transcription candidate file with unresolved redistribution status is omitted; it is not used in the released reference corpus.

Images, fonts, and components have separate licenses. See [sources and rights](NOTICE.md), `licenses/`, and `public/media/hd-asset-sources.json`. Visitor accounts and submitted database records are not included.
