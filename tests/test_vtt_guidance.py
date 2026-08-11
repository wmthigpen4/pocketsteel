from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts import vtt_guidance as cli
from steel_guitar_rag.vtt_guidance import (
    ENABLE_VTT_GUIDANCE_RETRIEVAL_ENV,
    BUILD_VERSION,
    SCHEMA_VERSION,
    VttGuidanceError,
    build_fts_index,
    contains_source_ngram,
    evaluate_index,
    is_vtt_teaching_query,
    render_guidance_section,
    search_index,
    search_vtt_guidance,
    sha256_file,
    validate_card,
    validate_technical_anchors,
    vtt_guidance_retrieval_enabled,
    write_jsonl,
)


def card(
    card_id: str,
    source_id: str,
    *,
    card_type: str = "procedure",
    concept: str = "Pick blocking uses the picking fingers to stop notes cleanly.",
    procedure: list[str] | None = None,
    mistakes: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "card_id": card_id,
        "source_id": source_id,
        "parent_overview_id": f"{source_id}-overview",
        "card_type": card_type,
        "instrument": "E9",
        "concept": concept,
        "setup": ["Use a quiet amplifier setting and listen to the note ending."],
        "procedure": procedure
        or [
            "Pick string 5, return the fingerpick to mute it, then play string 6.",
            "Repeat slowly until the silence between notes is deliberate.",
        ],
        "common_mistakes": mistakes or ["Do not let the previous string continue ringing."],
        "transfer": ["Apply the same motion to another adjacent-string pair."],
        "technical_anchors": {
            "strings": [5, 6],
            "frets": [],
            "pedals": [],
            "levers": [],
            "grips": ["5-6"],
            "keys": [],
            "chord_functions": [],
            "techniques": ["pick blocking"],
        },
        "source_sha256": "a" * 64,
        "corpus_class": "structured_lesson",
        "privacy_action": "converted",
        "licensing_action": "low_risk",
        "allowed_for_embedding": False,
        "answer_quote_allowed": False,
        "generation_model": "qwen3.5:27b",
        "generator_version": BUILD_VERSION,
        "privacy_review_model": "gemma4:12b",
        "privacy_review_status": "passed",
        "music_validation_status": "passed",
        "review_status": "approved",
        "human_approved": True,
    }


def test_flags_and_query_gate_are_default_off_and_exclude_forum_or_gear() -> None:
    assert vtt_guidance_retrieval_enabled({}) is False
    assert vtt_guidance_retrieval_enabled({ENABLE_VTT_GUIDANCE_RETRIEVAL_ENV: "1"}) is True
    assert is_vtt_teaching_query("How should I practice pick blocking?") is True
    assert is_vtt_teaching_query("What do forum players say about pick blocking?") is False
    assert is_vtt_teaching_query("Which amplifier should I buy?") is False


def test_card_validation_rejects_private_markers_verbatim_overlap_and_bad_e9_anchors() -> None:
    value = card("card-1", "source-1")
    assert validate_card(value, require_human_approval=True) == []

    private = dict(value)
    private["concept"] = "A subscriber on Zoom asked Travis for this lesson."
    findings = validate_card(private, require_human_approval=True)
    assert "presenter_or_brand" in findings
    assert "member_or_request" in findings

    bad_anchor = dict(value)
    bad_anchor["technical_anchors"] = {
        **dict(value["technical_anchors"]),
        "strings": [11],
        "pedals": ["mystery pedal"],
    }
    findings = validate_card(bad_anchor, require_human_approval=True)
    assert "invalid_e9_string" in findings
    assert "invalid_e9_pedal" in findings

    source = "one two three four five six seven eight nine ten eleven twelve"
    assert contains_source_ngram(source, source) is True
    overlap = dict(value)
    overlap["concept"] = "one two three four five six seven eight nine ten"
    assert "source_ten_word_overlap" in validate_card(overlap, source_text=source)


def test_e9_validation_accepts_ordinal_string_anchors() -> None:
    anchors = dict(card("card-1", "source-1")["technical_anchors"])
    anchors["strings"] = ["5th string", "6th", "10th"]
    anchors["frets"] = ["0 fret", "5th fret", 12]

    assert validate_technical_anchors(anchors, instrument="E9") == []


def test_e9_validation_accepts_word_strings_pedal_pairs_and_e_to_f_alias() -> None:
    anchors = dict(card("card-1", "source-1")["technical_anchors"])
    anchors["strings"] = ["three", "fifth string", "ten"]
    anchors["pedals"] = ["A and B pedals", "B and C pedals"]
    anchors["levers"] = ["E-to-F lever"]

    assert validate_technical_anchors(anchors, instrument="E9") == []


