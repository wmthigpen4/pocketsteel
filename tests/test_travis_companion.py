from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

import pytest

from partner_companions.travis_howdy.release import (
    CompanionReleaseError,
    DEFAULT_COMPANION,
    DEFAULT_RELATED_LESSONS,
    _normalized_artifact_hash,
    _merge_release_config,
    build_companion_bundle,
    generate_tablature_pdf,
    validate_companion,
    validate_related_lesson_coverage,
    validate_related_lessons,
)
from scripts.verify_travis_companion import BLOCKED_ROUTES, verify


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "partner_companions" / "travis_howdy" / "site"


def load_draft() -> dict[str, object]:
    return json.loads(DEFAULT_COMPANION.read_text(encoding="utf-8"))


def approved_release_data(*, review_phase: str = "owner_only", tester_count: int = 1) -> dict[str, object]:
    data = load_draft()
    data["contentStatus"] = "approved"
    data["approvals"] = {key: True for key in data["approvals"]}
    data["copedent"]["approved"] = True
    data["print"]["approved"] = True
    data["release"]["approvalReferences"] = ["music", "chords", "audio", "brand", "print"]
    data["release"]["reviewPhase"] = review_phase
    data["release"]["testerEmailCount"] = tester_count
    for event in data["events"]:
        event["musicalVerified"] = True
    for chord in data["chordTimeline"]:
        chord["verified"] = True
        chord["symbol"] = "C"
        chord["tabNotes"] = [
            {"string": 3, "fret": 8, "controls": [], "technique": "hold"},
            {"string": 4, "fret": 8, "controls": [], "technique": "hold"},
            {"string": 5, "fret": 8, "controls": [], "technique": "hold"},
        ]
    return data


def release_config(*, review_phase: str, tester_emails: list[str]) -> dict[str, object]:
    return {
        "reviewPhase": review_phase,
        "testerEmails": tester_emails,
        "feedbackEmail": "feedback@example.com",
        "approvalReferences": ["music", "chords", "audio", "brand", "print"],
        "approvals": {},
        "access": {
            "customDomainApplicationId": "custom-app",
            "pagesDevProductionApplicationId": "production-app",
            "pagesDevPreviewApplicationId": "preview-app",
            "customDomainAnonymousDenied": True,
            "pagesDevProductionAnonymousDenied": True,
            "pagesDevPreviewAnonymousDenied": True,
            "appSteelGuitarRagPolicyUnchanged": True,
        },
    }


def test_draft_is_deterministic_but_explicitly_unapproved() -> None:
    data = load_draft()
    validate_companion(data, release=False)
    assert data["runtimeMode"] == "published_deterministic"
    assert data["modelCallsAllowed"] is False
    assert data["contentStatus"] == "draft_review_required"
    assert not any(data["approvals"].values())
    assert all(chord["symbol"] is None and chord["verified"] is False for chord in data["chordTimeline"])
    assert all(event["musicalVerified"] is False for event in data["events"])
    with pytest.raises(CompanionReleaseError, match="contentStatus=approved"):
        validate_companion(data, release=True)


def test_all_views_share_one_event_graph() -> None:
    data = load_draft()
    events = {event["id"]: event for event in data["events"]}
    assert len(events) == 12
    assert sum(len(phrase["eventIds"]) for phrase in data["phrases"]) == len(events)
    assert {event["phraseId"] for event in events.values()} == {phrase["id"] for phrase in data["phrases"]}
    assert {event["chordEventId"] for event in events.values()} == {
        chord["id"] for chord in data["chordTimeline"]
    }
    assert all(event["tabNotes"] and event["notationPitch"] for event in events.values())


def test_full_song_and_taught_solo_scopes_preserve_solo_relative_tab_timing() -> None:
    data = load_draft()
    solo_duration = data["media"]["durationMs"]
    data["media"]["durationMs"] = 237_187
    data["media"]["scopes"] = {
        "fullSong": {
            "id": "full-song",
            "label": "Full song",
            "startMs": 0,
            "endMs": 237_187,
            "durationMs": 237_187,
        },
        "taughtSolo": {
            "id": "taught-solo",
            "label": "Taught solo",
            "startMs": 118_320,
            "endMs": 118_320 + solo_duration,
            "durationMs": solo_duration,
        },
    }
    validate_companion(data, release=False)
    assert data["events"][-1]["endMs"] == data["media"]["scopes"]["taughtSolo"]["durationMs"]
    assert data["media"]["scopes"]["fullSong"]["durationMs"] == data["media"]["durationMs"]

    data["media"]["scopes"]["taughtSolo"]["endMs"] += 1
    with pytest.raises(CompanionReleaseError, match="invalid timing"):
        validate_companion(data, release=False)


