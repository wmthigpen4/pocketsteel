from __future__ import annotations

import copy
import hashlib
import json
import stat
import threading
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image, ImageDraw

from pocketsteel.amazing_tablature_extraction import (
    DECISION_DERIVATION_VERSION,
    FEEDBACK_CORRECTION_PLAN_SCHEMA_VERSION,
    EXTRACTOR_VERSION,
    PAGE_REVIEW_COMPATIBILITY_VERSION,
    AudiverisReader,
    GridDetection,
    SCORE_AUDIT_SCOPE_SCHEMA_VERSION,
    SCORE_REPAIR_VERSION,
    SOURCE_SCORE_COMPONENT_CONTRACT,
    SOURCE_SCORE_COMPONENT_DETECTOR_VERSION,
    SOURCE_SCORE_HYBRID_DETECTOR_VERSION,
    SOURCE_SCORE_NOTEHEAD_DETECTOR_VERSION,
    SOURCE_SCORE_PROJECTION_CONTRACT,
    SOURCE_SCORE_PROJECTION_DETECTOR_VERSION,
    TAB_ONLY_APPROVAL_SECTIONS,
    VALIDATION_CAPTURE_ISSUE_KINDS,
    VALIDATION_LINE_PREFLIGHT_VERSION,
    AmazingTablatureExtractor,
    ExtractionWorkflowError,
    LocalTabVision,
    LocalTabSystemVision,
    _align_events,
    _apply_key_signature_to_score_events,
    _audiveris_notehead_columns,
    _approve_targeted_tab_corrections,
    _apply_feedback_correction_operation,
    _apply_pitch_only_score_audit_scope,
    _classify_page,
    _combined_score_tab_columns,
    _combined_score_tab_console_html,
    _combined_feedback_score_audit_bridge,
    _derive_exercises,
    _derive_grips,
    _derive_movement_sequences,
    _derive_teaching_concepts,
    _detect_score_staff_lines,
    _discovery_human_exposure_inventory,
    _digest_pinned_unindexed_score_repair_entry,
    _evaluate_event_count_fusion_rules,
    _full_line_score_recognition_events,
    _mark_grip_event_eligibility,
    _mark_review_submission_applied,
    _merge_current_source_discrepancies,
    _normalized_event_feedback,
    _normalize_score_audit_review,
    _normalize_score_payload_clef,
    _score_projection_fusion,
    _score_component_fusion,
    _score_projection_component_hybrid,
    _source_score_projection_shadow_metrics,
    _page_review_compatibility_version,
    _parse_audiveris_head_graph,
    _parse_musicxml,
    _prepare_score_tab_source_crop,
    _provisional_joint_review_blockers,
    _validation_audit_not_ready_html,
    _validation_capture_issue_count,
    _validation_line_preflight_blockers,
    _validation_machine_count_consensus,
    _machine_localized_score_events,
    _machine_localized_tab_events,
    _machine_score_is_contained_in_tab,
    _projection_tab_grid,
    _promote_full_line_record_to_combined_scope,
    _prepare_score_omr_crop,
    _prepare_guided_score_pitch_crop,
    _promote_confirmed_source_discrepancy,
    _replace_tab_event_from_score_audit,
    _profile_digest as extraction_profile_digest,
    _replace_score_attack_from_review,
    _replace_score_system_attacks_from_review,
    _review_tab_event_description,
    _rebase_score_repair_candidate_after_tab_correction,
    _review_record_counts,
    _reviewed_tab_facts_digest,
    _reviewed_tab_event_rhythmic_slot,
    _repair_repeated_score_glyph,
    _score_audit_diagnostics,
    _score_audit_equivalence_gates,
    _score_attack_groups,
    _score_repair_candidate,
    _score_tab_attack_counts_complete,
    _score_tab_pitch_relationship,
    _sha256_json,
    _separate_verified_alignments,
    _separate_verified_grips,
    _store_review_submission,
    _store_event_localization_submission,
    _store_full_line_score_recapture_submission,
    _store_score_audit_submission,
    _store_score_chord_omission_submission,
    _store_score_pitch_submission,
    _store_combined_score_tab_submission,
    _store_validation_line_audit_submission,
    _store_challenger_comparison_submission,
    _combined_review_alignments,
    _current_combined_line_entries,
    _load_combined_score_tab_packet,
    _snapshot_current_combined_score_tab_review,
    _system_x_in_source_crop,
    _tab_action_from_cell,
    _tab_action_from_token,
    _tab_action_sequence_from_cell,
    _tab_action_sequence_from_token,
    _tab_cell_horizontal_bounds,
    _tab_event_candidates,
    _tab_measure_context,
    _unreviewed_refresh_regression_gate,
    _write_normalized_score_musicxml,
    detect_tab_grids,
    extraction_acceptance_metrics,
    make_review_http_server,
    score_tab_pitch_relationship_findings,
)
from pocketsteel.amazing_tablature_training import _profile_digest as training_profile_digest
from pocketsteel.amazing_tablature_decisions import (
    _candidate,
    _voice_preserving_alternatives,
    derive_decision_annotations,
)
from pocketsteel.e9_copedents import e9_copedent_profile_digest, get_e9_copedent_profile


def _synthetic_tab() -> Image.Image:
    image = Image.new("L", (1200, 900), "white")
    draw = ImageDraw.Draw(image)
    lines = [400 + index * 22 for index in range(11)]
    for y in lines:
        draw.line((100, y, 1100, y), fill="black", width=2)
    for x in (100, 500, 1100):
        draw.line((x, lines[0], x, lines[-1]), fill="black", width=2)
    draw.rectangle((250, lines[4] + 3, 260, lines[5] - 3), fill="black")
    draw.rectangle((264, lines[4] + 3, 274, lines[5] - 3), fill="black")
    draw.rectangle((750, lines[2] + 3, 760, lines[3] - 3), fill="black")
    draw.rectangle((764, lines[2] + 3, 774, lines[3] - 3), fill="black")
    return image


def test_key_signature_application_preserves_explicit_accidentals() -> None:
    events = [
        {
            "pitchStep": "F",
            "pitchAlter": 0,
            "octave": 4,
            "pitch": "F4",
            "pitchValue": 65,
            "writtenAccidental": None,
        },
        {
            "pitchStep": "C",
            "pitchAlter": 0,
            "octave": 5,
            "pitch": "C5",
            "pitchValue": 72,
            "writtenAccidental": "natural",
        },
    ]

    normalized = _apply_key_signature_to_score_events(events, 3)

    assert normalized[0]["pitch"] == "F#4"
    assert normalized[0]["pitchValue"] == 66
    assert normalized[1]["pitch"] == "C5"
    assert normalized[1]["pitchValue"] == 72
    assert events[0]["pitch"] == "F4"


def test_detect_score_staff_lines_accepts_high_resolution_spacing() -> None:
    image = np.full((735, 3024), 255, dtype=np.uint8)
    for y in (431, 458, 485, 512, 539):
        image[y : y + 3, 390:1500] = 0
    image[472:474, 480:1300] = 0

    lines = _detect_score_staff_lines(image)

    assert len(lines) == 5
    assert lines == pytest.approx((432, 459, 486, 513, 540), abs=2)


def test_detect_score_staff_lines_rejects_tight_tab_fragment_above_staff() -> None:
    image = np.full((470, 3024), 255, dtype=np.uint8)
    # A partial ten-string grid retained from the preceding system. Its long,
    # tight rules must not win over the conventional staff below.
    for y in (16, 26, 36, 46, 56, 66):
        image[y : y + 3, 260:2750] = 0
    for y in (244, 268, 292, 316, 340):
        image[y : y + 3, 390:2735] = 0
    image[210:365, 390:400] = 0
    image[210:365, 2725:2735] = 0

    lines = _detect_score_staff_lines(image)

    assert lines == pytest.approx((245, 269, 293, 317, 341), abs=3)


def test_guided_score_crop_contains_geometry_but_no_tab_pitches(tmp_path: Path) -> None:
    source = Image.new("RGB", (1600, 500), "white")
    draw = ImageDraw.Draw(source)
    for y in (180, 205, 230, 255, 280):
        draw.line((180, y, 1450, y), fill="black", width=3)
    score_crop = tmp_path / "score-crops" / "input-1" / "score-system-01.png"
    score_crop.parent.mkdir(parents=True)
    source.save(score_crop)

    result = _prepare_guided_score_pitch_crop(
        output_root=tmp_path,
        audit_dir=tmp_path / "audit",
        input_id="input-1",
        score_system={
            "systemIndex": 1,
            "pageRegion": {"x": 0.0, "width": 1.0},
        },
        tab_system={
            "pageRegion": {"x": 0.2, "width": 0.6},
            "tabEvents": [
                {"tabEventId": "tab-1", "eventIndex": 1, "horizontalPosition": 0.25},
                {"tabEventId": "tab-2", "eventIndex": 2, "horizontalPosition": 0.75},
            ],
        },
    )

    assert Path(result["path"]).exists()
    assert [item["eventIndex"] for item in result["eventGuides"]] == [1, 2]
    assert result["tablaturePitchesIncluded"] is False
    assert "C4" in {item["pitch"] for item in result["pitchLabels"]}


def test_combined_score_tab_columns_include_movement_states_and_never_infer_harmony() -> None:
    score_system = {
        "scoreEvents": [
            {
                "scoreEventId": "score-1",
                "measure": 1,
                "beat": 1.0,
                "pitch": "E4",
                "pitchValue": 64,
                "rest": False,
            },
            {
                "scoreEventId": "score-2",
                "measure": 1,
                "beat": 2.0,
                "pitch": "F#4",
                "pitchValue": 66,
                "rest": False,
            },
        ]
    }
    tab_system = {
        "tabEvents": [
            {
                "tabEventId": "tab-1",
                "eventIndex": 1,
                "executionType": "attack",
                "steelActions": [
                    {
                        "string": 4,
                        "soundingPitchValue": 64,
                        "mechanicalValidation": {"valid": True},
                    },
                    {
                        "string": 5,
                        "soundingPitchValue": 59,
                        "mechanicalValidation": {"valid": True},
                    },
                ],
            },
            {
                "tabEventId": "tab-2",
                "eventIndex": 2,
                "executionType": "movement_only",
                "steelActions": [
                    {
                        "string": 4,
                        "soundingPitchValue": 66,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            },
        ]
    }

    result = _combined_score_tab_columns(score_system, tab_system)

    assert result["scoreAttackCount"] == 2
    assert result["tabAttackCount"] == 1
    assert result["tabMovementCount"] == 2
    assert result["movementOnlyCount"] == 1
    assert result["stateCountsAgree"] is True
    assert result["columns"][0]["relationship"] == "subset_requires_review"
    assert result["columns"][1]["relationship"] == "exact"
    assert result["columns"][1]["representsSustainMovement"] is True
    assert len(result["columns"]) == 2
    assert all(
        column["scoreAttack"] is not None and column["tabState"] is not None
        for column in result["anchorAlignedColumns"]
    )
    assert result["falseHarmonyInferenceAllowed"] is False
    assert result["automaticPitchGatePassed"] is False
    assert result["trainingEligible"] is False


def test_combined_score_tab_columns_anchor_later_exact_pitches_after_an_omission() -> None:
    score_system = {
        "scoreEvents": [
            {
                "scoreEventId": f"score-{index}",
                "measure": 1,
                "beat": float(index),
                "pitch": pitch,
                "pitchValue": pitch_value,
                "rest": False,
            }
            for index, (pitch, pitch_value) in enumerate(
                (("E4", 64), ("F4", 65), ("G4", 67)), start=1
            )
        ]
    }
    tab_system = {
        "tabEvents": [
            {
                "tabEventId": f"tab-{index}",
                "eventIndex": index,
                "executionType": "attack",
                "steelActions": [
                    {
                        "string": 4,
                        "soundingPitchValue": pitch_value,
                        "attack": True,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            }
            for index, pitch_value in enumerate((60, 64, 65, 67), start=1)
        ]
    }

    result = _combined_score_tab_columns(score_system, tab_system)

    assert result["exactColumnCount"] == 0
    assert result["exactAnchorCount"] == 3
    assert result["anchorImprovementCount"] == 3
    assert result["anchoredDiscrepancyColumnCount"] == 1
    assert [
        column["alignmentRole"] for column in result["anchorAlignedColumns"]
    ] == [
        "unmatched_tab_attack",
        "exact_pitch_anchor",
        "exact_pitch_anchor",
        "exact_pitch_anchor",
    ]
    assert [
        column["relationship"] for column in result["anchorAlignedColumns"]
    ] == ["score_attack_not_captured", "exact", "exact", "exact"]
    assert result["automaticPitchGatePassed"] is False
    assert result["trainingEligible"] is False


def test_combined_score_tab_console_explains_written_and_sustained_changes() -> None:
    html = _combined_score_tab_console_html(packet_digest="packet-anchor-test")

    assert "Exact pitch-and-octave matches are used as anchors" in html
    assert "one disagreement cannot shift every later comparison" in html
    assert "Each written musical change is compared with the sounding tablature change" in html
    assert "pedal/lever movement while the strings continue ringing" in html
    assert "validation?cmp.columns:(cmp.anchorAlignedColumns||cmp.columns)" in html
    assert "differences shown below" in html
    assert "function differenceCards(columns,keyFifths,validation=false)" in html
    assert "function displayTabPitches(column)" in html
    assert "spellings.get(Number(value))" in html
    assert "function eventStaff(pitches,label,keyFifths)" in html
    assert "function keySignatureSymbols(fifths,bottom=75,startX=80,gap=12)" in html
    assert "function eventAccidental(p,keyFifths)" in html
    assert "function staffSvg(attacks,label,keyFifths)" in html
    assert "staffSvg(cmp.scoreAttacks,'Independent score-only reading',keyFifths)" in html
    assert "staffSvg(displayColumns.map(c=>({pitches:displayTabPitches(c)})),tabStaffLabel,keyFifths)" in html
    assert "printed key:" in html
    assert "A and B are unverified machine outputs" in html
    assert "Each example uses the captured printed key signature" in html
    assert "printed key: ${keyLabel}" in html
    assert "keyKnown=system.keySignatureKnown===true" in html
    assert "class=\"event-staff\"" in html
    assert "No captured event" in html
    assert "Review only these differences" in html
    assert "Every event not shown here already agrees exactly in pitch and octave" in html
    assert "Open the full-line renderings and tablature only if needed" in html
    assert "Name only the affected event numbers" in html
    assert "function incompleteLines()" in html
    assert "function focusIncomplete(item)" in html
    assert "Finish ${first.sourceLabel} line ${first.lineNumber+1}" in html
    assert "submit').disabled=Boolean(missing.length)" in html
    assert "packet-anchor-test" in html
    digest = "a" * 64
    versioned = _combined_score_tab_console_html(
        packet_digest=digest,
        packet_filename=f"packet-{digest}.json",
    )
    assert f"fetch('./packet-{digest}.json'" in versioned


def test_current_combined_packet_snapshot_survives_later_canonical_packet(
    tmp_path: Path,
) -> None:
    review_dir = tmp_path / "combined-score-tab-audit"
    review_dir.mkdir()
    first_core = {
        "batchId": "batch-combined",
        "partition": "discovery",
        "pages": [{"inputId": "input-first", "systems": []}],
    }
    first_digest = _sha256_json(first_core)
    first_packet = {**first_core, "packetDigest": first_digest}
    canonical_path = review_dir / "packet.json"
    canonical_path.write_text(json.dumps(first_packet), encoding="utf-8")
    (review_dir / "score-candidate-index.jsonl").write_text(
        json.dumps({"inputId": "input-first"}) + "\n",
        encoding="utf-8",
    )
    canonical_before = canonical_path.read_bytes()

    snapshot = _snapshot_current_combined_score_tab_review(review_dir)

    assert snapshot is not None
    assert snapshot["packetDigest"] == first_digest
    assert canonical_path.read_bytes() == canonical_before
    assert (review_dir / f"packet-{first_digest}.json").exists()
    assert (review_dir / f"score-candidate-index-{first_digest}.jsonl").exists()
    assert (
        review_dir / f"combined-score-tab-audit-console-{first_digest[:12]}.html"
    ).exists()

    later_core = {
        "batchId": "batch-combined",
        "partition": "discovery",
        "pages": [{"inputId": "input-later", "systems": []}],
    }
    later_digest = _sha256_json(later_core)
    canonical_path.write_text(
        json.dumps({**later_core, "packetDigest": later_digest}), encoding="utf-8"
    )

    resolved, resolved_path = _load_combined_score_tab_packet(review_dir, first_digest)

    assert resolved == first_packet
    assert resolved_path == review_dir / f"packet-{first_digest}.json"


def test_combined_feedback_bridges_directly_to_score_correction_scope(
    tmp_path: Path,
) -> None:
    review_root = tmp_path / "review"
    combined_dir = review_root / "combined-score-tab-audit"
    application_dir = combined_dir / "application"
    application_dir.mkdir(parents=True)
    packet_core = {
        "batchId": "batch-combined",
        "partition": "discovery",
        "pages": [
            {
                "inputId": "input-0001",
                "systems": [
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-system-1",
                        "scoreCandidateDigest": "c" * 64,
                    }
                ],
            }
        ],
    }
    packet_digest = _sha256_json(packet_core)
    (combined_dir / f"packet-{packet_digest}.json").write_text(
        json.dumps({**packet_core, "packetDigest": packet_digest}),
        encoding="utf-8",
    )
    (application_dir / "feedback-queue.jsonl").write_text(
        json.dumps(
            {
                "feedbackId": "combined-feedback-1",
                "inputId": "input-0001",
                "scoreSystemId": "score-system-1",
                "packetDigest": packet_digest,
                "submissionDigest": "s" * 64,
                "comment": "Correct all seven score changes.",
                "status": "unresolved_requires_structured_correction",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    bridged = _combined_feedback_score_audit_bridge(review_root)

    assert bridged["combined-feedback-1"]["auditedCandidateDigest"] == "c" * 64
    assert bridged["combined-feedback-1"]["systemDecisions"] == [
        {
            "scoreSystemId": "score-system-1",
            "status": "feedback",
            "comment": "Correct all seven score changes.",
        }
    ]
    assert bridged["combined-feedback-1"]["source"] == "combined_score_tab_review"


def test_combined_score_tab_submission_requires_every_line_and_digest(tmp_path: Path) -> None:
    private = tmp_path / "private"
    review_dir = (
        private
        / "batches"
        / "batch-combined"
        / "extraction"
        / "discovery"
        / "review"
        / "combined-score-tab-audit"
    )
    review_dir.mkdir(parents=True)
    packet_core = {
        "batchId": "batch-combined",
        "partition": "discovery",
        "pages": [
            {
                "inputId": "input-0001",
                "systems": [
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-1",
                        "tabSystemId": "tab-1",
                        "machineRecordDigest": "machine-1",
                        "scoreCandidateDigest": "candidate-1",
                        "comparison": {"automaticPitchGatePassed": True},
                    },
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-2",
                        "tabSystemId": "tab-2",
                        "machineRecordDigest": "machine-1",
                        "scoreCandidateDigest": "candidate-1",
                        "comparison": {"automaticPitchGatePassed": False},
                    },
                ],
            }
        ],
    }
    digest = _sha256_json(packet_core)
    (review_dir / "packet.json").write_text(
        json.dumps({**packet_core, "packetDigest": digest}), encoding="utf-8"
    )

    base_payload = {
        "batchId": "batch-combined",
        "partition": "discovery",
        "packetDigest": digest,
    }
    with pytest.raises(ExtractionWorkflowError, match="Every combined score/tab line"):
        _store_combined_score_tab_submission(
            private,
            {
                **base_payload,
                "reviews": [
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-1",
                        "status": "both_match",
                    }
                ],
            },
        )
    with pytest.raises(ExtractionWorkflowError, match="only when their complete pitch sets agree"):
        _store_combined_score_tab_submission(
            private,
            {
                **base_payload,
                "reviews": [
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-1",
                        "status": "both_match",
                    },
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-2",
                        "status": "both_match",
                    },
                ],
            },
        )
    with pytest.raises(ExtractionWorkflowError, match="packet digest"):
        _store_combined_score_tab_submission(
            private,
            {
                **base_payload,
                "packetDigest": "stale",
                "reviews": [
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-1",
                        "status": "both_match",
                    }
                ],
            },
        )

    result = _store_combined_score_tab_submission(
        private,
        {
            **base_payload,
            "reviews": [
                {
                    "inputId": "input-0001",
                    "scoreSystemId": "score-1",
                    "status": "both_match",
                },
                {
                    "inputId": "input-0001",
                    "scoreSystemId": "score-2",
                    "status": "tab_pitch_hypothesis_matches",
                },
            ],
        },
    )
    assert result["reviewCount"] == 2
    assert result["status"] == "received_not_applied"
    assert result["deduplicated"] is False
    assert (
        _store_combined_score_tab_submission(
            private,
            {
                **base_payload,
                "reviews": [
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-1",
                        "status": "both_match",
                    },
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-2",
                        "status": "tab_pitch_hypothesis_matches",
                    },
                ],
            },
        )["deduplicated"]
        is True
    )


def test_challenger_comparison_submission_is_complete_and_digest_pinned(
    tmp_path: Path,
) -> None:
    private = tmp_path / "private"
    review_dir = (
        private
        / "batches/batch-challenger/extraction/discovery/review/challenger-comparison"
    )
    review_dir.mkdir(parents=True)
    packet_core = {
        "batchId": "batch-challenger",
        "modelId": "model-1",
        "systems": [
            {
                "disagreements": [
                    {
                        "decisionId": "decision-1",
                        "inputId": "input-0001",
                        "scoreSystemId": "score-1",
                        "sourceTabEventId": "tab-event-1",
                    },
                    {
                        "decisionId": "decision-2",
                        "inputId": "input-0001",
                        "scoreSystemId": "score-1",
                        "sourceTabEventId": "tab-event-2",
                    },
                ]
            }
        ],
    }
    digest = _sha256_json(packet_core)
    (review_dir / f"packet-{digest}.json").write_text(
        json.dumps({**packet_core, "packetDigest": digest}), encoding="utf-8"
    )
    base = {
        "batchId": "batch-challenger",
        "packetDigest": digest,
    }
    with pytest.raises(ExtractionWorkflowError, match="Every shown challenger difference"):
        _store_challenger_comparison_submission(
            private,
            {
                **base,
                "reviews": [
                    {"decisionId": "decision-1", "status": "source_preferred"}
                ],
            },
        )

    result = _store_challenger_comparison_submission(
        private,
        {
            **base,
            "reviews": [
                {"decisionId": "decision-1", "status": "source_preferred"},
                {"decisionId": "decision-2", "status": "both_valid"},
            ],
        },
    )

    assert result["reviewCount"] == 2
    assert result["status"] == "received_not_applied"


def test_joint_combined_submission_requires_explicit_tab_confirmation(tmp_path: Path) -> None:
    private = tmp_path / "private"
    review_dir = (
        private
        / "batches/batch-joint/extraction/discovery/review/combined-score-tab-audit"
    )
    review_dir.mkdir(parents=True)
    packet_core = {
        "batchId": "batch-joint",
        "partition": "discovery",
        "jointTabReviewRequired": True,
        "pages": [
            {
                "inputId": "input-0001",
                "systems": [
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-1",
                        "tabSystemId": "tab-1",
                        "machineRecordDigest": "machine-1",
                        "scoreCandidateDigest": "candidate-1",
                        "comparison": {"automaticPitchGatePassed": True},
                    }
                ],
            }
        ],
    }
    digest = _sha256_json(packet_core)
    (review_dir / "packet.json").write_text(
        json.dumps({**packet_core, "packetDigest": digest}), encoding="utf-8"
    )
    payload = {
        "batchId": "batch-joint",
        "partition": "discovery",
        "packetDigest": digest,
        "reviews": [
            {
                "inputId": "input-0001",
                "scoreSystemId": "score-1",
                "status": "both_match",
            }
        ],
    }

    with pytest.raises(ExtractionWorkflowError, match="explicit confirmation"):
        _store_combined_score_tab_submission(private, payload)

    result = _store_combined_score_tab_submission(
        private,
        {
            **payload,
            "reviews": [{**payload["reviews"][0], "tabConfirmed": True}],
        },
    )
    assert result["reviewCount"] == 1
    submission_path = review_dir / "submissions" / f"{result['submissionId']}.jsonl"
    submission = json.loads(submission_path.read_text(encoding="utf-8"))
    assert submission["tabConfirmed"] is True
    versioned_core = {
        "batchId": "batch-combined",
        "partition": "discovery",
        "pages": [
            {
                "inputId": "input-0002",
                "systems": [
                    {
                        "inputId": "input-0002",
                        "scoreSystemId": "score-versioned",
                        "tabSystemId": "tab-versioned",
                        "machineRecordDigest": "machine-versioned",
                        "scoreCandidateDigest": "candidate-versioned",
                        "comparison": {"automaticPitchGatePassed": False},
                    }
                ],
            }
        ],
    }
    versioned_digest = _sha256_json(versioned_core)
    versioned_review_dir = (
        private
        / "batches/batch-combined/extraction/discovery/review/combined-score-tab-audit"
    )
    versioned_review_dir.mkdir(parents=True, exist_ok=True)
    (versioned_review_dir / f"packet-{versioned_digest}.json").write_text(
        json.dumps({**versioned_core, "packetDigest": versioned_digest}),
        encoding="utf-8",
    )

    versioned_result = _store_combined_score_tab_submission(
        private,
        {
            "batchId": "batch-combined",
            "partition": "discovery",
            "packetDigest": versioned_digest,
            "reviews": [
                {
                    "inputId": "input-0002",
                    "scoreSystemId": "score-versioned",
                    "status": "score_reader_matches",
                }
            ],
        },
    )

    assert versioned_result["reviewCount"] == 1
    assert versioned_result["status"] == "received_not_applied"


def test_validation_line_audit_submission_is_complete_and_never_training(
    tmp_path: Path,
) -> None:
    private = tmp_path / "private"
    review_dir = (
        private
        / "batches/batch-validation/extraction/validation/review/validation-line-audit"
    )
    review_dir.mkdir(parents=True)
    packet_core = {
        "schemaVersion": "amazing-tablature-validation-line-audit-v1",
        "reviewType": "validation_line_audit",
        "preflightVersion": VALIDATION_LINE_PREFLIGHT_VERSION,
        "batchId": "batch-validation",
        "partition": "validation",
        "trainingEligible": False,
        "validationGroundTruthMayTrain": False,
        "sealedTestAccessed": False,
        "pages": [
            {
                "inputId": "input-0001",
                "systems": [
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-1",
                        "tabSystemId": "tab-1",
                        "machineRecordDigest": "machine-1",
                        "capturePreflightPassed": True,
                        "lineGatePassed": True,
                        "validationIssueSummary": {
                            "blockingCount": 0,
                            "digest": "issue-1",
                        },
                    },
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-2",
                        "tabSystemId": "tab-2",
                        "machineRecordDigest": "machine-1",
                        "capturePreflightPassed": True,
                        "lineGatePassed": False,
                        "validationIssueSummary": {
                            "blockingCount": 3,
                            "digest": "issue-2",
                        },
                    },
                ],
            }
        ],
    }
    packet_digest = _sha256_json(packet_core)
    (review_dir / f"packet-{packet_digest}.json").write_text(
        json.dumps({**packet_core, "packetDigest": packet_digest}),
        encoding="utf-8",
    )
    base_payload = {
        "reviewType": "validation_line_audit",
        "batchId": "batch-validation",
        "partition": "validation",
        "packetDigest": packet_digest,
    }

    with pytest.raises(ExtractionWorkflowError, match="Every validation line"):
        _store_validation_line_audit_submission(
            private,
            {
                **base_payload,
                "reviews": [
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-1",
                        "status": "both_match",
                        "tabConfirmed": True,
                    }
                ],
            },
        )

    result = _store_validation_line_audit_submission(
        private,
        {
            **base_payload,
            "reviews": [
                {
                    "inputId": "input-0001",
                    "scoreSystemId": "score-1",
                    "status": "both_match",
                    "tabConfirmed": True,
                },
                {
                    "inputId": "input-0001",
                    "scoreSystemId": "score-2",
                    "status": "capture_failed",
                    "tabConfirmed": False,
                },
            ],
        },
    )

    assert result["reviewCount"] == 2
    assert result["eligibleForTraining"] is False
    assert result["sealedTestAccessed"] is False
    metadata = json.loads(
        (
            review_dir
            / "submissions"
            / f"{result['submissionId']}.json"
        ).read_text(encoding="utf-8")
    )
    assert metadata["validationGroundTruthMayTrain"] is False
    assert metadata["status"] == "received_validation_ground_truth_not_scored"

    legacy_packet_core = {
        key: value
        for key, value in packet_core.items()
        if key != "preflightVersion"
    }
    legacy_packet_digest = _sha256_json(legacy_packet_core)
    (review_dir / f"packet-{legacy_packet_digest}.json").write_text(
        json.dumps(
            {**legacy_packet_core, "packetDigest": legacy_packet_digest}
        ),
        encoding="utf-8",
    )
    with pytest.raises(ExtractionWorkflowError, match="withdrawn"):
        _store_validation_line_audit_submission(
            private,
            {
                **base_payload,
                "packetDigest": legacy_packet_digest,
                "reviews": [
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-1",
                        "status": "both_match",
                        "tabConfirmed": True,
                    },
                    {
                        "inputId": "input-0001",
                        "scoreSystemId": "score-2",
                        "status": "capture_failed",
                        "tabConfirmed": False,
                    },
                ],
            },
        )


def test_combined_console_supports_validation_ground_truth_mode() -> None:
    digest = "b" * 64
    html = _combined_score_tab_console_html(
        packet_digest=digest,
        packet_filename=f"packet-{digest}.json",
        review_type="validation_line_audit",
    )

    assert "REVIEW_TYPE='validation_line_audit'" in html
    assert "This is validation, not more training" in html
    assert "prohibited from challenger training" in html
    assert "machine flagged this line" in html
    assert "Machine capture failed this line" in html
    assert "Machine-captured ten-string tablature (not ground truth)" in html
    assert "pitch calculated from machine-captured tab" in html
    assert "['capture_failed','feedback']" in html
    assert "partition:packet.partition" in html
    assert "bothMatch.disabled=false" in html


def test_provisional_joint_review_rejects_reviewer_reconstruction_work() -> None:
    comparison = {
        "countsAgree": False,
        "anchorAlignedColumns": [
            {"scoreAttack": None, "tabState": {"eventIndex": 1}},
            {"scoreAttack": {"attackIndex": 2}, "tabState": None},
        ],
    }

    assert _provisional_joint_review_blockers(
        comparison, key_signature_known=False
    ) == [
        "key_signature_not_captured",
        "score_tab_attack_count_mismatch",
        "empty_score_comparison_column",
        "empty_tablature_comparison_column",
    ]