def test_approved_cards_build_dedicated_checksummed_index_and_group_results(tmp_path: Path) -> None:
    cards_path = tmp_path / "approved/cards.jsonl"
    index_path = tmp_path / "index/vtt.sqlite"
    rows = [
        card("overview-a", "source-a", card_type="overview"),
        card("detail-a", "source-a"),
        card(
            "detail-b",
            "source-b",
            concept="Bar intonation improves when the bar arrives squarely over the fret.",
            procedure=["Move between frets 3 and 5 while listening for a centered pitch."],
        ),
    ]
    write_jsonl(cards_path, rows)
    result = build_fts_index(cards_path, index_path)

    assert result["card_count"] == 3
    assert result["source_count"] == 2
    assert index_path.is_file()
    assert index_path.with_suffix(".sqlite.sha256").is_file()

    found = search_index(index_path, "How should I practice pick blocking?", top_k=3)
    assert found
    assert {item.source_id for item in found} <= {"source-a", "source-b"}
    assert len(found) <= 3
    assert len({item.source_id for item in found}) <= 2

    through_flag = search_vtt_guidance(
        "How should I practice pick blocking?",
        index_path=index_path,
        env={ENABLE_VTT_GUIDANCE_RETRIEVAL_ENV: "1"},
    )
    assert through_flag
    assert search_vtt_guidance(
        "How should I practice pick blocking?",
        index_path=index_path,
        env={ENABLE_VTT_GUIDANCE_RETRIEVAL_ENV: "0"},
    ) == []


def test_index_checksum_tampering_fails_closed(tmp_path: Path) -> None:
    cards_path = tmp_path / "approved/cards.jsonl"
    index_path = tmp_path / "index/vtt.sqlite"
    write_jsonl(cards_path, [card("detail-a", "source-a")])
    build_fts_index(cards_path, index_path)
    index_path.write_bytes(index_path.read_bytes() + b"tamper")

    with pytest.raises(VttGuidanceError, match="checksum mismatch"):
        search_index(index_path, "How should I practice pick blocking?")


@pytest.mark.parametrize(
    ("statement", "message"),
    [
        ("UPDATE metadata SET value = 'old-build' WHERE key = 'build_version'", "build version mismatch"),
        ("UPDATE metadata SET value = '99' WHERE key = 'source_count'", "count mismatch"),
        ("UPDATE cards SET corpus_version = 'wrong'", "row version mismatch"),
    ],
)
def test_signed_but_mismatched_index_metadata_fails_closed(
    tmp_path: Path,
    statement: str,
    message: str,
) -> None:
    cards_path = tmp_path / "approved/cards.jsonl"
    index_path = tmp_path / "index/vtt.sqlite"
    write_jsonl(cards_path, [card("card-a", "source-a")])
    build_fts_index(cards_path, index_path)
    with sqlite3.connect(index_path) as connection:
        connection.execute(statement)
        connection.commit()
    sidecar = index_path.with_suffix(index_path.suffix + ".sha256")
    sidecar.write_text(f"{sha256_file(index_path)}  {index_path.name}\n", encoding="utf-8")

    with pytest.raises(VttGuidanceError, match=message):
        search_index(index_path, "How should I practice pick blocking?")


def test_retrieval_evaluation_enforces_detail_broad_and_human_gates(tmp_path: Path) -> None:
    cards_path = tmp_path / "approved/cards.jsonl"
    index_path = tmp_path / "index/vtt.sqlite"
    probes_path = tmp_path / "review/probes.jsonl"
    report_path = tmp_path / "reports/eval.json"
    write_jsonl(
        cards_path,
        [
            card("overview-a", "source-a", card_type="overview"),
            card("detail-a", "source-a"),
        ],
    )
    build_fts_index(cards_path, index_path)
    probes = [
        {
            "probe_id": f"detail-{index}",
            "kind": "detail",
            "question": "How should I practice pick blocking?",
            "useful_source_ids": ["source-a"],
        }
        for index in range(43)
    ]
    probes.extend(
        {
            "probe_id": f"broad-{index}",
            "kind": "broad",
            "question": "How should I practice pick blocking?",
            "useful_source_ids": ["source-a"],
        }
        for index in range(10)
    )
    probes.extend(
        {
            "probe_id": f"human-{index}",
            "kind": "human",
            "question": "How should I practice pick blocking?",
            "useful_source_ids": ["source-a"],
            "expected_instruments": ["E9"],
        }
        for index in range(5)
    )
    write_jsonl(probes_path, probes)

    report = evaluate_index(index_path, probes_path, report_path)

    assert report["gate_passed"] is True
    assert report["detail"] == {"top3": 43, "top5": 43, "mrr": 1.0}
    assert report["broad"] == {"useful_top3": 10}
    assert report["human"] == {
        "useful_top3": 5,
        "useful_top3_rate": 1.0,
        "wrong_instrument_results": 0,
    }
    report_text = report_path.read_text(encoding="utf-8")
    assert "source-a" not in report_text
    assert "pick blocking" not in report_text