def test_optional_full_song_chord_timeline_must_cover_complete_song() -> None:
    data = load_draft()
    duration = data["media"]["durationMs"]
    data["songChordTimeline"] = [
        {"id": "song-chord-1", "startMs": 0, "endMs": duration, "symbol": "D", "nns": "I"}
    ]
    validate_companion(data, release=False)

    data["songChordTimeline"][0]["startMs"] = 1
    with pytest.raises(CompanionReleaseError, match="contiguous and fully labeled"):
        validate_companion(data, release=False)

    data["songChordTimeline"][0]["startMs"] = 0
    data["songChordTimeline"][0]["endMs"] = duration - 1
    with pytest.raises(CompanionReleaseError, match="cover the complete song scope"):
        validate_companion(data, release=False)


def test_optional_song_form_must_be_contiguous_and_cover_the_recording() -> None:
    data = load_draft()
    duration = data["media"]["durationMs"]
    data["songForm"] = [
        {"id": "first", "label": "First", "startMs": 0, "endMs": duration // 2},
        {"id": "second", "label": "Second", "startMs": duration // 2, "endMs": duration},
    ]
    validate_companion(data, release=False)
    data["songForm"][1]["startMs"] += 1
    with pytest.raises(CompanionReleaseError, match="section map must be contiguous"):
        validate_companion(data, release=False)


def test_full_song_authoring_overlays_exact_solo_and_derives_nns() -> None:
    script = ROOT / "scripts" / "author_travis_song_chords.js"
    payload = subprocess.run(
        [
            "node",
            "-e",
            """
            const a=require(process.argv[1]);
            const companion={display:{key:'D'},media:{scopes:{fullSong:{durationMs:12000},taughtSolo:{startMs:4000,endMs:8000}}},chordTimeline:[
              {id:'solo-g',startMs:0,endMs:2000,barStart:1,barEnd:1,symbol:'G',nns:'IV'},
              {id:'solo-a',startMs:2000,endMs:4000,barStart:2,barEnd:2,symbol:'A',nns:'V'}
            ]};
            const analysis={analysisVersion:2,barStartsMs:[0,4000,8000],chords:[
              {id:'d1',bar:1,startMs:0,endMs:4000,symbol:'D',confidence:.9,needsAttention:false},
              {id:'a1',bar:2,startMs:4000,endMs:8000,symbol:'A',confidence:.7,needsAttention:true},
              {id:'g1',bar:3,startMs:8000,endMs:12000,symbol:'G7',confidence:.8,needsAttention:false}
            ]};
            console.log(JSON.stringify({timeline:a.buildSongChordTimeline(analysis,companion),nns:[a.nnsForSymbol('D','D'),a.nnsForSymbol('G7','D'),a.nnsForSymbol('Bm7','D'),a.nnsForSymbol('Dmaj7','D')]}));
            """,
            str(script),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(payload.stdout)
    assert result["nns"] == ["I", "IV7", "vi7", "Imaj7"]
    assert [(item["startMs"], item["endMs"]) for item in result["timeline"]] == [
        (0, 4000), (4000, 6000), (6000, 8000), (8000, 12000)
    ]
    assert [item["symbol"] for item in result["timeline"]] == ["D", "G", "A", "G"]
    assert result["timeline"][1]["sourceKind"] == "taught_solo_chord_timeline"


def test_reference_chart_aligns_sections_and_exact_lesson_scope_without_publishing_quality() -> None:
    module = ROOT / "scripts" / "lib" / "song_chart_authoring.js"
    payload = subprocess.run(
        [
            "node",
            "-e",
            """
            const author=require(process.argv[1]);
            const reference={schemaVersion:'song_chart_reference_v1',tempoBpm:160,meter:'4/4',gridUnit:'quarter_note',gridLength:16,qualityPolicy:'roots_only',corroboratedRoots:['D','G','A'],sources:[{id:'one'},{id:'two'}],runs:[
              {startBeat:0,endBeat:2,symbol:'Dmaj7'},
              {startBeat:2,endBeat:4,symbol:'D5'},
              {startBeat:4,endBeat:8,symbol:'G'},
              {startBeat:8,endBeat:12,symbol:'A7'},
              {startBeat:12,endBeat:16,symbol:'D'}
            ],sections:[
              {id:'verse',label:'Verse',startBeat:0,endBeat:8},
              {id:'break',label:'Break',startBeat:8,endBeat:16}
            ],scopeMappings:{taughtSolo:{startBeat:8,endBeat:12}}};
            const companion={display:{key:'D'},media:{scopes:{fullSong:{durationMs:16000},taughtSolo:{startMs:9000,endMs:12000}}}};
            const nns=(symbol)=>({D:'I',G:'IV',A:'V','N.C.':'N.C.'}[symbol]||'?');
            const result=author.alignReferenceChart(reference,companion,nns);
            const beatTimes=[0,1100,2200,3300,4400,5500,6600,7700,9000,10000,11000,12000,13000,14000,15000,16000];
            const snapped=author.alignReferenceChart(reference,companion,nns,beatTimes);
            console.log(JSON.stringify({result,snapped}));
            """,
            str(module),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    output = json.loads(payload.stdout)
    result = output["result"]
    snapped = output["snapped"]
    assert [item["label"] for item in result["sections"]] == ["Verse", "Break"]
    assert result["sections"][1]["startMs"] == 9_000
    assert result["timeline"][2]["startMs"] == 9_000
    assert result["timeline"][2]["endMs"] == 12_000
    assert [item["symbol"] for item in result["timeline"]] == ["D", "G", "A", "D"]
    assert result["timeline"][0]["observedSymbol"] == "Dmaj7"
    assert result["timeline"][0]["observedSymbols"] == ["Dmaj7", "D5"]
    assert result["timeline"][0]["referenceEndBeat"] == 4
    assert result["timeline"][2]["qualityStatus"] == "withheld"
    assert result["alignment"]["method"] == "piecewise_reference_grid_with_lesson_scope_anchors"
    assert snapped["timeline"][0]["endMs"] == 4_400
    assert snapped["timeline"][2]["startMs"] == 9_000
    assert snapped["alignment"]["method"] == "audio_beat_snapped_reference_grid_with_lesson_scope_anchors"
    assert snapped["alignment"]["beatSnap"]["detectedBeatCount"] == 16
    assert snapped["alignment"]["beatSnap"]["snappedBoundaryCount"] > 0


def test_reference_chart_uses_global_harmonic_evidence_to_choose_the_audible_beat() -> None:
    module = ROOT / "scripts" / "lib" / "song_chart_authoring.js"
    payload = subprocess.run(
        [
            "node",
            "-e",
            """
            const author=require(process.argv[1]);
            const reference={schemaVersion:'song_chart_reference_v1',tempoBpm:60,meter:'4/4',gridUnit:'quarter_note',gridLength:12,qualityPolicy:'roots_only',corroboratedRoots:['D','G','A'],sources:[{id:'one'}],runs:[
              {startBeat:0,endBeat:4,symbol:'D'},
              {startBeat:4,endBeat:8,symbol:'G'},
              {startBeat:8,endBeat:12,symbol:'A'}
            ],sections:[{id:'song',label:'Song',startBeat:0,endBeat:12}]};
            const companion={display:{key:'D'},media:{scopes:{fullSong:{durationMs:12000}}}};
            const beatTimes=Array.from({length:13},(_item,index)=>index*1000);
            const chroma=(pitch)=>Array.from({length:12},(_item,index)=>index===pitch?1:0);
            const neutral=chroma(0);
            const evidence=beatTimes.map((timeMs)=>({timeMs,beforeChroma:neutral,afterChroma:neutral,beforeEnergy:1,afterEnergy:1}));
            Object.assign(evidence[5],{beforeChroma:chroma(2),afterChroma:chroma(7)});
            Object.assign(evidence[8],{beforeChroma:chroma(7),afterChroma:chroma(9)});
            const nns=(symbol)=>({D:'I',G:'IV',A:'V'}[symbol]);
            console.log(JSON.stringify(author.alignReferenceChart(reference,companion,nns,beatTimes,evidence)));
            """,
            str(module),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(payload.stdout)
    assert [item["startMs"] for item in result["timeline"]] == [0, 5_000, 8_000]
    assert result["alignment"]["method"] == "global_harmonic_transition_constrained_beat_alignment"
    diagnostics = result["alignment"]["beatSnap"]
    assert diagnostics["musicallyScoredBoundaryCount"] == 2
    assert diagnostics["alignedBoundaryCount"] == 1
    assert diagnostics["neighboringBeatShiftCount"] == 1
    assert diagnostics["harmonicEvidenceGain"] > 0


def test_audio_only_song_form_groups_repeated_eight_measure_sections() -> None:
    module = ROOT / "scripts" / "lib" / "song_chart_authoring.js"
    payload = subprocess.run(
        [
            "node",
            "-e",
            """
            const author=require(process.argv[1]);
            const symbols=['D','G','A','D','D','G','A','D','D','G','A','D','D','G','A','D'];
            const bars=symbols.map((symbol,index)=>({bar:index+1,startMs:index*1000,endMs:(index+1)*1000}));
            const chords=symbols.map((symbol,index)=>({bar:index+1,symbol,rawCandidate:symbol,confidence:.9,reviewed:true,needsAttention:false,publicationSymbol:symbol}));
            console.log(JSON.stringify(author.inferRepeatedSections({analysisState:{bars},chords})));
            """,
            str(module),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(payload.stdout)
    assert [item["label"] for item in result] == ["Form A", "Form A · repeat"]
    assert result[-1]["endMs"] == 16_000


def test_chord_boundaries_are_exact_and_never_inferred() -> None:
    data = load_draft()
    by_chord: dict[str, list[dict[str, object]]] = {}
    for event in data["events"]:
        by_chord.setdefault(event["chordEventId"], []).append(event)
    for chord in data["chordTimeline"]:
        events = by_chord[chord["id"]]
        assert abs(events[0]["startMs"] - chord["startMs"]) <= 50
        assert abs(events[-1]["endMs"] - chord["endMs"]) <= 50
        assert chord["symbol"] is None


def test_normalized_artifact_hash_ignores_only_generated_fields() -> None:
    data = load_draft()
    generated = copy.deepcopy(data)
    generated["buildSha"] = "different"
    generated["artifactSha256"] = "different"
    generated["media"]["audioUrl"] = "/assets/example/audio.mp3"
    generated["media"]["soloAudioUrl"] = "/assets/example/solo.mp3"
    generated["media"]["pdfUrl"] = "/assets/example/tab.pdf"
    generated["media"]["brandHeroUrl"] = "/assets/example/photo.jpg"
    generated["relatedLessons"] = validate_related_lessons(
        json.loads(DEFAULT_RELATED_LESSONS.read_text(encoding="utf-8"))
    )
    for lesson in generated["relatedLessons"]:
        lesson["thumbnailUrl"] = "/assets/example/lesson.jpg"
    baseline = copy.deepcopy(data)
    baseline["relatedLessons"] = copy.deepcopy(generated["relatedLessons"])
    for lesson in baseline["relatedLessons"]:
        lesson["thumbnailUrl"] = None
    assert _normalized_artifact_hash(generated) == _normalized_artifact_hash(baseline)
    generated["events"][0]["instruction"] = "Changed music-facing content"
    assert _normalized_artifact_hash(generated) != _normalized_artifact_hash(baseline)


def test_related_video_cards_are_short_source_grounded_and_real() -> None:
    payload = json.loads(DEFAULT_RELATED_LESSONS.read_text(encoding="utf-8"))
    lessons = validate_related_lessons(payload)
    assert payload["companionProfileId"] == "howdy-54-event-route-v1"
    assert len(lessons) == 4
    assert {lesson["id"] for lesson in lessons} == {
        "hammer-ons-and-pull-offs",
        "pedals-really-doing",
        "intervals-make-chords",
        "pockets-positions-1",
    }
    assert all(lesson["url"].startswith("https://travis-toy-tutorials.teachable.com/") for lesson in lessons)
    assert all(lesson["startMs"] >= 0 and lesson["endMs"] > lesson["startMs"] for lesson in lessons)
    assert all(len(lesson["evidenceExcerpt"].split()) <= 22 for lesson in lessons)
    featured = [lesson for lesson in lessons if lesson.get("featuredForCompanion")]
    assert [lesson["id"] for lesson in featured] == [
        "hammer-ons-and-pull-offs",
        "pedals-really-doing",
        "intervals-make-chords",
        "pockets-positions-1",
    ]
    assert all(8 <= len(lesson["companionReason"].split()) <= 35 for lesson in featured)
    matches = [match for lesson in lessons for match in lesson["matches"]]
    assert {match["phraseId"] for match in matches} == {f"phrase-{number:02}" for number in range(1, 7)}
    assert all(match["sourceEventIds"] and match["conceptId"] and match["relation"] for match in matches)

    phrase_events: dict[str, set[str]] = {}
    for match in matches:
        phrase_events.setdefault(match["phraseId"], set()).update(match["sourceEventIds"])
    validate_related_lesson_coverage(
        {
            "phrases": [
                {"id": phrase_id, "eventIds": sorted(event_ids)}
                for phrase_id, event_ids in phrase_events.items()
            ],
            "relatedLessons": lessons,
        }
    )


def test_profile_specific_related_videos_are_not_attached_to_an_unmatched_companion(tmp_path: Path) -> None:
    thumbnail_dir = tmp_path / "thumbnails"
    thumbnail_dir.mkdir()
    lessons = validate_related_lessons(json.loads(DEFAULT_RELATED_LESSONS.read_text(encoding="utf-8")))
    for index, lesson in enumerate(lessons):
        (thumbnail_dir / lesson["thumbnailFile"]).write_bytes(b"jpeg-preview-" + bytes([index]))

    bundle = tmp_path / "bundle"
    build_companion_bundle(bundle, related_thumbnails_dir=thumbnail_dir, source_date_epoch=1)
    deployed = json.loads(next(bundle.rglob("lesson-companion.json")).read_text(encoding="utf-8"))
    assert deployed["relatedLessons"] == []
    assert not any(path.name.endswith(".jpg") for path in bundle.rglob("*.jpg"))


def test_coaching_cues_must_be_verbatim_and_timestamped() -> None:
    data = load_draft()
    event = data["events"][0]
    event["coachingCue"] = "Short exact lesson excerpt."
    event["sourceMoment"] = {
        "lessonTimeMs": 123_000,
        "quoteKind": "verbatim_excerpt",
        "excerpt": event["coachingCue"],
    }
    validate_companion(data, release=False)
    event["sourceMoment"]["excerpt"] = "A paraphrase is not allowed."
    with pytest.raises(CompanionReleaseError, match="verbatim excerpt"):
        validate_companion(data, release=False)


def test_draft_bundle_is_reproducible_allowlisted_and_isolated(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_manifest = tmp_path / "first-manifest.json"
    second_manifest = tmp_path / "second-manifest.json"
    result_one = build_companion_bundle(
        first,
        manifest_path=first_manifest,
        source_date_epoch=1_786_683_600,
    )
    result_two = build_companion_bundle(
        second,
        manifest_path=second_manifest,
        source_date_epoch=1_786_683_600,
    )
    assert result_one == result_two
    assert result_one["assetHashes"] == {
        path.relative_to(first).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(first.rglob("*"))
        if path.is_file()
    }
    report = verify(first, first_manifest)
    assert report["result"] == "pass"
    assert report["blockedRoutes"] == list(BLOCKED_ROUTES)
    assert not (first / "internal-release-manifest.json").exists()
    assert not list(first.rglob("*.vtt"))
    assert not list(first.rglob("*.srt"))
    assert not list(first.rglob("*.map"))


def test_local_draft_audio_is_private_and_hash_pinned(tmp_path: Path) -> None:
    audio = tmp_path / "private-preview.mp3"
    audio.write_bytes(b"ID3-local-owner-review")
    data = load_draft()
    data["media"]["audioSha256"] = hashlib.sha256(audio.read_bytes()).hexdigest()
    companion = tmp_path / "companion.json"
    companion.write_text(json.dumps(data), encoding="utf-8")
    bundle = tmp_path / "bundle"
    build_companion_bundle(
        bundle,
        companion_path=companion,
        draft_audio_path=audio,
        source_date_epoch=1,
    )
    packaged = list(bundle.rglob("howdy-backing-track.mp3"))
    assert len(packaged) == 1
    assert packaged[0].read_bytes() == audio.read_bytes()
    deployed_data = json.loads(next(bundle.rglob("lesson-companion.json")).read_text(encoding="utf-8"))
    assert deployed_data["media"]["audioUrl"].startswith("/assets/")
    assert deployed_data["media"]["draftClockOnly"] is False

    data["media"]["audioSha256"] = "0" * 64
    companion.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CompanionReleaseError, match="hash mismatch"):
        build_companion_bundle(
            tmp_path / "bad-bundle",
            companion_path=companion,
            draft_audio_path=audio,
        )


def test_scoped_draft_packages_distinct_full_song_and_taught_solo_assets(tmp_path: Path) -> None:
    full_audio = tmp_path / "full-song.mp3"
    solo_audio = tmp_path / "taught-solo.mp3"
    full_audio.write_bytes(b"ID3-full-song")
    solo_audio.write_bytes(b"ID3-taught-solo")
    data = load_draft()
    solo_duration = data["media"]["durationMs"]
    data["media"].update(
        {
            "audioSha256": hashlib.sha256(full_audio.read_bytes()).hexdigest(),
            "soloAudioSha256": hashlib.sha256(solo_audio.read_bytes()).hexdigest(),
            "durationMs": 237_187,
            "scopes": {
                "fullSong": {
                    "id": "full-song",
                    "label": "Full song",
                    "startMs": 0,
                    "endMs": 237_187,
                    "durationMs": 237_187,
                },
                "taughtSolo": {
                    "id": "taught-solo",
                    "label": "Taught solo",
                    "startMs": 118_320,
                    "endMs": 118_320 + solo_duration,
                    "durationMs": solo_duration,
                },
            },
        }
    )
    companion = tmp_path / "companion.json"
    companion.write_text(json.dumps(data), encoding="utf-8")
    bundle = tmp_path / "bundle"
    build_companion_bundle(
        bundle,
        companion_path=companion,
        draft_audio_path=full_audio,
        draft_solo_audio_path=solo_audio,
        source_date_epoch=1,
    )
    assert next(bundle.rglob("howdy-backing-track.mp3")).read_bytes() == full_audio.read_bytes()
    assert next(bundle.rglob("howdy-taught-solo.mp3")).read_bytes() == solo_audio.read_bytes()
    deployed = json.loads(next(bundle.rglob("lesson-companion.json")).read_text(encoding="utf-8"))
    assert deployed["media"]["audioUrl"] != deployed["media"]["soloAudioUrl"]
    assert deployed["media"]["audioUrl"].endswith("howdy-backing-track.mp3")
    assert deployed["media"]["soloAudioUrl"].endswith("howdy-taught-solo.mp3")


def test_bundle_verifier_rejects_access_phase_manifest_drift(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    manifest_path = tmp_path / "manifest.json"
    build_companion_bundle(bundle, manifest_path=manifest_path, source_date_epoch=1)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["reviewPhase"] = "partner_review"
    manifest["accessTesterCount"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CompanionReleaseError, match="review phase differs"):
        verify(bundle, manifest_path)


def test_security_headers_and_route_map_are_fail_closed(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    build_companion_bundle(bundle, source_date_epoch=1)
    redirects = (bundle / "_redirects").read_text(encoding="utf-8").splitlines()
    assert redirects == [
        "/ /howdy 302",
        "/howdy /howdy/index.html 200",
        "/howdy/embed-demo /howdy/embed-demo/index.html 200",
        "/howdy/print /howdy/print/index.html 200",
    ]
    headers = (bundle / "_headers").read_text(encoding="utf-8")
    assert "default-src 'self'" in headers
    assert "connect-src 'self'" in headers
    assert "media-src 'self' blob:" in headers
    assert "frame-ancestors 'none'" in headers
    assert "form-action 'none'" in headers
    assert "X-Robots-Tag: noindex, nofollow, noarchive" in headers
    assert "Referrer-Policy: no-referrer" in headers
    assert "X-Content-Type-Options: nosniff" in headers
    assert "Access-Control-Allow-Origin" not in headers


def test_local_practice_guide_alias_reuses_the_music_first_embed(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    manifest_path = tmp_path / "manifest.json"
    manifest = build_companion_bundle(
        bundle,
        manifest_path=manifest_path,
        practice_guide_alias=True,
        source_date_epoch=1,
    )
    alias = bundle / "practice-guide" / "howdy" / "index.html"
    assert alias.read_bytes() == (bundle / "howdy" / "embed-demo" / "index.html").read_bytes()
    assert "/practice-guide/howdy" in manifest["allowedRoutes"]
    assert "/practice-guide/howdy/ /practice-guide/howdy/index.html 200" in (
        bundle / "_redirects"
    ).read_text(encoding="utf-8")
    assert verify(bundle, manifest_path)["result"] == "pass"

    data = approved_release_data()
    companion = tmp_path / "approved.json"
    companion.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CompanionReleaseError, match="local-preview only"):
        build_companion_bundle(
            tmp_path / "release",
            companion_path=companion,
            release=True,
            release_config_path=tmp_path / "config.json",
            practice_guide_alias=True,
        )


def test_browser_runtime_has_one_same_origin_fetch_and_no_dynamic_clients() -> None:
    script = (SITE / "companion.js").read_text(encoding="utf-8")
    assert script.count("fetch(") == 2
    assert "fetch(companionUrl.href" in script
    assert "fetch(mediaUrl.href" in script
    assert "companionUrl.origin !== window.location.origin" in script
    assert "mediaUrl.origin !== window.location.origin" in script
    for token in ("XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon", "Worker("):
        assert token not in script
    lowered = script.lower()
    for endpoint in ("/api/answer", "/api/search", "ollama", "chroma", "openai.com/v1", "anthropic.com"):
        assert endpoint not in lowered


def test_companion_has_deterministic_search_layers_chords_and_step_study() -> None:
    script = (SITE / "companion.js").read_text(encoding="utf-8")
    markup = (ROOT / "partner_companions" / "travis_howdy" / "templates" / "companion.fragment.html").read_text(
        encoding="utf-8"
    )
    assert "function renderLessonSearch()" in script
    assert "function setLayer(" in script
    assert "function renderChordChart()" in script
    assert "function renderSongTimeline()" in script
    assert "function renderSongSections()" in script
    assert "function updateSongTimeline(" in script
    assert 'state.songDisplayMode === "nns" ? segment.nns : segment.symbol' in script
    assert "scroll.scrollLeft = target" not in script
    assert 'state.selectedLayer === "play-along" ? guideEvent()' in script
    assert 'playback will not move this guide' in script
    assert '!["phrase-practice", "play-along"].includes(layer.id)' in script
    assert "needs-attention" in script
    assert "function stepMove(" in script
    assert "function selectTabEvent(" in script
    assert "function bindTabControl(" in script
    assert 'node("button", "tab-cell-button"' in script
    assert "function scrollTabToEvent(" in script
    assert 'const events = state.data.events;' in script
    assert 'scrollTabToEvent(current.id, manualGuide ? "smooth" : "auto")' not in script
    assert '["phrase-practice", "play-along"].includes(state.selectedLayer)' in script
    assert "scrollTabToEvent(selected.id);" in script
    assert "pausePlayback();\n    seekTo(selected.startMs);" not in script
    assert "function renderRelatedLessons()" in script
    assert "function configureRelatedScroller()" in script
    assert 'link.target = "_blank"' in script
    assert 'return `${note.fret}h${pedal}`' in script
    assert 'return `${note.fret}h${destination}`' in script
    assert 'node("span", "related-why", "Why this lesson")' in script
    assert 'node("span", "related-reason", lesson.companionReason)' in script
    assert 'state.data.relatedLessons.filter((lesson) => lesson.featuredForCompanion)' in script
    assert script.count("renderRelatedLessons();") == 1
    assert "match.sourceEventIds" in script
    assert "match.conceptId" in script
    assert "match.relation" in script
    assert "current.instruction" in script
    assert "upcoming.instruction" in script
    assert "current.coachingCue || current.instruction" not in script
    assert "upcoming.coachingCue || upcoming.instruction" not in script
    for selector in (
        "data-lesson-search",
        "data-chord-chart",
        "data-song-timeline",
        "data-song-scroll",
        "data-song-sections",
        "data-song-tempo-label",
        "data-song-display",
        "data-song-chart-status",
        "data-song-chart-guardrail",
        "data-song-now-chord",
        "data-key-label",
        "data-study-controls",
        "data-study-title",
        "data-study-progress",
        "data-related-lessons",
        "data-related-scroll",
    ):
        assert selector in markup
    assert '"phrase-practice": `Taught solo · ${formatTime(mediaScopes().taughtSolo.durationMs)}`' in script
    assert '"play-along": `Full song · ${formatTime(mediaScopes().fullSong.durationMs)}`' in script
    assert "function renderMediaScope()" in script
    assert "function configureMediaScopeActions()" in script
    assert "taughtSoloTimeAt" in script
    assert 'if (!terms.length && presentation === "embed-demo") return;' in script
    assert 'aria-label="Full-song chords and Nashville numbers; manually scrollable"' in markup
    assert 'const tempoScope = fullSongActive ? "Full song" : "Taught solo";' in script
    assert 'state.data.display.fullSongTempoBpm' in script
    assert 'String(Math.round(bpm))' in script
    assert '`${tempoScope} · ${formatBpm(tempoValue)} BPM`' in script
    assert 'renderLessonFacts();' in script
    assert 'Solo grid' not in script
    assert 'Owner review' not in script
    assert 'owner review' not in script
    assert 'review-chip' not in markup
    assert 'Help with this lesson' in markup
    assert 'Use these when a technique or concept in Howdy needs more explanation.' in markup
    assert 'Go deeper after this lesson' not in markup
    assert 'Practice “Howdy”' in markup
    assert 'Practice the “Howdy” solo' not in markup
    assert 'title.textContent = "Practice “Howdy”";' in script
    assert "This chart stays still during playback" in script
    assert 'function configureSongDisplayToggle()' in script


def test_compact_embed_has_one_focused_workspace_per_layer() -> None:
    markup = (ROOT / "partner_companions" / "travis_howdy" / "templates" / "companion.fragment.html").read_text(
        encoding="utf-8"
    )
    styles = (SITE / "companion.css").read_text(encoding="utf-8")
    assert 'data-lesson-search-panel' in markup
    assert 'data-layer-tabs' in markup
    assert 'data-action="play"' in markup
    assert 'data-tab' in markup
    assert 'aria-label="Scrollable taught-solo tablature"' in markup
    assert "Scroll the solo or select any column for Travis’s guidance." in markup
    assert 'data-related-lessons' in markup
    assert 'Complete printable tab' in markup
    assert 'six practice sections' in markup
    assert 'data-action="loop"' not in markup
    assert 'Open larger practice view' in markup
    assert 'All six tab systems + expanded fretboard' in markup
    assert '<summary class="search-summary">' in markup
    assert '[data-active-layer]:not([data-active-layer="lesson-map"]) .lesson-search-card { display: none; }' in styles
    assert '[data-active-layer="phrase-practice"] .lesson-map { display: block; }' in styles
    assert '[data-active-layer="play-along"] .chord-chart-card { display: none; }' in styles
    assert '[data-active-layer="play-along"] .song-chart-card { display: block; }' in styles
    assert '[data-active-layer="play-along"] .tab-card { display: none; }' not in styles
    assert '[data-active-layer="play-along"] .move-card,' not in styles
    assert '[data-active-layer="play-along"] .position-details,' in styles
    assert '.song-sections { display: flex;' in styles
    assert '[data-active-layer="phrase-practice"].companion-shell .lesson-search-card { display: block; }' in styles
    assert '.related-video-grid { display: flex;' in styles
    assert 'scroll-snap-type: x mandatory' in styles
    assert '.related-scroll-controls' in styles
    assert '.tab-system + .tab-system' in styles
    assert markup.index('class="visual-card tab-card"') < markup.index('class="move-card"')
    assert ".tab-table td:hover, .tab-table td:focus-visible" in styles
    assert 'if (positionDetails && presentation === "full") positionDetails.open = true;' in (
        SITE / "companion.js"
    ).read_text(encoding="utf-8")
    assert '.compact-shell .layer-context, .compact-shell .mode-switcher, .compact-shell .source-card { display: none; }' in styles
    for rejected_copy in ("mechanical landmarks", "unverified transcription", "Use Travis’s own lesson moments"):
        assert rejected_copy not in markup


def test_taught_solo_uses_phrase_starts_without_forced_looping() -> None:
    script = (SITE / "companion.js").read_text(encoding="utf-8")
    assert '"Start from any phrase"' in script
    assert '"100% · continuous playback"' in script
    assert "setSpeed(0.5);" not in script
    assert "seekTo(phrase.startMs);" in script
    assert "state.loop" not in script
    assert 'data-action="loop"' not in script
    assert "state.timeMs >= phrase.endMs" not in script


def test_embed_matches_teachable_typeset_and_preserves_discussion_space() -> None:
    template = (ROOT / "partner_companions" / "travis_howdy" / "templates" / "embed.html").read_text(
        encoding="utf-8"
    )
    styles = (SITE / "companion.css").read_text(encoding="utf-8")
    assert 'data-demo-discussion' in template
    assert '>Discussion<' in template
    assert 'Post a comment' in template
    assert 'Member discussion stays in Teachable' not in template
    assert 'aria-label="Comment box preview"' in template
    assert 'disabled></textarea>' in template
    assert 'data-audio-download' in template
    assert 'Download the full-song backing track' in template
    assert 'href="{{AUDIO_URL}}"' in template
    assert 'download="Howdy - Full Song Play Along.mp3"' in template
    assert 'Primary play-along MP3' not in template
    assert 'Additional MP3s' not in template
    assert 'type="file"' not in template
    assert template.index('class="video-simulation"') < template.index('data-audio-download')
    assert template.index('data-audio-download') < template.index('id="companion"')
    assert template.index('id="companion"') < template.index('data-demo-discussion')
    script = (SITE / "companion.js").read_text(encoding="utf-8")
    assert 'function configureAudioSourceSetup()' not in script
    assert 'ttt:companion-audio-selection' not in script
    assert '[data-active-layer="play-along"] .related-videos { display: none; }' not in styles
    for exact_typeset in (
        "font-size: 22.784px",
        "font-weight: 600; line-height: 34.176px",
        "font-size: 18px; font-weight: 600; line-height: 19.8px",
        "font-size: 15px; font-weight: 400; line-height: 21.4286px",
    ):
        assert exact_typeset in styles


def test_release_validation_requires_every_human_signoff() -> None:
    data = approved_release_data()
    validate_companion(data, release=True)
    for field in sorted(data["approvals"]):
        candidate = copy.deepcopy(data)
        candidate["approvals"][field] = False
        with pytest.raises(CompanionReleaseError, match="Release approvals incomplete"):
            validate_companion(candidate, release=True)


@pytest.mark.parametrize(
    ("review_phase", "tester_count"),
    (("owner_only", 1), ("partner_review", 2)),
)
def test_release_validation_accepts_only_the_identity_count_for_the_review_phase(
    review_phase: str,
    tester_count: int,
) -> None:
    data = approved_release_data(review_phase=review_phase, tester_count=tester_count)
    validate_companion(data, release=True)

    data["release"]["testerEmailCount"] = tester_count + 1
    with pytest.raises(CompanionReleaseError, match="requires exactly"):
        validate_companion(data, release=True)


def test_release_validation_rejects_an_unrecognized_review_phase() -> None:
    data = approved_release_data(review_phase="automatic_partner_access")
    with pytest.raises(CompanionReleaseError, match="recognized review phase"):
        validate_companion(data, release=True)


@pytest.mark.parametrize(
    ("review_phase", "tester_emails"),
    (("owner_only", ["owner@example.com"]), ("partner_review", ["owner@example.com", "partner@example.com"])),
)
def test_private_release_config_enforces_phase_without_emitting_tester_addresses(
    review_phase: str,
    tester_emails: list[str],
) -> None:
    data = load_draft()
    _merge_release_config(data, release_config(review_phase=review_phase, tester_emails=tester_emails))
    assert data["release"]["reviewPhase"] == review_phase
    assert data["release"]["testerEmailCount"] == len(tester_emails)
    serialized = json.dumps(data)
    assert all(email not in serialized for email in tester_emails)


def test_owner_only_release_config_rejects_a_second_identity() -> None:
    data = load_draft()
    config = release_config(
        review_phase="owner_only",
        tester_emails=["owner@example.com", "partner@example.com"],
    )
    with pytest.raises(CompanionReleaseError, match="requires exactly 1 tester email"):
        _merge_release_config(data, config)


def test_pdf_contains_notation_tab_controls_and_revision(tmp_path: Path) -> None:
    pypdf = pytest.importorskip("pypdf")
    pdfplumber = pytest.importorskip("pdfplumber")
    data = load_draft()
    output = generate_tablature_pdf(data, tmp_path / "howdy.pdf")
    reader = pypdf.PdfReader(str(output))
    assert len(reader.pages) == 1
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Howdy - Taught Solo" in extracted
    assert "travistoytutorials.com" in extracted
    assert data["revision"] in extracted
    assert "DRAFT LAYOUT PROOF" in extracted
    assert all(phrase["label"] in extracted for phrase in data["phrases"])
    assert re.search(r"Page 1 of 1", extracted)
    assert "treble" not in extracted.lower()
    with pdfplumber.open(output) as document:
        for page in document.pages:
            words = page.extract_words()
            assert all(float(word["x0"]) >= 35.5 for word in words)
            assert all(float(word["x1"]) <= float(page.width) - 35.5 for word in words)


def test_pdf_renders_a_bar_hammer_as_a_fret_change(tmp_path: Path) -> None:
    pypdf = pytest.importorskip("pypdf")
    data = load_draft()
    note = data["events"][0]["tabNotes"][0]
    note.update(
        {
            "fret": 0,
            "controls": [],
            "technique": "bar-hammer",
            "toFret": 1,
            "fretPath": [0, 1],
            "tieFromPrevious": True,
        }
    )
    note.pop("toControls", None)
    output = generate_tablature_pdf(data, tmp_path / "howdy-bar-hammer.pdf")
    extracted = "\n".join(page.extract_text() or "" for page in pypdf.PdfReader(str(output)).pages)
    assert "0h1" in extracted
    assert "bar hammer from open to fret 1 without repicking" in extracted
    assert "bar stays at open fret" not in extracted
