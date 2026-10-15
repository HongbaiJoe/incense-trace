"""Generate high-recall formula-genealogy candidates for manual adjudication."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict

from xiangji.data import RESEARCH_ROOT

VARIANTS = str.maketrans({
    "沈": "沉", "馢": "棧", "栈": "棧", "爲": "為", "蘂": "蕊", "牙": "衙",
    "眞": "真", "逺": "遠", "靣": "面", "濕": "湿", "䭱": "馥", "蘭": "兰",
})
NON_UNIQUE = {"又", "又方", "又牙香法", "又衙香法", "衙香", "龍涎香", "龙涎香", "香餅", "香饼", "香煤"}


def normalize_text(text: str) -> str:
    text = text.translate(VARIANTS)
    return re.sub(r"[^\u3400-\u9fff]", "", text)


def normalize_title(text: str) -> str:
    title = normalize_text(text)
    title = re.sub(r"(?:新方|補遺|补遗|局方|沈譜|沉譜|法|方)$", "", title)
    return title


def ngrams(text: str, n: int = 3) -> set[str]:
    if len(text) < n:
        return {text} if text else set()
    return {text[index:index + n] for index in range(len(text) - n + 1)}


def jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left | right else 0.0


def material_set(record: dict) -> set[str]:
    return set((record.get("composition_aromatic_only") or {}).keys())


def composition_cosine(left: dict, right: dict) -> float:
    left_vector = left.get("composition_aromatic_only") or {}
    right_vector = right.get("composition_aromatic_only") or {}
    keys = set(left_vector) | set(right_vector)
    if not keys:
        return 0.0
    numerator = sum(left_vector.get(key, 0.0) * right_vector.get(key, 0.0) for key in keys)
    left_norm = math.sqrt(sum(value * value for value in left_vector.values()))
    right_norm = math.sqrt(sum(value * value for value in right_vector.values()))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def should_link(left: dict, right: dict, text_similarity: float) -> tuple[bool, str | None]:
    left_title = normalize_title(left["formula_title_candidate"])
    right_title = normalize_title(right["formula_title_candidate"])
    same_title = left_title == right_title
    cross_witness = left["witness_id"] != right["witness_id"]
    generic = left_title in {normalize_title(value) for value in NON_UNIQUE}
    title_similarity = jaccard(ngrams(left_title, 2), ngrams(right_title, 2))
    left_materials, right_materials = material_set(left), material_set(right)
    material_similarity = jaccard(left_materials, right_materials)
    ratio_similarity = composition_cosine(left, right)
    if text_similarity >= 0.72:
        return True, "high_text_similarity"
    if (
        cross_witness
        and same_title
        and not generic
        and len(left_title) >= 6
        and text_similarity >= 0.12
        and (material_similarity >= 0.25 or text_similarity >= 0.45)
    ):
        return True, "cross_witness_distinctive_title"
    if (
        cross_witness
        and len(left_materials | right_materials) >= 4
        and material_similarity >= 0.85
        and ratio_similarity >= 0.94
    ):
        return True, "cross_witness_composition_similarity"
    if (
        cross_witness
        and title_similarity >= 0.60
        and material_similarity >= 0.70
        and ratio_similarity >= 0.75
    ):
        return True, "cross_witness_title_material_similarity"
    title_text_threshold = 0.55 if generic else 0.30
    if (
        cross_witness
        and same_title
        and text_similarity >= title_text_threshold
        and (material_similarity >= 0.25 or text_similarity >= 0.55)
    ):
        return True, "cross_witness_title_and_text"
    if cross_witness and text_similarity >= 0.50:
        return True, "cross_witness_text_similarity"
    if same_title and not generic and text_similarity >= 0.48:
        return True, "within_witness_variant"
    return False, None


class UnionFind:
    def __init__(self, values: list[str]):
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def build_genealogy(records: list[dict]) -> tuple[list[dict], list[dict]]:
    usable = [record for record in records if 2 <= record["aromatic_mention_count"] <= 20]
    grams = {record["candidate_id"]: ngrams(normalize_text(record["parser_text"])) for record in usable}
    union_find = UnionFind([record["candidate_id"] for record in usable])
    edges = []
    for index, left in enumerate(usable):
        for right in usable[index + 1:]:
            title_same = normalize_title(left["formula_title_candidate"]) == normalize_title(right["formula_title_candidate"])
            if left["collection"] == right["collection"] and not title_same:
                continue
            similarity = jaccard(grams[left["candidate_id"]], grams[right["candidate_id"]])
            link, reason = should_link(left, right, similarity)
            if not link:
                continue
            union_find.union(left["candidate_id"], right["candidate_id"])
            edges.append({
                "left_candidate_id": left["candidate_id"],
                "right_candidate_id": right["candidate_id"],
                "left_collection": left["collection"],
                "right_collection": right["collection"],
                "left_title": left["formula_title_candidate"],
                "right_title": right["formula_title_candidate"],
                "text_3gram_jaccard": similarity,
                "title_2gram_jaccard": jaccard(
                    ngrams(normalize_title(left["formula_title_candidate"]), 2),
                    ngrams(normalize_title(right["formula_title_candidate"]), 2),
                ),
                "material_set_jaccard": jaccard(material_set(left), material_set(right)),
                "composition_cosine": composition_cosine(left, right),
                "reason": reason,
                "status": "candidate_edge_unverified",
            })
    groups: dict[str, list[str]] = defaultdict(list)
    for record in usable:
        groups[union_find.find(record["candidate_id"])].append(record["candidate_id"])
    families = []
    for members in groups.values():
        members = sorted(members)
        family_id = "ff-" + hashlib.sha1("|".join(members).encode()).hexdigest()[:12]
        families.append({
            "formula_family_candidate_id": family_id,
            "member_candidate_ids": members,
            "member_count": len(members),
            "status": "singleton_provisional" if len(members) == 1 else "cluster_requires_adjudication",
        })
    return edges, sorted(families, key=lambda row: (-row["member_count"], row["formula_family_candidate_id"]))


def main() -> None:
    source_path = RESEARCH_ROOT / "data" / "interim" / "structured_formula_candidates_v0.1.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    edges, families = build_genealogy(source["records"])
    pair_counts = Counter(tuple(sorted((edge["left_collection"], edge["right_collection"]))) for edge in edges)
    output = {
        "schema_version": "0.1",
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "edge_count": len(edges),
        "family_candidate_count": len(families),
        "multi_member_family_count": sum(family["member_count"] > 1 for family in families),
        "largest_family_size": max(family["member_count"] for family in families),
        "edge_counts_by_collection_pair": {" + ".join(pair): count for pair, count in sorted(pair_counts.items())},
        "thresholds": {
            "high_text_similarity": 0.72,
            "cross_witness_same_non_generic_title": 0.30,
            "cross_witness_same_generic_title": 0.55,
            "cross_witness_text_similarity": 0.50,
            "within_witness_same_title": 0.48,
            "cross_witness_distinctive_title_text": 0.12,
            "cross_witness_material_set": 0.85,
            "cross_witness_composition_cosine": 0.94,
            "cross_witness_title_2gram": 0.60,
        },
        "status": "candidate genealogy only; multi-member families require manual adjudication",
        "edges": edges,
        "families": families,
    }
    target = RESEARCH_ROOT / "data" / "interim" / "formula_genealogy_candidates_v0.1.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "edges": len(edges), "families": len(families),
        "multi_member": output["multi_member_family_count"], "output": str(target),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
