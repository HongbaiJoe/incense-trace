from xiangji.ingest.extract_ctext_chapter import extract_records, parse_rows


def test_ctext_row_parser_and_scoped_formula_ranges():
    html = "".join(
        f'<tr class="result" id="p{number}"><td class="ctext">{number}</td><td class="ctext">文本{number}</td></tr>'
        for number in list(range(126, 151)) + [155, 156]
    )
    rows = parse_rows(html)
    records = extract_records(rows)
    assert len(records) == 11
    assert records[0]["paragraph_start"] == 126
    assert records[0]["paragraph_end"] == 128
    assert records[-1]["paragraph_start"] == 155
    assert records[-1]["paragraph_end"] == 156