def test_validation_line_preflight_requires_complete_equal_renderings() -> None:
    score_attacks = [
        {"pitches": ["C5"], "pitchValues": [72]},
        {"pitches": ["D5"], "pitchValues": [74]},
    ]
    tab_states = [
        {"pitches": ["C5"], "steelActions": [{"string": 4, "fret": 8}]},
        {"pitches": ["D5"], "steelActions": [{"string": 1, "fret": 8}]},
    ]
    complete = {
        "scoreAttackCount": 2,
        "tabMovementCount": 2,
        "scoreAttacks": score_attacks,
        "tabStates": tab_states,
        "columns": [
            {"scoreAttack": score_attacks[0], "tabState": tab_states[0]},
            {"scoreAttack": score_attacks[1], "tabState": tab_states[1]},
        ],
        "mechanicallyValid": True,
    }

    assert _validation_line_preflight_blockers(
        complete, key_signature_known=True, blocking_issue_count=0
    ) == []

    incomplete = {
        **complete,
        "scoreAttackCount": 0,
        "scoreAttacks": [],
        "columns": [
            {"scoreAttack": None, "tabState": tab_states[0]},
            {"scoreAttack": None, "tabState": tab_states[1]},
        ],
    }
    blockers = _validation_line_preflight_blockers(
        incomplete, key_signature_known=False, blocking_issue_count=1
    )
    assert blockers == [
        "score_events_missing",
        "score_tablature_event_count_mismatch",
        "blank_or_misaligned_comparison_event",
        "key_signature_not_captured",
        "unresolved_reader_issue",
    ]

    incomplete_tab = {
        **complete,
        "tabStates": [
            tab_states[0],
            {
                **tab_states[1],
                "steelActions": [{"string": 1, "fret": None}],
            },
        ],
    }
    assert _validation_line_preflight_blockers(
        incomplete_tab, key_signature_known=True, blocking_issue_count=0
    ) == ["incomplete_tablature_event_payload"]


def test_validation_capture_issues_distinguish_reader_failures_from_musical_differences() -> None:
    assert "score_omr_failure" in VALIDATION_CAPTURE_ISSUE_KINDS
    issues = [
        {"kind": "score_omr_failure", "blocking": True},
        {"kind": "unresolved_tab_event_candidate", "blocking": True},
        {"kind": "unverified_score_tab_alignment", "blocking": True},
        {"kind": "score_pitch_not_in_tab", "blocking": True},
        {"kind": "tab_cell_vision_failure", "blocking": False},
    ]

    assert _validation_capture_issue_count(issues) == 2


def test_validation_machine_count_consensus_requires_two_confident_matching_readers() -> None:
    tab_system = {"tabEventCandidates": [{}, {}, {}]}

    assert _validation_machine_count_consensus(
        tab_system,
        {"eventCount": 3, "confidence": 0.94, "uncertain": False},
    ) == (3, [])
    assert _validation_machine_count_consensus(
        tab_system,
        {"eventCount": 2, "confidence": 0.94, "uncertain": False},
    ) == (None, ["independent_tab_count_disagreement"])
    assert _validation_machine_count_consensus(
        tab_system,
        {"eventCount": 3, "confidence": 0.7, "uncertain": True},
    ) == (None, ["low_confidence_tab_count"])


def test_machine_localized_events_require_complete_valid_tab_and_source_pitch_containment() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    tab_system = {
        "tabSystemId": "tab-1",
        "tabEventCandidates": [
            {"horizontalPosition": 0.2, "candidateStrings": [4, 5]},
            {"horizontalPosition": 0.8, "candidateStrings": [4]},
        ],
    }
    localization = {
        "events": [
            {
                "x": 0.3043478,
                "execution": "attack",
                "cells": [
                    {"string": 4, "token": "8"},
                    {"string": 5, "token": "8"},
                ],
            },
            {
                "x": 0.826087,
                "execution": "movement_only",
                "cells": [{"string": 4, "token": "10"}],
            },
        ],
        "confidence": 0.96,
        "uncertain": False,
    }
    tab_events = _machine_localized_tab_events(
        input_id="input-1",
        tab_system=tab_system,
        localization=localization,
        crop_metadata={
            "contentX0": 150,
            "contentX1": 1150,
            "width": 1150,
        },
        expected_count=2,
        profile=profile,
    )

    assert [event["candidateStrings"] for event in tab_events] == [[4, 5], [4]]
    assert [event["executionType"] for event in tab_events] == ["attack", "movement_only"]
    assert all(
        action["mechanicalValidation"]["valid"]
        for event in tab_events
        for action in event["steelActions"]
    )

    recognition = {
        "events": [
            {"pitches": ["C5"], "pitchValues": [72]},
            {"pitches": ["D5"], "pitchValues": [74]},
        ],
        "confidence": 0.97,
        "uncertain": False,
    }
    score_events = _machine_localized_score_events(
        input_id="input-1",
        score_system={"scoreSystemId": "score-1"},
        recognition=recognition,
        tab_events=tab_events,
    )

    assert [event["pitch"] for event in score_events] == ["C5", "D5"]
    assert _machine_score_is_contained_in_tab(score_events, tab_events) is True

    wrong_score = copy.deepcopy(score_events)
    wrong_score[1]["pitch"] = "E5"
    wrong_score[1]["pitchValue"] = 76
    assert _machine_score_is_contained_in_tab(wrong_score, tab_events) is False


def test_machine_localized_tab_events_fail_closed_on_blank_or_invalid_states() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    common = {
        "input_id": "input-1",
        "tab_system": {"tabSystemId": "tab-1"},
        "crop_metadata": {"contentX0": 150, "contentX1": 1150, "width": 1150},
        "expected_count": 1,
        "profile": profile,
    }

    with pytest.raises(ExtractionWorkflowError, match="blank event"):
        _machine_localized_tab_events(
            **common,
            localization={
                "events": [{"x": 0.5, "execution": "attack", "cells": []}],
                "confidence": 0.95,
                "uncertain": False,
            },
        )
    with pytest.raises(ExtractionWorkflowError, match="invalid state"):
        _machine_localized_tab_events(
            **common,
            localization={
                "events": [
                    {
                        "x": 0.5,
                        "execution": "attack",
                        "cells": [{"string": 4, "token": "8A"}],
                    }
                ],
                "confidence": 0.95,
                "uncertain": False,
            },
        )


def test_validation_not_ready_page_contains_no_review_controls() -> None:
    html = _validation_audit_not_ready_html(
        {
            "lineCount": 8,
            "blockedLineCount": 8,
            "noLinePageCount": 2,
            "readinessDigest": "a" * 64,
        }
    )

    assert "Not ready for human review" in html
    assert "validation audit has been withdrawn" in html
    assert "same event count" in html
    assert "<form" not in html
    assert "Submit all reviewed lines" not in html


