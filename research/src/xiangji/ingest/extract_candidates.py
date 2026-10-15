"""Deterministically segment formula candidates from preserved Wikisource wikitext."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

from xiangji.data import RESEARCH_ROOT

COLLECTION_DIRS = {
    "xiangcheng": "xiangcheng_20260901",
    "hong_xiangpu": "hong_xiangpu_20260901",
    "chen_xiangpu": "chen_xiangpu_20260901",
}

ANCHOR = re.compile(r"\{\{SK anchor\|([^{}|]+)(?:\|[^{}]*)?\}\}")
NOTE = re.compile(r"\{\{SK notes\|([^{}]*)\}\}")
SKCHAR = re.compile(r"\{\{SKchar\|[^{}]*\}\}")
SKCHAR_CAPTURE = re.compile(r"\{\{SKchar\|([^{}|]+)(?:\|[^{}]*)?\}\}")
OTHER_TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")
COMMENT = re.compile(r"<!--.*?-->")
QUANTITY = re.compile(
    r"(?:[一二三四五六七八九十百千廿卅半兩两錢钱分字觔斤枚粒箇个升合盞盏撮]+|各)"
    r"\s*(?:兩|两|錢|钱|分|字|觔|斤|枚|粒|箇|个|升|合|盞|盏|撮|等分)"
)
METHOD_ANYWHERE = re.compile(r"右(?:爲|為|以|同|用|將|各|皆|細|并|入|搗|擣|研|和|除|等|件|[一二三四五六七八九十])")
METHOD_PREFIX = re.compile(
    r"^(?:共(?:爲|為)|各等分|和窨|以上諸香|已上諸香|諸香(?:爲|為)|每香油)"
)
# Some late-Ming witnesses close a recipe with an imperative rather than the
# common ``右...`` construction.  Keep this list deliberately anchored to
# preparation verbs and terminal-use phrases: loose matches such as ``蜜`` or
# ``香`` would split ingredient rows.
METHOD_TERMINAL = re.compile(
    r"^(?:"
    r"共合一處研細拌勻|"
    r"共[一二三四五六七八九十百廿卅]+味爲末|"
    r"共[一二三四五六七八九十百廿卅]+味為末|"
    r"印餅用|印饼用|印造各式|"
    r"用白芨.*(?:焚之|印餅|印饼)|"
    r"煉蜜爲濕膏|煉蜜為濕膏|炼蜜为湿膏|"
    r"散用如印餅|散用如印饼|"
    r"以白芨.*(?:竹篾|印餅|印饼)|"
    r"和印或散燒|和印或散烧|"
    r"和劑印餅用|和剂印饼用|"
    r"先煉蜜.*印餅|先炼蜜.*印饼|"
    r"印作餅燒|印作饼烧|"
    r"入丸.*(?:香花皆然|香花皆然)|"
    r"已上作末.*(?:棒兒香|棒儿香)|"
    r"和成(?:滚|滾)棒"
    r")"
)
METHOD_SUFFIX = re.compile(r"(?:日熏之|磁盒貯之|磁盒贮之|一月用)$")
NON_TITLE_PREFIXES = ("已上", "以上", "香譜補遺", "香谱补遗", "此乃", "按")
META_ANCHORS = {
    "法和衆妙香", "法和众妙香", "凝合花香", "熏佩之香", "塗傅之香", "涂傅之香",
    "印篆諸香", "印篆诸香", "晦齋香譜", "晦斋香谱", "墨娥小錄香譜", "墨娥小录香谱",
    "獵香新譜", "猎香新谱", "香乘卷十四", "香乗卷十四", "香乘卷十五", "香乗卷十五",
    "香乘卷十六", "香乗卷十六", "香乘卷十七", "香乗卷十七", "香乘卷十八", "香乗卷十八",
    "香乘卷十九", "香乗卷十九", "香乘卷二十", "香乗卷二十", "香乘卷二十一", "香乗卷二十一",
    "香乘卷二十二", "香乗卷二十二", "香乘卷二十三", "香乗卷二十三", "香乘卷二十四",
    "香乗卷二十四", "香乘卷二十五", "香乗卷二十五",
}


@lru_cache(maxsize=1)
def skchar_resolutions() -> dict[str, str]:
    path = RESEARCH_ROOT / "ontology" / "skchar_resolutions_v0.1.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["template_id"]: row["character"] for row in payload["resolutions"]}


def visible_text(line: str) -> str:
    """Approximate visible text without changing the preserved source string."""
    text = COMMENT.sub("", line)
    text = ANCHOR.sub(lambda match: match.group(1), text)
    text = NOTE.sub(lambda match: match.group(1), text)
    resolutions = skchar_resolutions()
    text = SKCHAR_CAPTURE.sub(lambda match: resolutions.get(match.group(1), "□"), text)
    text = SKCHAR.sub("□", text)
    text = OTHER_TEMPLATE.sub("", text)
    return text.replace("<onlyinclude>", "").replace("</onlyinclude>", "").strip("　 \t")


def heading_text(line: str) -> str:
    """Render a heading while omitting editorial/source notes."""
    text = NOTE.sub("", line)
    return visible_text(text)


def is_method_line(line: str) -> bool:
    rendered = visible_text(line)
    return bool(
        rendered.startswith("右")
        or METHOD_ANYWHERE.search(rendered)
        or METHOD_PREFIX.match(rendered)
        or METHOD_TERMINAL.match(rendered)
        or METHOD_SUFFIX.search(rendered)
    )


def _heading_value(line: str) -> str | None:
    """Return a plausible title from one pre-ingredient line."""
    anchors = [value.strip() for value in ANCHOR.findall(line)]
    for value in anchors:
        if value not in META_ANCHORS and not value.startswith(("香乘卷", "香乗卷")):
            if (
                not QUANTITY.search(line)
                and not METHOD_PREFIX.match(value)
                and not METHOD_ANYWHERE.search(value)
                and not METHOD_TERMINAL.match(value)
                and not value.startswith(NON_TITLE_PREFIXES)
            ):
                return value
    rendered = heading_text(line)
    if (
        rendered
        and len(rendered) <= 30
        and rendered not in META_ANCHORS
        and not rendered.startswith(("<!--", "-->", "<", "香乘卷", "香乗卷", "欽定四庫全書", "明　"))
        and not rendered.startswith(NON_TITLE_PREFIXES)
        and not re.search(r"(?:　{2,}|\s{3,})", rendered)
        and not QUANTITY.search(line)
        and not METHOD_PREFIX.match(rendered)
        and not METHOD_ANYWHERE.search(rendered)
        and not METHOD_TERMINAL.match(rendered)
    ):
        if len(rendered) > 18 and "香" in rendered:
            return rendered[: rendered.index("香") + 1]
        return rendered
    return None


def choose_heading_with_index(block_lines: list[str]) -> tuple[str, int] | None:
    if not any(QUANTITY.search(line) for line in block_lines):
        return None

    # Select the closest plausible heading before the first quantified line.
    # This excludes intervening historical prose (common in Hong's Xiangpu)
    # without looking ahead into the ingredient list itself.
    in_comment = False
    pre_quantity: list[tuple[int, str]] = []
    for index, line in enumerate(block_lines):
        if "<!--" in line:
            in_comment = "-->" not in line.split("<!--", 1)[1]
            continue
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if QUANTITY.search(line):
            break
        pre_quantity.append((index, line))
    for index, line in reversed(pre_quantity):
        if value := _heading_value(line):
            return value, index
    return None


def choose_heading(block_lines: list[str]) -> str | None:
    result = choose_heading_with_index(block_lines)
    return result[0] if result else None


def segment_page(text: str, title: str, revision_id: int) -> list[dict]:
    lines = text.splitlines()
    candidates, start = [], 0
    for end, line in enumerate(lines):
        if not is_method_line(line):
            continue
        block_lines = lines[start : end + 1]
        heading_result = choose_heading_with_index(block_lines)
        if heading_result:
            heading, heading_offset = heading_result
            block_lines = block_lines[heading_offset:]
        else:
            heading, heading_offset = None, 0
        block = "\n".join(block_lines).strip()
        anchors = ANCHOR.findall(block)
        quantities = QUANTITY.findall(block)
        # Ingredient names are inconsistently wrapped in anchors; requiring a
        # minimum anchor count silently drops otherwise well-formed formulas.
        if heading and len(quantities) >= 2:
            record_start = start + heading_offset + 1
            key = f"{title}:{revision_id}:{record_start}:{end + 1}:{heading}"
            candidates.append({
                "candidate_id": hashlib.sha1(key.encode()).hexdigest()[:16],
                "page_title": title,
                "revision_id": revision_id,
                "line_start": record_start,
                "line_end": end + 1,
                "formula_title_candidate": heading,
                "raw_wikitext": block,
                "anchor_count": len(anchors),
                "quantity_expression_count": len(quantities),
                "status": "candidate_unverified",
            })
        start = end + 1
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", choices=sorted(COLLECTION_DIRS), default="xiangcheng")
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source_dir = args.source_dir or (
        RESEARCH_ROOT / "data" / "sources" / "wikisource" / COLLECTION_DIRS[args.collection]
    )
    manifest = json.loads((source_dir / "manifest.json").read_text(encoding="utf-8"))
    output = []
    for page in manifest["pages"]:
        if "/卷" not in page["title"]:
            continue
        text = (RESEARCH_ROOT / page["path"]).read_text(encoding="utf-8")
        page_records = segment_page(text, page["title"], page["revision_id"])
        for record in page_records:
            record.update({
                "collection": args.collection,
                "witness_id": f"zhwikisource-{manifest['dump_date']}-{page['page_id']}-{page['revision_id']}",
                "source_path": page["path"],
                "source_url": page["source_url"],
                "stable_revision_url": page["stable_revision_url"],
            })
        output.extend(page_records)
    target = args.output or (
        RESEARCH_ROOT / "data" / "interim" / f"{args.collection}_formula_candidates.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({
        "generator": "xiangji.ingest.extract_candidates v0.1",
        "candidate_count": len(output),
        "status": "machine-segmented candidates; not gold data",
        "records": output,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"candidate_count": len(output), "output": str(target)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
