from pathlib import Path


LANDING_PAGE = Path("ui/steel-guitar-rag-landing.html")


def test_public_landing_page_has_required_beta_copy_and_ctas() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    assert "Steel Guitar RAG is a source-backed AI assistant" in html or "Source-backed AI for pedal steel players." in html
    assert "Private beta coming" in html
    assert "Join the private beta" in html
    assert "See example questions" in html
    assert "Get a Backstage Pass" in html
    assert "Go Backstage" in html
    assert "Live AI access will require login during private beta." in html


def test_public_landing_page_lists_expected_example_questions() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    expected_questions = [
        "What are common Fender Steel King settings?",
        "How do I use the E9 6th string lower?",
        "What should I practice tonight?",
        "Why does my amp buzz until I touch the changer?",
        "How do players use B+C pedals?",
    ]

    for question in expected_questions:
        assert question in html


def test_public_landing_page_is_static_and_uses_local_assets() -> None:
    html = LANDING_PAGE.read_text(encoding="utf-8")

    assert 'src="assets/steel-guitar-rag-logo-transparent.png"' in html
    assert 'url("assets/steel_on_stage2.png")' in html
    assert "/api/answer" not in html
    assert "chromadb" not in html.lower()
    assert "bb.steelguitarforum.com" not in html.lower()
    assert "stripe" not in html.lower()
