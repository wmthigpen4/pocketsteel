"""The small deterministic E9 contract consumed by TTT Steel Map.

This module intentionally imports only deterministic copedent and grip data.
It must never import retrieval, corpus, server, storage, or UI modules.  TTT
keeps its own sounding-register convention and exact-voicing admission gate;
the contract supplies the shared facts that can otherwise drift.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from steel_guitar_rag.e9_copedents import EMMONS_E9, NOTE_TO_SEMITONE
from steel_guitar_rag.fretboard_explorer import THREE_STRING_GRIP_VOCABULARY


CONTRACT_VERSION = "1"
TTT_PROFILE_ID = "standard-e9-emmons"
# This is the audited deterministic-model revision, not the exporter commit.
# Advance it only with a reviewed theory-data change and a regenerated snapshot.
THEORY_SOURCE_REVISION = "4a77e849c9c9ba8e13429d91ae055d06d0de7ce5"
_TTT_CONTROL_IDS = ("A", "B", "C", "E-raise", "E-lower")

# This is TTT's intentionally narrow exact-chart-chord subset of the broader
# browser quality registry.  It does not grant partial/rootless admission.
_TTT_FORMULAS = (
    ("major-triad", (0, 4, 7), ("1", "3", "5")),
    ("minor-triad", (0, 3, 7), ("1", "b3", "5")),
    ("dominant-seventh", (0, 4, 7, 10), ("1", "3", "5", "b7")),
    ("major-seventh", (0, 4, 7, 11), ("1", "3", "5", "7")),
    ("minor-seventh", (0, 3, 7, 10), ("1", "b3", "5", "b7")),
)


def canonical_json(value: object) -> str:
    """Return the stable serialization used for the snapshot digest."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def contract_content_digest(content: object) -> str:
    return hashlib.sha256(canonical_json(content).encode("utf-8")).hexdigest()


def build_ttt_steel_map_contract(source_revision: str) -> dict[str, Any]:
    """Build the browser-safe, deterministic snapshot without any I/O."""
    profile_controls = EMMONS_E9.controls_by_id()
    controls = []
    for control_id in _TTT_CONTROL_IDS:
        control = profile_controls[control_id]
        controls.append({
            "id": control.id,
            "kind": control.control_type,
            "changes": [
                {"string": change.string, "semitones": change.semitones}
                for change in control.changes
            ],
        })

    grips = [
        {
            "label": entry.label,
            "strings": list(entry.strings),
            "tier": entry.tier,
            "roles": list(entry.roles),
            "defaultVisible": entry.default_visible,
            "finderEligible": entry.allowed_in_chord_finder,
            "identifierEligible": entry.allowed_in_voicing_identifier,
        }
        for entry in THREE_STRING_GRIP_VOCABULARY.values()
    ]
    # The existing TTT dominant-7 template uses this reviewed RAG browser grip.
    # Keep it as data only: a string set never makes a chord without validation.
    grips.append({
        "label": "4-5-6-9",
        "strings": [4, 5, 6, 9],
        "tier": "advanced",
        "roles": ["dominant_color", "chord_voicing"],
        "defaultVisible": False,
        "finderEligible": True,
        "identifierEligible": True,
    })

    content = {
        "contractVersion": CONTRACT_VERSION,
        "profile": {
            "sourceProfileId": EMMONS_E9.id,
            "tttProfileId": TTT_PROFILE_ID,
            # Deliberately omit absolute pitch values: #65 found a register
            # mismatch and TTT retains its established local MIDI convention.
            "strings": [
                {
                    "string": string,
                    "openSpelling": EMMONS_E9.open_notes_by_string()[string],
                    "pitchClass": NOTE_TO_SEMITONE[EMMONS_E9.open_notes_by_string()[string]],
                }
                for string in sorted(EMMONS_E9.open_notes_by_string())
            ],
            "controls": controls,
        },
        "grips": grips,
        "formulas": [
            {"id": formula_id, "intervals": list(intervals), "degrees": list(degrees)}
            for formula_id, intervals, degrees in _TTT_FORMULAS
        ],
    }
    return {
        "contractVersion": CONTRACT_VERSION,
        "source": {
            "repository": "wmthigpen4/steel-guitar-rag",
            "revision": source_revision,
            "profileId": EMMONS_E9.id,
        },
        "contentDigest": contract_content_digest(content),
        **content,
    }
