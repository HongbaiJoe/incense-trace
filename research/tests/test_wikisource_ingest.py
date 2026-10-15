from xiangji.ingest.extract_candidates import is_method_line, segment_page, visible_text


def test_candidate_segmentation_preserves_span_and_text():
    text = """{{SK anchor|法和衆妙香}}
{{SK anchor|測試香}}
{{SK anchor|沉香}}{{SK notes|一兩}}
{{SK anchor|檀香}}{{SK notes|半兩}}
　右爲細末煉蜜和匀
"""
    records = segment_page(text, "測試/卷01", 7)
    assert len(records) == 1
    assert records[0]["formula_title_candidate"] == "測試香"
    assert records[0]["line_start"] == 2
    assert records[0]["line_end"] == 5
    assert records[0]["raw_wikitext"] == "\n".join(text.splitlines()[1:])


def test_method_detection_handles_anchor_wrapped_method():
    line = "　　{{SK anchor|右為末煉蜜和劑作餅焚之}}"
    assert visible_text(line) == "右為末煉蜜和劑作餅焚之"
    assert is_method_line(line)


def test_visible_text_resolves_provenance_controlled_skchar_only():
    assert visible_text("夾{{SKchar|202}}香 {{SKchar|999999}}") == "夾箋香 □"


def test_plain_heading_after_previous_formula_is_selected():
    text = """{{SK anchor|甲香}}
{{SK anchor|沉香}}{{SK notes|一兩}}
{{SK anchor|檀香}}{{SK notes|一兩}}
右為末
乙香
沉香{{SK notes|二兩}}
{{SK anchor|丁香}}{{SK notes|半兩}}
右為末
"""
    records = segment_page(text, "測試/卷01", 9)
    assert [record["formula_title_candidate"] for record in records] == ["甲香", "乙香"]


def test_method_detection_handles_inline_and_variant_endings():
    assert is_method_line("沉香檀香各一兩右為末煉蜜和之")
    assert is_method_line("　右六件一處和匀")
    assert is_method_line("　共為細末白芨水調")
    assert is_method_line("{{SK anchor|各等分生蜜搗成劑或作餅用}}")


def test_method_detection_handles_liexing_imperative_endings():
    endings = [
        "{{SK anchor|共合一處研細拌勻}}{{SK notes|秘傳}}",
        "{{SK anchor|印餅用}}",
        "共二十四味為末用白芨糊入血結五錢杵擣千餘下印枕頂式隂乾製枕",
        "{{SK anchor|印造各式}}",
        "{{SK anchor|用白芨末成糊脫餅焚之}}",
        "煉蜜為濕膏入磁瓶封固取焚之",
        "{{SK anchor|散用如印餅和蜜去榆麫}}",
        "{{SK anchor|以白芨汁上竹篾}}",
        "{{SK anchor|和印或散燒}}",
        "{{SK anchor|和劑印餅用}}",
        "先煉蜜熟下欖油化開又入唵叭揉勻印餅",
        "{{SK anchor|印作餅燒之佳甚}}",
        "入丸三兩磨汁入絹袋灰乾有香花皆然",
        "已上作末為骨先和上竹心子作第一層一名安席香俗名棒兒香",
        "{{SK anchor|和成滚棒如前}}",
    ]
    assert all(is_method_line(line) for line in endings)


def test_liexing_adjacent_formulas_are_not_merged():
    text = """宣廟御衣攢香
{{SK anchor|玫瑰花}}{{SK notes|四錢}}
{{SK anchor|檀香}}{{SK notes|二兩}}
{{SK anchor|共合一處研細拌勻}}
{{SK anchor|御前香}}
{{SK anchor|沈香}}{{SK notes|三兩五錢}}
{{SK anchor|片腦}}{{SK notes|二錢四分}}
{{SK anchor|印餅用}}
萬春香
{{SK anchor|沈香}}{{SK notes|十二兩}}
{{SK anchor|檀香}}{{SK notes|十八兩}}
煉蜜為濕膏入磁瓶封固取焚之
"""
    records = segment_page(text, "測試/卷25", 12)
    assert [record["formula_title_candidate"] for record in records] == [
        "宣廟御衣攢香",
        "御前香",
        "萬春香",
    ]
    assert all(record["line_end"] - record["line_start"] < 5 for record in records)


def test_closest_heading_before_quantities_excludes_intervening_prose():
    text = """{{SK anchor|鵲尾香爐}}
宋玉賢山隂人也既稟女質厥志彌髙
{{SK anchor|香篆}}
鏤木以為之以範香塵為篆文
{{SK anchor|香之法}}
蜀王薰御衣法
丁香　　　馢香　　　沈香
檀香　　　麝香{{SK notes|已上各一兩}}甲香{{SK notes|三兩製如常法}}
右件香為末用白沙蜜合和令勻
"""
    records = segment_page(text, "測試/卷下", 13)
    assert len(records) == 1
    assert records[0]["formula_title_candidate"] == "蜀王薰御衣法"
    assert records[0]["line_start"] == 6
    assert records[0]["raw_wikitext"].startswith("蜀王薰御衣法\n")


def test_narrative_formula_endings_segment_huang_taishi_group():
    text = """{{SK anchor|黄太史四香}}
意和
沉檀為主每沉一兩半檀一兩以棗肉合之作模如龍涎香様日熏之
{{SK anchor|意可}}
海南沉水香三兩檀一兩木香四錢右皆末之用白蜜六兩和香末勻
{{SK anchor|深静}}
海南沉水香二兩羊脛炭四兩婆津膏三錢麝一錢以磁盒貯之
{{SK anchor|小宗香}}
海南沉水一兩棧香半兩紫檀二兩蘇合油二錢入磁盒埋窨一月用
"""
    records = segment_page(text, "測試/卷17", 14)
    assert [record["formula_title_candidate"] for record in records] == [
        "意和",
        "意可",
        "深静",
        "小宗香",
    ]


def test_shared_quantity_ingredient_line_is_not_title():
    text = """{{SK anchor|荔枝香}}{{SK notes|沈}}
沉香　　　　檀香　　　白荳䓻仁
西香附子　金顔香　肉桂{{SK notes|已上各一兩}}
馬牙硝{{SK notes|五錢}}
右先研香為末
"""
    records = segment_page(text, "測試/卷02", 10)
    assert records[0]["formula_title_candidate"] == "荔枝香"


def test_page_comment_and_heading_note_do_not_become_title():
    text = """<!--
校對提示
-->
{{SK anchor|香乘卷二十三}}
{{SK anchor|蝴蝶香}}{{SK notes|春月花圃中焚之}}
檀香{{SK notes|二錢}}
丁香{{SK notes|三錢}}
右為末
"""
    records = segment_page(text, "測試/卷23", 11)
    assert records[0]["formula_title_candidate"] == "蝴蝶香"
