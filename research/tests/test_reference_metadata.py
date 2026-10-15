from xiangji.ingest.fetch_reference_metadata import compare, normalized_title


def test_normalized_title_ignores_markup_punctuation_and_case():
    assert normalized_title("Study of <i>Foeniculum vulgare</i>: GC-MS") == normalized_title(
        "study of Foeniculum vulgare GC MS"
    )


def test_online_first_difference_remains_a_warning():
    source = {"source_id": "example", "doi": "10.example/x", "title": "Same title", "year": 2020}
    metadata = {"title": "Same title", "published_date_parts": [2019, 12, 1]}
    result = compare(source, metadata)
    assert result["title_exact_after_normalization"] is True
    assert result["status"] == "warning"
    assert result["warning"] is not None


def test_exact_title_and_year_are_verified():
    source = {"source_id": "example", "pmid": "1", "title": "Same title", "year": 2020}
    metadata = {"title": "Same title.", "published_date_parts": [2020]}
    assert compare(source, metadata)["status"] == "verified"
