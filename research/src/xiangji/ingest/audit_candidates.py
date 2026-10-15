"""Create deterministic quality-control summaries for machine-segmented formulas."""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter, defaultdict

from xiangji.data import RESEARCH_ROOT

FORMULA_MARKERS = ("香", "方", "餅", "饼", "煤", "丸", "篆", "印", "茶")
INGREDIENT_LIKE = re.compile(r"(?:　{2,}|\s{3,})")
SECTION_TITLES = {
    "香屬", "香属", "凝和諸香", "凝和诸香", "香珠", "晦齋香譜序", "晦斋香谱序",
    "陳氏香譜卷二", "陳氏香譜卷三", "陳氏香譜卷四",
}
WORK_BY_VOLUME = {
    "卷23": "huizhai_xiangpu",
    "卷24": "moe_xiaolu_xiangpu",
    "卷25": "liexiang_xinpu",
}


def title_flags(record: dict) -> list[str]:
    title = record["formula_title_candidate"]
    flags = []
    if INGREDIENT_LIKE.search(title):
        flags.append("ingredient_list_like")
    if len(title) > 18:
        flags.append("heading_note_contamination")
    if title in {"又", "又方", "又方補遺"}:
        flags.append("non_unique_title")
    if not any(marker in title for marker in FORMULA_MARKERS) and len(title) > 8:
        flags.append("weak_formula_title_signal")
    if title in SECTION_TITLES:
        flags.append("section_or_preface")
    if record["line_end"] - record["line_start"] + 1 > 20:
        flags.append("long_candidate_block")
    return flags


def infer_scope(record: dict) -> str:
    text = record["raw_wikitext"]
    title = record["formula_title_candidate"]
    if any(token in title for token in ("茶", "髮", "发", "靣脂", "面脂", "粉", "身丸", "香珠", "數珠", "数珠")):
        return "other_aromatic_preparation"
    if any(token in text for token in ("爇", "焚", "燒", "烧", "香篆", "爐", "炉")):
        return "burned_incense"
    if any(token in title for token in ("印香", "香餅", "香饼", "香煤", "線香", "线香")):
        return "likely_burned_incense"
    return "scope_unresolved"


def infer_work_id(page_title: str, collection: str) -> str:
    if collection == "zunsheng_bajian":
        return "zunsheng_bajian"
    if collection == "hong_xiangpu":
        return "hong_xiangpu_attributed"
    if collection == "chen_xiangpu":
        return "chen_xiangpu_compilation"
    volume = page_title.rsplit("/", 1)[-1]
    return WORK_BY_VOLUME.get(volume, "xiangcheng_compilation_unresolved_source")


def sample_for_review(records: list[dict], seed: int = 20260906) -> list[dict]:
    rng = random.Random(seed)
    by_page: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_page[record["page_title"]].append(record)
    sample = []
    for page in sorted(by_page):
        rows = by_page[page]
        flagged = [row for row in rows if row["qc_flags"]]
        clean = [row for row in rows if not row["qc_flags"]]
        if flagged:
            sample.append(rng.choice(flagged))
        if clean:
            sample.append(rng.choice(clean))
    return sample


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--collection",
        choices=("xiangcheng", "hong_xiangpu", "chen_xiangpu", "zunsheng_bajian"),
        default="xiangcheng",
    )
    args = parser.parse_args()
    candidate_path = RESEARCH_ROOT / "data" / "interim" / f"{args.collection}_formula_candidates.json"
    payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    records = payload["records"]
    for record in records:
        record["work_id_provisional"] = infer_work_id(record["page_title"], args.collection)
        record["qc_flags"] = title_flags(record)
        record["formula_scope_provisional"] = infer_scope(record)

    by_page = Counter(record["page_title"] for record in records)
    by_work = Counter(record["work_id_provisional"] for record in records)
    by_scope = Counter(record["formula_scope_provisional"] for record in records)
    flag_counts = Counter(flag for record in records for flag in record["qc_flags"])
    duplicate_titles = {
        title: count
        for title, count in Counter(record["formula_title_candidate"] for record in records).items()
        if count > 1
    }
    clean = [record for record in records if not record["qc_flags"]]
    report = {
        "candidate_count": len(records),
        "automatic_qc_clean_count": len(clean),
        "automatic_qc_flagged_count": len(records) - len(clean),
        "page_counts": dict(sorted(by_page.items())),
        "provisional_work_counts": dict(sorted(by_work.items())),
        "provisional_scope_counts": dict(sorted(by_scope.items())),
        "flag_counts": dict(sorted(flag_counts.items())),
        "duplicate_title_count": len(duplicate_titles),
        "duplicate_titles": dict(sorted(duplicate_titles.items())),
        "interpretation": (
            "These are high-recall machine candidates. Automatic QC is not historical validation, "
            "and unresolved Xiangcheng compilation records cannot be treated as independent works."
        ),
    }
    report_path = RESEARCH_ROOT / "reports" / f"{args.collection}_candidate_audit.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    review_path = RESEARCH_ROOT / "data" / "interim" / f"{args.collection}_review_batch_001.csv"
    fields = [
        "candidate_id", "page_title", "revision_id", "line_start", "line_end",
        "formula_title_candidate", "work_id_provisional", "qc_flags",
        "boundary_ok", "title_ok", "formula_scope", "reviewer", "review_notes",
    ]
    with review_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for record in sample_for_review(records):
            writer.writerow({
                **{key: record[key] for key in fields if key in record},
                "qc_flags": ";".join(record["qc_flags"]),
                "boundary_ok": "",
                "title_ok": "",
                "formula_scope": "",
                "reviewer": "",
                "review_notes": "",
            })
    print(json.dumps({
        "report": str(report_path),
        "review_batch": str(review_path),
        "review_rows": len(sample_for_review(records)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
