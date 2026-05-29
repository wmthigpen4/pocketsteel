from __future__ import annotations

from pocketsteel.answering import final_answer_quality_gate
from pocketsteel.curated_source_registry import (
    answer_contains_unapproved_url,
    filter_active_sources,
    format_curated_links,
    get_curated_sources_for_intent,
    is_approved_curated_url,
    slide_bar_vendor_bullets,
)


def test_inactive_curated_sources_are_not_shown() -> None:
    sources = [
        {"name": "Active Source", "url": "https://active.example/", "active": True},
        {"name": "Inactive Source", "url": "https://inactive.example/", "active": False},
    ]

    active = filter_active_sources(sources)

    assert [source["name"] for source in active] == ["Active Source"]


def test_vendor_intent_selects_vendor_sources_with_caveats() -> None:
    sources = get_curated_sources_for_intent("vendor_buying_guidance", tags=("tone_bars",))
    names = {source["name"] for source in sources}
    bullets = format_curated_links(sources)

    assert {"Steel Guitar Shopper", "BJS Steel Guitar Bars", "Jim Dunlop Tonebars"} <= names
    assert any("Do not claim" in bullet or "Confirm the exact model" in bullet for bullet in bullets)
    assert all(source["active"] is True for source in sources)


def test_non_vendor_intent_does_not_randomly_get_vendor_sources() -> None:
    sources = get_curated_sources_for_intent("organization_event_lookup")
    names = {source["name"] for source in sources}

    assert "Texas Steel Guitar Association" in names
    assert "Steel Guitar Shopper" not in names
    assert "BJS Steel Guitar Bars" not in names


def test_slide_bar_vendor_bullets_use_curated_registry_order_and_caveats() -> None:
    bullets = slide_bar_vendor_bullets()
    text = "\n".join(bullets)

    assert bullets[0].startswith("- Steel Guitar Shopper")
    assert "https://steelguitarshopper.com/accessories/" in text
    assert "https://www.bjsbars.com/" in text
    assert "https://www.jimdunlop.com/products/accessories/slides-tonebars/tonebars/" in text
    assert "https://bb.steelguitarforum.com/viewforum.php?f=9" in text
    assert "current availability" in text.lower() or "inventory" in text.lower()


def test_final_answer_url_gate_allows_only_approved_curated_domains() -> None:
    approved = "Website: https://www.steelerschoice.com/"
    unapproved = "Go here: https://private.example.invalid/source"

    assert is_approved_curated_url("https://www.steelerschoice.com/")
    assert not is_approved_curated_url("https://private.example.invalid/source")
    assert not answer_contains_unapproved_url(approved)
    assert answer_contains_unapproved_url(unapproved)

    cleaned = final_answer_quality_gate(unapproved, "Where can I buy a seat?")
    assert "private.example.invalid" not in cleaned
    assert "reliable information" in cleaned