def test_human_review_refuses_partial_manifest_candidate_set(tmp_path: Path) -> None:
    candidates_path = tmp_path / "candidates.jsonl"
    decisions_path = tmp_path / "decisions.jsonl"
    write_jsonl(candidates_path, [card("overview-a", "source-a", card_type="overview")])
    write_jsonl(
        decisions_path,
        [{"card_id": "overview-a", "decision": "approve", "reviewer": "human-reviewer"}],
    )

    with pytest.raises(VttGuidanceError, match="all 62 manifest sources"):
        cli.apply_review(
            candidates_path,
            decisions_path,
            tmp_path / "approved.jsonl",
            tmp_path / "report.json",
        )


def test_renderer_exposes_only_distinct_guidance_text_and_caps_length() -> None:
    result = {
        "card_id": "private-card-id",
        "source_id": "private-source-id",
        "parent_overview_id": "private-parent-id",
        "card_type": "procedure",
        "instrument": "E9",
        "concept": "Use deliberate muting so each picked note has a clean ending.",
        "procedure": ["Alternate strings 5 and 6 slowly."] * 8,
        "common_mistakes": ["Avoid leaving the previous note ringing."],
        "score": 1.0,
        "corpus_version": "private-version",
    }
    section = render_guidance_section([result])

    assert section is not None
    assert section["title"] == "Curated lesson guidance"
    assert section["style"] == "guidance"
    assert len(section["body"]) <= 1_200
    payload = json.dumps(section)
    assert "private-card-id" not in payload
    assert "private-source-id" not in payload
    assert "private-version" not in payload


def test_manifest_builder_selects_exact_structured_cohort_without_body_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    records_path = tmp_path / "records.jsonl"
    summary_root = tmp_path / "summaries"
    rows: list[dict[str, object]] = []
    for index in range(3):
        slug = f"lesson-{index}"
        source = tmp_path / "sources" / slug / f"{slug}.clean.txt"
        guidance = tmp_path / "guidance" / slug / "guidance_draft.md"
        summary = summary_root / slug / "summary_guidance.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        guidance.parent.mkdir(parents=True, exist_ok=True)
        summary.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("private raw source", encoding="utf-8")
        guidance.write_text("privacy cleaned steel guidance", encoding="utf-8")
        summary.write_text("# Summary\n\nCompact guidance.", encoding="utf-8")
        rows.append(
            {
                "candidate_status": "candidate_after_human_review",
                "corpus_class": "structured_lesson",
                "privacy_action": "converted",
                "licensing_action": "low_risk",
                "guidance_risk_counts": {},
                "source_path": source.as_posix(),
                "source_relpath": f"section/{slug}/{slug}.clean.txt",
                "source_title": slug,
                "outputs": {"guidance_draft": guidance.as_posix()},
            }
        )
    write_jsonl(records_path, rows)
    monkeypatch.setattr(cli, "EXPECTED_MANIFEST_COUNT", 3)
    output = tmp_path / "manifest.jsonl"

    result = cli.prepare_manifest(records_path, summary_root, output)

    assert result["manifest_count"] == 3
    manifest = cli.read_jsonl(output)
    assert all(row["allowed_for_embedding"] is False for row in manifest)
    assert all(row["answer_quote_allowed"] is False for row in manifest)


def test_purge_is_dry_run_without_exact_confirmation_and_rejects_wrong_root(tmp_path: Path) -> None:
    root = tmp_path / "vtt-guidance-v2"
    (root / "index").mkdir(parents=True)
    (root / "index/data.sqlite").write_text("derived", encoding="utf-8")

    dry_run = cli.purge(root, "", expected_root=root)
    assert dry_run["dry_run"] is True
    assert root.is_dir()

    with pytest.raises(VttGuidanceError, match="resolve exactly"):
        cli.purge(root, cli.PURGE_CONFIRMATION, expected_root=tmp_path / "different")
