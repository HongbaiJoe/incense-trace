"""Create a deterministic median-performance confirmation case study."""

from __future__ import annotations

import csv
import gzip
import json

import numpy as np

from xiangji.data import RESEARCH_ROOT


def build() -> dict:
    raw = json.loads(gzip.decompress((RESEARCH_ROOT / "experiments/cycle4_hong_records.json.gz").read_bytes()))
    seed_run = next(
        row for row in raw["results"]["full_no_chemistry"]["seed_runs"] if row["seed"] == 17
    )
    evaluated = [row for row in seed_run["records"] if row["status"] == "evaluated"]
    median_f1 = float(np.median([row["metrics"]["hidden_f1"] for row in evaluated]))
    case = min(evaluated, key=lambda row: (abs(row["metrics"]["hidden_f1"] - median_f1), row["reference_id"]))

    reference = json.loads((RESEARCH_ROOT / "data/curated/formula_reference_v0.1.json").read_text())
    record = next(row for row in reference["records"] if row["reference_id"] == case["reference_id"])
    ontology = json.loads((RESEARCH_ROOT / "ontology/materials_v0.1.json").read_text())
    labels = {row["id"]: row["label_zh"] for row in ontology["entities"]}
    predicted = {row["material_id"]: row for row in case["selected_materials"]}
    observed = set(case["observed_materials"])
    truth = set(record["composition_aromatic_only"])
    hidden_predicted = [material for material in predicted if material not in observed]
    hidden_total = sum(predicted[material]["posterior_mean_ratio"] for material in hidden_predicted)
    remaining_mass = 1.0 - sum(case["observed_materials"].values())
    constrained_ratios = dict(case["observed_materials"])
    constrained_ratios.update({
        material: remaining_mass * predicted[material]["posterior_mean_ratio"] / hidden_total
        for material in hidden_predicted
    })
    metric_support = sorted(truth | set(constrained_ratios))
    truth_vector = np.asarray([record["composition_aromatic_only"].get(material, 0.0) for material in metric_support])
    predicted_vector = np.asarray([constrained_ratios.get(material, 0.0) for material in metric_support])
    constrained_weighted_jaccard = float(np.minimum(truth_vector, predicted_vector).sum() / np.maximum(truth_vector, predicted_vector).sum())
    rows = []
    for material in sorted(truth | set(predicted)):
        if material in observed:
            outcome = "observed input"
        elif material in truth and material in predicted:
            outcome = "recovered hidden"
        elif material in truth:
            outcome = "missed hidden"
        else:
            outcome = "false positive"
        prediction = predicted.get(material)
        rows.append({
            "material_id": material,
            "label_zh": labels.get(material, ""),
            "outcome": outcome,
            "reference_ratio": record["composition_aromatic_only"].get(material, 0.0),
            "predicted_ratio": None if prediction is None else constrained_ratios[material],
            "inclusion_probability": None if prediction is None else prediction["inclusion_probability"],
        })

    source_counts = {}
    source_pages = {}
    for item in reference["records"]:
        source_counts[item["work_id"]] = source_counts.get(item["work_id"], 0) + 1
        source_pages.setdefault(item["work_id"], set()).add(item["source"]["page_title"])
    source_rows = [
        {
            "work_id": work,
            "formula_count": source_counts[work],
            "source_pages": "; ".join(sorted(source_pages[work])),
        }
        for work in sorted(source_counts)
    ]
    return {
        "schema_version": "0.1",
        "selection_rule": "seed 17 confirmation formula with hidden F1 closest to the six-formula median; reference ID breaks ties",
        "seed": 17,
        "median_hidden_f1": median_f1,
        "reference_id": record["reference_id"],
        "formula_title_verbatim": record["formula_title_verbatim"],
        "work_id": record["work_id"],
        "source": record["source"],
        "observed_materials": case["observed_materials"],
        "metrics": case["metrics"],
        "mass_constrained_weighted_jaccard": constrained_weighted_jaccard,
        "ratio_output": "observed ratios fixed; hidden ratios closed to remaining mass",
        "material_rows": rows,
        "source_rows": source_rows,
    }


def main() -> None:
    result = build()
    output = RESEARCH_ROOT / "experiments" / "cycle6_case_study.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    table_dir = RESEARCH_ROOT / "manuscript" / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    with (table_dir / "table8_case_study.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result["material_rows"][0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(result["material_rows"])
    with (table_dir / "table9_source_mapping.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result["source_rows"][0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(result["source_rows"])
    print(json.dumps({
        "output": str(output),
        "reference_id": result["reference_id"],
        "title": result["formula_title_verbatim"],
        "hidden_f1": result["metrics"]["hidden_f1"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
