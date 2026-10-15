"""Measure the locked model's small-data computational footprint."""

from __future__ import annotations

import json
import platform
from statistics import median
from time import perf_counter

import numpy as np

from xiangji.data import RESEARCH_ROOT
from xiangji.models.cgir import XiangjiCGIR
from xiangji.models.data import load_development_corpus


PROXY_MAP = {
    "agarwood_raw_resin": "agarwood",
    "agarwood_soku_grade": "agarwood",
    "agarwood_yellow_grade": "agarwood",
    "agarwood_zhan_grade": "agarwood",
    "agarwood_zhala_grade": "agarwood",
    "agarwood_qinan_grade": "agarwood",
    "clove_bark": "clove_bud",
}


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "median_seconds": float(median(values)),
        "iqr_seconds": float(np.quantile(values, 0.75) - np.quantile(values, 0.25)),
        "minimum_seconds": float(min(values)),
        "maximum_seconds": float(max(values)),
    }


def run(repetitions: int = 11) -> dict:
    if repetitions < 3:
        raise ValueError("At least three repetitions are required")
    lock = json.loads((RESEARCH_ROOT / "configs" / "model" / "xiangji_cgir_v1_locked.json").read_text())
    corpus = load_development_corpus()
    channels = set(lock["channels"])
    fit_times, prediction_times = [], []
    example = corpus.records[0]
    observed = dict(list(example.composition.items())[: max(1, len(example.composition) // 2)])
    for repetition in range(repetitions):
        start = perf_counter()
        model = XiangjiCGIR(
            random_seed=17 + repetition,
            C=lock["C"],
            group_dro_iterations=lock["group_dro_iterations"],
            graph_reducer=lock["graph_reducer"],
            chemistry_proxy_map=PROXY_MAP,
            enabled_channels=channels,
        ).fit(corpus.records)
        fit_times.append(perf_counter() - start)
        start = perf_counter()
        model.predict(
            title=example.title,
            work_id=example.work_id,
            observed=observed,
            posterior_samples=200,
            random_seed=17 + repetition,
            observation_fraction=0.5,
        )
        prediction_times.append(perf_counter() - start)
    return {
        "schema_version": "0.1",
        "model": "xiangji-cgir-v1 locked full decoder without chemistry",
        "formula_count": len(corpus.records),
        "material_vocabulary_size": len({m for row in corpus.records for m in row.composition}),
        "repetitions": repetitions,
        "posterior_samples_per_prediction": 200,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor() or "not_reported_by_platform",
            "numpy": np.__version__,
        },
        "fit_wall_time": _summary(fit_times),
        "single_prediction_wall_time": _summary(prediction_times),
        "timing_scope": "data already loaded; one process; no parallelism; wall-clock descriptive benchmark",
    }


def main() -> None:
    result = run()
    target = RESEARCH_ROOT / "experiments" / "cycle5_computational_profile.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), **result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