def test_validation_audit_is_withdrawn_before_incomplete_lines_are_published(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    private = tmp_path / "private"
    batch_dir = private / "batches" / "batch-validation"
    output_root = batch_dir / "extraction" / "validation"
    pages_dir = output_root / "pages"
    pages_dir.mkdir(parents=True)
    (output_root / "summary.json").write_text(
        json.dumps(
            {
                "partition": "validation",
                "extractorVersion": EXTRACTOR_VERSION,
                "failedPageCount": 0,
                "sealedTestAccessed": False,
                "runDigest": "run-validation",
                "validationModel": {
                    "modelId": "at-frozen",
                    "artifactSha256": "a" * 64,
                },
            }
        ),
        encoding="utf-8",
    )
    (pages_dir / "input-0001.json").write_text(
        json.dumps(
            {
                "inputId": "input-0001",
                "datasetPartition": "validation",
                "extractorVersion": EXTRACTOR_VERSION,
                "runDigest": "run-validation",
                "scoreSystems": [
                    {
                        "scoreSystemId": "score-system-1",
                        "systemIndex": 1,
                        "pairedTabSystemId": "tab-system-1",
                        "scoreEvents": [],
                    }
                ],
                "tabSystems": [
                    {
                        "tabSystemId": "tab-system-1",
                        "systemIndex": 1,
                        "tabEvents": [
                            {
                                "tabEventId": "tab-event-1",
                                "eventIndex": 1,
                                "steelActions": [
                                    {
                                        "steelActionId": "action-1",
                                        "string": 4,
                                        "fret": 8,
                                        "attack": True,
                                        "soundingPitch": "C5",
                                        "soundingPitchValue": 72,
                                        "mechanicalValidation": {"valid": True},
                                    }
                                ],
                            }
                        ],
                    }
                ],
                "unresolved": [
                    {
                        "kind": "score_omr_failure",
                        "scoreSystemId": "score-system-1",
                        "blocking": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    extractor = AmazingTablatureExtractor(private)
    monkeypatch.setattr(
        extractor,
        "_batch_paths",
        lambda _batch_id, _partition: (
            batch_dir,
            {
                "inputs": [
                    {"inputId": "input-0001", "relativePath": "SOURCE.JPG"}
                ]
            },
            [{"inputId": "input-0001", "datasetPartition": "validation"}],
        ),
    )

    result = extractor.prepare_validation_line_audit("batch-validation")

    assert result["status"] == "blocked_before_human_review"
    assert result["auditPublished"] is False
    assert result["blockedLineCount"] == 1
    assert result["sealedTestAccessed"] is False
    audit_dir = output_root / "review" / "validation-line-audit"
    active_html = (audit_dir / "validation-line-audit-console.html").read_text(
        encoding="utf-8"
    )
    assert "Not ready for human review" in active_html
    assert not (audit_dir / "packet.json").exists()


def test_provisional_joint_review_allows_explicit_sustain_movement() -> None:
    comparison = {
        "countsAgree": True,
        "anchorAlignedColumns": [
            {
                "scoreAttack": {"attackIndex": 1},
                "tabState": {"eventIndex": 1},
                "relationship": "exact",
            },
            {
                "scoreAttack": None,
                "tabState": {"eventIndex": 2},
                "relationship": "movement_during_sustain",
                "alignmentRole": "sustain_movement",
            },
        ],
    }

    assert _provisional_joint_review_blockers(
        comparison, key_signature_known=True
    ) == []


def test_combined_review_key_lookup_accepts_canonical_key_fifths_field() -> None:
    score_system = {"keyFifths": 2}
    key_signature = score_system.get("keySignature") or {}
    captured = (
        score_system.get("keySignatureFifths")
        if score_system.get("keySignatureFifths") is not None
        else (
            key_signature.get("fifths")
            if isinstance(key_signature, dict) and key_signature.get("fifths") is not None
            else score_system.get("keyFifths")
        )
    )

    assert captured == 2


def test_combined_review_alignments_distinguish_exact_and_melody_to_grip() -> None:
    score_system = {
        "scoreEvents": [
            {
                "scoreEventId": "score-1",
                "measure": 1,
                "beat": 1.0,
                "pitch": "E4",
                "pitchValue": 64,
                "rest": False,
            },
            {
                "scoreEventId": "score-2",
                "measure": 1,
                "beat": 2.0,
                "pitch": "F#4",
                "pitchValue": 66,
                "rest": False,
            },
        ]
    }
    tab_system = {
        "tabEvents": [
            {
                "tabEventId": "tab-1",
                "eventIndex": 1,
                "executionType": "attack",
                "steelActions": [
                    {"string": 4, "soundingPitchValue": 64, "mechanicalValidation": {"valid": True}},
                    {"string": 5, "soundingPitchValue": 59, "mechanicalValidation": {"valid": True}},
                ],
            },
            {
                "tabEventId": "tab-2",
                "eventIndex": 2,
                "executionType": "attack",
                "steelActions": [
                    {"string": 4, "soundingPitchValue": 66, "mechanicalValidation": {"valid": True}}
                ],
            },
        ]
    }

    alignments, scope = _combined_review_alignments(
        score_system, tab_system, decision_id="decision-1"
    )

    assert scope["mode"] == "melody_top_note_to_grip"
    assert scope["pitchToTabTrainingEligible"] is True
    assert len(alignments) == 2
    assert alignments[0]["alignmentType"] == "melody_top_note_to_grip"
    assert alignments[1]["tabStateExecutionType"] == "attack"
    assert all(item["scoreRhythmTrainingEligible"] is False for item in alignments)


def test_combined_review_alignments_attach_no_pick_movement_to_prior_score_attack() -> None:
    score_system = {
        "scoreEvents": [
            {
                "scoreEventId": "score-1",
                "measure": 1,
                "beat": 1.0,
                "pitch": "E4",
                "pitchValue": 64,
                "rest": False,
            }
        ]
    }
    tab_system = {
        "tabEvents": [
            {
                "tabEventId": "tab-1",
                "eventIndex": 1,
                "executionType": "attack",
                "steelActions": [
                    {
                        "string": 4,
                        "soundingPitchValue": 64,
                        "attack": True,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            },
            {
                "tabEventId": "tab-2",
                "eventIndex": 2,
                "executionType": "movement_only",
                "steelActions": [
                    {
                        "string": 4,
                        "soundingPitchValue": 66,
                        "attack": False,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            },
        ]
    }

    comparison = _combined_score_tab_columns(score_system, tab_system)
    alignments, scope = _combined_review_alignments(
        score_system, tab_system, decision_id="decision-sustain"
    )

    assert comparison["countsAgree"] is True
    assert comparison["automaticPitchGatePassed"] is True
    assert comparison["movementOnlyCount"] == 1
    assert scope["pitchToTabTrainingEligible"] is True
    assert [item["alignmentType"] for item in alignments] == [
        "score_attack_to_tab_state",
        "sustained_score_to_control_movement",
    ]
    assert alignments[1]["scoreEventIds"] == ["score-1"]
    assert (
        alignments[1]["fieldReviewStates"]["pitchCorrespondence"]
        == "not_applicable_sustain_movement"
    )


def test_combined_review_alignments_map_written_change_to_no_pick_movement() -> None:
    score_system = {
        "scoreEvents": [
            {
                "scoreEventId": "score-1",
                "measure": 1,
                "beat": 1.0,
                "pitch": "E4",
                "pitchValue": 64,
                "rest": False,
            },
            {
                "scoreEventId": "score-2",
                "measure": 1,
                "beat": 2.0,
                "pitch": "F#4",
                "pitchValue": 66,
                "rest": False,
            },
        ]
    }
    tab_system = {
        "tabEvents": [
            {
                "tabEventId": "tab-1",
                "eventIndex": 1,
                "executionType": "attack",
                "steelActions": [
                    {
                        "string": 4,
                        "soundingPitchValue": 64,
                        "attack": True,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            },
            {
                "tabEventId": "tab-2",
                "eventIndex": 2,
                "executionType": "movement_only",
                "steelActions": [
                    {
                        "string": 4,
                        "soundingPitchValue": 66,
                        "attack": False,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            },
        ]
    }

    comparison = _combined_score_tab_columns(score_system, tab_system)
    alignments, scope = _combined_review_alignments(
        score_system, tab_system, decision_id="decision-written-sustain-change"
    )

    assert comparison["stateCountsAgree"] is True
    assert comparison["automaticPitchGatePassed"] is True
    assert [column["relationship"] for column in comparison["columns"]] == [
        "exact",
        "exact",
    ]
    assert scope["mode"] == "exact_pitch_sets_including_sustain_changes"
    assert scope["pitchToTabTrainingEligible"] is True
    assert alignments[1]["alignmentType"] == "sustained_score_to_control_movement"
    assert alignments[1]["scoreEventIds"] == ["score-2"]
    assert alignments[1]["pitchRelationship"] == "exact"
    assert (
        alignments[1]["fieldReviewStates"]["pitchCorrespondence"]
        == "human_approved"
    )


def test_combined_review_alignments_withhold_ambiguous_correspondence() -> None:
    score_system = {
        "scoreEvents": [
            {
                "scoreEventId": "score-1",
                "measure": 1,
                "beat": 1.0,
                "pitch": "E4",
                "pitchValue": 64,
                "rest": False,
            }
        ]
    }
    tab_system = {
        "tabEvents": [
            {
                "tabEventId": "tab-1",
                "eventIndex": 1,
                "steelActions": [
                    {"string": 4, "soundingPitchValue": 62, "mechanicalValidation": {"valid": True}}
                ],
            }
        ]
    }

    alignments, scope = _combined_review_alignments(
        score_system, tab_system, decision_id="decision-2"
    )

    assert alignments == []
    assert scope["mode"] == "unresolved_correspondence"
    assert scope["pitchToTabTrainingEligible"] is False


def test_current_combined_line_entries_supersede_older_append_only_decisions() -> None:
    shared = {
        "batchId": "batch-1",
        "partition": "discovery",
        "inputId": "input-0001",
        "scoreSystemId": "score-1",
    }
    entries = _current_combined_line_entries(
        [
            {**shared, "decisionId": "old", "trainingEligible": True},
            {**shared, "decisionId": "new", "trainingEligible": False},
            {
                **shared,
                "scoreSystemId": "score-2",
                "decisionId": "other-line",
                "trainingEligible": True,
            },
        ]
    )

    assert len(entries) == 2
    assert {
        (item["scoreSystemId"], item["decisionId"])
        for item in entries
    } == {("score-1", "new"), ("score-2", "other-line")}


def test_score_recognition_is_reused_when_only_confirmed_tab_facts_change(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "extraction/discovery"
    candidate_root = (
        output_root
        / "review/score-audit/repair/candidate-records/input-0001"
    )
    candidate_root.mkdir(parents=True)
    musicxml = output_root / "review/score-audit/repair/omr-output/score.musicxml"
    musicxml.parent.mkdir(parents=True)
    musicxml.write_bytes(b"recognized-score")
    musicxml_digest = hashlib.sha256(b"recognized-score").hexdigest()
    score_system = {
        "scoreSystemId": "score-1",
        "pairedTabSystemId": "tab-1",
        "cropSha256": "score-crop-sha",
        "pageRegion": {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.2},
        "recognizedMusicXml": {
            "relativePath": str(musicxml.relative_to(output_root)),
            "sha256": musicxml_digest,
        },
        "scoreEvents": [
            {
                "scoreEventId": "score-event-1",
                "measure": 1,
                "beat": 1.0,
                "pitch": "E4",
                "pitchValue": 64,
                "rest": False,
            }
        ],
    }
    old_tab = {
        "tabSystemId": "tab-1",
        "tabEvents": [
            {
                "tabEventId": "tab-event-1",
                "eventIndex": 1,
                "steelActions": [
                    {
                        "string": 4,
                        "fret": 0,
                        "controls": [],
                        "attack": True,
                        "soundingPitchValue": 64,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            }
        ],
    }
    identity = {
        "batchId": "batch-1",
        "inputId": "input-0001",
        "datasetPartition": "discovery",
        "assetSha256": "asset-sha",
        "sourceCopedent": {"id": "source-e9-abc-defg-v1", "revision": 1},
    }
    prior = {
        **identity,
        "revision": 2,
        "scoreSystems": [copy.deepcopy(score_system)],
        "tabSystems": [copy.deepcopy(old_tab)],
        "eventAlignments": [],
        "unresolved": [],
        "scoreRepair": {"repairVersion": SCORE_REPAIR_VERSION},
    }
    prior_path = candidate_root / f"{_sha256_json(prior)}.json"
    prior_path.write_text(json.dumps(prior), encoding="utf-8")
    current = copy.deepcopy(prior)
    current.pop("scoreRepair")
    current["revision"] = 3
    current["tabSystems"][0]["tabEvents"][0]["executionType"] = "attack"
    current["tabSystems"][0]["tabEvents"][0]["reviewedTransitionToken"] = "0"
    current_digest = _sha256_json(current)

    result = _rebase_score_repair_candidate_after_tab_correction(
        output_root,
        input_id="input-0001",
        base_record=current,
        base_reviewed_record_digest=current_digest,
        prior_review_decision_id="tab-confirmation-2",
    )

    assert result is not None
    assert result["scoreRecognitionReusedAfterTabOnlyCorrection"] is True
    rebased = json.loads((output_root / result["candidateRecordPath"]).read_text())
    assert rebased["scoreSystems"][0]["scoreEvents"][0]["pitch"] == "E4"
    assert rebased["tabSystems"] == current["tabSystems"]
    assert rebased["scoreRepair"]["baseReviewedRecordDigest"] == current_digest
    assert rebased["scoreRepair"]["priorReviewDecisionId"] == "tab-confirmation-2"
    assert rebased["scoreRepair"]["scoreRecognitionReusedAfterTabOnlyCorrection"] is True
    assert rebased["eventAlignments"][0]["notationAdjustedPitchAgreement"] is True


def test_replace_tab_system_events_builds_complete_reviewable_sequence() -> None:
    record = {
        "inputId": "input-recapture",
        "derivative": {"width": 1000, "height": 1000},
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "systemIndex": 1,
                "pageRegion": {"x": 0.1, "y": 0.2, "width": 0.8, "height": 0.3},
                "stringCenters": [220 + index * 20 for index in range(10)],
                "tabEvents": [],
            }
        ],
    }
    _apply_feedback_correction_operation(
        record,
        {
            "operationId": "recapture-line-1",
            "type": "replace_tab_system_events",
            "tabSystemId": "tab-system-1",
            "tabEvents": [
                {
                    "horizontalPosition": 0.2,
                    "steelActions": [
                        {"string": 5, "fret": 3, "controls": ["A"], "attack": True}
                    ],
                },
                {
                    "horizontalPosition": 0.4,
                    "steelActions": [
                        {
                            "string": 5,
                            "fret": 3,
                            "controls": [],
                            "attack": False,
                            "sustain": True,
                            "releaseTiming": "during_sustain",
                            "controlTransition": {
                                "beforeControls": ["A"],
                                "afterControls": [],
                                "timing": "during_sustain",
                            },
                        }
                    ],
                    "controlChanges": [
                        {"control": "A", "action": "release", "timing": "during_sustain"}
                    ],
                    "sustainBehavior": {"type": "continue_without_repick"},
                },
            ],
            "feedbackItemIds": ["feedback-1"],
        },
        feedback_item_ids=["feedback-1"],
    )

    system = record["tabSystems"][0]
    assert len(system["tabEvents"]) == 2
    assert system["tabEvents"][0]["executionType"] == "attack"
    assert system["tabEvents"][1]["executionType"] == "movement_only"
    assert system["tabEvents"][1]["steelActions"][0]["attack"] is False
    assert system["recapture"]["expectedEventCount"] == 2
    assert system["recapture"]["feedbackItemIds"] == ["feedback-1"]


def test_projection_tab_grid_recovers_ten_string_rows_from_curved_lines() -> None:
    image = np.full((800, 1200), 255, dtype=np.uint8)
    for line_index in range(11):
        base_y = 100 + line_index * 55
        for x in range(1200):
            y = int(round(base_y + 2.5 * np.sin(x / 180.0)))
            image[max(0, y - 1) : min(image.shape[0], y + 2), x] = 0

    grid = _projection_tab_grid(image)

    assert grid is not None
    assert len(grid.line_ys) == 11
    assert len(grid.string_centers) == 10
    assert grid.cell_height == pytest.approx(55, abs=2)


def test_page_review_compatibility_preserves_review_fact_versions_and_rejects_unknown() -> None:
    assert (
        _page_review_compatibility_version("lane20-score-tab-v12")
        == PAGE_REVIEW_COMPATIBILITY_VERSION
    )
    assert (
        _page_review_compatibility_version("lane20-score-tab-v13")
        == PAGE_REVIEW_COMPATIBILITY_VERSION
    )
    assert (
        _page_review_compatibility_version("lane20-score-tab-v14")
        == PAGE_REVIEW_COMPATIBILITY_VERSION
    )
    assert (
        _page_review_compatibility_version("lane20-score-tab-v15")
        == PAGE_REVIEW_COMPATIBILITY_VERSION
    )
    assert _page_review_compatibility_version("stale-extractor") is None


def test_unreviewed_refresh_gate_withholds_event_and_action_explosions() -> None:
    prior = {
        "tabSystems": [{"tabEvents": [{} for _ in range(6)]}],
        "validationSummary": {"steelActionCount": 12, "mechanicallyValidCount": 12},
    }
    improved = {
        "tabSystems": [{"tabEvents": [{} for _ in range(8)]}],
        "validationSummary": {"steelActionCount": 16, "mechanicallyValidCount": 16},
    }
    exploded = {
        "tabSystems": [{"tabEvents": [{} for _ in range(18)]}],
        "validationSummary": {"steelActionCount": 40, "mechanicallyValidCount": 40},
    }

    assert _unreviewed_refresh_regression_gate(prior, improved)["passed"] is True
    result = _unreviewed_refresh_regression_gate(prior, exploded)
    assert result["passed"] is False
    assert "event_explosion_regression" in result["reasons"]

    empty_line = {
        "tabSystems": [{"tabEvents": []}],
        "validationSummary": {"steelActionCount": 0, "mechanicallyValidCount": 0},
    }
    empty_result = _unreviewed_refresh_regression_gate(prior, empty_line)
    assert empty_result["passed"] is False
    assert "empty_tab_system" in empty_result["reasons"]


def test_score_tab_attack_count_completeness_detects_incomplete_score_capture() -> None:
    prior = {
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "tabEvents": [{"steelActions": [{"attack": True}]} for _ in range(3)],
            }
        ],
        "validationSummary": {"steelActionCount": 3, "mechanicallyValidCount": 3},
    }
    current = {
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "tabEvents": [{"steelActions": [{"attack": True}]} for _ in range(3)],
            }
        ],
        "scoreSystems": [
            {
                "pairedTabSystemId": "tab-system-1",
                "scoreEvents": [
                    {"measure": 1, "beat": 1, "pitch": "C4"},
                    {"measure": 1, "beat": 2, "pitch": "D4"},
                ],
            }
        ],
        "validationSummary": {"steelActionCount": 3, "mechanicallyValidCount": 3},
    }

    assert _unreviewed_refresh_regression_gate(prior, current)["passed"] is True
    assert _score_tab_attack_counts_complete(current) is False


def test_score_pitch_subset_requires_review_instead_of_claiming_added_harmony() -> None:
    assert _score_tab_pitch_relationship([59, 62], [59, 62]) == "exact"
    assert _score_tab_pitch_relationship([59], [59, 62]) == "subset_requires_review"
    assert _score_tab_pitch_relationship([60], [59, 62]) == "mismatch"


def test_system_local_marker_x_is_mapped_into_the_displayed_source_crop() -> None:
    assert _system_x_in_source_crop(
        0.1092735,
        system_region={"x": 0.0763305, "width": 0.7903828},
        source_crop_region={"x": 0.0, "width": 1.0},
    ) == 0.1626984
    assert _system_x_in_source_crop(
        0.5,
        system_region={"x": 0.2, "width": 0.4},
        source_crop_region={"x": 0.1, "width": 0.8},
    ) == 0.375


def test_score_chord_omission_submission_requires_every_flagged_relationship(
    tmp_path: Path,
) -> None:
    private = tmp_path / "private"
    review_dir = (
        private
        / "batches"
        / "batch-1"
        / "extraction"
        / "discovery"
        / "review"
        / "analysis"
        / "amazing-tablature-score-chord-omission-replay-v1"
        / "review"
    )
    review_dir.mkdir(parents=True)
    packet = {
        "packetDigest": "a" * 64,
        "systems": [
            {
                "flaggedRelationships": [
                    {"eventAlignmentId": "alignment-1"},
                    {"eventAlignmentId": "alignment-2"},
                ]
            }
        ],
    }
    (review_dir / "packet.json").write_text(json.dumps(packet), encoding="utf-8")
    payload = {
        "reviewType": "score_chord_omission",
        "batchId": "batch-1",
        "partition": "discovery",
        "packetDigest": "a" * 64,
        "reviews": [
            {
                "eventAlignmentId": "alignment-1",
                "status": "score_missing_notes",
                "comment": "D4 is also printed.",
            },
            {
                "eventAlignmentId": "alignment-2",
                "status": "intentional_harmony",
                "comment": None,
            },
        ],
    }

    first = _store_score_chord_omission_submission(private, payload)
    second = _store_score_chord_omission_submission(private, payload)

    assert first["reviewCount"] == 2
    assert first["status"] == "received_not_applied"
    assert second["submissionId"] == first["submissionId"]
    assert second["deduplicated"] is True


def test_full_line_score_submission_requires_every_line_and_is_idempotent(
    tmp_path: Path,
) -> None:
    private = tmp_path / "private"
    review_dir = (
        private
        / "batches"
        / "batch-1"
        / "extraction"
        / "discovery"
        / "review"
        / "analysis"
        / "amazing-tablature-full-line-score-recapture-v1"
        / "review"
    )
    review_dir.mkdir(parents=True)
    packet = {
        "packetDigest": "b" * 64,
        "systems": [
            {"inputId": "input-1", "scoreSystemId": "score-system-1"},
            {"inputId": "input-2", "scoreSystemId": "score-system-2"},
        ],
    }
    (review_dir / "packet.json").write_text(json.dumps(packet), encoding="utf-8")
    payload = {
        "reviewType": "full_line_score_recapture",
        "batchId": "batch-1",
        "partition": "discovery",
        "packetDigest": "b" * 64,
        "reviews": [
            {
                "inputId": "input-1",
                "scoreSystemId": "score-system-1",
                "status": "accept",
                "comment": None,
            },
            {
                "inputId": "input-2",
                "scoreSystemId": "score-system-2",
                "status": "feedback",
                "comment": "Event 2 has another printed notehead.",
            },
        ],
    }

    first = _store_full_line_score_recapture_submission(private, payload)
    second = _store_full_line_score_recapture_submission(private, payload)

    assert first["reviewCount"] == 2
    assert first["status"] == "received_not_applied"
    assert second["submissionId"] == first["submissionId"]
    assert second["deduplicated"] is True

    incomplete = copy.deepcopy(payload)
    incomplete["reviews"] = incomplete["reviews"][:1]
    with pytest.raises(ExtractionWorkflowError, match="Every full score line"):
        _store_full_line_score_recapture_submission(private, incomplete)


def test_full_line_score_recognition_uses_labelled_tab_hypothesis_for_missing_alignment() -> None:
    score_system = {
        "scoreEvents": [
            {"scoreEventId": "score-1", "pitchValue": 60},
        ]
    }
    tab_system = {
        "tabEvents": [
            {
                "eventIndex": 1,
                "tabEventId": "tab-1",
                "executionType": "attack",
                "steelActions": [
                    {
                        "string": 4,
                        "soundingPitchValue": 60,
                        "attack": True,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            },
            {
                "eventIndex": 2,
                "tabEventId": "tab-2",
                "executionType": "movement_only",
                "steelActions": [
                    {
                        "string": 4,
                        "soundingPitchValue": 62,
                        "attack": False,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            },
        ]
    }
    alignments = [
        {
            "eventAlignmentId": "alignment-1",
            "scoreEventIds": ["score-1"],
            "tabEventIds": ["tab-1"],
            "alignmentType": "simultaneous_attack",
        }
    ]

    events, alignment_ids = _full_line_score_recognition_events(
        score_system,
        tab_system,
        alignments,
    )

    assert alignment_ids == ["alignment-1"]
    assert events[0]["pitchValues"] == [60]
    assert events[0]["scoreFactOrigin"] == "captured_score_alignment"
    assert events[1]["pitchValues"] == [62]
    assert events[1]["stateType"] == "hypothesis_requires_visual_confirmation"
    assert events[1]["scoreFactOrigin"] == (
        "tab_derived_pitch_hypothesis_requires_visual_confirmation"
    )
    assert events[1]["eventAlignmentId"] is None


def test_full_line_score_recognition_rejects_ambiguous_existing_alignments() -> None:
    score_system = {
        "scoreEvents": [
            {"scoreEventId": "score-1", "pitchValue": 60},
        ]
    }
    tab_system = {
        "tabEvents": [
            {
                "eventIndex": 1,
                "tabEventId": "tab-1",
                "steelActions": [
                    {
                        "string": 4,
                        "soundingPitchValue": 60,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            }
        ]
    }
    alignments = [
        {
            "eventAlignmentId": "alignment-1",
            "scoreEventIds": ["score-1"],
            "tabEventIds": ["tab-1"],
        },
        {
            "eventAlignmentId": "alignment-2",
            "scoreEventIds": ["score-1"],
            "tabEventIds": ["tab-1"],
        },
    ]

    with pytest.raises(ExtractionWorkflowError, match="multiple current"):
        _full_line_score_recognition_events(score_system, tab_system, alignments)


def test_digest_pinned_unindexed_score_candidate_is_recoverable(tmp_path: Path) -> None:
    output_root = tmp_path / "extraction" / "discovery"
    candidate = {
        "inputId": "input-0001",
        "tabSystems": [],
        "scoreRepair": {
            "repairVersion": SCORE_REPAIR_VERSION,
            "baseReviewedRecordDigest": "base-digest",
            "priorReviewDecisionId": "review-1",
            "priorTabApprovalPreserved": True,
        },
    }
    candidate["scoreRepair"]["reviewedTabFactsDigest"] = _reviewed_tab_facts_digest(candidate)
    digest = _sha256_json(candidate)
    path = (
        output_root
        / "review"
        / "score-audit"
        / "repair"
        / "candidate-records"
        / "input-0001"
        / f"{digest}.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(candidate), encoding="utf-8")

    entry = _digest_pinned_unindexed_score_repair_entry(
        output_root,
        input_id="input-0001",
        candidate_digest=digest,
    )

    assert entry is not None
    assert entry["candidateRecordDigest"] == digest
    assert entry["recoveredFromDigestPinnedCombinedPacket"] is True
    assert _digest_pinned_unindexed_score_repair_entry(
        output_root,
        input_id="input-0001",
        candidate_digest="missing",
    ) is None


def test_reviewed_tab_event_rhythmic_slot_recovers_missing_measure_context() -> None:
    tab_system = {"barlineHorizontalPositions": [0.001, 0.36, 0.69]}

    first = _reviewed_tab_event_rhythmic_slot(
        tab_system,
        {"horizontalPosition": 0.13},
        beats=4,
    )
    second_measure = _reviewed_tab_event_rhythmic_slot(
        tab_system,
        {"horizontalPosition": 0.46},
        beats=4,
    )
    preserved = _reviewed_tab_event_rhythmic_slot(
        tab_system,
        {"measure": 7, "measureHorizontalPosition": 0.5, "horizontalPosition": 0.1},
        beats=4,
    )

    assert first[0] == 1
    assert second_measure[0] == 2
    assert first != second_measure
    assert preserved == (7, 2.5)


def test_full_line_approval_promotes_to_canonical_combined_training_scope() -> None:
    score_system = {
        "scoreSystemId": "score-system-1",
        "pairedTabSystemId": "tab-system-1",
        "scoreEvents": [
            {
                "scoreEventId": "score-1",
                "measure": 1,
                "beat": 1.0,
                "pitch": "C4",
                "pitchValue": 60,
                "rest": False,
            },
            {
                "scoreEventId": "score-2",
                "measure": 1,
                "beat": 2.0,
                "pitch": "D4",
                "pitchValue": 62,
                "rest": False,
            },
        ],
    }
    tab_system = {
        "tabSystemId": "tab-system-1",
        "tabEvents": [
            {
                "tabEventId": "tab-1",
                "eventIndex": 1,
                "executionType": "attack",
                "steelActions": [
                    {
                        "string": 4,
                        "fret": 0,
                        "attack": True,
                        "soundingPitchValue": 60,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            },
            {
                "tabEventId": "tab-2",
                "eventIndex": 2,
                "executionType": "movement_only",
                "steelActions": [
                    {
                        "string": 4,
                        "fret": 0,
                        "attack": False,
                        "soundingPitchValue": 60,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            },
            {
                "tabEventId": "tab-3",
                "eventIndex": 3,
                "executionType": "attack",
                "steelActions": [
                    {
                        "string": 4,
                        "fret": 2,
                        "attack": True,
                        "soundingPitchValue": 62,
                        "mechanicalValidation": {"valid": True},
                    }
                ],
            },
        ],
    }
    record = {
        "inputId": "input-1",
        "revision": 1,
        "scoreSystems": [score_system],
        "tabSystems": [tab_system],
        "eventAlignments": [],
    }
    line = {
        "batchId": "batch-1",
        "partition": "discovery",
        "inputId": "input-1",
        "scoreSystemId": "score-system-1",
        "tabSystemId": "tab-system-1",
        "decisionId": "full-line-decision-1",
        "packetDigest": "a" * 64,
        "submissionDigest": "b" * 64,
    }

    revised, canonical = _promote_full_line_record_to_combined_scope(
        record,
        line,
        source_copedent_id="source-e9-abc-defg-v1",
        source_copedent_digest="c" * 64,
    )

    assert canonical["status"] == "human_approved_pitch_only"
    assert canonical["pitchToTabTrainingEligible"] is True
    assert canonical["scoreRhythmTrainingEligible"] is False
    assert canonical["scoreAttackCount"] == 2
    assert canonical["tabAttackCount"] == 2
    assert canonical["tabMovementCount"] == 3
    assert revised["scoreSystems"][0]["combinedScoreTabDecisionId"] == (
        "full-line-decision-1"
    )
    assert len(revised["eventAlignments"]) == 3
    movement = next(
        item
        for item in revised["eventAlignments"]
        if item["tabEventIds"] == ["tab-2"]
    )
    assert movement["alignmentType"] == "sustained_score_to_control_movement"
    assert movement["pitchToTabTrainingEligible"] is True


def test_full_line_leading_movement_is_preserved_but_fail_closed_for_training() -> None:
    record = {
        "inputId": "input-1",
        "revision": 1,
        "scoreSystems": [
            {
                "scoreSystemId": "score-system-1",
                "pairedTabSystemId": "tab-system-1",
                "scoreEvents": [
                    {
                        "scoreEventId": "score-1",
                        "measure": 1,
                        "beat": 1.0,
                        "pitch": "C4",
                        "pitchValue": 60,
                        "rest": False,
                    }
                ],
            }
        ],
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "tabEvents": [
                    {
                        "tabEventId": "tab-leading-move",
                        "eventIndex": 1,
                        "executionType": "movement_only",
                        "steelActions": [
                            {
                                "string": 4,
                                "fret": 0,
                                "attack": False,
                                "soundingPitchValue": 60,
                                "mechanicalValidation": {"valid": True},
                            }
                        ],
                    },
                    {
                        "tabEventId": "tab-attack",
                        "eventIndex": 2,
                        "executionType": "attack",
                        "steelActions": [
                            {
                                "string": 4,
                                "fret": 0,
                                "attack": True,
                                "soundingPitchValue": 60,
                                "mechanicalValidation": {"valid": True},
                            }
                        ],
                    },
                ],
            }
        ],
        "eventAlignments": [],
    }
    line = {
        "batchId": "batch-1",
        "partition": "discovery",
        "inputId": "input-1",
        "scoreSystemId": "score-system-1",
        "tabSystemId": "tab-system-1",
        "decisionId": "full-line-decision-leading-move",
        "packetDigest": "a" * 64,
        "submissionDigest": "b" * 64,
    }

    revised, canonical = _promote_full_line_record_to_combined_scope(
        record,
        line,
        source_copedent_id="source-e9-abc-defg-v1",
        source_copedent_digest="c" * 64,
    )

    assert canonical["scorePitchTrainingEligible"] is True
    assert canonical["pitchToTabTrainingEligible"] is False
    assert canonical["trainingEligible"] is False
    assert canonical["alignmentMode"] == "unresolved_correspondence"
    assert canonical["alignmentExclusionReason"] == "tab_movement_precedes_first_score_attack"
    assert revised["eventAlignments"] == []


def test_pitch_only_scope_withholds_score_chord_omission_from_training() -> None:
    record = {
        "scoreSystems": [
            {
                "scoreSystemId": "score-system-1",
                "scoreEvents": [
                    {
                        "scoreEventId": "score-event-1",
                        "pitch": "B3",
                        "pitchValue": 59,
                        "rest": False,
                    }
                ],
            }
        ],
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "tabEvents": [
                    {
                        "tabEventId": "tab-event-1",
                        "steelActions": [
                            {"soundingPitchValue": 59, "attack": True},
                            {"soundingPitchValue": 62, "attack": True},
                        ],
                    }
                ],
            }
        ],
        "eventAlignments": [
            {
                "eventAlignmentId": "alignment-1",
                "scoreEventIds": ["score-event-1"],
                "tabEventIds": ["tab-event-1"],
            }
        ],
    }

    findings = score_tab_pitch_relationship_findings(record)
    scope = _apply_pitch_only_score_audit_scope(
        record,
        {"score-system-1"},
        reviewer_reference="score-reviewer",
    )

    assert findings[0]["relationshipStatus"] == "subset_requires_review"
    assert findings[0]["eligibleForPitchToTabTraining"] is False
    assert record["eventAlignments"][0]["pitchToTabTrainingEligible"] is False
    assert record["scoreSystems"][0]["scoreEvents"][0]["pitchToTabTrainingEligible"] is False
    assert scope["pitchToTabEligibleAlignmentCount"] == 0
    assert scope["excludedScoreChordOmissionCount"] == 1


def test_score_audit_allows_feedback_only_for_blocked_system_on_mixed_page() -> None:
    packet = {
        "reviewedRecordDigest": "a" * 64,
        "reviewedRecord": {
            "scoreSystems": [
                {"scoreSystemId": "score-ready", "scoreEvents": []},
                {"scoreSystemId": "score-blocked", "scoreEvents": []},
            ],
            "tabSystems": [],
            "eventAlignments": [],
        },
        "scoreAuditGatesBySystem": {
            "score-ready": {"readyForHumanReview": True},
            "score-blocked": {"readyForHumanReview": False},
        },
    }
    review = {
        "inputId": "input-0001",
        "expectedReviewedRecordDigest": "a" * 64,
        "action": "feedback",
        "reviewerReference": "score-reviewer",
        "systemDecisions": [
            {"scoreSystemId": "score-ready", "status": "accept", "comment": None},
            {
                "scoreSystemId": "score-blocked",
                "status": "feedback",
                "comment": "One printed attack is missing from the capture.",
            },
        ],
        "eventFeedback": [],
    }

    normalized = _normalize_score_audit_review(review, packet)

    assert normalized["action"] == "feedback"
    assert {item["status"] for item in normalized["systemDecisions"]} == {
        "accept",
        "feedback",
    }
    blocked_accept = copy.deepcopy(review)
    blocked_accept["action"] = "accept"
    blocked_accept["systemDecisions"][1] = {
        "scoreSystemId": "score-blocked",
        "status": "accept",
        "comment": None,
    }
    with pytest.raises(ExtractionWorkflowError, match="failed the automatic equivalence gate"):
        _normalize_score_audit_review(blocked_accept, packet)


def test_score_audit_source_crop_keeps_printed_score_and_tab_together(tmp_path: Path) -> None:
    output_root = tmp_path / "extraction" / "discovery"
    audit_dir = output_root / "review" / "score-audit"
    derivative_path = output_root / "derivatives" / "input-0001.png"
    derivative_path.parent.mkdir(parents=True)
    image = Image.new("RGB", (1000, 1000), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((100, 200, 900, 350), fill="red")
    draw.rectangle((150, 400, 850, 650), fill="blue")
    image.save(derivative_path)
    record = {"derivative": {"relativePath": "derivatives/input-0001.png"}}
    score_system = {
        "scoreSystemId": "score-1",
        "systemIndex": 1,
        "pageRegion": {"x": 0.1, "y": 0.2, "width": 0.8, "height": 0.15},
    }
    tab_system = {
        "tabSystemId": "tab-1",
        "pageRegion": {"x": 0.15, "y": 0.4, "width": 0.7, "height": 0.25},
    }

    result = _prepare_score_tab_source_crop(
        output_root=output_root,
        audit_dir=audit_dir,
        input_id="input-0001",
        record=record,
        score_system=score_system,
        tab_system=tab_system,
    )

    crop_path = output_root / result["relativePath"]
    with Image.open(crop_path) as crop:
        assert crop.getpixel((crop.width // 2, 90)) == (255, 0, 0)
        assert crop.getpixel((crop.width // 2, crop.height - 100)) == (0, 0, 255)
    assert result["relativeUrl"] == "./source-pairs/input-0001/score-tab-system-01.png"
    assert result["scoreSystemId"] == "score-1"
    assert result["tabSystemId"] == "tab-1"
    assert result["rawSourceModified"] is False
    assert stat.S_IMODE(crop_path.stat().st_mode) == 0o600


def test_audiveris_mac_bundle_uses_headless_java_launcher(tmp_path: Path) -> None:
    contents = tmp_path / "Audiveris.app" / "Contents"
    binary = contents / "MacOS" / "Audiveris"
    java = contents / "runtime" / "Contents" / "Home" / "bin" / "java"
    jar = contents / "app" / "audiveris.jar"
    for path in (binary, java, jar):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test")
    binary.chmod(0o700)
    java.chmod(0o700)

    reader = AudiverisReader(binary)

    assert reader.launch_mode == "bundled-java-headless"
    assert reader._command_prefix() == [
        str(java),
        "-Djava.awt.headless=true",
        "-Djpackage.app-version=5.11.0",
        "--add-exports=java.desktop/sun.awt.image=ALL-UNNAMED",
        "--enable-native-access=ALL-UNNAMED",
        "-Dfile.encoding=UTF-8",
        "-Xms512m",
        "-Xmx8G",
        "-cp",
        f"{contents / 'app'}/*",
        "Audiveris",
    ]
    assert reader.contract()["desktopWindowAllowed"] is False


def test_detects_ten_string_grid_and_rejects_barlines_as_events() -> None:
    gray = np.asarray(_synthetic_tab())
    grids = detect_tab_grids(gray)
    assert len(grids) == 1
    assert len(grids[0].line_ys) == 11
    assert len(grids[0].barline_xs) >= 3
    assert _tab_measure_context(grids[0], 200)[0] == 1
    assert _tab_measure_context(grids[0], 700)[0] == 2
    events = _tab_event_candidates(gray, grids[0])
    assert [event["candidateStrings"] for event in events] == [[5], [3]]


def test_left_string_number_legend_is_not_counted_as_music_event() -> None:
    image = _synthetic_tab()
    draw = ImageDraw.Draw(image)
    lines = [400 + index * 22 for index in range(11)]
    for string, x in ((1, 106), (4, 111), (5, 114)):
        draw.rectangle(
            (x, lines[string - 1] + 5, x + 5, lines[string] - 5),
            fill="black",
        )

    gray = np.asarray(image)
    grid = detect_tab_grids(gray)[0]
    events = _tab_event_candidates(gray, grid)

    assert [event["candidateStrings"] for event in events] == [[5], [3]]


def test_dense_neighboring_tab_columns_are_not_merged_into_one_event() -> None:
    image = _synthetic_tab()
    draw = ImageDraw.Draw(image)
    lines = [400 + index * 22 for index in range(11)]
    for x in (284, 300):
        draw.rectangle((x, lines[4] + 3, x + 10, lines[5] - 3), fill="black")

    grids = detect_tab_grids(np.asarray(image))
    events = _tab_event_candidates(np.asarray(image), grids[0])
    legacy_events = _tab_event_candidates(
        np.asarray(image),
        grids[0],
        same_string_gap_ratio=0.42,
        cross_string_tolerance_ratio=0.75,
    )

    string_five_events = [event for event in events if event["candidateStrings"] == [5]]
    legacy_string_five_events = [
        event for event in legacy_events if event["candidateStrings"] == [5]
    ]
    assert len(string_five_events) == 2
    assert len(legacy_string_five_events) == 1


def test_page_classifier_uses_tab_texture_and_specific_instructional_cues() -> None:
    grid = detect_tab_grids(np.asarray(_synthetic_tab()))[0]
    single_note = [{"tabEvents": [{"steelActions": [{"string": 4}]} for _ in range(5)]}]
    assert _classify_page([], [grid], single_note)["primary"] == "single_note_melody"

    chordal = [{"tabEvents": [{"steelActions": [{"string": 4}, {"string": 5}]} for _ in range(5)]}]
    assert _classify_page([{"text": "Chord voicing study"}], [grid], chordal)["primary"] == "chordal_arrangement"
    assert _classify_page([{"text": "Adapted banjo lick"}], [grid], single_note)["primary"] == "lick_or_fill"


def test_source_profiles_decode_control_letters_differently() -> None:
    training = get_e9_copedent_profile("source-e9-abc-defg-v1")
    licks = get_e9_copedent_profile("source-e9-abc-defg-d48-e29-v1")

    training_action, training_issue = _tab_action_from_token(
        "3D",
        string=2,
        profile=training,
        confidence=0.99,
        region_id="region-1",
    )
    licks_action, licks_issue = _tab_action_from_token(
        "3D",
        string=2,
        profile=licks,
        confidence=0.99,
        region_id="region-2",
    )

    assert training_action is not None
    assert training_action["soundingPitchValue"] == 65
    assert training_issue is None
    assert licks_action is not None
    assert licks_action["soundingPitchValue"] == 66
    assert licks_issue is not None
    assert "control_does_not_affect_string" in licks_issue["issues"]


def test_both_source_copedent_contracts_pin_every_control_change() -> None:
    training = get_e9_copedent_profile("source-e9-abc-defg-v1")
    licks = get_e9_copedent_profile("source-e9-abc-defg-d48-e29-v1")

    def changes(profile: Any) -> dict[str, list[tuple[int, int]]]:
        return {
            control.id: [(change.string, change.semitones) for change in control.changes]
            for control in profile.controls
        }

    shared = {
        "A": [(5, 2), (10, 2)],
        "B": [(3, 1), (6, 1)],
        "C": [(4, 2), (5, 2)],
        "F": [(4, 1), (8, 1)],
        "G": [(1, 1), (7, 1)],
    }
    assert changes(training) == {
        **shared,
        "D": [(2, -1)],
        "E": [(4, -1), (8, -1)],
    }
    assert changes(licks) == {
        **shared,
        "D": [(4, -1), (8, -1)],
        "E": [(2, -1), (9, -1)],
    }
    assert training.revision == 1
    assert licks.revision == 1

    expected_digests = {
        training.id: "76a2395879adc0ce19fe075ac3a3030f84d690d416988a0a736fc357397965a7",
        licks.id: "5b48f77bfea3802f417bd48c147ab0258dd98cb399dd95bb3b77af33eb4f652f",
    }
    for profile in (training, licks):
        expected = expected_digests[profile.id]
        assert e9_copedent_profile_digest(profile) == expected
        assert training_profile_digest(profile) == expected
        assert extraction_profile_digest(profile) == expected


def test_musicxml_parser_preserves_measure_tempo_articulation_phrase_and_repeat_facts(tmp_path: Path) -> None:
    musicxml = tmp_path / "score.musicxml"
    musicxml.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>Music</part-name></score-part></part-list>
  <part id="P1">
    <measure number="12">
      <attributes>
        <divisions>2</divisions><key><fifths>1</fifths></key>
        <time symbol="common"><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <direction><direction-type><words>Allegro</words><metronome><per-minute>120</per-minute></metronome></direction-type><sound tempo="120"/></direction>
      <note default-x="100"><pitch><step>E</step><alter>-1</alter><octave>4</octave></pitch><duration>2</duration><voice>1</voice><staff>1</staff><accidental>flat</accidental><tie type="start"/><notations><articulations><staccato/></articulations><slur type="start"/></notations></note>
      <barline location="right"><ending number="1" type="start"/><repeat direction="backward"/></barline>
    </measure>
  </part>
</score-partwise>
""",
        encoding="utf-8",
    )

    parsed = _parse_musicxml(musicxml, "score-system-1")
    assert parsed["measures"][0]["printedMeasureNumber"] == "12"
    assert parsed["measures"][0]["repeatDirections"] == ["backward"]
    assert parsed["tempoMarkings"][0]["beatsPerMinute"] == 120.0
    assert parsed["timeSignature"] == {"beats": 4, "beatType": 4, "symbol": "common"}
    assert parsed["clef"]["sign"] == "G"
    assert parsed["clef"]["line"] == 2
    assert parsed["scoreEvents"][0]["pitch"] == "Eb4"
    assert parsed["scoreEvents"][0]["pitchStep"] == "E"
    assert parsed["scoreEvents"][0]["pitchAlter"] == -1
    assert parsed["scoreEvents"][0]["writtenAccidental"] == "flat"
    assert parsed["scoreEvents"][0]["articulations"] == ["staccato"]
    assert parsed["scoreEvents"][0]["phraseBoundaries"] == ["start"]
    assert parsed["repeatStructures"][0]["endings"] == [{"number": "1", "type": "start"}]


def test_measure_slice_clef_is_reinterpreted_from_full_score_context() -> None:
    payload = {
        "clef": {"sign": "C", "line": 3, "octaveChange": 0},
        "scoreEvents": [
            {
                "pitch": "C4",
                "pitchValue": 60,
                "pitchStep": "C",
                "pitchAlter": 0,
                "octave": 4,
                "writtenAccidental": "natural",
                "rest": False,
            },
            {
                "pitch": "E4",
                "pitchValue": 64,
                "pitchStep": "E",
                "pitchAlter": 0,
                "octave": 4,
                "rest": False,
            },
            {
                "pitch": "G4",
                "pitchValue": 67,
                "pitchStep": "G",
                "pitchAlter": 0,
                "octave": 4,
                "rest": False,
            },
        ],
    }

    normalization = _normalize_score_payload_clef(
        payload,
        {"sign": "G", "line": 2, "octaveChange": 0},
    )

    assert normalization is not None
    assert normalization["diatonicShift"] == 6
    assert payload["clef"]["sign"] == "G"
    assert [event["pitch"] for event in payload["scoreEvents"]] == ["B4", "D5", "F5"]
    assert [event["pitchValue"] for event in payload["scoreEvents"]] == [71, 74, 77]
    assert payload["scoreEvents"][0]["writtenAccidental"] == "natural"


def test_repeated_source_glyph_repairs_a_missed_chord_without_copying_tab_pitches() -> None:
    image = Image.new("RGB", (400, 200), "white")
    draw = ImageDraw.Draw(image)
    staff_lines = (60, 75, 90, 105, 120)
    for y in staff_lines:
        draw.line((0, y, 399, y), fill="black", width=1)
    for x in (100, 250):
        draw.line((x + 7, 73, x + 7, 132), fill="black", width=3)
        for y in (90, 105, 128):
            draw.ellipse((x - 9, y - 5, x + 9, y + 5), fill="black")
    score_payload = {
        "scoreEvents": [
            {
                "scoreEventId": f"reference-{pitch}",
                "measure": 1,
                "beat": 1.0,
                "durationBeats": 1.0,
                "pitch": name,
                "pitchValue": pitch,
                "pitchStep": name[0],
                "pitchAlter": 0,
                "octave": int(name[-1]),
                "rest": False,
                "voice": 1,
                "confidence": 0.95,
            }
            for pitch, name in ((62, "D4"), (67, "G4"), (71, "B4"))
        ]
        + [
            {
                "scoreEventId": f"target-{pitch}",
                "measure": 1,
                "beat": 2.0,
                "durationBeats": 1.0,
                "pitch": name,
                "pitchValue": pitch,
                "pitchStep": name[0],
                "pitchAlter": 0,
                "octave": int(name[-1]),
                "rest": False,
                "voice": 1,
                "confidence": 0.9,
            }
            for pitch, name in ((62, "D4"), (69, "A4"))
        ],
        "chordContexts": [],
    }
    tab_events = [
        {
            "tabEventId": f"tab-{index}",
            "measure": 2,
            "horizontalPosition": position,
            "steelActions": [
                {"soundingPitchValue": pitch, "attack": True}
                for pitch in (62, 67, 71)
            ],
        }
        for index, position in enumerate((0.25, 0.625), start=1)
    ]
    grid = GridDetection(
        x0=0,
        y0=130,
        x1=400,
        y1=190,
        line_ys=tuple(130 + index * 6 for index in range(11)),
        confidence=1.0,
        barline_xs=(),
    )

    repair = _repair_repeated_score_glyph(
        score_payload=score_payload,
        score_measure=1,
        tab_events=tab_events,
        source_image=image,
        staff_lines=staff_lines,
        grid=grid,
        system_id="score-system-1",
    )

    assert repair is not None
    assert repair["tabUsedAsValidatorOnly"] is True
    repaired = [event for event in score_payload["scoreEvents"] if event["beat"] == 2.0]
    assert sorted(event["pitchValue"] for event in repaired) == [62, 67, 71]
    assert all(event["evidenceClass"] == "deterministic_derivation" for event in repaired)
    assert all(event["scoreGlyphRepair"]["method"] == "repeated_source_glyph_v1" for event in repaired)


def test_score_audit_diagnostics_preselect_score_tab_review_priorities() -> None:
    record = {
        "scoreSystems": [
            {
                "scoreSystemId": "score-system-1",
                "pairedTabSystemId": "tab-system-1",
                "timeSignature": {"beats": 4, "beatType": 4},
                "scoreEvents": [
                    {
                        "scoreEventId": "score-event-1",
                        "pitch": "C4",
                        "measure": 1,
                        "beat": 1,
                        "rest": False,
                    },
                    {
                        "scoreEventId": "score-event-2",
                        "pitch": "D4",
                        "measure": 1,
                        "beat": 5,
                        "rest": False,
                    },
                ],
            }
        ],
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "tabEvents": [
                    {
                        "tabEventId": "tab-event-1",
                        "measure": 2,
                        "steelActions": [{"string": 4, "fret": 3, "attack": True}],
                    },
                    {
                        "tabEventId": "tab-event-2",
                        "measure": 2,
                        "steelActions": [{"string": 5, "fret": 3, "attack": True}],
                    },
                ],
            }
        ],
        "eventAlignments": [
            {
                "eventAlignmentId": "alignment-1",
                "scoreEventIds": ["score-event-1"],
                "tabEventIds": ["tab-event-1"],
                "scoreMeasure": 1,
                "tabMeasure": 2,
                "measureAgreement": False,
                "soundingPitchAgreement": False,
                "notationAdjustedPitchAgreement": True,
                "scoreNotationTranspositionSemitones": 12,
            }
        ],
    }

    system = _score_audit_diagnostics(record)["score-system-1"]
    kinds = {item["kind"] for item in system["flags"]}

    assert system["mappedScoreEventCount"] == 1
    assert system["mappedTabEventCount"] == 1
    assert {
        "score_event_unmapped",
        "score_beat_exceeds_time_signature",
        "alignment_measure_disagreement",
        "alignment_requires_notation_offset",
        "tab_attack_unmapped",
    } <= kinds
    assert all(item["approvalEffect"] == "review_priority_only" for item in system["flags"])


def test_score_audit_equivalence_gate_withholds_incomplete_systems() -> None:
    record = {
        "scoreSystems": [
            {
                "scoreSystemId": "score-system-1",
                "pairedTabSystemId": "tab-system-1",
                "scoreEvents": [
                    {"scoreEventId": "score-event-1", "measure": 1, "beat": 1, "pitchValue": 60},
                    {"scoreEventId": "score-event-2", "measure": 1, "beat": 3, "pitchValue": 62},
                ],
            }
        ],
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "tabEvents": [
                    {"tabEventId": "tab-event-1", "measure": 1, "steelActions": [{"attack": True}]},
                    {"tabEventId": "tab-event-2", "measure": 2, "steelActions": [{"attack": True}]},
                ],
            }
        ],
        "eventAlignments": [
            {
                "eventAlignmentId": "alignment-1",
                "scoreEventIds": ["score-event-1"],
                "tabEventIds": ["tab-event-1"],
                "scoreMeasure": 1,
                "tabMeasure": 1,
                "notationAdjustedPitchAgreement": True,
            },
            {
                "eventAlignmentId": "alignment-2",
                "scoreEventIds": ["score-event-2"],
                "tabEventIds": ["tab-event-2"],
                "scoreMeasure": 1,
                "tabMeasure": 2,
                "notationAdjustedPitchAgreement": True,
            },
        ],
    }

    gate = _score_audit_equivalence_gates(record)["score-system-1"]

    assert gate["readyForHumanReview"] is False
    assert gate["reviewEffect"] == "withheld_for_internal_repair"
    assert {item["code"] for item in gate["blockingReasons"]} >= {
        "occupied_measure_count_mismatch",
        "relative_measure_alignment_below_gate",
    }


def test_confirmed_source_pitch_discrepancy_is_auditable_but_not_training_eligible() -> None:
    record = {
        "scoreSystems": [
            {
                "scoreSystemId": "score-system-1",
                "pairedTabSystemId": "tab-system-1",
                "scoreEvents": [
                    {
                        "scoreEventId": "score-event-1",
                        "measure": 1,
                        "beat": 1.0,
                        "pitch": "C4",
                        "pitchValue": 60,
                        "rest": False,
                    }
                ],
            }
        ],
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "tabEvents": [
                    {
                        "tabEventId": "tab-event-1",
                        "measure": 1,
                        "horizontalPosition": 0.5,
                        "steelActions": [
                            {
                                "attack": True,
                                "soundingPitch": "A3",
                                "soundingPitchValue": 57,
                            }
                        ],
                    }
                ],
            }
        ],
        "unresolved": [],
    }
    candidates = _align_events(
        record["scoreSystems"][0]["scoreEvents"],
        record["tabSystems"][0]["tabEvents"],
    )
    verified, unresolved = _separate_verified_alignments(candidates)
    assert verified == []

    promoted, discrepancy = _promote_confirmed_source_discrepancy(
        record,
        unresolved,
        {
            "scoreSystemId": "score-system-1",
            "feedbackTargetId": "tab-event-1",
            "expectedScorePitches": ["C4"],
            "expectedTabPitches": ["A3"],
            "expertTargetPitches": ["C4"],
            "reasonCode": "printed_score_tab_pitch_mismatch",
        },
    )
    record["eventAlignments"] = [promoted]
    record["sourceScoreTabDiscrepancies"] = [discrepancy]

    gate = _score_audit_equivalence_gates(record)["score-system-1"]

    assert unresolved == []
    assert gate["readyForHumanReview"] is True
    assert gate["metrics"]["pitchAgreement"] == 1.0
    assert gate["metrics"]["rawPitchAgreement"] == 0.0
    assert gate["metrics"]["confirmedSourcePitchDiscrepancyCount"] == 1
    assert promoted["eligibleForTransformationTraining"] is False
    assert promoted["expertCorrectedTargetPitches"] == ["C4"]
    assert discrepancy["eligibleForTransformationTraining"] is False
    assert discrepancy["expertCorrectedTargetPitches"] == ["C4"]
    scope = _apply_pitch_only_score_audit_scope(
        record,
        {"score-system-1"},
        reviewer_reference="score-reviewer",
    )
    assert promoted["pitchToTabTrainingEligible"] is False
    assert record["scoreSystems"][0]["scoreEvents"][0]["pitchToTabTrainingEligible"] is False
    assert scope["pitchToTabEligibleAlignmentCount"] == 0
    assert scope["excludedSourceDiscrepancyCount"] == 1


def test_revised_source_discrepancy_replaces_stale_fact_for_same_tab_event() -> None:
    existing = [
        {
            "sourceScoreTabDiscrepancyId": "old",
            "scoreSystemId": "score-system-1",
            "tabEventIds": ["tab-event-1"],
            "scorePitches": ["B4"],
            "tabSoundingPitches": ["A4"],
        },
        {
            "sourceScoreTabDiscrepancyId": "unrelated",
            "scoreSystemId": "score-system-2",
            "tabEventIds": ["tab-event-2"],
        },
    ]
    corrected = {
        "sourceScoreTabDiscrepancyId": "new",
        "scoreSystemId": "score-system-1",
        "tabEventIds": ["tab-event-1"],
        "scorePitches": ["D5"],
        "tabSoundingPitches": ["A4"],
    }

    merged = _merge_current_source_discrepancies(existing, [corrected])

    assert [item["sourceScoreTabDiscrepancyId"] for item in merged] == [
        "unrelated",
        "new",
    ]


def test_targeted_score_audit_tab_correction_preserves_literal_event() -> None:
    record = {
        "inputId": "input-0001",
        "derivative": {"width": 1000, "height": 1000},
        "scoreSystems": [
            {
                "scoreSystemId": "score-system-1",
                "pairedTabSystemId": "tab-system-1",
            }
        ],
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "pageRegion": {"x": 0.1, "y": 0.4, "width": 0.8, "height": 0.3},
                "stringCenters": [430 + index * 20 for index in range(10)],
                "tabEvents": [
                    {
                        "tabEventId": "tab-event-1",
                        "horizontalPosition": 0.5,
                        "steelActions": [
                            {
                                "steelActionId": "steel-action-original",
                                "string": 7,
                                "fret": 3,
                                "controls": [],
                                "attack": True,
                                "reviewState": "human_approved",
                            }
                        ],
                    }
                ],
            }
        ],
    }
    original = copy.deepcopy(record["tabSystems"][0]["tabEvents"][0])
    applied, provenance = _replace_tab_event_from_score_audit(
        record,
        {
            "operationId": "operation-1",
            "scoreSystemId": "score-system-1",
            "feedbackTargetId": "tab-event-1",
            "expectedTabEventDigest": _sha256_json(original),
            "replacementSteelActions": [
                {"string": 6, "fret": 3, "controls": ["B"], "attack": True}
            ],
        },
        feedback_id="feedback-1",
    )

    corrected = record["tabSystems"][0]["tabEvents"][0]
    assert corrected["candidateStrings"] == [6]
    assert corrected["steelActions"][0]["string"] == 6
    assert corrected["steelActions"][0]["fret"] == 3
    assert corrected["steelActions"][0]["controls"] == ["B"]
    assert corrected["reviewState"] == "needs_human_review"
    assert corrected["eligibleForTransformationTraining"] is False
    assert provenance["literalSourceTabEvent"] == original
    assert provenance["priorTabApprovalSupersededForEvent"] is True
    assert applied["type"] == "replace_tab_event_with_expert_solution"
    action, unresolved = _tab_action_from_token(
        "3B",
        string=6,
        profile=get_e9_copedent_profile("source-e9-abc-defg-v1"),
        confidence=1.0,
        region_id="region-1",
    )
    assert unresolved is None
    assert action is not None and action["soundingPitch"] == "C4"


def test_targeted_tab_correction_requires_and_records_human_approval() -> None:
    record = {
        "tabSystems": [
            {
                "tabEvents": [
                    {
                        "tabEventId": "tab-event-1",
                        "reviewState": "needs_human_review",
                        "eligibleForTransformationTraining": False,
                        "steelActions": [{"reviewState": "needs_human_review"}],
                    }
                ]
            }
        ],
        "sourceTabCorrections": [
            {
                "targetedTabCorrectionId": "correction-1",
                "scoreSystemId": "score-system-1",
                "tabEventId": "tab-event-1",
                "reviewState": "needs_human_review",
                "eligibleForTransformationTraining": False,
            }
        ],
        "sourceScoreTabDiscrepancies": [
            {"targetedTabCorrectionId": "correction-1"}
        ],
    }
    with pytest.raises(ExtractionWorkflowError, match="must be accepted"):
        _approve_targeted_tab_corrections(
            copy.deepcopy(record),
            set(),
            reviewer_reference="score-reviewer",
            reviewed_at="2026-07-18T20:00:00Z",
        )

    approved = _approve_targeted_tab_corrections(
        record,
        {"score-system-1"},
        reviewer_reference="score-reviewer",
        reviewed_at="2026-07-18T20:00:00Z",
    )

    assert approved == ["correction-1"]
    event = record["tabSystems"][0]["tabEvents"][0]
    assert event["reviewState"] == "human_approved"
    assert event["eligibleForTransformationTraining"] is True
    assert event["steelActions"][0]["reviewState"] == "human_approved"
    assert record["sourceTabCorrections"][0]["reviewState"] == "human_approved"
    assert (
        record["sourceScoreTabDiscrepancies"][0]["resolutionState"]
        == "expert_corrected_normalized_tab_human_approved"
    )


def test_score_omr_derivative_suppresses_only_connector_tails(tmp_path: Path) -> None:
    source = tmp_path / "score.png"
    target = tmp_path / "prepared" / "score.png"
    score = Image.new("RGB", (1200, 900), "white")
    draw = ImageDraw.Draw(score)
    staff_lines = [100 + index * 20 for index in range(5)]
    for y in staff_lines:
        draw.line((100, y, 1100, y), fill="black", width=3)
    for x in (100, 500, 1100):
        draw.line((x, staff_lines[0] - 5, x, 500), fill="black", width=5)
    score.save(source)
    grid = detect_tab_grids(np.asarray(_synthetic_tab()))[0]
    events = [
        {"horizontalPosition": 0.2, "steelActions": [{"attack": True}]},
        {"horizontalPosition": 0.8, "steelActions": [{"attack": True}]},
    ]

    metadata = _prepare_score_omr_crop(source, target, grid=grid, tab_events=events)

    with Image.open(source) as original, Image.open(target) as prepared:
        assert original.getpixel((500, 400)) == (0, 0, 0)
        crop = metadata["cropBounds"]
        assert crop["bottom"] < 400
        assert prepared.getpixel(
            (500 - crop["left"], staff_lines[2] - crop["top"])
        ) == (0, 0, 0)
        assert prepared.width == crop["right"] - crop["left"]
        assert prepared.height == crop["bottom"] - crop["top"]
    assert metadata["sourcePreserved"] is True
    assert metadata["aspectRatioPreserved"] is True
    assert any(abs(value - 500) <= 2 for value in metadata["suppressedBarlineXs"])


def test_score_omr_derivative_ignores_connector_tail_below_crop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "short-score.png"
    target = tmp_path / "prepared" / "short-score.png"
    Image.new("RGB", (120, 100), "white").save(source)
    monkeypatch.setattr(
        "pocketsteel.amazing_tablature_extraction._detect_score_staff_lines",
        lambda _gray: (80, 90, 100, 110, 120),
    )
    grid = GridDetection(
        x0=0,
        y0=0,
        x1=120,
        y1=99,
        line_ys=tuple(range(10, 100, 10)),
        confidence=1.0,
        barline_xs=(60,),
    )
    metadata = _prepare_score_omr_crop(
        source,
        target,
        grid=grid,
        tab_events=[
            {"horizontalPosition": 0.2, "steelActions": [{"attack": True}]},
            {"horizontalPosition": 0.8, "steelActions": [{"attack": True}]},
        ],
    )

    assert target.exists()
    assert metadata["suppressedBarlineXs"] == []
    assert metadata["sourcePreserved"] is True


def test_audiveris_head_graph_recovers_visible_pitches_and_written_accidental(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "score.omr"
    sheet_xml = b"""\
<sheet>
  <clef kind="TREBLE" shape="G_CLEF" grade="0.9" staff="1" id="1">
    <bounds x="10" y="10" w="20" h="80"/>
  </clef>
  <head pitch="5" shape="NOTEHEAD_BLACK" grade="0.8" staff="1" id="10">
    <bounds x="100" y="100" w="20" h="14"/>
  </head>
  <head pitch="3" shape="NOTEHEAD_BLACK" grade="0.85" staff="1" id="11">
    <bounds x="200" y="80" w="20" h="14"/>
  </head>
  <head-chord grade="0.8" id="20"><bounds x="100" y="50" w="20" h="64"/></head-chord>
  <head-chord grade="0.85" id="21"><bounds x="200" y="30" w="20" h="64"/></head-chord>
  <alter pitch="3" shape="SHARP" grade="0.9" staff="1" id="30">
    <bounds x="175" y="70" w="15" h="35"/>
  </alter>
  <relation source="20" target="10"/>
  <relation source="21" target="11"/>
  <relation source="30" target="11"/>
</sheet>
"""
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("sheet#1/sheet#1.xml", sheet_xml)

    result = _parse_audiveris_head_graph(archive_path, "score-system-1")

    assert [event["pitch"] for event in result["scoreEvents"]] == ["D4", "F#4"]
    assert [event["pitchValue"] for event in result["scoreEvents"]] == [62, 66]
    assert result["scoreEvents"][1]["writtenAccidental"] == "sharp"
    assert all(event["rhythmPlaceholder"] for event in result["scoreEvents"])
    assert result["headGraph"] == {
        "reader": "audiveris-internal-head-graph-v1",
        "attackCount": 2,
        "noteheadCount": 2,
        "writtenAccidentalCount": 1,
        "tablaturePitchesProvided": False,
        "rhythmAuthoritative": False,
    }


def test_source_notehead_columns_recovers_count_without_a_clef(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "score.omr"
    sheet_xml = b"""\
<sheet>
  <head pitch="5" shape="NOTEHEAD_BLACK" grade="0.8" staff="1" id="10">
    <bounds x="100" y="100" w="20" h="14"/>
  </head>
  <head pitch="3" shape="NOTEHEAD_BLACK" grade="0.85" staff="1" id="11">
    <bounds x="104" y="80" w="20" h="14"/>
  </head>
  <head pitch="1" shape="NOTEHEAD_BLACK" grade="0.9" staff="1" id="12">
    <bounds x="200" y="70" w="20" h="14"/>
  </head>
</sheet>
"""
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("sheet#1/sheet#1.xml", sheet_xml)

    result = _audiveris_notehead_columns(archive_path)

    assert result["columnCount"] == 2
    assert result["geometryColumnCount"] == 2
    assert result["detectionMode"] == "clef_independent_geometry_fallback"
    assert result["relationColumnCount"] is None
    assert result["sourceOnly"] is True
    assert result["clefRequired"] is False
    assert result["pitchesEmitted"] is False
    assert result["tablatureCountProvided"] is False
    assert result["tablaturePitchesProvided"] is False


def test_score_projection_fusion_recovers_a_missing_source_column(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "score.png"
    image = Image.new("L", (600, 180), 255)
    draw = ImageDraw.Draw(image)
    for y in (60, 70, 80, 90, 100):
        draw.line((20, y, 580, y), fill=0, width=1)
    for x in (150, 300, 450):
        for y in (65, 80, 95):
            draw.ellipse((x - 7, y - 4, x + 7, y + 4), fill=0)
        draw.line((x + 7, 40, x + 7, 115), fill=0, width=8)
    draw.line((225, 55, 225, 105), fill=0, width=2)
    image.save(image_path)
    baseline = {
        "columnCount": 2,
        "columns": [{"x": 150.0}, {"x": 450.0}],
    }

    result = _score_projection_fusion(image_path, baseline)

    assert result["baselineAttackCount"] == 2
    assert result["imageProjectionCount"] == 3
    assert result["fusedAttackCount"] == 3
    assert result["fusionApplied"] is True
    assert result["sourceOnly"] is True
    assert result["expectedCountProvided"] is False
    assert result["tablatureProvided"] is False
    assert result["pitchesEmitted"] is False


def test_score_component_fusion_recovers_compact_heads_missed_by_baseline(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "compact-score.png"
    image = Image.new("L", (600, 180), 255)
    draw = ImageDraw.Draw(image)
    for y in (60, 70, 80, 90, 100):
        draw.line((20, y, 580, y), fill=0, width=1)
    for index, x in enumerate((150, 300, 450)):
        y = (65, 75, 95)[index]
        draw.rectangle((x - 2, y - 1, x + 2, y + 1), fill=0)
        draw.line((x + 2, y - 20, x + 2, y + 1), fill=0, width=1)
    image.save(image_path)
    baseline = {
        "columnCount": 2,
        "columns": [{"x": 150.0}, {"x": 450.0}],
    }

    component = _score_component_fusion(image_path, baseline)
    hybrid = _score_projection_component_hybrid(image_path, baseline)

    assert component["imageComponentCount"] == 3
    assert component["fusedAttackCount"] == 3
    assert component["fusionApplied"] is True
    assert component["sourceOnly"] is True
    assert component["expectedCountProvided"] is False
    assert component["tablatureProvided"] is False
    assert component["pitchesEmitted"] is False
    assert hybrid["fusedAttackCount"] == 3
    assert hybrid["sourceOnly"] is True


def test_discovery_human_exposure_inventory_is_conservative_and_excludes_automation(
    tmp_path: Path,
) -> None:
    review_root = tmp_path / "review"
    review_root.mkdir()
    (review_root / "page-review-packet.jsonl").write_text(
        json.dumps(
            {
                "inputId": "input-0001",
                "scoreSystems": [{"scoreSystemId": "score-system-1"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    submissions = review_root / "submissions"
    submissions.mkdir()
    (submissions / "review.json").write_text(
        json.dumps(
            {
                "inputIds": ["input-0002"],
                "approvedScoreSystemIds": ["score-system-2"],
            }
        ),
        encoding="utf-8",
    )
    automation = review_root / "automation"
    automation.mkdir()
    (automation / "internal.json").write_text(
        json.dumps(
            {"inputId": "input-hidden", "scoreSystemId": "score-system-hidden"}
        ),
        encoding="utf-8",
    )
    revisions = review_root / "machine-record-revisions"
    revisions.mkdir()
    (revisions / "revision.json").write_text(
        json.dumps(
            {"inputId": "input-machine", "scoreSystemId": "score-system-machine"}
        ),
        encoding="utf-8",
    )

    inventory = _discovery_human_exposure_inventory(review_root)

    assert inventory["artifactCount"] == 2
    assert inventory["inputIds"] == ["input-0001", "input-0002"]
    assert inventory["scoreSystemIds"] == ["score-system-1", "score-system-2"]
    assert len(inventory["inventoryDigest"]) == 64


def test_source_score_projection_shadow_metrics_counts_pages_and_errors() -> None:
    metrics = _source_score_projection_shadow_metrics(
        [
            {
                "inputId": "input-1",
                "baselineExact": False,
                "baselineAbsoluteError": 2,
                "challengerExact": True,
                "challengerAbsoluteError": 0,
                "fusionApplied": True,
            },
            {
                "inputId": "input-1",
                "baselineExact": True,
                "baselineAbsoluteError": 0,
                "challengerExact": True,
                "challengerAbsoluteError": 0,
                "fusionApplied": False,
            },
            {
                "inputId": "input-2",
                "baselineExact": False,
                "baselineAbsoluteError": 1,
                "challengerExact": False,
                "challengerAbsoluteError": 1,
                "fusionApplied": False,
            },
        ]
    )

    assert metrics == {
        "caseCount": 3,
        "sourcePageCount": 2,
        "baselineExactCount": 1,
        "baselineAbsoluteError": 3,
        "challengerExactCount": 2,
        "challengerAbsoluteError": 1,
        "fusionAppliedCount": 1,
    }


def test_future_projection_shadow_captures_before_review_and_scores_later(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private = tmp_path / "private"
    batch_id = "batch-future-shadow"
    batch_dir = private / "batches" / batch_id
    output_root = batch_dir / "extraction" / "discovery"
    pages_dir = output_root / "pages"
    benchmark_root = (
        output_root
        / "review"
        / "automation"
        / "source-score-notehead-challenger"
    )
    pages_dir.mkdir(parents=True)
    benchmark_root.mkdir(parents=True)
    (batch_dir / "manifest.json").write_text(
        json.dumps(
            {
                "batchId": batch_id,
                "sourceCopedentId": "source-e9-abc-defg-v1",
                "sourceCopedentRevision": 1,
            }
        ),
        encoding="utf-8",
    )
    (batch_dir / "discovery-work.jsonl").write_text(
        json.dumps({"inputId": "input-0001"}) + "\n",
        encoding="utf-8",
    )
    (batch_dir / "partition-summary.json").write_text(
        json.dumps({"groupingReviewStatus": "independent_review_passed"}),
        encoding="utf-8",
    )
    crop_path = output_root / "score-crops/input-0001/system-01.png"
    music_xml_path = output_root / "omr/input-0001/system-01.mxl"
    omr_path = music_xml_path.with_suffix(".omr")
    crop_path.parent.mkdir(parents=True)
    music_xml_path.parent.mkdir(parents=True)
    crop_path.write_bytes(b"crop")
    music_xml_path.write_bytes(b"musicxml")
    omr_path.write_bytes(b"omr")
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    page = {
        "inputId": "input-0001",
        "assetSha256": "a" * 64,
        "reviewState": "needs_human_review",
        "humanApprovalComplete": False,
        "scoreSystems": [
            {
                "scoreSystemId": "score-system-1",
                "systemIndex": 1,
                "reviewState": "needs_human_review",
                "scoreAttackCount": 99,
                "omrPreparedDerivative": {
                    "relativePath": str(crop_path.relative_to(output_root)),
                    "sha256": digest(crop_path),
                },
                "musicXml": {
                    "relativePath": str(music_xml_path.relative_to(output_root)),
                    "sha256": digest(music_xml_path),
                },
            }
        ],
    }
    (pages_dir / "input-0001.json").write_text(
        json.dumps(page), encoding="utf-8"
    )
    projection_contract = {
        "detectorVersion": SOURCE_SCORE_PROJECTION_DETECTOR_VERSION,
        "parameters": dict(SOURCE_SCORE_PROJECTION_CONTRACT),
        "anchorDetectorVersion": SOURCE_SCORE_NOTEHEAD_DETECTOR_VERSION,
        "source": "printed_score_crop_and_audiveris_source_notehead_anchors",
        "expectedCountProvided": False,
        "tablatureProvided": False,
        "pitchesEmitted": False,
    }
    selection_core = {
        "schemaVersion": "test",
        "batchId": batch_id,
        "partition": "discovery",
        "benchmarkManifestDigest": "benchmark",
        "contract": projection_contract,
        "contractDigest": _sha256_json(projection_contract),
        "fitReportDigest": "fit",
        "fitReportPath": "fit.json",
        "selectionClass": "frozen_for_future_unseen_discovery_shadow_only",
        "promotionEligible": False,
        "validationAccessed": False,
        "sealedTestAccessed": False,
        "frozenAt": "2026-07-21T00:00:00Z",
    }
    (benchmark_root / "selected-projection-contract.json").write_text(
        json.dumps(
            {**selection_core, "selectionDigest": _sha256_json(selection_core)}
        ),
        encoding="utf-8",
    )
    hybrid_contract = {
        "detectorVersion": SOURCE_SCORE_HYBRID_DETECTOR_VERSION,
        "projectionDetectorVersion": SOURCE_SCORE_PROJECTION_DETECTOR_VERSION,
        "projectionContract": dict(SOURCE_SCORE_PROJECTION_CONTRACT),
        "componentDetectorVersion": SOURCE_SCORE_COMPONENT_DETECTOR_VERSION,
        "componentContract": dict(SOURCE_SCORE_COMPONENT_CONTRACT),
        "selectionRule": "projection_change_then_component_change_then_baseline",
        "anchorDetectorVersion": SOURCE_SCORE_NOTEHEAD_DETECTOR_VERSION,
        "source": "printed_score_crop_and_audiveris_source_notehead_anchors",
        "expectedCountProvided": False,
        "tablatureProvided": False,
        "pitchesEmitted": False,
    }
    hybrid_selection_core = {
        **selection_core,
        "contract": hybrid_contract,
        "contractDigest": _sha256_json(hybrid_contract),
    }
    (benchmark_root / "selected-component-hybrid-contract.json").write_text(
        json.dumps(
            {
                **hybrid_selection_core,
                "selectionDigest": _sha256_json(hybrid_selection_core),
            }
        ),
        encoding="utf-8",
    )
    (benchmark_root / "benchmark-manifest.json").write_text(
        json.dumps({"cases": []}), encoding="utf-8"
    )
    monkeypatch.setattr(
        "pocketsteel.amazing_tablature_extraction._audiveris_notehead_columns",
        lambda _path: {"columnCount": 2, "columns": [{"x": 10}, {"x": 20}]},
    )
    monkeypatch.setattr(
        "pocketsteel.amazing_tablature_extraction._score_projection_component_hybrid",
        lambda _path, _prediction: {
            "projectionAttackCount": 2,
            "componentAttackCount": 3,
            "fusedAttackCount": 3,
            "selectedDetector": SOURCE_SCORE_COMPONENT_DETECTOR_VERSION,
            "fusionApplied": True,
            "projection": {"fusedAttackCount": 2, "fusionApplied": False},
            "component": {"fusedAttackCount": 3, "fusionApplied": True},
        },
    )
    monkeypatch.setattr(
        "pocketsteel.amazing_tablature_extraction._score_projection_fusion",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("future shadow must not run projection outside the hybrid")
        ),
    )
    extractor = AmazingTablatureExtractor(private, repo_root=tmp_path)

    captured = extractor.capture_source_score_projection_shadow(batch_id)

    assert captured["capturedCandidateCount"] == 1
    candidate_path = next(
        (benchmark_root / "future-discovery-shadow/candidates").glob("*.json")
    )
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    assert candidate["baselineAttackCount"] == 2
    assert candidate["projectionAttackCount"] == 2
    assert candidate["componentAttackCount"] == 3
    assert candidate["challengerAttackCount"] == 3
    assert candidate["selectedDetector"] == SOURCE_SCORE_COMPONENT_DETECTOR_VERSION
    assert candidate["projectionSelectionDigest"] == captured[
        "projectionSelectionDigest"
    ]
    assert candidate["hybridSelectionDigest"] == captured["hybridSelectionDigest"]
    assert candidate["reviewTruthAvailableAtCapture"] is False
    assert candidate["humanExposureAtCapture"] is False
    assert candidate.get("sourceAttackCount") is None
    assert candidate["baselineAttackCount"] != page["scoreSystems"][0]["scoreAttackCount"]

    approval_path = (
        output_root
        / "review/combined-score-tab-audit/application/approved-line-index.jsonl"
    )
    approval_path.parent.mkdir(parents=True)
    approval_path.write_text(
        json.dumps(
            {
                "inputId": "input-0001",
                "scoreSystemId": "score-system-1",
                "status": "human_approved_pitch_only",
                "scoreAttackCount": 3,
                "decisionId": "review-1",
                "reviewedRecordDigest": "b" * 64,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    scored = extractor.score_source_score_projection_shadow(
        batch_id, minimum_cases=1
    )
    recaptured = extractor.capture_source_score_projection_shadow(batch_id)

    assert scored["scoredCaseCount"] == 1
    assert scored["metrics"]["baselineExactCount"] == 0
    assert scored["metrics"]["challengerExactCount"] == 1
    assert scored["gates"]["minimumSourcePageCountMet"] is False
    assert scored["gatePassed"] is False
    assert scored["promotionEligible"] is False
    assert recaptured["capturedCandidateCount"] == 0
    assert recaptured["existingCandidateCount"] == 1
    hybrid_selection_path = (
        benchmark_root / "selected-component-hybrid-contract.json"
    )
    hybrid_selection_path.unlink()
    with pytest.raises(ExtractionWorkflowError, match="component-hybrid"):
        extractor.capture_source_score_projection_shadow(batch_id)


def test_unknown_tab_symbol_remains_unresolved() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    action, unresolved = _tab_action_from_token(
        "?",
        string=4,
        profile=profile,
        confidence=0.2,
        region_id="region-3",
    )
    assert action is None
    assert unresolved is not None
    assert unresolved["evidenceClass"] == "unknown_or_unresolved"
    assert unresolved["blocking"] is True


def test_parenthesized_number_is_quarantined_instead_of_inventing_tab_action() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    action, unresolved = _tab_action_from_token(
        "(2)",
        string=1,
        profile=profile,
        confidence=0.99,
        region_id="region-parenthetical",
    )

    assert action is None
    assert unresolved is not None
    assert unresolved["kind"] == "parenthetical_annotation_candidate"
    assert unresolved["excludedFromNormalizedFacts"] is True
    assert unresolved["blocking"] is False


def test_half_pedal_suffix_preserves_action_and_uses_one_semitone_raise() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    full_action, full_issue = _tab_action_from_token(
        "8A", string=5, profile=profile, confidence=0.99, region_id="full-a"
    )
    half_action, half_issue = _tab_action_from_token(
        "8A1/2", string=5, profile=profile, confidence=0.99, region_id="half-a"
    )

    assert full_issue is None
    assert half_issue is None
    assert half_action is not None
    assert half_action["halfStop"] is True
    assert half_action["controlSemitoneChanges"] == [1]
    assert half_action["soundingPitchValue"] == full_action["soundingPitchValue"] - 1


def test_low_confidence_tab_cell_cannot_create_a_training_action() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    action, unresolved = _tab_action_from_cell(
        {"token": "5A", "confidence": 0.62, "uncertain": True},
        string=5,
        profile=profile,
        region_id="region-low-confidence",
    )

    assert action is None
    assert unresolved is not None
    assert unresolved["kind"] == "low_confidence_tab_symbol"
    assert unresolved["candidateToken"] == "5A"
    assert unresolved["blocking"] is True


def test_mechanically_invalid_tab_cell_is_quarantined_from_normalized_actions() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    action, unresolved = _tab_action_from_cell(
        {"token": "3EF", "confidence": 0.99, "uncertain": False},
        string=4,
        profile=profile,
        region_id="region-invalid-mechanics",
    )

    assert action is None
    assert unresolved is not None
    assert unresolved["kind"] == "mechanically_invalid_tab_candidate"
    assert unresolved["excludedFromNormalizedFacts"] is True
    assert unresolved["candidateAction"]["mechanicalValidation"]["valid"] is False


def test_local_tab_reader_retries_one_transient_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sheet = tmp_path / "sheet.jpg"
    sheet.write_bytes(b"synthetic-sheet")
    calls = 0

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        @staticmethod
        def read() -> bytes:
            return json.dumps(
                {"message": {"content": json.dumps({"cells": {"e1s5": {"token": "5A", "confidence": 0.99}}})}}
            ).encode()

    def fake_urlopen(_request: object, timeout: int) -> _Response:
        nonlocal calls
        assert timeout == 120
        calls += 1
        if calls == 1:
            raise urllib.error.URLError("transient")
        return _Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = LocalTabVision().read(sheet, ["e1s5"])

    assert calls == 2
    assert result["e1s5"]["token"] == "5A"


def test_whole_system_counter_returns_only_bounded_count_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    image = tmp_path / "score-tab-system.png"
    Image.new("RGB", (400, 240), "white").save(image)
    captured_prompt = ""

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        @staticmethod
        def read() -> bytes:
            return json.dumps(
                {
                    "message": {
                        "content": json.dumps(
                            {"eventCount": 17, "confidence": 0.91, "uncertain": False}
                        )
                    }
                }
            ).encode()

    def fake_urlopen(request: object, timeout: int) -> _Response:
        nonlocal captured_prompt
        assert timeout == 120
        payload = json.loads(getattr(request, "data").decode("utf-8"))
        captured_prompt = payload["messages"][0]["content"]
        return _Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = LocalTabSystemVision().read_event_count(image)

    assert result["eventCount"] == 17
    assert result["confidence"] == 0.91
    assert result["uncertain"] is False
    assert "Do not transcribe" in captured_prompt
    assert "using ONLY the printed fret/control tokens" in captured_prompt
    assert "do not count staff noteheads" in captured_prompt
    assert "distinct horizontal token columns inside the grid" in captured_prompt
    assert result["promptVersion"] == "tab-system-event-count-v3"
    assert "sourceEventCount" not in captured_prompt
    assert "reviewer" not in captured_prompt.lower()


def test_whole_system_localizer_honors_reviewed_count_and_preserves_visible_cells(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    image = tmp_path / "score-tab-system.png"
    Image.new("RGB", (400, 240), "white").save(image)
    captured_prompt = ""

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        @staticmethod
        def read() -> bytes:
            return json.dumps(
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "events": [
                                    {
                                        "x": 0.6,
                                        "guideIndex": 2,
                                        "execution": "movement_only",
                                        "cells": [{"string": 4, "token": "3F"}],
                                    },
                                    {
                                        "x": 0.2,
                                        "guideIndex": 1,
                                        "execution": "attack",
                                        "cells": [{"string": 5, "token": "3A"}],
                                    },
                                ],
                                "confidence": 0.92,
                                "uncertain": False,
                            }
                        )
                    }
                }
            ).encode()

    def fake_urlopen(request: object, timeout: int) -> _Response:
        nonlocal captured_prompt
        assert timeout == 180
        payload = json.loads(getattr(request, "data").decode("utf-8"))
        captured_prompt = payload["messages"][0]["content"]
        return _Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = LocalTabSystemVision().localize_events(
        image,
        expected_event_count=2,
        constraint_source="machine_visual_candidate_geometry",
        guided=True,
    )

    assert [event["eventIndex"] for event in result["events"]] == [1, 2]
    assert result["events"][0]["cells"] == [{"string": 5, "token": "3A"}]
    assert result["events"][1]["execution"] == "movement_only"
    assert [event["guideIndex"] for event in result["events"]] == [1, 2]
    assert result["reviewedCountConstraint"] == 2
    assert result["deterministicGeometryGuidesProvided"] is True
    assert "exactly 2" in captured_prompt
    assert "during sustain" in captured_prompt


def test_score_pitch_reader_is_score_only_and_preserves_scientific_octaves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    image = tmp_path / "score-only.png"
    Image.new("RGB", (900, 300), "white").save(image)
    captured_prompt = ""

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        @staticmethod
        def read() -> bytes:
            return json.dumps(
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "keySignatureFifths": 1,
                                "events": [
                                    {"x": 0.2, "pitches": ["B3", "D4"]},
                                    {"x": 0.7, "pitches": ["F4", "A4"]},
                                ],
                                "confidence": 0.94,
                                "uncertain": False,
                            }
                        )
                    }
                }
            ).encode()

    def fake_urlopen(request: object, timeout: int) -> _Response:
        nonlocal captured_prompt
        assert timeout == 180
        payload = json.loads(getattr(request, "data").decode("utf-8"))
        captured_prompt = payload["messages"][0]["content"]
        return _Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = LocalTabSystemVision().read_score_pitch_events(image, expected_event_count=2)

    assert result["events"][0]["pitchValues"] == [59, 62]
    assert result["events"][1]["pitches"] == ["F4", "A4"]
    assert result["keySignatureFifths"] == 1
    assert result["tablatureOrExpectedPitchesProvidedToReader"] is False
    assert "does not contain tablature" in captured_prompt
    assert "expected pitch" not in captured_prompt.lower()


def test_unconstrained_score_reader_has_no_count_or_tablature_constraint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    image = tmp_path / "printed-score-only.png"
    Image.new("RGB", (900, 300), "white").save(image)
    captured_prompt = ""

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        @staticmethod
        def read() -> bytes:
            return json.dumps(
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "events": [
                                    {
                                        "x": 0.2,
                                        "continuationOnly": False,
                                    },
                                    {
                                        "x": 0.7,
                                        "continuationOnly": True,
                                    },
                                ],
                                "confidence": 0.93,
                                "uncertain": False,
                            }
                        )
                    }
                }
            ).encode()

    def fake_urlopen(request: object, timeout: int) -> _Response:
        nonlocal captured_prompt
        assert timeout == 180
        payload = json.loads(getattr(request, "data").decode("utf-8"))
        captured_prompt = payload["messages"][0]["content"]
        return _Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = LocalTabSystemVision().read_unconstrained_score_columns(image)

    assert result["visibleColumnCount"] == 2
    assert result["attackCount"] == 1
    assert result["continuationOnlyCount"] == 1
    assert result["expectedCountProvided"] is False
    assert result["tablatureProvided"] is False
    assert "No expected count is supplied" in captured_prompt
    assert "no tablature" in captured_prompt
    assert "every distinct horizontal column" in captured_prompt
    assert "Do not name pitches in this stage" in captured_prompt


def test_score_pitch_reader_does_not_default_an_unknown_key_to_c_major(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    image = tmp_path / "score-only.png"
    Image.new("RGB", (900, 300), "white").save(image)

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        @staticmethod
        def read() -> bytes:
            return json.dumps(
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "events": [{"x": 0.2, "pitches": ["D4"]}],
                                "confidence": 0.94,
                                "uncertain": False,
                            }
                        )
                    }
                }
            ).encode()

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: _Response())

    with pytest.raises(ExtractionWorkflowError, match="explicitly capture the key"):
        LocalTabSystemVision().read_score_pitch_events(image, expected_event_count=1)


def test_event_count_fusion_requires_both_omission_and_false_positive_reduction() -> None:
    cases = [
        {
            "sourceEventCount": 10,
            "highRecallEventCount": 8,
            "wholeSystemEventCount": 10,
            "wholeSystemConfidence": 0.95,
            "wholeSystemUncertain": False,
        },
        {
            "sourceEventCount": 10,
            "highRecallEventCount": 12,
            "wholeSystemEventCount": 10,
            "wholeSystemConfidence": 0.95,
            "wholeSystemUncertain": False,
        },
    ]

    result = _evaluate_event_count_fusion_rules(cases)

    assert result["gatePassed"] is True
    assert result["selectedRule"] == "whole_system_if_confident"
    assert result["selectedPredictions"] == [10, 10]
    assert result["metricsByRule"]["baseline"]["omissionCount"] == 2
    assert result["metricsByRule"]["baseline"]["falsePositiveCount"] == 2
    assert result["metricsByRule"]["whole_system_if_confident"]["omissionCount"] == 0
    assert result["metricsByRule"]["whole_system_if_confident"]["falsePositiveCount"] == 0
    assert result["gate"]["minimumExactCountRate"] == 0.8

    one_sided = _evaluate_event_count_fusion_rules([cases[0]])
    assert one_sided["gatePassed"] is False
    assert one_sided["selectedRule"] is None


def test_event_count_fusion_rejects_low_exact_count_rate() -> None:
    cases = [
        {
            "sourceEventCount": 10,
            "highRecallEventCount": 5,
            "wholeSystemEventCount": 9,
            "wholeSystemConfidence": 0.95,
            "wholeSystemUncertain": False,
        }
        for _index in range(4)
    ]
    cases.append(
        {
            "sourceEventCount": 10,
            "highRecallEventCount": 15,
            "wholeSystemEventCount": 10,
            "wholeSystemConfidence": 0.95,
            "wholeSystemUncertain": False,
        }
    )

    result = _evaluate_event_count_fusion_rules(cases)

    assert result["metricsByRule"]["whole_system_if_confident"]["exactCount"] == 1
    assert result["gatePassed"] is False
    assert result["selectedRule"] is None


def test_event_count_exception_replay_writes_only_isolated_candidates(tmp_path: Path) -> None:
    private = tmp_path / "private"
    batch_dir = private / "batches" / "batch-count-replay"
    output_root = batch_dir / "extraction" / "discovery"
    pages_dir = output_root / "pages"
    derivative_dir = output_root / "derivatives"
    contact_dir = output_root / "contact-sheets" / "input-0001"
    submission_dir = output_root / "review" / "submissions"
    for directory in (pages_dir, derivative_dir, contact_dir, submission_dir):
        directory.mkdir(parents=True)
    (batch_dir / "manifest.json").write_text(
        json.dumps(
            {
                "batchId": "batch-count-replay",
                "sourceCopedentId": "source-e9-abc-defg-v1",
                "sourceCopedentRevision": 1,
            }
        ),
        encoding="utf-8",
    )
    (batch_dir / "discovery-work.jsonl").write_text("{}\n", encoding="utf-8")
    (batch_dir / "partition-summary.json").write_text(
        json.dumps({"groupingReviewStatus": "independent_review_passed"}),
        encoding="utf-8",
    )
    derivative_path = derivative_dir / "input-0001.jpg"
    Image.new("RGB", (1000, 1000), "white").save(derivative_path)
    contact_path = contact_dir / "tab-system-01-cards-001-002.jpg"
    Image.new("RGB", (400, 200), "white").save(contact_path)
    contact_path.with_suffix(".tokens.json").write_text(
        json.dumps(
            {
                "labels": ["e1s5", "e2s5"],
                "cells": {
                    "e1s5": {"token": "3A", "confidence": 0.99, "uncertain": False},
                    "e2s5": {"token": "5A", "confidence": 0.99, "uncertain": False},
                },
            }
        ),
        encoding="utf-8",
    )
    record = {
        "inputId": "input-0001",
        "derivative": {"relativePath": "derivatives/input-0001.jpg"},
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "systemIndex": 1,
                "pageRegion": {"x": 0.1, "y": 0.5, "width": 0.8, "height": 0.2},
                "tabEvents": [{"tabEventId": "tab-1"}, {"tabEventId": "tab-2"}],
                "contactSheets": [
                    {"relativePath": "contact-sheets/input-0001/tab-system-01-cards-001-002.jpg"}
                ],
            }
        ],
        "scoreSystems": [
            {
                "scoreSystemId": "score-system-1",
                "pairedTabSystemId": "tab-system-1",
                "pageRegion": {"x": 0.1, "y": 0.25, "width": 0.8, "height": 0.2},
                "scoreEvents": [
                    {"scoreEventId": f"score-{index}", "measure": 1, "beat": index, "rest": False}
                    for index in range(1, 4)
                ],
            }
        ],
    }
    page_path = pages_dir / "input-0001.json"
    page_path.write_text(json.dumps(record), encoding="utf-8")
    original_page = page_path.read_bytes()
    (submission_dir / "review-count.jsonl").write_text(
        json.dumps(
            {
                "inputId": "input-0001",
                "sourceEventCounts": {"tab-system-1": 3},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    class _StubSystemVision:
        @staticmethod
        def contract() -> dict[str, Any]:
            return {"reader": "stub-count-reader", "promptVersion": "test-v1"}

        @staticmethod
        def read_event_count(_path: Path) -> dict[str, Any]:
            return {
                "eventCount": 3,
                "confidence": 0.95,
                "uncertain": False,
                "promptVersion": "test-v1",
                "model": "stub",
            }

    extractor = AmazingTablatureExtractor(private, repo_root=tmp_path)
    extractor.tab_system_vision = _StubSystemVision()
    result = extractor.replay_event_count_exceptions("batch-count-replay")

    assert result["exceptionSystemCount"] == 1
    assert result["reviewedRecordsModified"] is False
    assert result["validationAccessed"] is False
    assert result["sealedTestAccessed"] is False
    assert page_path.read_bytes() == original_page
    report = json.loads(Path(result["reportPath"]).read_text(encoding="utf-8"))
    assert report["cases"][0]["highRecallEventCount"] == 2
    assert report["cases"][0]["wholeSystemEventCount"] == 3
    assert report["cases"][0]["sourceEventCount"] == 3
    assert report["cases"][0]["eligibleForNormalizedEvents"] is False
    assert report["cases"][0]["requiresEventLocalization"] is True
    assert "diagnosticEventCount" not in report["cases"][0]
    assert report["reviewedRecordsModified"] is False
    assert stat.S_IMODE(Path(result["reportPath"]).stat().st_mode) == 0o600


def test_event_localization_review_is_isolated_compact_and_submittable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    private = tmp_path / "private"
    batch_dir = private / "batches" / "batch-localization"
    replay_dir = (
        batch_dir
        / "extraction"
        / "discovery"
        / "review"
        / "analysis"
        / "amazing-tablature-event-count-replay-v1"
    )
    source_pairs = replay_dir / "source-pairs"
    source_pairs.mkdir(parents=True)
    output_root = batch_dir / "extraction" / "discovery"
    derivatives = output_root / "derivatives"
    pages = output_root / "pages"
    derivatives.mkdir(parents=True)
    pages.mkdir(parents=True)
    (batch_dir / "manifest.json").write_text(
        json.dumps(
            {
                "batchId": "batch-localization",
                "sourceCopedentId": "source-e9-abc-defg-v1",
                "sourceCopedentRevision": 1,
                "inputs": [{"inputId": "input-0001", "relativePath": "IMG_0001.JPG"}],
            }
        ),
        encoding="utf-8",
    )
    (batch_dir / "discovery-work.jsonl").write_text("{}\n", encoding="utf-8")
    (batch_dir / "partition-summary.json").write_text(
        json.dumps({"groupingReviewStatus": "independent_review_passed"}),
        encoding="utf-8",
    )
    crop_path = source_pairs / "input-0001-system-01.png"
    Image.new("RGB", (800, 300), "white").save(crop_path)
    derivative_path = derivatives / "input-0001.png"
    Image.new("RGB", (1000, 1000), "white").save(derivative_path)
    (pages / "input-0001.json").write_text(
        json.dumps(
            {
                "inputId": "input-0001",
                "derivative": {"relativePath": "derivatives/input-0001.png"},
                "tabSystems": [
                    {
                        "tabSystemId": "tab-system-1",
                        "systemIndex": 1,
                        "pageRegion": {"x": 0.1, "y": 0.5, "width": 0.8, "height": 0.2},
                        "stringCenters": [520 + index * 18 for index in range(10)],
                    }
                ],
                "scoreSystems": [
                    {
                        "scoreSystemId": "score-system-1",
                        "systemIndex": 1,
                        "pairedTabSystemId": "tab-system-1",
                        "pageRegion": {"x": 0.05, "y": 0.15, "width": 0.9, "height": 0.25},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    count_report = {
        "fusionEvaluation": {"gatePassed": True},
        "cases": [
            {
                "status": "exception_replayed",
                "inputId": "input-0001",
                "tabSystemId": "tab-system-1",
                "systemIndex": 1,
                "sourceEventCount": 2,
                "diagnosticEventCount": 1,
            }
        ],
    }
    (replay_dir / "event-count-replay-report.json").write_text(
        json.dumps(count_report), encoding="utf-8"
    )

    class _StubLocalizer:
        model = "stub"
        seed = 1
        num_ctx = 1024

        @staticmethod
        def localize_events(_path: Path, *, expected_event_count: int) -> dict[str, Any]:
            assert expected_event_count == 2
            return {
                "events": [
                    {
                        "eventIndex": 1,
                        "x": 0.2,
                        "execution": "attack",
                        "cells": [{"string": 5, "token": "3A"}],
                    },
                    {
                        "eventIndex": 2,
                        "x": 0.7,
                        "execution": "movement_only",
                        "cells": [{"string": 4, "token": "3F"}],
                    },
                ],
                "confidence": 0.95,
                "uncertain": False,
            }

        @staticmethod
        def read_score_pitch_events(
            _path: Path, *, expected_event_count: int
        ) -> dict[str, Any]:
            assert expected_event_count == 2
            return {
                "keySignatureFifths": 0,
                "events": [
                    {
                        "eventIndex": 1,
                        "x": 0.2,
                        "pitches": ["E4"],
                        "pitchValues": [64],
                    },
                    {
                        "eventIndex": 2,
                        "x": 0.7,
                        "pitches": ["G#4"],
                        "pitchValues": [68],
                    },
                ],
                "confidence": 0.96,
                "uncertain": False,
                "tablatureOrExpectedPitchesProvidedToReader": False,
            }

    extractor = AmazingTablatureExtractor(private, repo_root=tmp_path)
    extractor.tab_system_vision = _StubLocalizer()
    monkeypatch.setattr(
        "pocketsteel.amazing_tablature_extraction._tab_event_candidates",
        lambda _gray, _grid: [
            {"x": 319, "candidateStrings": [5]},
            {"x": 1495, "candidateStrings": [4]},
        ],
    )
    result = extractor.prepare_event_localization_review("batch-localization")

    assert result["systemCount"] == 1
    assert result["mechanicallyValidSystemCount"] == 1
    assert result["reviewedRecordsModified"] is False
    assert result["validationAccessed"] is False
    assert result["sealedTestAccessed"] is False
    console = Path(result["consolePath"]).read_text(encoding="utf-8")
    assert "Original printed score and tablature system" in console
    assert "for(let string=1;string<=10;string++)" in console
    assert "no internal IDs or line-by-line form is required" in console
    assert "Submit completed review to Lane 20" in console
    assert "Your saved work remains in this browser" in console
    assert "localStorage" in console

    packet = json.loads((replay_dir / "localization-review" / "packet.json").read_text())
    payload = {
        "reviewType": "event_localization",
        "batchId": "batch-localization",
        "partition": "discovery",
        "packetDigest": packet["packetDigest"],
        "reviews": [
            {
                "inputId": "input-0001",
                "tabSystemId": "tab-system-1",
                "status": "accept",
                "comment": None,
            }
        ],
    }
    first = _store_event_localization_submission(private, payload)
    second = _store_event_localization_submission(private, payload)
    assert first["status"] == "received_not_applied"
    assert second["submissionId"] == first["submissionId"]
    assert second["deduplicated"] is True

    pitch_result = extractor.prepare_score_pitch_correspondence_review("batch-localization")
    assert pitch_result["eventCount"] == 2
    assert pitch_result["exactPitchMatchCount"] == 2
    assert pitch_result["allExactPitchMatches"] is True
    assert pitch_result["reviewedRecordsModified"] is False
    pitch_console = Path(pitch_result["consolePath"]).read_text(encoding="utf-8")
    assert "Seven-column score → tablature pitch audit" in pitch_console
    assert "possible missed score note" in pitch_console
    assert "Score-to-tab relationship" in pitch_console
    pitch_packet = json.loads(
        (
            replay_dir
            / "localization-review"
            / "score-pitch-audit"
            / "packet.json"
        ).read_text()
    )
    pitch_payload = {
        "reviewType": "score_pitch_correspondence",
        "batchId": "batch-localization",
        "partition": "discovery",
        "packetDigest": pitch_packet["packetDigest"],
        "reviews": [
            {
                "inputId": "input-0001",
                "tabSystemId": "tab-system-1",
                "status": "accept",
                "comment": None,
            }
        ],
    }
    pitch_first = _store_score_pitch_submission(private, pitch_payload)
    pitch_second = _store_score_pitch_submission(private, pitch_payload)
    assert pitch_first["status"] == "received_not_applied"
    assert pitch_second["submissionId"] == pitch_first["submissionId"]
    assert pitch_second["deduplicated"] is True


def test_tab_modifier_is_preserved_without_inventing_its_meaning() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    action, unresolved = _tab_action_from_token(
        "-3B-",
        string=3,
        profile=profile,
        confidence=0.95,
        region_id="region-modifier",
    )

    assert action is not None
    assert action["mechanicalValidation"]["valid"] is True
    assert action["notationPrefix"] == "-"
    assert action["notationSuffix"] == "-"
    assert action["notationMarks"][0]["candidateMeanings"] == ["sustain", "slide", "bar_movement"]
    assert unresolved is not None
    assert unresolved["kind"] == "uncertain_tab_modifier"
    assert unresolved["blocking"] is True


@pytest.mark.parametrize(
    ("token", "string", "expected_frets", "expected_controls", "expected_change"),
    [
        ("3B-5B", 6, [3, 5], [["B"], ["B"]], None),
        ("8A-8", 5, [8, 8], [["A"], []], ("A", "release")),
        ("8-8B", 6, [8, 8], [[], ["B"]], ("B", "engage")),
        ("3-15B", 6, [3, 15], [[], ["B"]], ("B", "engage")),
        ("10A10", 5, [10, 10], [["A"], []], ("A", "release")),
    ],
)
def test_printed_tab_movement_chain_becomes_sustained_state_events(
    token: str,
    string: int,
    expected_frets: list[int],
    expected_controls: list[list[str]],
    expected_change: tuple[str, str] | None,
) -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    actions, unresolved = _tab_action_sequence_from_token(
        token,
        string=string,
        profile=profile,
        confidence=0.99,
        region_id="region-movement-chain",
    )

    assert unresolved is None
    assert [action["fret"] for action in actions] == expected_frets
    assert [action["controls"] for action in actions] == expected_controls
    assert [action["attack"] for action in actions] == [True, False]
    assert actions[1]["sustain"] is True
    if expected_frets[0] != expected_frets[1]:
        assert actions[1]["slide"] is True
        assert actions[1]["barMovement"] == {
            "fromFret": expected_frets[0],
            "toFret": expected_frets[1],
            "timing": "during_sustain",
        }
    if expected_change is not None:
        control, change = expected_change
        assert actions[1]["controlChanges"] == [
            {"control": control, "action": change, "timing": "during_sustain"}
        ]


def test_movement_chain_cell_is_retained_while_low_confidence_cell_is_quarantined() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    actions, issue = _tab_action_sequence_from_cell(
        {"token": "8A-8", "confidence": 0.97, "uncertain": False},
        string=5,
        profile=profile,
        region_id="region-chain-cell",
    )
    assert issue is None
    assert len(actions) == 2

    actions, issue = _tab_action_sequence_from_cell(
        {"token": "8A-8", "confidence": 0.62, "uncertain": True},
        string=5,
        profile=profile,
        region_id="region-chain-cell-low-confidence",
    )
    assert actions == []
    assert issue is not None
    assert issue["excludedFromNormalizedFacts"] is True


def test_empty_high_recall_string_cell_is_not_a_symbol_failure() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")

    actions, issue = _tab_action_sequence_from_cell(
        {"token": None, "confidence": 0.0, "uncertain": True},
        string=7,
        profile=profile,
        region_id="region-empty-high-recall-cell",
    )

    assert actions == []
    assert issue is None


def test_tab_cell_crop_stops_between_neighboring_event_components() -> None:
    events = [
        {"x": 100, "x0": 88, "x1": 112},
        {"x": 140, "x0": 128, "x1": 152},
        {"x": 220, "x0": 208, "x1": 232},
    ]

    first = _tab_cell_horizontal_bounds(events, 0, image_width=300, cell_height=24)
    middle = _tab_cell_horizontal_bounds(events, 1, image_width=300, cell_height=24)
    last = _tab_cell_horizontal_bounds(events, 2, image_width=300, cell_height=24)

    assert first == (52, 120)
    assert middle == (120, 180)
    assert last == (180, 268)


def test_movement_chain_uses_the_exact_batch_copedent_for_lever_changes() -> None:
    licks_profile = get_e9_copedent_profile("source-e9-abc-defg-d48-e29-v1")
    actions, issue = _tab_action_sequence_from_token(
        "8D-8",
        string=4,
        profile=licks_profile,
        confidence=0.99,
        region_id="region-licks-d-release",
    )

    assert issue is None
    assert len(actions) == 2
    assert actions[0]["controls"] == ["D"]
    assert actions[1]["controls"] == []
    assert actions[1]["releaseTiming"] == "during_sustain"
    assert actions[1]["soundingPitchValue"] == actions[0]["soundingPitchValue"] + 1


def test_identical_connected_tab_states_do_not_invent_a_movement_or_repick() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    actions, issue = _tab_action_sequence_from_token(
        "8-8",
        string=4,
        profile=profile,
        confidence=0.99,
        region_id="region-identical-connected-state",
    )

    assert len(actions) == 1
    assert actions[0]["attack"] is True
    assert actions[0]["notationMarks"][-1]["candidateMeanings"] == [
        "sustain",
        "repeated_pick",
    ]
    assert issue is not None
    assert issue["kind"] == "uncertain_repeated_tab_state"


def test_overlapping_identical_raises_do_not_double_and_opposed_controls_conflict() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    shared_raise, shared_issue = _tab_action_from_token(
        "3AC",
        string=5,
        profile=profile,
        confidence=0.99,
        region_id="region-shared-raise",
    )
    assert shared_raise is not None
    assert shared_raise["soundingPitchValue"] == 64
    assert shared_raise["mechanicalValidation"]["valid"] is True
    assert shared_issue is None

    conflict, conflict_issue = _tab_action_from_token(
        "3EF",
        string=4,
        profile=profile,
        confidence=0.99,
        region_id="region-conflict",
    )
    assert conflict is not None
    assert conflict["mechanicalValidation"]["valid"] is False
    assert conflict_issue is not None
    assert "conflicting_control_changes_on_string" in conflict_issue["issues"]


def test_alignment_records_octave_transposing_score_convention() -> None:
    score = [
        {
            "scoreEventId": "score-1",
            "measure": 1,
            "beat": 1.0,
            "pitchValue": 71,
            "rest": False,
        }
    ]
    tab = [
        {
            "tabEventId": "tab-1",
            "steelActions": [{"soundingPitchValue": 59}],
        }
    ]

    alignment = _align_events(score, tab)[0]
    assert alignment["scoreNotationTranspositionSemitones"] == 12
    assert alignment["notationAdjustedPitchAgreement"] is True
    assert alignment["soundingPitchAgreement"] is False


def test_ordered_alignment_ignores_movement_only_events_and_never_reuses_score_notes() -> None:
    score = [
        {"scoreEventId": "score-1", "measure": 1, "beat": 1.0, "pitchValue": 60, "rest": False},
        {"scoreEventId": "score-2", "measure": 1, "beat": 2.0, "pitchValue": 62, "rest": False},
    ]
    tab = [
        {"tabEventId": "tab-1", "steelActions": [{"soundingPitchValue": 60, "attack": True}]},
        {"tabEventId": "move-1", "steelActions": [{"soundingPitchValue": 61, "attack": False}]},
        {"tabEventId": "tab-2", "steelActions": [{"soundingPitchValue": 62, "attack": True}]},
    ]

    alignments = _align_events(score, tab)

    assert [item["tabEventIds"] for item in alignments] == [["tab-1"], ["tab-2"]]
    assert [item["scoreEventIds"] for item in alignments] == [["score-1"], ["score-2"]]
    assert all(item["alignmentMethod"] == "ordered_attack_group_v3" for item in alignments)


def test_reviewed_line_alignment_can_include_sustained_pitch_changes() -> None:
    score = [
        {"scoreEventId": "score-1", "measure": 1, "beat": 1.0, "pitchValue": 60, "rest": False},
        {"scoreEventId": "score-2", "measure": 1, "beat": 2.0, "pitchValue": 62, "rest": False},
    ]
    tab = [
        {"tabEventId": "tab-1", "steelActions": [{"soundingPitchValue": 60, "attack": True}]},
        {
            "tabEventId": "move-1",
            "steelActions": [
                {
                    "soundingPitchValue": 62,
                    "attack": False,
                    "sustain": True,
                    "slide": {"fromFret": 1, "toFret": 3, "withoutRepick": True},
                }
            ],
        },
    ]

    alignments = _align_events(score, tab, include_movement_only=True)

    assert [item["tabEventIds"] for item in alignments] == [["tab-1"], ["move-1"]]
    assert [item["scoreEventIds"] for item in alignments] == [["score-1"], ["score-2"]]
    assert alignments[1]["alignmentType"] == "sustained_pitch_change"
    assert alignments[1]["alignmentMethod"] == "ordered_sounding_state_v1"


def test_review_description_shows_slide_origin_pitch_and_control_changes() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    event = {
        "controlChanges": [
            {"action": "release", "control": "B", "timing": "during_sustain"}
        ],
        "steelActions": [
            {
                "string": 5,
                "fret": 3,
                "controls": [],
                "attack": False,
                "sustain": True,
                "slide": {"fromFret": 1, "toFret": 3, "withoutRepick": True},
            }
        ],
    }

    description = _review_tab_event_description(event, profile)

    assert "S5 fret 1→3 [C4→D4]" in description
    assert "slide/hold, no repick" in description
    assert "release B during sustain" in description


def test_normalized_score_musicxml_round_trips_the_audited_score_facts(tmp_path: Path) -> None:
    target = tmp_path / "normalized.musicxml"
    payload = {
        "keyFifths": 1,
        "timeSignature": {"beats": 4, "beatType": 4, "symbol": "common"},
        "measures": [
            {
                "measure": 1,
                "printedMeasureNumber": "1",
                "durationBeats": 4.0,
                "rhythmicStart": 0.0,
                "keyFifths": 1,
                "timeSignature": {"beats": 4, "beatType": 4, "symbol": "common"},
            }
        ],
        "scoreEvents": [
            {
                "measure": 1,
                "beat": 1.0,
                "durationBeats": 2.0,
                "pitch": "Db4",
                "pitchValue": 61,
                "pitchStep": "D",
                "pitchAlter": -1,
                "octave": 4,
                "writtenAccidental": "flat",
                "rest": False,
            },
            {"measure": 1, "beat": 1.0, "durationBeats": 2.0, "pitchValue": 67, "rest": False},
            {"measure": 1, "beat": 1.0, "durationBeats": 2.0, "pitchValue": 71, "rest": False},
            {"measure": 1, "beat": 3.0, "durationBeats": 2.0, "pitchValue": 59, "rest": False},
            {"measure": 1, "beat": 3.0, "durationBeats": 2.0, "pitchValue": 62, "rest": False},
            {"measure": 1, "beat": 3.0, "durationBeats": 2.0, "pitchValue": 67, "rest": False},
        ],
        "chordContexts": [{"measure": 1, "beat": 1.0, "symbol": "G"}],
    }

    metadata = _write_normalized_score_musicxml(payload, target)
    parsed = _parse_musicxml(target, "system-1")

    assert metadata["reader"] == "normalized-score-facts-v1"
    assert len(parsed["measures"]) == 1
    assert len(parsed["scoreEvents"]) == 6
    assert {
        (event["beat"], event["pitchValue"]) for event in parsed["scoreEvents"]
    } == {(1.0, 61), (1.0, 67), (1.0, 71), (3.0, 59), (3.0, 62), (3.0, 67)}
    assert parsed["timeSignature"]["symbol"] == "common"
    flat = next(event for event in parsed["scoreEvents"] if event["pitchValue"] == 61)
    assert flat["pitch"] == "Db4"
    assert flat["writtenAccidental"] == "flat"


def test_normalized_score_musicxml_separates_concurrent_voices(tmp_path: Path) -> None:
    target = tmp_path / "voices.musicxml"
    payload = {
        "timeSignature": {"beats": 4, "beatType": 4},
        "measures": [{"measure": 1, "durationBeats": 4.0}],
        "scoreEvents": [
            {
                "measure": 1,
                "beat": 1.0,
                "durationBeats": 1.0,
                "pitchValue": 60,
                "voice": 1,
                "staff": 1,
                "rest": False,
            },
            {
                "measure": 1,
                "beat": 1.0,
                "durationBeats": 1.0,
                "pitchValue": 64,
                "voice": 1,
                "staff": 1,
                "rest": False,
            },
            {
                "measure": 1,
                "beat": 1.0,
                "durationBeats": 4.0,
                "voice": 2,
                "staff": 1,
                "rest": True,
            },
        ],
    }

    _write_normalized_score_musicxml(payload, target)
    root = __import__("xml.etree.ElementTree", fromlist=["parse"]).parse(target).getroot()
    notes = root.findall(".//note")

    assert root.find(".//backup/duration").text == "480"
    assert [note.findtext("voice") for note in notes] == ["1", "1", "2"]
    assert notes[1].find("chord") is not None
    assert notes[2].find("chord") is None


def test_reviewed_score_attack_correction_adds_missing_chord_tones() -> None:
    system = {
        "scoreSystemId": "score-system-1",
        "scoreEvents": [
            {
                "scoreEventId": "score-event-d",
                "measure": 4,
                "beat": 2.0,
                "durationBeats": 3.0,
                "pitch": "D4",
                "pitchValue": 62,
                "pitchStep": "D",
                "pitchAlter": 0,
                "octave": 4,
                "rest": False,
                "defaultX": 79.0,
            }
        ],
    }
    operation = {
        "operationId": "restore-d-major-triad",
        "measure": 4,
        "beat": 2.0,
        "expectedPitches": ["D4"],
        "replacementPitches": ["D4", "F#4", "A4"],
    }

    result = _replace_score_attack_from_review(system, operation)

    assert [event["pitch"] for event in system["scoreEvents"]] == ["D4", "F#4", "A4"]
    assert [event["pitchValue"] for event in system["scoreEvents"]] == [62, 66, 69]
    assert all(event["durationBeats"] == 3.0 for event in system["scoreEvents"])
    assert system["scoreEvents"][0]["scoreEventId"] == "score-event-d"
    assert all(event["reviewState"] == "needs_human_review" for event in system["scoreEvents"])
    assert result["expectedPitches"] == ["D4"]
    assert result["replacementPitches"] == ["D4", "F#4", "A4"]


def test_reviewed_score_system_correction_replaces_attack_sequence_without_approving_rhythm() -> None:
    system = {
        "scoreSystemId": "score-system-1",
        "timeSignature": {"beats": 4, "beatType": 4},
        "measures": [{"measure": 1, "durationBeats": 2.0}],
        "scoreEvents": [
            {
                "scoreEventId": "score-event-c",
                "measure": 1,
                "beat": 1.0,
                "durationBeats": 2.0,
                "pitch": "C4",
                "pitchValue": 60,
                "pitchStep": "C",
                "pitchAlter": 0,
                "octave": 4,
                "rest": False,
                "defaultX": 50.0,
            },
            {
                "scoreEventId": "score-event-extra",
                "measure": 1,
                "beat": 2.0,
                "durationBeats": 1.0,
                "pitch": "D4",
                "pitchValue": 62,
                "pitchStep": "D",
                "pitchAlter": 0,
                "octave": 4,
                "rest": False,
                "defaultX": 100.0,
            },
        ],
    }
    expected_projection = [
        {"measure": 1, "beat": 1.0, "pitches": ["C4"]},
        {"measure": 1, "beat": 2.0, "pitches": ["D4"]},
    ]
    operation = {
        "operationId": "replace-complete-reviewed-system",
        "expectedScoreAttackDigest": _sha256_json(expected_projection),
        "replacementAttacks": [
            {"measure": 1, "beat": 1.0, "pitches": ["C#4", "Eb4", "G4"]},
            {"measure": 2, "beat": 1.0, "pitches": ["D4"]},
        ],
    }

    result = _replace_score_system_attacks_from_review(system, operation)

    assert [event["pitch"] for event in system["scoreEvents"]] == [
        "C#4",
        "Eb4",
        "G4",
        "D4",
    ]
    assert [event["writtenAccidental"] for event in system["scoreEvents"]] == [
        "sharp",
        "flat",
        None,
        None,
    ]
    assert [measure["measure"] for measure in system["measures"]] == [1, 2]
    assert all(
        event["fieldReviewStates"]["duration"] == "not_reviewed_excluded"
        for event in system["scoreEvents"]
    )
    assert result["replacementAttackCount"] == 2
    assert result["replacementScoreEventCount"] == 4
    assert result["durationReviewState"] == "not_reviewed_excluded"


def test_score_audit_cross_scope_conflict_blocks_only_its_system() -> None:
    record = {
        "scoreSystems": [
            {
                "scoreSystemId": "score-system-1",
                "pairedTabSystemId": "tab-system-1",
                "scoreEvents": [
                    {
                        "scoreEventId": "score-event-1",
                        "measure": 1,
                        "beat": 1.0,
                        "pitchValue": 60,
                        "rest": False,
                    }
                ],
            }
        ],
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "tabEvents": [
                    {
                        "tabEventId": "tab-event-1",
                        "measure": 1,
                        "horizontalPosition": 0.5,
                        "steelActions": [
                            {"attack": True, "soundingPitchValue": 60}
                        ],
                    }
                ],
            }
        ],
        "unresolved": [
            {
                "kind": "score_audit_cross_scope_conflict",
                "scoreSystemId": "score-system-1",
            }
        ],
    }
    record["eventAlignments"] = _align_events(
        record["scoreSystems"][0]["scoreEvents"],
        record["tabSystems"][0]["tabEvents"],
    )

    gates = _score_audit_equivalence_gates(record)

    assert gates["score-system-1"]["readyForHumanReview"] is False
    assert {item["code"] for item in gates["score-system-1"]["blockingReasons"]} == {
        "cross_scope_conflict_pending"
    }


def test_alignment_uses_horizontal_order_and_accepts_melody_inside_grip() -> None:
    score = [
        {"scoreEventId": "score-1", "measure": 1, "beat": 1.0, "pitchValue": 60, "defaultX": 100, "rest": False},
        {"scoreEventId": "score-2", "measure": 1, "beat": 2.0, "pitchValue": 62, "defaultX": 200, "rest": False},
        {"scoreEventId": "score-3", "measure": 1, "beat": 3.0, "pitchValue": 64, "defaultX": 300, "rest": False},
    ]
    tab = [
        {
            "tabEventId": "tab-1",
            "horizontalPosition": 0.1,
            "steelActions": [{"soundingPitchValue": 60}],
        },
        {
            "tabEventId": "tab-2",
            "horizontalPosition": 0.9,
            "steelActions": [{"soundingPitchValue": 57}, {"soundingPitchValue": 64}],
        },
    ]

    alignments = _align_events(score, tab)
    assert alignments[0]["scoreEventIds"] == ["score-1"]
    assert alignments[1]["scoreEventIds"] == ["score-3"]
    assert alignments[1]["notationAdjustedPitchAgreement"] is True
    assert alignments[1]["alignmentType"] == "grip"
    assert alignments[1]["alignmentMethod"] == "monotonic_pitch_position_v2"


def test_sustained_tab_action_aligns_to_later_matching_score_event() -> None:
    score = [
        {
            "scoreEventId": "score-1",
            "measure": 1,
            "beat": 1.0,
            "pitchValue": 60,
            "defaultX": 100,
            "rest": False,
        },
        {
            "scoreEventId": "score-2",
            "measure": 1,
            "beat": 2.0,
            "pitchValue": 60,
            "defaultX": 200,
            "rest": False,
            "tie": "stop",
        },
        {
            "scoreEventId": "score-3",
            "measure": 1,
            "beat": 3.0,
            "pitchValue": 62,
            "defaultX": 300,
            "rest": False,
        },
    ]
    tab = [
        {
            "tabEventId": "tab-1",
            "horizontalPosition": 0.1,
            "steelActions": [{"soundingPitchValue": 60, "sustain": True}],
        },
        {
            "tabEventId": "tab-2",
            "horizontalPosition": 0.9,
            "steelActions": [{"soundingPitchValue": 62}],
        },
    ]

    alignments = _align_events(score, tab)
    assert alignments[0]["scoreEventIds"] == ["score-1", "score-2"]
    assert alignments[0]["sustainInheritedScoreEventIds"] == ["score-2"]
    assert alignments[0]["alignmentType"] == "sustained_tab_event"


def test_score_attack_groups_ignore_dots_and_tied_continuations() -> None:
    score = [
        {
            "scoreEventId": "dotted-attack",
            "measure": 1,
            "beat": 1.0,
            "durationBeats": 1.5,
            "pitchValue": 60,
            "rest": False,
        },
        {
            "scoreEventId": "tie-continuation",
            "measure": 1,
            "beat": 2.5,
            "durationBeats": 0.5,
            "pitchValue": 60,
            "rest": False,
            "tie": ["stop"],
        },
        {
            "scoreEventId": "next-attack",
            "measure": 1,
            "beat": 3.0,
            "durationBeats": 1.0,
            "pitchValue": 62,
            "rest": False,
        },
    ]

    groups = _score_attack_groups(score)

    assert [[event["scoreEventId"] for event in group] for group in groups] == [
        ["dotted-attack"],
        ["next-attack"],
    ]


def test_score_attack_groups_split_same_beat_notes_at_distinct_printed_positions() -> None:
    score = [
        {
            "scoreEventId": "sequential-1",
            "measure": 1,
            "beat": 1.0,
            "defaultX": 16.0,
            "pitch": "D5",
            "pitchValue": 74,
            "chordMember": False,
            "rest": False,
        },
        {
            "scoreEventId": "sequential-2",
            "measure": 1,
            "beat": 1.0,
            "defaultX": 129.0,
            "pitch": "G5",
            "pitchValue": 79,
            "chordMember": False,
            "rest": False,
        },
        {
            "scoreEventId": "chord-tone",
            "measure": 1,
            "beat": 1.0,
            "defaultX": 129.0,
            "pitch": "B5",
            "pitchValue": 83,
            "chordMember": True,
            "rest": False,
        },
    ]

    groups = _score_attack_groups(score)
    comparison = _combined_score_tab_columns(
        {"scoreEvents": score},
        {
            "tabEvents": [
                {
                    "eventIndex": 1,
                    "steelActions": [
                        {"attack": True, "soundingPitch": "D5", "soundingPitchValue": 74}
                    ],
                },
                {
                    "eventIndex": 2,
                    "steelActions": [
                        {"attack": True, "soundingPitch": "G5", "soundingPitchValue": 79},
                        {"attack": True, "soundingPitch": "B5", "soundingPitchValue": 83},
                    ],
                },
            ]
        },
    )
    legacy_comparison = _combined_score_tab_columns(
        {"scoreEvents": score},
        {
            "tabEvents": [
                {
                    "eventIndex": 1,
                    "steelActions": [
                        {"attack": True, "soundingPitch": "D5", "soundingPitchValue": 74},
                        {"attack": True, "soundingPitch": "G5", "soundingPitchValue": 79},
                        {"attack": True, "soundingPitch": "B5", "soundingPitchValue": 83},
                    ],
                }
            ]
        },
        grouping_contract="combined-score-tab-evidence-gate-v3",
    )

    assert [[event["scoreEventId"] for event in group] for group in groups] == [
        ["sequential-1"],
        ["sequential-2", "chord-tone"],
    ]
    assert comparison["scoreAttackCount"] == 2
    assert comparison["automaticPitchGatePassed"] is True
    assert legacy_comparison["scoreAttackCount"] == 1
    assert legacy_comparison["automaticPitchGatePassed"] is True


def test_score_attack_groups_do_not_merge_normalized_sequential_positions() -> None:
    score = [
        {
            "scoreEventId": "score-1",
            "measure": 1,
            "beat": 1.0,
            "pitchValue": 60,
            "defaultX": 0.10,
            "rest": False,
        },
        {
            "scoreEventId": "score-2",
            "measure": 1,
            "beat": 1.0,
            "pitchValue": 62,
            "defaultX": 0.20,
            "rest": False,
        },
        {
            "scoreEventId": "score-3",
            "measure": 1,
            "beat": 1.0,
            "pitchValue": 65,
            "defaultX": 0.20,
            "chordMember": True,
            "rest": False,
        },
    ]

    groups = _score_attack_groups(score)
    v4_comparison = _combined_score_tab_columns(
        {"scoreEvents": score},
        {"tabEvents": []},
        grouping_contract="combined-score-tab-evidence-gate-v4",
    )

    assert [[event["scoreEventId"] for event in group] for group in groups] == [
        ["score-1"],
        ["score-2", "score-3"],
    ]
    assert v4_comparison["scoreAttackCount"] == 1


def test_combined_columns_flag_isolated_chord_in_monophonic_line() -> None:
    score = [
        {
            "scoreEventId": f"score-{index}",
            "measure": 1,
            "beat": float(index),
            "pitchValue": 59 + index,
            "defaultX": index * 20,
            "rest": False,
        }
        for index in range(1, 5)
    ]
    score.append(
        {
            "scoreEventId": "false-chord-tone",
            "measure": 1,
            "beat": 3.0,
            "pitchValue": 67,
            "defaultX": 60,
            "chordMember": True,
            "rest": False,
        }
    )
    tab_events = [
        {
            "tabEventId": f"tab-{index}",
            "eventIndex": index,
            "steelActions": [
                {
                    "attack": True,
                    "soundingPitchValue": 59 + index,
                    "soundingPitch": f"P{index}",
                }
            ],
        }
        for index in range(1, 5)
    ]

    comparison = _combined_score_tab_columns(
        {"scoreEvents": score},
        {"tabEvents": tab_events},
    )

    assert comparison["scoreTextureSizes"] == [1, 1, 2, 1]
    assert comparison["tabAttackTextureSizes"] == [1, 1, 1, 1]
    assert comparison["monophonicScoreTextureConflict"] is True


def test_tab_system_feedback_requires_no_event_by_event_comment() -> None:
    normalized = _normalized_event_feedback(
        {
            "tabSystems": [
                {"tabSystemId": "tab-system-1", "systemIndex": 0, "tabEvents": []}
            ],
            "movementSequences": [],
        },
        [
            {
                "targetType": "tab_system",
                "tabSystemId": "tab-system-1",
                "feedbackType": "needs_correction",
                "comment": "Recapture this complete system.",
            }
        ],
        input_id="input-1",
        machine_digest="a" * 64,
    )

    assert normalized[0]["target"] == {
        "targetType": "tab_system",
        "tabSystemId": "tab-system-1",
    }
    assert normalized[0]["context"]["label"] == "System 1"


def test_semantically_identical_browser_feedback_is_deduplicated() -> None:
    feedback = {
        "targetType": "tab_system",
        "tabSystemId": "tab-system-1",
        "feedbackType": "needs_correction",
        "comment": "Recapture this complete system.",
    }

    normalized = _normalized_event_feedback(
        {
            "tabSystems": [
                {"tabSystemId": "tab-system-1", "systemIndex": 0, "tabEvents": []}
            ],
            "movementSequences": [],
        },
        [feedback, dict(feedback)],
        input_id="input-1",
        machine_digest="a" * 64,
    )

    assert len(normalized) == 1


def test_alignment_prefers_matching_tab_measure_for_repeated_pitch() -> None:
    score = [
        {
            "scoreEventId": "score-m1",
            "measure": 1,
            "beat": 1.0,
            "pitchValue": 60,
            "defaultX": 100,
            "rest": False,
        },
        {
            "scoreEventId": "score-m2",
            "measure": 2,
            "beat": 1.0,
            "pitchValue": 60,
            "defaultX": 200,
            "rest": False,
        },
    ]
    tab = [
        {
            "tabEventId": "tab-m2",
            "measure": 2,
            "horizontalPosition": 0.05,
            "steelActions": [{"soundingPitchValue": 60}],
        }
    ]

    alignment = _align_events(score, tab)[0]
    assert alignment["scoreEventIds"] == ["score-m2"]
    assert alignment["measureAgreement"] is True


def test_pitch_mismatched_alignment_candidate_is_preserved_but_not_normalized() -> None:
    candidate = _align_events(
        [{"scoreEventId": "score-1", "measure": 1, "beat": 1.0, "pitchValue": 60, "rest": False}],
        [{"tabEventId": "tab-1", "steelActions": [{"soundingPitchValue": 66}]}],
    )[0]

    verified, unresolved = _separate_verified_alignments([candidate])

    assert verified == []
    assert unresolved[0]["kind"] == "unverified_score_tab_alignment"
    assert unresolved[0]["excludedFromNormalizedFacts"] is True
    assert unresolved[0]["candidateAlignment"]["eventAlignmentId"] == candidate["eventAlignmentId"]


def test_movement_and_teaching_taxonomy_preserves_transition_mechanics() -> None:
    previous = {
        "tabEventId": "tab-1",
        "confidence": 0.96,
        "steelActions": [
            {"steelActionId": "action-1", "string": 5, "fret": 3, "controls": [], "soundingPitchValue": 62},
            {"steelActionId": "action-2", "string": 4, "fret": 3, "controls": [], "soundingPitchValue": 67},
        ],
    }
    current = {
        "tabEventId": "tab-2",
        "confidence": 0.94,
        "steelActions": [
            {"steelActionId": "action-3", "string": 5, "fret": 3, "controls": ["A"], "soundingPitchValue": 64},
            {"steelActionId": "action-4", "string": 4, "fret": 3, "controls": [], "soundingPitchValue": 67},
        ],
    }
    systems = [{"tabSystemId": "system-1", "tabEvents": [previous, current]}]
    movements = _derive_movement_sequences(systems, "page-1")

    assert len(movements) == 1
    classifications = {item["concept"] for item in movements[0]["classifications"]}
    assert "pedal_change_without_bar_movement" in classifications
    assert "pedal_squeeze" in classifications
    assert "common_tone_retention" in classifications
    assert movements[0]["controlsAdded"] == ["A"]


    grips = _derive_grips(systems)
    assert len(grips) == 2
    assert grips[0]["strings"] == [4, 5]
    assert grips[1]["topSteelActionId"] == "action-4"
    assert all(grip["mechanicalValidation"]["valid"] for grip in grips)

    concepts = _derive_teaching_concepts(
        [
            {
                "explicitTextId": "text-concept",
                "pageRegionId": "region-concept",
                "text": "Practice this E9 banjo technique as a C to F transition",
                "pageRegion": {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.1},
            }
        ],
        systems,
        movements,
        "page-1",
    )
    concept_names = {item["concept"] for item in concepts}
    assert "practice_method" in concept_names
    assert "chord_transition" in concept_names
    assert "e9_material_reference" in concept_names
    assert "adapted_banjo_vocabulary" in concept_names
    assert "technique_explanation" in concept_names
    e9_concept = next(item for item in concepts if item["concept"] == "e9_material_reference")
    assert e9_concept["supportingExplicitTextIds"] == ["text-concept"]
    assert e9_concept["supportingPageRegionIds"] == ["region-concept"]
    assert e9_concept["supportingPageRegions"]
    assert "top_note_targeting" in concept_names
    assert "pedal_change_without_bar_movement" in concept_names

    exercises = _derive_exercises(
        {"primary": "practice_method", "evidenceClass": "interpretive_inference", "confidence": 0.8},
        [
            {
                "explicitTextId": "text-1",
                "text": (
                    "Before you begin, you should know the tuning. Practice from 60 to 80 BPM, "
                    "repeat 10 times, and use smooth bar movement so the melody resolves."
                ),
            }
        ],
        systems,
        concepts,
        "page-1",
    )
    assert exercises[0]["recommendedTempoBpm"] == [80]
    assert exercises[0]["recommendedTempoProgressionsBpm"] == [{"fromBpm": 60, "toBpm": 80}]
    assert exercises[0]["recommendedRepetitions"] == [10]
    assert exercises[0]["prerequisiteStatementIds"] == ["text-1"]
    assert exercises[0]["statedMusicalPurposeStatementIds"] == ["text-1"]
    assert exercises[0]["statedMechanicalPurposeStatementIds"] == ["text-1"]
    assert exercises[0]["instructionalStatementIds"] == ["text-1"]


def test_unmarked_multi_fret_grip_cannot_create_movement_or_training_evidence() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    previous = {
        "tabEventId": "tab-valid",
        "confidence": 0.99,
        "steelActions": [
            {
                "steelActionId": "action-valid",
                "string": 4,
                "fret": 3,
                "controls": [],
                "soundingPitchValue": 67,
                "confidence": 0.99,
                "mechanicalValidation": {"valid": True},
            }
        ],
    }
    current = {
        "tabEventId": "tab-unmarked-slant",
        "gripId": "grip-unmarked-slant",
        "confidence": 0.99,
        "steelActions": [
            {
                "steelActionId": "action-fret-3",
                "string": 4,
                "fret": 3,
                "controls": [],
                "soundingPitchValue": 67,
                "confidence": 0.99,
                "mechanicalValidation": {"valid": True},
            },
            {
                "steelActionId": "action-fret-4",
                "string": 5,
                "fret": 4,
                "controls": [],
                "soundingPitchValue": 63,
                "confidence": 0.99,
                "mechanicalValidation": {"valid": True},
            },
        ],
    }
    systems = [{"tabSystemId": "system-invalid-grip", "tabEvents": [previous, current]}]
    verified, unresolved, ineligible = _separate_verified_grips(_derive_grips(systems))
    _mark_grip_event_eligibility(systems, ineligible)

    assert verified == []
    assert unresolved[0]["kind"] == "mechanically_invalid_grip_candidate"
    assert ineligible == {"tab-unmarked-slant"}
    assert _derive_movement_sequences(systems, "page-invalid-grip") == []
    record = {
        "batchId": "batch-invalid-grip",
        "inputId": "input-invalid-grip",
        "datasetPartition": "discovery",
        "sourceDocumentId": "source-document-001",
        "sourceStructure": {},
        "pageClassification": {"primary": "lick_or_fill"},
        "tabSystems": systems,
        "movementSequences": [],
        "teachingConcepts": [],
        "unresolved": unresolved,
    }
    assert derive_decision_annotations(record, profile) == []


def test_grip_validation_rejects_multiple_frets_without_explicit_slant() -> None:
    systems = [
        {
            "tabSystemId": "system-slant",
            "tabEvents": [
                {
                    "tabEventId": "event-slant",
                    "gripId": "grip-slant",
                    "confidence": 0.95,
                    "steelActions": [
                        {"steelActionId": "a1", "string": 4, "fret": 3, "controls": [], "soundingPitchValue": 67},
                        {"steelActionId": "a2", "string": 5, "fret": 4, "controls": [], "soundingPitchValue": 64},
                    ],
                }
            ],
        }
    ]

    grip = _derive_grips(systems)[0]
    assert grip["mechanicalValidation"]["valid"] is False
    assert grip["mechanicalValidation"]["issues"] == ["multiple_frets_without_slant"]


def test_reviewable_decisions_capture_grip_choice_and_mechanical_alternatives() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    previous = {
        "tabEventId": "tab-previous",
        "confidence": 0.99,
        "steelActions": [
            {
                "steelActionId": "previous-4",
                "string": 4,
                "fret": 3,
                "controls": [],
                "soundingPitchValue": 67,
                "confidence": 0.99,
                "mechanicalValidation": {"valid": True},
            },
            {
                "steelActionId": "previous-5",
                "string": 5,
                "fret": 3,
                "controls": [],
                "soundingPitchValue": 62,
                "confidence": 0.99,
                "mechanicalValidation": {"valid": True},
            },
        ],
    }
    current = {
        "tabEventId": "tab-current",
        "confidence": 0.99,
        "steelActions": [
            {
                "steelActionId": "current-4",
                "string": 4,
                "fret": 3,
                "controls": ["F"],
                "soundingPitchValue": 68,
                "confidence": 0.99,
                "mechanicalValidation": {"valid": True},
            },
            {
                "steelActionId": "current-5",
                "string": 5,
                "fret": 3,
                "controls": ["A"],
                "soundingPitchValue": 64,
                "confidence": 0.99,
                "mechanicalValidation": {"valid": True},
            },
        ],
    }
    tab_systems = [{"tabSystemId": "system-1", "tabEvents": [previous, current]}]
    movements = _derive_movement_sequences(tab_systems, "page-1")
    record = {
        "batchId": "batch-1",
        "inputId": "input-1",
        "datasetPartition": "discovery",
        "sourceDocumentId": "source-document-001",
        "sourceStructure": {"orientation": "portrait", "luminanceBin": "middle", "densityBin": "high"},
        "pageClassification": {"primary": "lick_or_fill"},
        "tabSystems": tab_systems,
        "movementSequences": movements,
        "teachingConcepts": [{"concept": "chord_transition"}],
        "unresolved": [],
    }

    decisions = derive_decision_annotations(record, profile)

    assert len(decisions) == 1
    decision = decisions[0]
    assert decision["chosen"]["textureSize"] == 2
    assert decision["styleFamily"] == "lever_driven"
    assert decision["sourceAction"]["controls"] == ["F"]
    assert decision["abstractDecision"]["melodyPitchValue"] == 68
    assert decision["alternatives"]
    assert all(max(item["voicePitchValues"]) == 68 for item in decision["alternatives"])
    assert "page:lick_or_fill" in decision["categoryTags"]
    assert "notation_density:low" in decision["categoryTags"]
    assert "alignment:tab_only" in decision["categoryTags"]


def test_voice_preserving_alternatives_keep_the_complete_grip_pitch_set() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    previous_actions = [
        {
            "string": 4,
            "fret": 2,
            "controls": [],
            "soundingPitchValue": 66,
            "mechanicalValidation": {"valid": True},
        },
        {
            "string": 5,
            "fret": 2,
            "controls": [],
            "soundingPitchValue": 61,
            "mechanicalValidation": {"valid": True},
        },
    ]
    source_actions = [
        {
            "string": 4,
            "fret": 3,
            "controls": [],
            "soundingPitchValue": 67,
            "mechanicalValidation": {"valid": True},
        },
        {
            "string": 5,
            "fret": 3,
            "controls": [],
            "soundingPitchValue": 62,
            "mechanicalValidation": {"valid": True},
        },
    ]
    chosen = _candidate(source_actions, previous_actions, phrase_role="passing_tone")

    alternatives = _voice_preserving_alternatives(
        profile,
        actions=source_actions,
        previous_actions=previous_actions,
        phrase_role="passing_tone",
        chosen=chosen,
    )

    assert alternatives
    assert any(
        alternative["textureSize"] == 2
        and alternative["voicePitchValues"] == [62, 67]
        for alternative in alternatives
    )


def test_score_backed_decisions_require_verified_top_note_alignment() -> None:
    profile = get_e9_copedent_profile("source-e9-abc-defg-v1")
    previous = {
        "tabEventId": "tab-previous",
        "steelActions": [
            {
                "steelActionId": "previous-action",
                "string": 4,
                "fret": 0,
                "controls": [],
                "soundingPitchValue": 64,
                "confidence": 0.99,
                "mechanicalValidation": {"valid": True},
            }
        ],
    }
    current = {
        "tabEventId": "tab-current",
        "steelActions": [
            {
                "steelActionId": "current-action",
                "string": 4,
                "fret": 2,
                "controls": [],
                "soundingPitchValue": 66,
                "confidence": 0.99,
                "mechanicalValidation": {"valid": True},
            }
        ],
    }
    base_record = {
        "batchId": "batch-score-backed",
        "inputId": "input-score-backed",
        "datasetPartition": "discovery",
        "sourceDocumentId": "source-document-001",
        "sourceStructure": {},
        "pageClassification": {"primary": "single_note_melody"},
        "scoreSystems": [
            {
                "scoreEvents": [
                    {"scoreEventId": "score-previous", "pitchValue": 64},
                    {"scoreEventId": "score-current", "pitchValue": 66},
                ]
            }
        ],
        "tabSystems": [{"tabSystemId": "tab-system-1", "tabEvents": [previous, current]}],
        "movementSequences": _derive_movement_sequences(
            [{"tabSystemId": "tab-system-1", "tabEvents": [previous, current]}],
            "page-score-backed",
        ),
        "teachingConcepts": [],
        "unresolved": [],
    }
    supported = {
        **base_record,
        "eventAlignments": [
            {
                "eventAlignmentId": "alignment-previous",
                "tabEventIds": ["tab-previous"],
                "scoreEventIds": ["score-previous"],
                "scoreNotationTranspositionSemitones": 0,
                "notationAdjustedPitchAgreement": True,
            },
            {
                "eventAlignmentId": "alignment-current",
                "tabEventIds": ["tab-current"],
                "scoreEventIds": ["score-current"],
                "scoreNotationTranspositionSemitones": 0,
                "notationAdjustedPitchAgreement": True,
            },
        ],
    }

    decisions = derive_decision_annotations(supported, profile)
    assert len(decisions) == 1
    assert "alignment:score_supported" in decisions[0]["categoryTags"]
    assert decisions[0]["scoreToTabSupport"]["current"]["melodyTopAgreement"] is True

    missing_current_alignment = {**base_record, "eventAlignments": supported["eventAlignments"][:1]}
    assert derive_decision_annotations(missing_current_alignment, profile) == []


def test_review_metrics_count_atomic_and_alignment_corrections() -> None:
    machine = {
        "scoreSystems": [
            {
                "systemIndex": 1,
                "scoreSystemId": "score-system-1",
                "pairedTabSystemId": "tab-system-1",
                "pageRegion": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 0.4},
                "scoreEvents": [
                    {
                        "scoreEventId": "score-event-1",
                        "measure": 1,
                        "beat": 1.0,
                        "pitchValue": 64,
                        "durationBeats": 1.0,
                        "rest": False,
                    }
                ],
                "chordContexts": [],
            }
        ],
        "tabSystems": [
            {
                "systemIndex": 1,
                "tabSystemId": "tab-system-1",
                "pageRegion": {"x": 0.0, "y": 0.4, "width": 1.0, "height": 0.4},
                "tabEvents": [
                    {
                        "tabEventId": "tab-event-1",
                        "steelActions": [
                            {
                                "steelActionId": "action-1",
                                "pageRegionId": "region-1",
                                "string": 5,
                                "fret": 3,
                                "controls": ["A"],
                                "mechanicalValidation": {"valid": True},
                            }
                        ],
                    }
                ],
            }
        ],
        "eventAlignments": [
            {
                "tabEventIds": ["tab-event-1"],
                "scoreEventIds": ["score-event-1"],
                "notationAdjustedPitchAgreement": True,
            }
        ],
        "teachingConcepts": [{"concept": "pedal_squeeze", "evidenceClass": "deterministic_derivation"}],
        "provenance": {"assetSha256": "abc"},
        "rightsAndAccess": {"rightsStatus": "unknown", "accessClassification": "private_research"},
    }
    reviewed = json.loads(json.dumps(machine))
    reviewed["tabSystems"][0]["tabEvents"][0]["steelActions"][0]["fret"] = 4

    counts = _review_record_counts(machine, reviewed)
    assert counts["atomicFieldReference"] == 3
    assert counts["atomicFieldChanged"] == 1
    assert counts["eventAlignmentExact"] == 1
    assert counts["scoreTabPairingExact"] == 1

    exact = extraction_acceptance_metrics([(machine, machine)])
    assert exact["allAcceptanceCriteriaPassed"] is True
    mismatched = extraction_acceptance_metrics([(machine, reviewed)])
    assert mismatched["metrics"]["fretRecognitionAccuracy"] == 0.0
    assert mismatched["acceptance"]["stringAndFret"] is False


def test_extractor_never_accepts_sealed_test_partition(tmp_path: Path) -> None:
    extractor = AmazingTablatureExtractor(tmp_path, repo_root=tmp_path)
    with pytest.raises(ExtractionWorkflowError, match="sealed test is forbidden"):
        extractor._batch_paths("batch", "test")
    with pytest.raises(ExtractionWorkflowError, match="between 1 and 100"):
        extractor.prepare_review("batch", limit=0)


def test_validation_queue_requires_exact_complete_discovery_challenger(tmp_path: Path) -> None:
    batch_dir = tmp_path / "batches" / "batch-validation-gate"
    batch_dir.mkdir(parents=True)
    (batch_dir / "manifest.json").write_text(json.dumps({"batchId": "batch-validation-gate"}))
    (batch_dir / "validation-work.jsonl").write_text(json.dumps({"inputId": "input-1"}) + "\n")
    (batch_dir / "partition-summary.json").write_text(
        json.dumps({"groupingReviewStatus": "independent_review_passed"})
    )
    extractor = AmazingTablatureExtractor(tmp_path)

    with pytest.raises(ExtractionWorkflowError, match="exact canonical discovery model ID"):
        extractor._batch_paths("batch-validation-gate", "validation")

    models_dir = tmp_path / "models"
    models_dir.mkdir()
    model_path = models_dir / "canonical-1.json"
    model_path.write_text(
        json.dumps(
            {
                "modelId": "canonical-1",
                "sourceBatchIds": ["batch-validation-gate"],
                "fullDiscoveryReviewComplete": True,
                "fullDiscoveryScoreAuditComplete": False,
                "codeRevision": "clean-head",
                "discoverySeedId": "seed-1",
            }
        )
    )
    model_sha = hashlib.sha256(model_path.read_bytes()).hexdigest()
    (tmp_path / "training-registry.json").write_text(
        json.dumps(
            {
                "models": {
                    "canonical-1": {
                        "artifact": "models/canonical-1.json",
                        "artifactSha256": model_sha,
                        "datasetEligibility": "complete_discovery",
                        "canonicalEvaluationEligible": True,
                    }
                }
            }
        )
    )
    _batch_dir, _manifest, work = extractor._batch_paths(
        "batch-validation-gate",
        "validation",
        validation_model_id="canonical-1",
    )
    assert work == [{"inputId": "input-1"}]

    summary_path = batch_dir / "extraction/validation/summary.json"
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(
        json.dumps({"validationModel": {"modelId": "canonical-1"}})
    )
    _batch_dir, _manifest, resumed_work = extractor._batch_paths(
        "batch-validation-gate", "validation"
    )
    assert resumed_work == work


class _FakeOCR:
    def read(self, _path: Path) -> list[dict[str, Any]]:
        return [
            {
                "text": "Practice this chord lick slowly",
                "confidence": 0.98,
                "x": 0.1,
                "y": 0.9,
                "width": 0.5,
                "height": 0.05,
            }
        ]


class _FakeOMR:
    available = True

    def read(self, _crop: Path, _output: Path, system_id: str) -> dict[str, Any]:
        return {
            "scoreEvents": [
                {
                    "scoreEventId": f"score-{system_id}",
                    "measure": 1,
                    "beat": 1.0,
                    "pitchValue": 64,
                    "pitch": "E4",
                    "durationBeats": 1.0,
                    "rest": False,
                }
            ],
            "chordContexts": [],
            "keyFifths": 1,
            "timeSignature": {"beats": 4, "beatType": 4},
        }


class _FakeTabVision:
    def read(
        self,
        _path: Path,
        labels: list[str],
        _cell_boxes: dict[str, dict[str, int]] | None = None,
    ) -> dict[str, dict[str, Any]]:
        return {label: {"token": "5", "confidence": 0.99, "uncertain": False} for label in labels}


def test_discovery_run_writes_private_provenance_and_requires_human_review(tmp_path: Path) -> None:
    private = tmp_path / "private"
    batch_dir = private / "batches" / "batch-1"
    source = tmp_path / "source"
    source.mkdir()
    batch_dir.mkdir(parents=True)
    image_path = source / "page.jpg"
    _synthetic_tab().convert("RGB").save(image_path)
    raw = image_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    manifest = {
        "batchId": "batch-1",
        "sourceRoot": str(source),
        "sourceCopedentId": "source-e9-abc-defg-v1",
        "sourceCopedentRevision": 1,
        "inputs": [
            {
                "inputId": "input-0001",
                "relativePath": "page.jpg",
                "sha256": digest,
                "size": len(raw),
                "mediaType": "jpg",
            }
        ],
    }
    (batch_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    work = {
        **manifest["inputs"][0],
        "datasetPartition": "discovery",
        "sourceDocumentId": "source-document-001",
        "contentUnitId": "content-unit-001",
    }
    (batch_dir / "discovery-work.jsonl").write_text(json.dumps(work) + "\n", encoding="utf-8")
    (batch_dir / "partition-summary.json").write_text(
        json.dumps({"groupingReviewStatus": "independent_review_passed"}),
        encoding="utf-8",
    )
    rights_digest = "c" * 64
    (batch_dir / "rights-and-access.json").write_text(
        json.dumps(
            {
                "rightsStatus": "user_provided_authorized",
                "reviewStatus": "approved",
                "recordDigest": rights_digest,
                "revision": 2,
                "allowedUses": {
                    "privateExtraction": True,
                    "privateEvaluation": True,
                    "modelTraining": True,
                },
            }
        ),
        encoding="utf-8",
    )

    extractor = AmazingTablatureExtractor(private, repo_root=tmp_path)
    extractor.ocr = _FakeOCR()
    extractor.omr = _FakeOMR()
    extractor.tab_vision = _FakeTabVision()
    summary = extractor.run("batch-1")

    assert summary["processedCount"] == 1
    assert summary["sealedTestAccessed"] is False
    assert summary["humanApprovalComplete"] is False
    page = json.loads((batch_dir / "extraction" / "discovery" / "pages" / "input-0001.json").read_text())
    assert page["sourceCopedent"]["id"] == "source-e9-abc-defg-v1"
    assert page["rightsAndAccess"]["rightsStatus"] == "user_provided_authorized"
    assert page["rightsAndAccess"]["authorizationRecordDigest"] == rights_digest
    assert page["rightsAndAccess"]["allowedUses"]["modelTraining"] is True
    assert {region["role"] for region in page["pageRegions"]} >= {
        "explicit_text",
        "score_system",
        "tab_system",
        "steel_action",
    }
    assert all(region["sourcePageId"] == page["objectId"] for region in page["pageRegions"])
    assert page["reviewState"] == "needs_human_review"
    assert page["provenance"]["assetSha256"] == digest

    review_packet_summary = extractor.prepare_review("batch-1")
    assert review_packet_summary["pageCount"] == 1
    assert review_packet_summary["sealedTestAccessed"] is False
    assert review_packet_summary["extractionVersion"] == EXTRACTOR_VERSION
    assert (
        review_packet_summary["pageReviewCompatibilityVersion"]
        == PAGE_REVIEW_COMPATIBILITY_VERSION
    )
    packet_path = batch_dir / review_packet_summary["packetPath"]
    console_path = batch_dir / review_packet_summary["reviewConsolePath"]
    packet = json.loads(packet_path.read_text(encoding="utf-8").splitlines()[0])
    assert packet["requiredApprovalSections"]
    assert packet["approvalScope"] == "tab_only_score_audit_required"
    assert packet["scoreAuditRequired"] is True
    assert packet["machineRecordDigest"]
    assert packet["extractionVersion"] == EXTRACTOR_VERSION
    assert packet["pageReviewCompatibilityVersion"] == PAGE_REVIEW_COMPATIBILITY_VERSION
    assert packet["machineRecord"]["inputId"] == "input-0001"
    assert packet["hardBlockers"] == []
    assert any(item["kind"] == "unverified_score_tab_alignment" for item in packet["unresolvedItems"])
    console = console_path.read_text(encoding="utf-8")
    assert "Review the extracted tablature" in console
    assert "Line-by-line score and tablature review" in console
    assert "Add feedback for this note or movement" in console
    assert "Each numbered column should represent one thing you play" in console
    assert "Recapture line" in console
    assert "automaticSystemDisposition" in console
    assert "How many event columns should this printed line show?" in console
    assert "Show this many columns" in console
    assert "event column${sourceCount===1?'':'s'} shown" in console
    assert "missing. Choose Recapture line." in console
    assert "sourceEventCounts" in console
    assert "written note not captured" in console
    assert "Recapture selected for this line" in console
    assert "Missing event ${column.position} selected" in console
    assert "expectedEventPosition:column.position" in console
    assert "Missing event ${selectedTarget.expectedEventPosition}: ${comment}" in console
    assert "else button.disabled=true" not in console
    assert "Uncertain items (advanced)" in console
    assert "Complete extraction details (advanced)" in console
    assert "machine found" not in console.lower()
    assert "score attacks" not in console.lower()
    assert "tab attacks" not in console.lower()
    assert "Original printed score and tablature for this line" in console
    assert "Save and next line" in console
    assert "prior comment" in console
    assert "fetch(ref.packetUrl" in console
    assert "Submit saved review to Lane 20" in console
    assert "fetch('/__lane20_review_submission'" in console
    assert "Reviewer reference (optional)" in console
    assert "primary-human-reviewer" in console
    assert 'id="submissionMessage"' in console
    assert "migratedFeedbackDraft" in console
    assert "!draft.saved && !draft.systemReviews && ref" in console
    assert "draft.saved = true" in console
    assert "Localized correction saved. Finish the remaining lines" in console
    assert 'id="navigationMessage"' in console
    assert "saveCurrentPage({fromNavigation:true})" in console
    assert "Choose a page decision or add feedback before moving on." in console
    assert "Page decision saved locally and ready to submit." in console
    assert "send the written score to internal audit" in console
    assert "do not recapture this line just because the score row is incomplete" in console
    assert "gold-highlighted corrections" in console
    assert "The highlighted corrections look right" in console
    assert "corrected-target" in console
    assert "action.attack === false && (action.slide || action.barMovement)" in console
    assert "action.engagementTiming === 'during_sustain' && controls" in console
    assert "return `${fret} --- ⏜${controls}`" in console
    assert "'hold '" not in console
    assert "controls ? ' ' + controls" not in console
    assert "if (!action || !reviewerReference)" not in console
    assert "Enter your reviewer name or initials before submitting." not in console
    assert "data:application/x-ndjson;charset=utf-8," not in console
    assert "URL.createObjectURL(new Blob" not in console
    assert "reviews: ready" in console
    assert '"machineRecord":' not in console
    assert "saved.correctedRecord || packet.machineRecord" not in console
    assert len(console.encode("utf-8")) < 80_000
    assert stat.S_IMODE(console_path.stat().st_mode) == 0o600
    lazy_packet_path = batch_dir / review_packet_summary["packetDirectory"] / "input-0001.json"
    assert json.loads(lazy_packet_path.read_text(encoding="utf-8"))["machineRecordDigest"] == packet[
        "machineRecordDigest"
    ]
    assert stat.S_IMODE(lazy_packet_path.stat().st_mode) == 0o600

    decisions_path = tmp_path / "review-decisions.jsonl"
    accept = {
        "inputId": "input-0001",
        "expectedMachineRecordDigest": packet["machineRecordDigest"],
        "action": "accept",
        "reviewerReference": "human-review-test",
        "approvedSections": packet["requiredApprovalSections"],
    }
    decisions_path.write_text(json.dumps(accept) + "\n", encoding="utf-8")
    review_summary = extractor.apply_review("batch-1", decisions_path)
    assert review_summary["humanApprovalComplete"] is False
    assert review_summary["humanApprovedPageCount"] == 1
    assert review_summary["tabOnlyApprovedPageCount"] == 1
    assert review_summary["excludedPageCount"] == 0
    assert review_summary["sealedTestAccessed"] is False
    score_audit_packet_summary = extractor.prepare_score_audit_review("batch-1")
    assert score_audit_packet_summary["eligibleApprovedPageCount"] == 1
    assert score_audit_packet_summary["scoreSystemCount"] == 0
    assert score_audit_packet_summary["pageCount"] == 0
    assert score_audit_packet_summary["blockedInternalRepairPageCount"] == 1
    assert score_audit_packet_summary["blockedInternalRepairSystemCount"] == 1
    assert score_audit_packet_summary["priorTabApprovalsPreserved"] is True
    assert score_audit_packet_summary["diagnosticAttentionCount"] >= 0
    repair_queue_path = batch_dir / score_audit_packet_summary["repairQueuePath"]
    repair_item = json.loads(repair_queue_path.read_text(encoding="utf-8").splitlines()[0])
    score_audit_console = (
        batch_dir / score_audit_packet_summary["reviewConsolePath"]
    ).read_text(encoding="utf-8")
    assert "Music score audit" in score_audit_console
    assert "Complete rendering of the recognized MusicXML" in score_audit_console
    assert "Original printed score and its printed tablature together" in score_audit_console
    assert "scoreTabSourceCropsBySystem" in score_audit_console
    assert "Captured score directly above ten-string tablature" in score_audit_console
    assert "miniature staff note or chord" in score_audit_console
    assert "className='score-visual-row'" in score_audit_console
    assert "miniatureScoreSvg(scoreEvents)" in score_audit_console
    assert "captured score notehead" in score_audit_console
    assert "written accidental" in score_audit_console
    assert "Numbered score-to-tablature checklist" not in score_audit_console
    assert "score-to-tab connections" in score_audit_console
    assert "Lane 20 automatic pre-check" in score_audit_console
    assert "Something is wrong" in score_audit_console
    assert "This system still needs correction" in score_audit_console
    assert "Automatic gate not passed" in score_audit_console
    assert "!gateReady&&status==='accept'" in score_audit_console
    assert "Previously accepted — unchanged" in score_audit_console
    assert "preapprovedScoreSystemIds" in score_audit_console
    assert "Prior feedback carried forward" in score_audit_console
    assert "carriedForwardSystemFeedback" in score_audit_console
    assert "You do not need to type it again" in score_audit_console
    assert "prior tablature approval preserved" in score_audit_console
    assert "withheld" in score_audit_console
    assert "packet.scoreSourceCropsBySystem" in score_audit_console
    assert "[system.scoreSystemId]" in score_audit_console
    assert "[score.scoreSystemId]" not in score_audit_console
    assert repair_item["repairState"] == "internal_repair_required"
    assert repair_item["humanReviewRequested"] is False
    remaining_packet = extractor.prepare_review("batch-1")
    assert remaining_packet["pageCount"] == 0
    assert remaining_packet["alreadyReviewedPageCount"] == 1
    assert remaining_packet["remainingPageCount"] == 0
    metrics = extractor.review_metrics("batch-1")
    assert metrics["humanApprovalComplete"] is True
    assert metrics["humanApprovedPageCount"] == 1
    assert metrics["excludedPageCount"] == 0
    assert metrics["sealedTestAccessed"] is False
    assert metrics["scoreAuditComplete"] is False
    assert metrics["scoreAuditedPageCount"] == 0

    extraction_summary_path = batch_dir / "extraction" / "discovery" / "summary.json"
    stale_summary = json.loads(extraction_summary_path.read_text(encoding="utf-8"))
    stale_summary["extractorVersion"] = "stale-extractor"
    extraction_summary_path.write_text(json.dumps(stale_summary), encoding="utf-8")
    with pytest.raises(ExtractionWorkflowError, match="current-version extraction"):
        extractor.prepare_review("batch-1")


def test_unreviewed_refresh_preserves_feedback_pages_and_scopes_next_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private = tmp_path / "private"
    batch_dir = private / "batches" / "batch-refresh"
    source = tmp_path / "source"
    source.mkdir()
    batch_dir.mkdir(parents=True)
    inputs: list[dict[str, Any]] = []
    work: list[dict[str, Any]] = []
    for index in (1, 2):
        image_path = source / f"page-{index}.jpg"
        _synthetic_tab().convert("RGB").save(image_path)
        raw = image_path.read_bytes()
        item = {
            "inputId": f"input-{index:04d}",
            "relativePath": image_path.name,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size": len(raw),
            "mediaType": "jpg",
        }
        inputs.append(item)
        work.append(
            {
                **item,
                "datasetPartition": "discovery",
                "sourceDocumentId": "source-document-001",
                "contentUnitId": f"content-unit-{index:03d}",
            }
        )
    (batch_dir / "manifest.json").write_text(
        json.dumps(
            {
                "batchId": "batch-refresh",
                "sourceRoot": str(source),
                "sourceCopedentId": "source-e9-abc-defg-v1",
                "sourceCopedentRevision": 1,
                "inputs": inputs,
            }
        ),
        encoding="utf-8",
    )
    (batch_dir / "discovery-work.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in work),
        encoding="utf-8",
    )
    (batch_dir / "partition-summary.json").write_text(
        json.dumps({"groupingReviewStatus": "independent_review_passed"}),
        encoding="utf-8",
    )
    (batch_dir / "rights-and-access.json").write_text(
        json.dumps(
            {
                "rightsStatus": "user_provided_authorized",
                "reviewStatus": "approved",
                "recordDigest": "d" * 64,
                "allowedUses": {"modelTraining": True},
            }
        ),
        encoding="utf-8",
    )
    extractor = AmazingTablatureExtractor(private, repo_root=tmp_path)
    extractor.ocr = _FakeOCR()
    extractor.omr = _FakeOMR()
    extractor.tab_vision = _FakeTabVision()
    extractor.run("batch-refresh")
    pages_dir = batch_dir / "extraction" / "discovery" / "pages"
    review_dir = batch_dir / "extraction" / "discovery" / "review"
    protected_before = _sha256_json(
        json.loads((pages_dir / "input-0001.json").read_text(encoding="utf-8"))
    )
    (review_dir / "human-review-feedback.jsonl").write_text(
        json.dumps(
            {
                "inputId": "input-0001",
                "machineRecordDigest": protected_before,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    refreshed = extractor.refresh_unreviewed(
        "batch-refresh",
        limit=1,
        workers=1,
    )

    protected_after = _sha256_json(
        json.loads((pages_dir / "input-0001.json").read_text(encoding="utf-8"))
    )
    refreshed_page = json.loads(
        (pages_dir / "input-0002.json").read_text(encoding="utf-8")
    )
    assert protected_after == protected_before
    assert refreshed["unreviewedRefresh"]["targetPageCount"] == 1
    assert refreshed_page["runDigest"] == refreshed["runDigest"]
    assert (
        refreshed_page["unreviewedRefresh"]["schemaVersion"]
        == "amazing-tablature-unreviewed-refresh-v1"
    )
    assert list(
        (review_dir / "unreviewed-refresh-revisions" / "input-0002").glob("*.json")
    )

    packet = extractor.prepare_review(
        "batch-refresh",
        never_reviewed_only=True,
        current_extractor_only=True,
    )
    assert packet["pageCount"] == 1
    assert packet["neverReviewedOnly"] is True
    assert packet["currentExtractorOnly"] is True
    packet_row = json.loads(
        (batch_dir / packet["packetPath"]).read_text(encoding="utf-8").splitlines()[0]
    )
    assert packet_row["inputId"] == "input-0002"

    refreshed_page["pageClassification"]["primary"] = "lick_or_fill"
    refreshed_page["scoreSystems"] = []
    refreshed_page["eventAlignments"] = []
    refreshed_page["grips"] = []
    refreshed_page["unresolved"] = []
    for system in refreshed_page["tabSystems"]:
        for event in system["tabEvents"]:
            for action in event["steelActions"]:
                action.setdefault("mechanicalValidation", {})["valid"] = True
    (pages_dir / "input-0002.json").write_text(
        json.dumps(refreshed_page), encoding="utf-8"
    )
    audit = extractor.audit_discovery_completion("batch-refresh")
    assert audit["outcomeCounts"] == {
        "protected_feedback_pending": 1,
        "review_ready": 1,
    }
    assert audit["reviewKindCounts"] == {"tab_only": 1}
    assert audit["reviewPacketCreated"] is False
    assert audit["humanApprovalCreated"] is False
    assert audit["noRereviewGuard"] == {
        "finalizedPageCount": 0,
        "feedbackProtectedPageCount": 1,
        "confirmedCorrectionPageCount": 0,
        "preserved": True,
    }
    assert audit["validationAccessed"] is False
    assert audit["sealedTestAccessed"] is False
    audit_queue = [
        json.loads(line)
        for line in (
            batch_dir / "extraction/discovery" / audit["queuePath"]
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert {item["inputId"] for item in audit_queue} == {
        "input-0001",
        "input-0002",
    }

    confirmed_page = json.loads(
        (pages_dir / "input-0001.json").read_text(encoding="utf-8")
    )
    confirmed_page["machineCorrection"] = {"correctionId": "correction-001"}
    confirmed_page["unresolved"] = [
        {"kind": "score_omr_failure", "blocking": True}
    ]
    (pages_dir / "input-0001.json").write_text(
        json.dumps(confirmed_page), encoding="utf-8"
    )
    confirmed_digest = _sha256_json(confirmed_page)
    (review_dir / "feedback-correction-confirmation-decisions.jsonl").write_text(
        json.dumps(
            {
                "decisionId": "confirmation-decision-001",
                "inputId": "input-0001",
                "machineRecordDigest": confirmed_digest,
                "correctionId": "correction-001",
                "status": "confirm",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    confirmed_audit = extractor.audit_discovery_completion("batch-refresh")
    assert confirmed_audit["noRereviewGuard"] == {
        "finalizedPageCount": 0,
        "feedbackProtectedPageCount": 0,
        "confirmedCorrectionPageCount": 1,
        "preserved": True,
    }
    confirmed_queue = [
        json.loads(line)
        for line in (
            batch_dir / "extraction/discovery" / confirmed_audit["queuePath"]
        ).read_text(encoding="utf-8").splitlines()
    ]
    confirmed_row = next(
        item for item in confirmed_queue if item["inputId"] == "input-0001"
    )
    assert confirmed_row["outcome"] != "protected_feedback_pending"

    def fake_score_repair(**kwargs: Any) -> dict[str, Any]:
        candidate = copy.deepcopy(kwargs["base_record"])
        candidate["unresolved"] = []
        candidate_path = (
            batch_dir
            / "extraction/discovery/review/score-audit/repair/candidate-records"
            / kwargs["input_id"]
            / "candidate.json"
        )
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        return {
            "status": "candidate_ready",
            "candidateRecordPath": str(
                candidate_path.relative_to(batch_dir / "extraction/discovery")
            ),
            "candidateRecordDigest": _sha256_json(candidate),
        }

    monkeypatch.setattr(extractor, "_build_score_repair_candidate", fake_score_repair)
    monkeypatch.setattr(
        "pocketsteel.amazing_tablature_extraction._score_audit_equivalence_gates",
        lambda record: {
            str(system["scoreSystemId"]): {"readyForHumanReview": True}
            for system in record.get("scoreSystems") or []
        },
    )
    monkeypatch.setattr(
        "pocketsteel.amazing_tablature_extraction._combined_score_tab_columns",
        lambda score, tab: {
            "scoreAttackCount": 1,
            "tabAttackCount": 1,
            "tabMovementCount": 1,
            "relationshipCounts": {"exact": 1},
            "automaticPitchGatePassed": True,
            "scoreReaderIndependentOfTabPitches": True,
        },
    )
    monkeypatch.setattr(
        "pocketsteel.amazing_tablature_extraction._provisional_joint_review_blockers",
        lambda comparison, key_signature_known: [],
    )
    monkeypatch.setattr(
        "pocketsteel.amazing_tablature_extraction._hard_review_blockers",
        lambda record: [],
    )
    immutable_digest = _sha256_json(
        json.loads((pages_dir / "input-0001.json").read_text(encoding="utf-8"))
    )
    remediation = extractor.remediate_discovery_score_correspondence(
        "batch-refresh", limit=1
    )
    assert remediation["selectedPageCount"] == 1
    assert remediation["candidateReadyPageCount"] == 1
    assert remediation["exceptionalReviewEligiblePageCount"] == 1
    assert remediation["diagnosticScoreSystemCount"] >= 1
    assert remediation["baselineCountExactSystemCount"] >= 1
    assert remediation["candidateCountExactSystemCount"] >= 1
    assert remediation["baseLineageEligiblePageCount"] == 1
    assert remediation["reviewPacketCreated"] is False
    assert remediation["humanApprovalCreated"] is False
    assert remediation["currentPageRecordsModified"] is False
    assert remediation["validationAccessed"] is False
    assert remediation["sealedTestAccessed"] is False
    assert _sha256_json(
        json.loads((pages_dir / "input-0001.json").read_text(encoding="utf-8"))
    ) == immutable_digest

    with pytest.raises(ExtractionWorkflowError, match="confirmation flag"):
        extractor.quarantine_discovery_remainder(
            "batch-refresh",
            approval_reference="explicit synthetic approval",
        )
    quarantine = extractor.quarantine_discovery_remainder(
        "batch-refresh",
        approval_reference="explicit synthetic approval",
        confirm_bulk_quarantine=True,
    )
    assert quarantine["pageCount"] == 2
    assert quarantine["remainingPageCount"] == 0
    assert quarantine["humanApprovalComplete"] is True
    assert quarantine["factualApprovalGranted"] is False
    assert quarantine["sourceAssetsModified"] is False
    assert quarantine["validationAccessed"] is False
    assert quarantine["sealedTestAccessed"] is False
    reviewed_index = [
        json.loads(line)
        for line in (review_dir / "approved-record-index.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert {item["status"] for item in reviewed_index} == {"excluded"}


def test_targeted_feedback_is_validated_logged_and_does_not_approve_page(tmp_path: Path) -> None:
    private = tmp_path / "private"
    batch_dir = private / "batches" / "batch-feedback"
    pages_dir = batch_dir / "extraction" / "discovery" / "pages"
    review_dir = batch_dir / "extraction" / "discovery" / "review"
    pages_dir.mkdir(parents=True)
    review_dir.mkdir(parents=True)
    (batch_dir / "manifest.json").write_text(
        json.dumps({"batchId": "batch-feedback", "sourceCopedentId": "source-e9-abc-defg-v1"}),
        encoding="utf-8",
    )
    work = {
        "inputId": "input-feedback",
        "datasetPartition": "discovery",
        "sha256": "a" * 64,
    }
    (batch_dir / "discovery-work.jsonl").write_text(json.dumps(work) + "\n", encoding="utf-8")
    (batch_dir / "partition-summary.json").write_text(
        json.dumps({"groupingReviewStatus": "independent_review_passed"}),
        encoding="utf-8",
    )
    record = {
        "schemaVersion": "test",
        "objectId": "page-feedback",
        "revision": 1,
        "batchId": "batch-feedback",
        "inputId": "input-feedback",
        "datasetPartition": "discovery",
        "assetSha256": "a" * 64,
        "runDigest": "run-feedback",
        "extractorVersion": EXTRACTOR_VERSION,
        "provenance": {"imageFilename": "feedback-page.jpg"},
        "derivative": {"relativePath": "derivatives/input-feedback.png"},
        "sourceCopedent": {"id": "source-e9-abc-defg-v1", "revision": 1},
        "sourceStructure": {},
        "rightsAndAccess": {},
        "pageClassification": {},
        "pageRegions": [],
        "scoreSystems": [],
        "eventAlignments": [],
        "grips": [],
        "derivedDecisions": [],
        "teachingConcepts": [],
        "exercises": [],
        "unresolved": [],
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "systemIndex": 0,
                "tabEvents": [
                    {
                        "tabEventId": "tab-event-1",
                        "eventIndex": 0,
                        "measure": 1,
                        "steelActions": [
                            {
                                "steelActionId": "steel-action-1",
                                "string": 5,
                                "fret": 3,
                                "controls": ["A"],
                            }
                        ],
                    }
                ],
            }
        ],
        "movementSequences": [
            {
                "movementSequenceId": "movement-1",
                "tabSystemId": "tab-system-1",
            }
        ],
    }
    (pages_dir / "input-feedback.json").write_text(json.dumps(record), encoding="utf-8")
    (batch_dir / "extraction" / "discovery" / "summary.json").write_text(
        json.dumps(
            {
                "extractorVersion": EXTRACTOR_VERSION,
                "decisionDerivationVersion": DECISION_DERIVATION_VERSION,
                "processedCount": 1,
                "failedPageCount": 0,
                "runDigest": "run-feedback",
                "rightsAuthorizationDigest": None,
            }
        ),
        encoding="utf-8",
    )
    machine_digest = _sha256_json(record)
    feedback_path = tmp_path / "feedback.jsonl"
    feedback_path.write_text(
        json.dumps(
            {
                "inputId": "input-feedback",
                "expectedMachineRecordDigest": machine_digest,
                "action": "feedback",
                "reviewerReference": "player-reviewer",
                "approvedSections": [],
                "eventFeedback": [
                    {
                        "targetType": "tab_cell",
                        "tabSystemId": "tab-system-1",
                        "tabEventId": "tab-event-1",
                        "steelActionId": "steel-action-1",
                        "string": 5,
                        "feedbackType": "needs_correction",
                        "comment": "The pedal timing should be checked.",
                        "friendlyContext": "Untrusted browser label is not authoritative",
                    },
                    {
                        "targetType": "movement",
                        "tabSystemId": "tab-system-1",
                        "movementSequenceId": "movement-1",
                        "feedbackType": "general_comment",
                        "comment": "Show the release after the sustained note.",
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    extractor = AmazingTablatureExtractor(private, repo_root=tmp_path)
    summary = extractor.apply_review("batch-feedback", feedback_path)
    assert summary["reviewedPageCount"] == 0
    assert summary["remainingPageCount"] == 1
    assert summary["humanApprovalComplete"] is False
    assert summary["feedbackSubmissionCount"] == 1
    assert summary["feedbackPageCount"] == 1
    feedback_log_path = review_dir / "human-review-feedback.jsonl"
    feedback_log = json.loads(feedback_log_path.read_text(encoding="utf-8").splitlines()[0])
    assert feedback_log["approvalEffect"] == "none"
    assert feedback_log["approvedSections"] == []
    assert feedback_log["eventFeedback"][0]["target"]["string"] == 5
    assert feedback_log["eventFeedback"][0]["context"]["label"].startswith("System 1 · Measure 1")
    assert "Untrusted browser label" not in json.dumps(feedback_log)
    assert stat.S_IMODE(feedback_log_path.stat().st_mode) == 0o600
    assert not (review_dir / "approved-record-index.jsonl").read_text(encoding="utf-8").strip()

    pending_packet = extractor.prepare_review("batch-feedback")
    assert pending_packet["pageCount"] == 0
    assert pending_packet["pendingFeedbackCorrectionPageCount"] == 1
    assert pending_packet["availableForReviewPageCount"] == 0

    accept_path = tmp_path / "accept-after-feedback.jsonl"
    accept_path.write_text(
        json.dumps(
            {
                "inputId": "input-feedback",
                "expectedMachineRecordDigest": machine_digest,
                "action": "accept",
                "reviewerReference": "player-reviewer",
                "approvedSections": list(TAB_ONLY_APPROVAL_SECTIONS),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ExtractionWorkflowError, match="unresolved reviewer feedback"):
        extractor.apply_review("batch-feedback", accept_path)

    invalid_path = tmp_path / "invalid-feedback.jsonl"
    invalid_path.write_text(
        json.dumps(
            {
                "inputId": "input-feedback",
                "expectedMachineRecordDigest": machine_digest,
                "action": "feedback",
                "reviewerReference": "player-reviewer",
                "approvedSections": [],
                "eventFeedback": [
                    {
                        "targetType": "tab_cell",
                        "tabSystemId": "tab-system-1",
                        "tabEventId": "tab-event-1",
                        "steelActionId": "not-a-real-action",
                        "string": 5,
                        "feedbackType": "needs_correction",
                        "comment": "Invalid target should be rejected.",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ExtractionWorkflowError, match="unknown tablature cell"):
        extractor.apply_review("batch-feedback", invalid_path)

    record["revision"] = 2
    (pages_dir / "input-feedback.json").write_text(json.dumps(record), encoding="utf-8")
    untouched_work = {
        "inputId": "input-untouched",
        "datasetPartition": "discovery",
        "sha256": "b" * 64,
    }
    (batch_dir / "discovery-work.jsonl").write_text(
        json.dumps(work) + "\n" + json.dumps(untouched_work) + "\n",
        encoding="utf-8",
    )
    untouched_record = copy.deepcopy(record)
    untouched_record.update(
        {
            "objectId": "page-untouched",
            "inputId": "input-untouched",
            "assetSha256": "b" * 64,
            "provenance": {"imageFilename": "untouched-page.jpg"},
        }
    )
    (pages_dir / "input-untouched.json").write_text(json.dumps(untouched_record), encoding="utf-8")
    extraction_summary_path = batch_dir / "extraction" / "discovery" / "summary.json"
    extraction_summary = json.loads(extraction_summary_path.read_text(encoding="utf-8"))
    extraction_summary["processedCount"] = 2
    extraction_summary_path.write_text(json.dumps(extraction_summary), encoding="utf-8")

    corrected_packet_summary = extractor.prepare_review(
        "batch-feedback",
        prior_feedback_only=True,
    )
    corrected_packet = json.loads(
        (batch_dir / corrected_packet_summary["packetPath"]).read_text(encoding="utf-8").splitlines()[0]
    )
    assert corrected_packet_summary["pageCount"] == 1
    assert corrected_packet_summary["reviewScope"] == "feedback_corrections"
    assert corrected_packet_summary["scopeRemainingPageCount"] == 1
    assert corrected_packet_summary["availableForReviewPageCount"] == 1
    assert corrected_packet_summary["deferredPageCount"] == 0
    assert corrected_packet_summary["pendingFeedbackCorrectionPageCount"] == 0
    assert corrected_packet["inputId"] == "input-feedback"
    assert len(corrected_packet["priorFeedback"]) == 1
    assert corrected_packet["priorFeedback"][0]["feedbackSubmissionId"] == feedback_log["feedbackSubmissionId"]


def test_feedback_correction_revises_machine_event_without_granting_approval(tmp_path: Path) -> None:
    private = tmp_path / "private"
    batch_dir = private / "batches" / "batch-correction"
    pages_dir = batch_dir / "extraction" / "discovery" / "pages"
    review_dir = batch_dir / "extraction" / "discovery" / "review"
    pages_dir.mkdir(parents=True)
    review_dir.mkdir(parents=True)
    (batch_dir / "manifest.json").write_text(
        json.dumps({"batchId": "batch-correction", "sourceCopedentId": "source-e9-abc-defg-v1"}),
        encoding="utf-8",
    )
    (batch_dir / "discovery-work.jsonl").write_text(
        json.dumps({"inputId": "input-correction", "datasetPartition": "discovery", "sha256": "a" * 64})
        + "\n",
        encoding="utf-8",
    )
    (batch_dir / "partition-summary.json").write_text(
        json.dumps({"groupingReviewStatus": "independent_review_passed"}),
        encoding="utf-8",
    )
    record = {
        "schemaVersion": "test",
        "objectId": "page-correction",
        "revision": 1,
        "batchId": "batch-correction",
        "inputId": "input-correction",
        "datasetPartition": "discovery",
        "assetSha256": "a" * 64,
        "runDigest": "run-correction",
        "extractorVersion": EXTRACTOR_VERSION,
        "provenance": {"imageFilename": "correction-page.jpg", "assetSha256": "a" * 64},
        "derivative": {"relativePath": "derivatives/input-correction.png", "width": 1000, "height": 1000},
        "sourceCopedent": {"id": "source-e9-abc-defg-v1", "revision": 1},
        "sourceStructure": {},
        "rightsAndAccess": {},
        "pageClassification": {},
        "pageRegions": [],
        "scoreSystems": [],
        "eventAlignments": [],
        "grips": [],
        "derivedDecisions": [],
        "teachingConcepts": [],
        "exercises": [],
        "unresolved": [],
        "tabSystems": [
            {
                "tabSystemId": "tab-system-1",
                "systemIndex": 1,
                "pageRegion": {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.3},
                "stringCenters": [100 + index * 20 for index in range(10)],
                "tabEvents": [
                    {
                        "tabEventId": "tab-event-1",
                        "eventIndex": 1,
                        "measure": 1,
                        "horizontalPosition": 0.2,
                        "steelActions": [
                            {
                                "steelActionId": "steel-action-1",
                                "string": 5,
                                "fret": 3,
                                "controls": ["A"],
                                "attack": True,
                                "confidence": 1.0,
                            }
                        ],
                    },
                    {
                        "tabEventId": "tab-event-2",
                        "eventIndex": 2,
                        "measure": 1,
                        "horizontalPosition": 0.3,
                        "steelActions": [
                            {
                                "steelActionId": "steel-action-2",
                                "string": 5,
                                "fret": 3,
                                "controls": [],
                                "attack": True,
                                "slide": True,
                                "confidence": 1.0,
                            }
                        ],
                    },
                ],
            }
        ],
        "movementSequences": [],
    }
    (pages_dir / "input-correction.json").write_text(json.dumps(record), encoding="utf-8")
    (batch_dir / "extraction" / "discovery" / "summary.json").write_text(
        json.dumps(
            {
                "extractorVersion": EXTRACTOR_VERSION,
                "decisionDerivationVersion": DECISION_DERIVATION_VERSION,
                "processedCount": 1,
                "failedPageCount": 0,
                "runDigest": "run-correction",
                "rightsAuthorizationDigest": None,
            }
        ),
        encoding="utf-8",
    )
    machine_digest = _sha256_json(record)
    feedback_path = tmp_path / "feedback-correction.jsonl"
    feedback_path.write_text(
        json.dumps(
            {
                "inputId": "input-correction",
                "expectedMachineRecordDigest": machine_digest,
                "action": "feedback",
                "reviewerReference": "player-reviewer",
                "approvedSections": [],
                "eventFeedback": [
                    {
                        "targetType": "tab_cell",
                        "tabSystemId": "tab-system-1",
                        "tabEventId": "tab-event-2",
                        "steelActionId": "steel-action-2",
                        "string": 5,
                        "feedbackType": "needs_correction",
                        "comment": "This releases the A pedal without repicking.",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    extractor = AmazingTablatureExtractor(private, repo_root=tmp_path)
    extractor.apply_review("batch-correction", feedback_path)
    feedback = json.loads((review_dir / "human-review-feedback.jsonl").read_text(encoding="utf-8"))
    feedback_item_id = feedback["eventFeedback"][0]["feedbackItemId"]
    correction_path = tmp_path / "correction-plan.jsonl"
    correction_path.write_text(
        json.dumps(
            {
                "schemaVersion": FEEDBACK_CORRECTION_PLAN_SCHEMA_VERSION,
                "inputId": "input-correction",
                "expectedMachineRecordDigest": machine_digest,
                "feedbackSubmissionIds": [feedback["feedbackSubmissionId"]],
                "acknowledgedPageNote": False,
                "operations": [
                    {
                        "operationId": "release-without-repick",
                        "type": "update_steel_action",
                        "tabSystemId": "tab-system-1",
                        "tabEventId": "tab-event-2",
                        "steelActionId": "steel-action-2",
                        "changes": {
                            "attack": False,
                            "sustain": True,
                            "releaseTiming": "during_sustain",
                            "controlTransition": {
                                "beforeControls": ["A"],
                                "afterControls": [],
                                "timing": "during_sustain",
                            },
                        },
                        "feedbackItemIds": [feedback_item_id],
                    },
                    {
                        "operationId": "add-held-b-movement",
                        "type": "insert_tab_event",
                        "tabSystemId": "tab-system-1",
                        "tabEventId": "tab-event-2",
                        "position": "after",
                        "newTabEventId": "tab-event-added-hold",
                        "steelActions": [
                            {
                                "string": 6,
                                "fret": 3,
                                "controls": ["B"],
                                "attack": False,
                                "sustain": True,
                            }
                        ],
                        "feedbackItemIds": [feedback_item_id],
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    dry_run = extractor.apply_feedback_corrections(
        "batch-correction", correction_path, dry_run=True
    )
    assert dry_run["dryRun"] is True
    assert dry_run["correctedPageCount"] == 1
    unchanged = json.loads((pages_dir / "input-correction.json").read_text(encoding="utf-8"))
    assert unchanged["revision"] == 1
    assert not (review_dir / "machine-correction-log.jsonl").exists()

    summary = extractor.apply_feedback_corrections("batch-correction", correction_path)
    assert summary["correctedPageCount"] == 1
    assert summary["feedbackItemCount"] == 1
    assert summary["dryRun"] is False
    assert summary["humanApprovalGranted"] is False
    corrected = json.loads((pages_dir / "input-correction.json").read_text(encoding="utf-8"))
    corrected_event = corrected["tabSystems"][0]["tabEvents"][1]
    assert corrected["revision"] == 2
    assert corrected["reviewState"] == "needs_human_review"
    assert corrected["humanApprovalComplete"] is False
    assert corrected_event["executionType"] == "movement_only"
    assert corrected_event["steelActions"][0]["attack"] is False
    assert corrected_event["steelActions"][0]["controlTransition"] == {
        "beforeControls": ["A"],
        "afterControls": [],
        "timing": "during_sustain",
    }
    assert corrected["movementSequences"][0]["controlsReleased"] == ["A"]
    assert corrected["movementSequences"][0]["executionType"] == "movement_only"
    assert stat.S_IMODE((review_dir / "machine-correction-log.jsonl").stat().st_mode) == 0o600
    archived = list(
        (review_dir / "machine-record-revisions" / "input-correction").glob(
            "revision-0001-*.json"
        )
    )
    assert len(archived) == 1
    assert stat.S_IMODE(archived[0].stat().st_mode) == 0o600
    assert json.loads(archived[0].read_text(encoding="utf-8"))["revision"] == 1
    rereview = extractor.prepare_review("batch-correction")
    assert rereview["pageCount"] == 1
    assert rereview["pendingFeedbackCorrectionPageCount"] == 0
    duplicate = extractor.apply_feedback_corrections("batch-correction", correction_path)
    assert duplicate["deduplicated"] is True

    correction_log = json.loads(
        (review_dir / "machine-correction-log.jsonl").read_text(encoding="utf-8")
    )
    assert correction_log["feedbackItemIds"] == [feedback_item_id]

    confirmation_packet = extractor.prepare_feedback_correction_confirmation(
        "batch-correction", correction_path
    )
    assert confirmation_packet["pageCount"] == 1
    assert confirmation_packet["approvalScope"] == "applied_feedback_corrections_only"
    assert confirmation_packet["scoreApprovalGranted"] is False
    assert confirmation_packet["pageApprovalGranted"] is False
    confirmation_record = json.loads(
        (
            batch_dir
            / "extraction"
            / "discovery"
            / "review"
            / "feedback-correction-confirmation-packet.jsonl"
        ).read_text(encoding="utf-8")
    )
    assert confirmation_record["correctedTabEventIds"] == [
        "tab-event-2",
        "tab-event-added-hold",
    ]
    inserted_action_id = corrected["tabSystems"][0]["tabEvents"][2]["steelActions"][0][
        "steelActionId"
    ]
    assert inserted_action_id in confirmation_record["correctedSteelActionIds"]
    assert confirmation_record["changeSummaries"][0]["label"] == (
        "Corrected line 1, column 2: the prior pedal or lever comes off during the "
        "sustain; resulting column: string 5 3A---3."
    )
    console = (
        batch_dir
        / "extraction"
        / "discovery"
        / "review"
        / "feedback-correction-confirmation-console.html"
    ).read_text(encoding="utf-8")
    assert "Confirm only the corrected tablature" in console
    assert "action.engagementTiming === 'during_sustain' && controls" in console
    assert "const transition = action.controlTransition || null;" in console
    assert "return `${action.fret}${before}---${action.fret}${after}`;" in console
    assert "if (action.attack === false && action.slide)" in console
    assert "if (action.attack === false && action.releaseTiming) return `---${action.fret}" in console
    assert "if (action.attack === false) return '~';" in console
    assert "This is not a music-score audit" in console
    confirmation_path = tmp_path / "feedback-correction-confirmation.jsonl"
    confirmation_path.write_text(
        json.dumps(
            {
                "inputId": "input-correction",
                "expectedMachineRecordDigest": _sha256_json(corrected),
                "expectedCorrectionId": corrected["machineCorrection"]["correctionId"],
                "status": "confirm",
                "comment": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    confirmation_summary = extractor.apply_feedback_correction_confirmation_review(
        "batch-correction", confirmation_path
    )
    assert confirmation_summary["confirmedPageCount"] == 1
    assert confirmation_summary["tabCorrectionApprovalGranted"] is True
    assert confirmation_summary["scoreApprovalGranted"] is False
    assert confirmation_summary["pageApprovalGranted"] is False
    unchanged_after_confirmation = json.loads(
        (pages_dir / "input-correction.json").read_text(encoding="utf-8")
    )
    assert _sha256_json(unchanged_after_confirmation) == _sha256_json(corrected)


def test_feedback_correction_can_record_score_work_without_faking_tab_change() -> None:
    record = {
        "scoreSystems": [{"scoreSystemId": "score-system-1"}],
        "tabSystems": [],
    }
    _apply_feedback_correction_operation(
        record,
        {
            "operationId": "pending-score-step",
            "type": "record_score_feedback_pending",
            "scoreSystemId": "score-system-1",
        },
        feedback_item_ids=["combined-feedback-1"],
    )

    assert record["pendingScoreFeedbackCorrections"] == [
        {
            "operationId": "pending-score-step",
            "scoreSystemId": "score-system-1",
            "feedbackItemIds": ["combined-feedback-1"],
            "reviewState": "unresolved_requires_score_candidate_correction",
            "humanApprovalGranted": False,
        }
    ]
    assert record["tabSystems"] == []


def test_score_repair_candidate_prefers_latest_index_entry_over_filename_sort(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "extraction" / "discovery"
    repair_root = output_root / "review" / "score-audit" / "repair"
    candidate_root = repair_root / "candidate-records" / "input-1"
    candidate_root.mkdir(parents=True)
    base_digest = "a" * 64
    tab_facts_digest = _reviewed_tab_facts_digest({"tabSystems": []})

    def candidate(revision: int) -> dict[str, Any]:
        return {
            "revision": revision,
            "tabSystems": [],
            "scoreRepair": {
                "baseReviewedRecordDigest": base_digest,
                "reviewedTabFactsDigest": tab_facts_digest,
            },
        }

    older = candidate(1)
    newer = candidate(2)
    older_path = candidate_root / "z-older.json"
    newer_path = candidate_root / "a-newer.json"
    older_path.write_text(json.dumps(older), encoding="utf-8")
    newer_path.write_text(json.dumps(newer), encoding="utf-8")
    entries = [
        {
            "inputId": "input-1",
            "baseReviewedRecordDigest": base_digest,
            "repairVersion": SCORE_REPAIR_VERSION,
            "status": "candidate_ready",
            "candidateRecordPath": str(older_path.relative_to(output_root)),
            "candidateRecordDigest": _sha256_json(older),
            "reviewedTabFactsDigest": tab_facts_digest,
        },
        {
            "inputId": "input-1",
            "baseReviewedRecordDigest": base_digest,
            "repairVersion": SCORE_REPAIR_VERSION,
            "status": "candidate_ready",
            "candidateRecordPath": str(newer_path.relative_to(output_root)),
            "candidateRecordDigest": _sha256_json(newer),
            "reviewedTabFactsDigest": tab_facts_digest,
        },
    ]
    (repair_root / "score-repair-index.jsonl").write_text(
        "\n".join(json.dumps(item) for item in entries) + "\n",
        encoding="utf-8",
    )

    selected = _score_repair_candidate(
        output_root,
        input_id="input-1",
        base_reviewed_record_digest=base_digest,
    )

    assert selected is not None
    selected_candidate, selected_path, _selected_entry = selected
    assert selected_candidate["revision"] == 2
    assert selected_path.endswith("a-newer.json")


def test_loopback_review_submission_is_private_validated_and_idempotent(tmp_path: Path) -> None:
    private = tmp_path / "private"
    review_dir = (
        private
        / "batches"
        / "batch-submit"
        / "extraction"
        / "discovery"
        / "review"
    )
    review_dir.mkdir(parents=True)
    packet_digest = "b" * 64
    machine_digest = "c" * 64
    (review_dir / "page-review-packet-summary.json").write_text(
        json.dumps({"packetDigest": packet_digest, "pageCount": 1}),
        encoding="utf-8",
    )
    (review_dir / "page-review-packet.jsonl").write_text(
        json.dumps({"inputId": "input-0001", "machineRecordDigest": machine_digest}) + "\n",
        encoding="utf-8",
    )
    payload = {
        "batchId": "batch-submit",
        "partition": "discovery",
        "packetDigest": packet_digest,
        "reviews": [
            {
                "inputId": "input-0001",
                "expectedMachineRecordDigest": machine_digest,
                "action": "feedback",
                "reviewerReference": "player-reviewer",
                "approvedSections": [],
                "eventFeedback": [],
                "notes": "Whole-page feedback.",
            }
        ],
    }

    first = _store_review_submission(private, payload)
    assert first["status"] == "received_not_applied"
    assert first["reviewCount"] == 1
    assert first["deduplicated"] is False
    second = _store_review_submission(private, payload)
    assert second["submissionId"] == first["submissionId"]
    assert second["deduplicated"] is True
    submission_path = review_dir / "submissions" / f"{first['submissionId']}.jsonl"
    metadata_path = review_dir / "submissions" / f"{first['submissionId']}.json"
    assert json.loads(submission_path.read_text(encoding="utf-8"))["inputId"] == "input-0001"
    assert json.loads(metadata_path.read_text(encoding="utf-8"))["status"] == "received_not_applied"
    assert stat.S_IMODE(submission_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(metadata_path.stat().st_mode) == 0o600
    _mark_review_submission_applied(
        submission_path,
        {
            "batchId": "batch-submit",
            "partition": "discovery",
            "reviewedPageCount": 0,
            "humanApprovedPageCount": 0,
            "excludedPageCount": 0,
            "feedbackPageCount": 1,
            "remainingPageCount": 1,
            "decisionLogDigest": "d" * 64,
            "feedbackLogDigest": "e" * 64,
            "approvedIndexDigest": "f" * 64,
        },
    )
    applied_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert applied_metadata["status"] == "applied"
    assert applied_metadata["applicationSummary"]["feedbackPageCount"] == 1
    _mark_review_submission_applied(submission_path, applied_metadata["applicationSummary"] | {
        "batchId": "batch-submit",
        "partition": "discovery",
    })

    server = make_review_http_server(private, port=0)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_address[1]}/__lane20_review_submission",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode("utf-8"))
        assert response.status == 201
        assert result["submissionId"] == first["submissionId"]
        assert result["deduplicated"] is True
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)

    stale_payload = {**payload, "packetDigest": "d" * 64}
    with pytest.raises(ExtractionWorkflowError, match="stale packet digest"):
        _store_review_submission(private, stale_payload)


def test_score_audit_submission_requires_every_system_and_is_idempotent(tmp_path: Path) -> None:
    private = tmp_path / "private"
    audit_dir = private / "batches/batch-score/extraction/discovery/review/score-audit"
    audit_dir.mkdir(parents=True)
    packet_digest = "a" * 64
    reviewed_digest = "b" * 64
    record = {
        "scoreSystems": [
            {
                "scoreSystemId": "score-system-1",
                "scoreEvents": [{"scoreEventId": "score-event-1"}],
            }
        ],
        "tabSystems": [
            {"tabSystemId": "tab-system-1", "tabEvents": [{"tabEventId": "tab-event-1"}]}
        ],
        "eventAlignments": [{"eventAlignmentId": "alignment-1"}],
    }
    (audit_dir / "score-audit-packet-summary.json").write_text(
        json.dumps({"packetDigest": packet_digest, "pageCount": 1}), encoding="utf-8"
    )
    (audit_dir / "score-audit-packet.jsonl").write_text(
        json.dumps(
            {
                "inputId": "input-0001",
                "reviewedRecordDigest": reviewed_digest,
                "reviewedRecord": record,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "reviewType": "score_audit",
        "batchId": "batch-score",
        "partition": "discovery",
        "packetDigest": packet_digest,
        "reviews": [
            {
                "inputId": "input-0001",
                "expectedReviewedRecordDigest": reviewed_digest,
                "action": "accept",
                "reviewerReference": "score-reviewer",
                "systemDecisions": [
                    {"scoreSystemId": "score-system-1", "status": "accept", "comment": None}
                ],
                "eventFeedback": [],
            }
        ],
    }
    first = _store_score_audit_submission(private, payload)
    second = _store_score_audit_submission(private, payload)
    assert first["status"] == "received_not_applied"
    assert second["submissionId"] == first["submissionId"]
    assert second["deduplicated"] is True
    incomplete = copy.deepcopy(payload)
    incomplete["reviews"][0]["systemDecisions"] = []
    with pytest.raises(ExtractionWorkflowError, match="explicitly review every score system"):
        _store_score_audit_submission(private, incomplete)
    tab_feedback = copy.deepcopy(payload)
    tab_feedback["reviews"][0]["action"] = "feedback"
    tab_feedback["reviews"][0]["systemDecisions"][0] = {
        "scoreSystemId": "score-system-1",
        "status": "feedback",
        "comment": "The selected tab event does not belong with this score note.",
    }
    tab_feedback["reviews"][0]["eventFeedback"] = [
        {
            "targetType": "tab_event",
            "targetId": "tab-event-1",
            "scoreSystemId": "score-system-1",
            "friendlyContext": "Tab event 1",
            "comment": "The selected tab event does not belong with this score note.",
        }
    ]
    assert _store_score_audit_submission(private, tab_feedback)["reviewCount"] == 1


def test_score_audit_acceptance_promotes_candidate_without_changing_reviewed_tab_facts(
    tmp_path: Path,
) -> None:
    private = tmp_path / "private"
    batch_dir = private / "batches/batch-score-promotion"
    output_root = batch_dir / "extraction/discovery"
    review_dir = output_root / "review"
    repair_dir = review_dir / "score-audit/repair"
    approved_dir = review_dir / "approved-records"
    candidate_dir = repair_dir / "candidate-records/input-0001"
    candidate_dir.mkdir(parents=True)
    approved_dir.mkdir(parents=True)
    (batch_dir / "manifest.json").write_text(
        json.dumps(
            {
                "batchId": "batch-score-promotion",
                "sourceCopedentId": "source-e9-abc-defg-v1",
            }
        ),
        encoding="utf-8",
    )
    (batch_dir / "discovery-work.jsonl").write_text(
        json.dumps({"inputId": "input-0001", "datasetPartition": "discovery"}) + "\n",
        encoding="utf-8",
    )
    tab_system = {
        "tabSystemId": "tab-system-1",
        "systemIndex": 1,
        "reviewState": "human_approved",
        "measures": [{"measure": 1, "reviewState": "human_approved"}],
        "tabEvents": [
            {
                "tabEventId": "tab-event-1",
                "measure": 1,
                "reviewState": "human_approved",
                "steelActions": [
                    {
                        "steelActionId": "action-1",
                        "string": 5,
                        "fret": 3,
                        "attack": True,
                        "soundingPitchValue": 60,
                        "reviewState": "human_approved",
                    },
                    {
                        "steelActionId": "action-2",
                        "string": 4,
                        "fret": 3,
                        "attack": True,
                        "soundingPitchValue": 64,
                        "reviewState": "human_approved",
                    },
                ],
            }
        ],
    }
    score_system = {
        "scoreSystemId": "score-system-1",
        "pairedTabSystemId": "tab-system-1",
        "systemIndex": 1,
        "reviewState": "needs_human_review",
        "measures": [{"measure": 1, "reviewState": "needs_human_review"}],
        "scoreEvents": [
            {
                "scoreEventId": "score-event-1",
                "measure": 1,
                "beat": 1.0,
                "pitchValue": 60,
                "pitch": "C4",
                "rest": False,
                "reviewState": "needs_human_review",
            },
            {
                "scoreEventId": "score-event-2",
                "measure": 1,
                "beat": 1.0,
                "pitchValue": 64,
                "pitch": "E4",
                "rest": False,
                "reviewState": "needs_human_review",
            },
        ],
    }
    candidate = {
        "batchId": "batch-score-promotion",
        "inputId": "input-0001",
        "datasetPartition": "discovery",
        "assetSha256": "a" * 64,
        "revision": 3,
        "reviewState": "needs_human_review",
        "humanApprovalComplete": False,
        "pageClassification": {"primary": "score_with_aligned_tab"},
        "scoreSystems": [score_system],
        "tabSystems": [tab_system],
        "eventAlignments": _align_events(score_system["scoreEvents"], tab_system["tabEvents"]),
        "grips": [],
        "movementSequences": [],
        "derivedDecisions": [],
        "teachingConcepts": [],
        "exercises": [],
        "explicitText": [],
    }
    base = copy.deepcopy(candidate)
    base["revision"] = 2
    base["reviewState"] = "human_approved"
    base["humanApprovalComplete"] = True
    base["scoreSystems"][0]["scoreEvents"][1]["pitchValue"] = 65
    base["scoreSystems"][0]["scoreEvents"][1]["pitch"] = "F4"
    base_digest = _sha256_json(base)
    tab_digest = _reviewed_tab_facts_digest(base)
    candidate["scoreRepair"] = {
        "baseReviewedRecordDigest": base_digest,
        "reviewedTabFactsDigest": tab_digest,
    }
    assert _reviewed_tab_facts_digest(candidate) == tab_digest
    base_path = approved_dir / "input-0001-r2.json"
    base_path.write_text(json.dumps(base), encoding="utf-8")
    candidate_digest = _sha256_json(candidate)
    candidate_path = candidate_dir / f"{candidate_digest}.json"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    (review_dir / "approved-record-index.jsonl").write_text(
        json.dumps(
            {
                "inputId": "input-0001",
                "status": "human_approved",
                "reviewDecisionId": "prior-tab-review",
                "recordRevision": 2,
                "reviewedRecordPath": str(base_path.relative_to(output_root)),
                "reviewedRecordDigest": base_digest,
                "assetSha256": "a" * 64,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (repair_dir / "score-repair-index.jsonl").write_text(
        json.dumps(
            {
                "schemaVersion": "amazing-tablature-score-repair-v1",
                "repairVersion": SCORE_REPAIR_VERSION,
                "inputId": "input-0001",
                "status": "candidate_ready",
                "baseReviewedRecordDigest": base_digest,
                "reviewedTabFactsDigest": tab_digest,
                "candidateRecordPath": str(candidate_path.relative_to(output_root)),
                "candidateRecordDigest": candidate_digest,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    decision_path = tmp_path / "score-audit.jsonl"
    decision_path.write_text(
        json.dumps(
            {
                "inputId": "input-0001",
                "expectedReviewedRecordDigest": candidate_digest,
                "action": "accept",
                "reviewerReference": "score-reviewer",
                "systemDecisions": [
                    {
                        "scoreSystemId": "score-system-1",
                        "status": "accept",
                        "comment": None,
                    }
                ],
                "eventFeedback": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    summary = AmazingTablatureExtractor(private).apply_score_audit_review(
        "batch-score-promotion",
        decision_path,
    )

    approved_index = json.loads(
        (review_dir / "approved-record-index.jsonl").read_text(encoding="utf-8")
    )
    final_record = json.loads(
        (output_root / approved_index["reviewedRecordPath"]).read_text(encoding="utf-8")
    )
    score_index = json.loads(
        (review_dir / "score-audit/approved-score-index.jsonl").read_text(encoding="utf-8")
    )
    assert summary["scoreAuditComplete"] is True
    assert approved_index["scoreRepairCandidateDigest"] == candidate_digest
    assert approved_index["reviewedRecordDigest"] == _sha256_json(final_record)
    assert score_index["reviewedRecordDigest"] == approved_index["reviewedRecordDigest"]
    assert score_index["auditedCandidateDigest"] == candidate_digest
    assert _reviewed_tab_facts_digest(final_record) == tab_digest
    assert final_record["scoreSystems"][0]["reviewState"] == "human_approved"
    assert final_record["scoreAuditApprovalScope"]["schemaVersion"] == (
        SCORE_AUDIT_SCOPE_SCHEMA_VERSION
    )
    assert final_record["scoreAuditApprovalScope"]["pitchToTabTrainingEligible"] is True
    assert final_record["scoreAuditApprovalScope"]["scoreRhythmTrainingEligible"] is False
    assert final_record["scoreSystems"][0]["scoreEvents"][0]["fieldReviewStates"] == {
        "chordMembership": "human_approved",
        "duration": "not_reviewed_excluded",
        "pitch": "human_approved",
        "rhythmicPosition": "not_reviewed_excluded",
        "tie": "not_reviewed_excluded",
    }
    assert score_index["pitchToTabTrainingEligible"] is True
    assert score_index["scoreRhythmTrainingEligible"] is False
    assert final_record["tabSystems"] == base["tabSystems"]
    assert _sha256_json(json.loads(base_path.read_text(encoding="utf-8"))) == base_digest

    replay = AmazingTablatureExtractor(private).apply_score_audit_review(
        "batch-score-promotion",
        decision_path,
    )
    assert replay["auditedPageCount"] == 1
    prepared_after_replay = AmazingTablatureExtractor(private).prepare_score_audit_review(
        "batch-score-promotion"
    )
    assert prepared_after_replay["alreadyAuditedPageCount"] == 1
    assert prepared_after_replay["pageCount"] == 0

    amendment = AmazingTablatureExtractor(private).qualify_score_audit_scope(
        "batch-score-promotion",
        input_id="input-0001",
        expected_score_audit_decision_id=score_index["scoreAuditDecisionId"],
        reviewer_reference="scope-clarification",
    )
    amended_index = json.loads(
        (review_dir / "approved-record-index.jsonl").read_text(encoding="utf-8")
    )
    amended_record = json.loads(
        (output_root / amended_index["reviewedRecordPath"]).read_text(encoding="utf-8")
    )
    amended_score_index = json.loads(
        (review_dir / "score-audit/approved-score-index.jsonl").read_text(encoding="utf-8")
    )
    assert amendment["pitchToTabTrainingEligible"] is True
    assert amendment["scoreRhythmTrainingEligible"] is False
    assert amended_record["revision"] == final_record["revision"] + 1
    assert amended_record["scoreAuditScopeAmendment"]["scoreAuditDecisionId"] == (
        score_index["scoreAuditDecisionId"]
    )
    assert amended_score_index["reviewedRecordDigest"] == _sha256_json(amended_record)
    assert _reviewed_tab_facts_digest(amended_record) == tab_digest
    assert (
        AmazingTablatureExtractor(private).qualify_score_audit_scope(
            "batch-score-promotion",
            input_id="input-0001",
            expected_score_audit_decision_id=score_index["scoreAuditDecisionId"],
            reviewer_reference="scope-clarification",
        )["deduplicated"]
        is True
    )
