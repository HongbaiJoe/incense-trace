"""Parse material mentions and within-formula mass ratios from candidate text."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from functools import lru_cache

from xiangji.data import RESEARCH_ROOT
from xiangji.ingest.extract_candidates import ANCHOR, NOTE, OTHER_TEMPLATE, SKCHAR

CN_NUM = "零〇一二三四五六七八九十百千廿卅"
MASS_FACTORS_QIAN = {"斤": 160.0, "觔": 160.0, "兩": 10.0, "两": 10.0, "錢": 1.0, "钱": 1.0, "分": 0.1}
COUNT_UNITS = {"字", "枚", "粒", "顆", "颗", "箇", "個", "个", "朶", "朵", "撮", "升", "合", "盞", "盏"}
NUMBER_TOKEN = rf"(?:半|[{CN_NUM}]+(?:餘|余)?)"
QUANTITY = re.compile(
    rf"(?:已上|以上)?各等分|各等分|等分|"
    rf"(?:已上|以上)?各?{NUMBER_TOKEN}(?:斤|觔|兩|两|錢|钱|分|字|枚|粒|顆|颗|箇|個|个|朶|朵|撮|升|合|盞|盏)"
    rf"(?:半|(?:[{CN_NUM}]+)(?:錢|钱|分))?|少許|少许|不拘多少"
)
SKCHAR_CAPTURE = re.compile(r"\{\{SKchar\|([^{}|]+)(?:\|[^{}]*)?\}\}")
METHOD_MARKERS = (
    "右", "共為末", "共为末", "上以香料為末", "上以香料为末", "以上作末",
    "用煉蜜", "用炼蜜", "先煉蜜", "先炼蜜", "為末", "为末", "和成", "和劑",
    "和剂", "印作", "和印", "印餅", "印饼", "散用",
)


def chinese_number(text: str) -> float:
    if text == "半":
        return 0.5
    digits = {"零": 0, "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if text == "廿":
        return 20.0
    if text == "卅":
        return 30.0
    if all(char in digits for char in text):
        value = 0
        for char in text:
            value = value * 10 + digits[char]
        return float(value)
    total, current = 0, 0
    for char in text:
        if char in digits:
            current = digits[char]
        elif char == "十":
            total += (current or 1) * 10
            current = 0
        elif char == "百":
            total += (current or 1) * 100
            current = 0
        elif char == "千":
            total += (current or 1) * 1000
            current = 0
        elif char == "廿":
            total += 20
        elif char == "卅":
            total += 30
    return float(total + current)


def normalize_quantity(raw: str) -> dict:
    cleaned = raw.replace("已上", "").replace("以上", "").replace("各", "")
    applies_to_group = "各" in raw or "已上" in raw or "以上" in raw
    if "等分" in cleaned:
        return {"raw": raw, "basis": "relative_equal", "value_qian": 1.0, "applies_to_group": True}
    if cleaned in {"少許", "少许", "不拘多少"}:
        return {"raw": raw, "basis": "qualitative", "value_qian": None, "applies_to_group": applies_to_group}

    tokens = re.findall(rf"({NUMBER_TOKEN})(斤|觔|兩|两|錢|钱|分|字|枚|粒|顆|颗|箇|個|个|朶|朵|撮|升|合|盞|盏)", cleaned)
    trailing_half = cleaned.endswith("半")
    if not tokens:
        return {"raw": raw, "basis": "unparsed", "value_qian": None, "applies_to_group": applies_to_group}
    units = {unit for _, unit in tokens}
    if units & COUNT_UNITS:
        return {"raw": raw, "basis": "non_mass", "value_qian": None, "applies_to_group": applies_to_group}
    if "餘" in cleaned or "余" in cleaned:
        return {"raw": raw, "basis": "approximate_mass", "value_qian": None, "applies_to_group": applies_to_group}
    value = sum(chinese_number(number) * MASS_FACTORS_QIAN[unit] for number, unit in tokens)
    if trailing_half:
        last_unit = tokens[-1][1]
        value += 0.5 * MASS_FACTORS_QIAN[last_unit]
    return {"raw": raw, "basis": "mass_qian", "value_qian": value, "applies_to_group": applies_to_group}


@lru_cache(maxsize=1)
def load_skchar_resolutions() -> dict[str, str]:
    path = RESEARCH_ROOT / "ontology" / "skchar_resolutions_v0.1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["template_id"]: row["character"] for row in payload["resolutions"]}


def make_parser_text(text: str) -> str:
    """Keep source ingredient text and quantities, but remove process prose inside notes."""
    text = ANCHOR.sub(lambda match: match.group(1), text)
    text = NOTE.sub(lambda match: " " + note_quantity_projection(match.group(1)), text)
    resolutions = load_skchar_resolutions()
    text = SKCHAR_CAPTURE.sub(lambda match: resolutions.get(match.group(1), "□"), text)
    text = SKCHAR.sub("□", text)
    text = OTHER_TEMPLATE.sub("", text)
    return text


def note_quantity_projection(note: str) -> str:
    """Keep only quantities that govern the enclosing source-list mention(s)."""
    note = note.strip()
    values = []
    leading = re.match(rf"^(?:即|計|计)?\s*({QUANTITY.pattern})", note)
    if leading:
        values.append(leading.group(1))
    group = re.search(rf"(?:上|前)[{CN_NUM}]+味\s*({QUANTITY.pattern})", note)
    if group and group.group(1) not in values:
        values.append(group.group(1))
    return " ".join(values)


def note_addition_mentions(text: str, aliases: dict[str, list[str]]) -> tuple[str, list[dict]]:
    """Extract explicitly quantified materials mentioned inside editorial/preparation notes."""
    fragments, mentions = [], []
    offset = 0
    for note_match in NOTE.finditer(text):
        fragment = SKCHAR_CAPTURE.sub(
            lambda match: load_skchar_resolutions().get(match.group(1), "□"),
            note_match.group(1),
        )
        fragment = OTHER_TEMPLATE.sub("", fragment)
        local_mentions = find_materials(fragment, aliases)
        assign_quantities(fragment, local_mentions, group_window=10)
        local_mentions = [row for row in local_mentions if row["quantity"] is not None]
        for row in local_mentions:
            row["start"] += offset
            row["end"] += offset
            row["source_zone"] = "note_quantified_addition"
        fragments.append(fragment)
        mentions.extend(local_mentions)
        offset += len(fragment) + 1
    return "\n".join(fragments), mentions


def split_final_line(line: str) -> tuple[str, str]:
    """Separate an ingredient prefix from method prose without discarding quantified additions."""
    positions = [position for marker in METHOD_MARKERS if (position := line.find(marker)) >= 0]
    if not positions:
        return line, ""
    position = min(positions)
    return line[:position], line[position:]


def ingredient_body(lines: list[str]) -> str:
    if len(lines) < 2:
        return "\n".join(lines)
    body_lines = list(lines[1:-1])
    final = lines[-1]
    prefix, method = split_final_line(final)
    if prefix.strip("　 \t"):
        body_lines.append(prefix)
    elif not method and QUANTITY.search(final):
        body_lines.append(final)
    return "\n".join(body_lines)


def method_tail(lines: list[str]) -> str:
    if not lines:
        return ""
    _, method = split_final_line(lines[-1])
    return method


def load_ontology() -> tuple[dict, dict[str, list[str]]]:
    path = RESEARCH_ROOT / "ontology" / "materials_v0.1.json"
    ontology = json.loads(path.read_text(encoding="utf-8"))
    entities = {entity["id"]: entity for entity in ontology["entities"]}
    aliases: dict[str, list[str]] = {}
    for entity in ontology["entities"]:
        for alias in entity["aliases"]:
            aliases.setdefault(alias, []).append(entity["id"])
    for compound in ontology["compound_mentions"]:
        aliases[compound["mention"]] = compound["expands_to"]
    return entities, aliases


def find_materials(text: str, aliases: dict[str, list[str]]) -> list[dict]:
    pattern = re.compile("|".join(re.escape(alias) for alias in sorted(aliases, key=len, reverse=True)))
    occupied: list[tuple[int, int]] = []
    mentions = []
    for match in pattern.finditer(text):
        if any(match.start() < end and match.end() > start for start, end in occupied):
            continue
        occupied.append(match.span())
        for entity_id in aliases[match.group(0)]:
            mentions.append({
                "surface": match.group(0),
                "entity_id": entity_id,
                "start": match.start(),
                "end": match.end(),
                "quantity": None,
            })
    return sorted(mentions, key=lambda row: (row["start"], row["end"], row["entity_id"]))


def assign_quantities(text: str, mentions: list[dict], group_window: int | None = None) -> None:
    pending: list[dict] = []
    events = [(row["start"], "material", row) for row in mentions]
    events += [(match.start(), "quantity", match) for match in QUANTITY.finditer(text)]
    for event_position, kind, item in sorted(events, key=lambda row: (row[0], 0 if row[1] == "material" else 1)):
        if kind == "material":
            pending.append(item)
            continue
        quantity = normalize_quantity(item.group(0))
        if not pending:
            continue
        if quantity["applies_to_group"]:
            targets = list(pending)
            if group_window is not None:
                nearby = [target for target in targets if event_position - target["start"] <= group_window]
                if nearby:
                    targets = nearby
        else:
            latest_start = pending[-1]["start"]
            targets = [target for target in pending if target["start"] == latest_start]
            if len(targets) > 1:
                quantity = {
                    "raw": quantity["raw"],
                    "basis": "collective_ambiguous",
                    "value_qian": None,
                    "applies_to_group": False,
                }
        for target in targets:
            if target["quantity"] is None:
                target["quantity"] = quantity
        # Unassigned earlier mentions remain explicitly missing; they must not
        # absorb a later ingredient's quantity.
        pending = []


def structure_candidate(record: dict, entities: dict, aliases: dict[str, list[str]]) -> dict:
    lines = record["raw_wikitext"].splitlines()
    body = ingredient_body(lines)
    method = method_tail(lines)
    body_parser_text = make_parser_text(body)
    method_parser_text = make_parser_text(method)
    note_parser_text, note_mentions = note_addition_mentions(body + "\n" + method, aliases)

    body_mentions = find_materials(body_parser_text, aliases)
    assign_quantities(body_parser_text, body_mentions)
    for mention in body_mentions:
        mention["source_zone"] = "ingredient_list"

    method_mentions = find_materials(method_parser_text, aliases)
    assign_quantities(method_parser_text, method_mentions, group_window=10)
    # Method prose contains many repeated or process-only names.  Retain only
    # explicit quantitative additions here; curation still adjudicates whether
    # an addition is retained, discarded, or outside the aromatic target.
    method_mentions = [mention for mention in method_mentions if mention["quantity"] is not None]

    parser_parts = [part for part in (body_parser_text, method_parser_text, note_parser_text) if part]
    parser_text = "\n".join(parser_parts)
    method_offset = len(body_parser_text) + (1 if body_parser_text and method_parser_text else 0)
    for mention in method_mentions:
        mention["start"] += method_offset
        mention["end"] += method_offset
        mention["source_zone"] = "method_quantified_addition"

    note_offset = len(body_parser_text)
    if body_parser_text and (method_parser_text or note_parser_text):
        note_offset += 1
    if method_parser_text:
        note_offset += len(method_parser_text) + (1 if note_parser_text else 0)
    for mention in note_mentions:
        mention["start"] += note_offset
        mention["end"] += note_offset

    # A note may repeat a source-list material while explaining a group amount.
    # Drop only exact entity/value duplicates; distinct additions remain additive.
    existing_keys = {
        (row["entity_id"], row["quantity"]["basis"], row["quantity"]["value_qian"])
        for row in body_mentions + method_mentions if row["quantity"] is not None
    }
    unique_note_mentions = []
    for mention in note_mentions:
        quantity = mention["quantity"]
        key = (mention["entity_id"], quantity["basis"], quantity["value_qian"])
        if key in existing_keys:
            continue
        unique_note_mentions.append(mention)
        existing_keys.add(key)

    mentions = sorted(
        body_mentions + method_mentions + unique_note_mentions,
        key=lambda row: (row["start"], row["end"], row["entity_id"]),
    )
    for mention in mentions:
        entity = entities[mention["entity_id"]]
        mention["role"] = entity["role"]
        mention["identity_status"] = entity["identity_status"]

    aromatic = [mention for mention in mentions if mention["role"] == "aromatic_material"]
    comparable = [
        mention for mention in aromatic
        if mention["quantity"] and mention["quantity"]["basis"] in {"mass_qian", "relative_equal"}
    ]
    bases = {mention["quantity"]["basis"] for mention in comparable}
    ratio_ready = len(aromatic) >= 2 and len(comparable) == len(aromatic) and len(bases) == 1
    composition = None
    if ratio_ready:
        totals: dict[str, float] = defaultdict(float)
        for mention in comparable:
            totals[mention["entity_id"]] += mention["quantity"]["value_qian"]
        total = sum(totals.values())
        composition = {key: value / total for key, value in sorted(totals.items())}

    return {
        **{key: value for key, value in record.items() if key != "raw_wikitext"},
        "raw_wikitext": record["raw_wikitext"],
        "body_wikitext": body,
        "method_tail_wikitext": method,
        "parser_text": parser_text,
        "mention_offsets_relative_to": "parser_text",
        "material_mentions": mentions,
        "aromatic_mention_count": len(aromatic),
        "assigned_aromatic_quantity_count": sum(mention["quantity"] is not None for mention in aromatic),
        "method_quantified_addition_count": len(method_mentions),
        "note_quantified_addition_count": len(unique_note_mentions),
        "ratio_ready_automatic": ratio_ready,
        "composition_aromatic_only": composition,
        "status": "structured_candidate_unverified",
    }


def main() -> None:
    entities, aliases = load_ontology()
    # CText candidates are intentionally kept outside the public structured
    # build until scan verification and redistribution review are complete.
    collections = ("xiangcheng", "hong_xiangpu", "chen_xiangpu")
    structured = []
    source_hashes = {}
    for collection in collections:
        path = RESEARCH_ROOT / "data" / "interim" / f"{collection}_formula_candidates.json"
        source_hashes[collection] = hashlib.sha256(path.read_bytes()).hexdigest()
        records = json.loads(path.read_text(encoding="utf-8"))["records"]
        structured.extend(structure_candidate(record, entities, aliases) for record in records)
    output = {
        "schema_version": "0.1",
        "source_hashes": source_hashes,
        "ontology": "ontology/materials_v0.1.json",
        "record_count": len(structured),
        "ratio_ready_automatic_count": sum(record["ratio_ready_automatic"] for record in structured),
        "status": "automatic parser output; gold labels require source review",
        "records": structured,
    }
    target = RESEARCH_ROOT / "data" / "interim" / "structured_formula_candidates_v0.1.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "records": len(structured),
        "ratio_ready": output["ratio_ready_automatic_count"],
        "output": str(target),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
