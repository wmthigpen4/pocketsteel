"""Curated song-reference resources used by source-backed answer routes."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


STEEL_GUITAR_RAG_REFERENCE_PATH = (
    Path(__file__).resolve().parent
    / "resources"
    / "curated"
    / "steel-guitar-rag-expert-reference.md"
)


def load_steel_guitar_rag_reference() -> str:
    return STEEL_GUITAR_RAG_REFERENCE_PATH.read_text(encoding="utf-8")


def is_steel_guitar_rag_question(question: str) -> bool:
    return "steel guitar rag" in (question or "").lower()


def steel_guitar_rag_source_cards() -> tuple[dict[str, Any], ...]:
    source_path = str(STEEL_GUITAR_RAG_REFERENCE_PATH.relative_to(Path(__file__).resolve().parents[1]))
    return (
        {
            "score": 1.0,
            "excerpt": (
                "Curated Steel Guitar Rag expert reference covering history, authorship, form, "
                "source links, listening links, copyright guardrails, and an original E9 teaching study."
            ),
            "forum_name": "The Turnaround curated resources",
            "thread_title": "Steel Guitar Rag expert reference",
            "thread_url": source_path,
            "chunk_id": "steel-guitar-rag-curated-reference",
            "post_uid": "steel-guitar-rag-reference",
            "source_system": "curated_reference",
        },
        {
            "score": 0.98,
            "excerpt": (
                "UCSB DAHR lists Brunswick matrix C1479, Steel guitar rag / Texas Playboys, "
                "recorded in Chicago on 9/29/1936."
            ),
            "forum_name": "UCSB Discography of American Historical Recordings",
            "thread_title": "Steel guitar rag / Texas Playboys, Brunswick matrix C1479",
            "thread_url": "https://adp.library.ucsb.edu/index.php/matrix/detail/2000442978/C1479-Steel_guitar_rag",
            "chunk_id": "steel-guitar-rag-ucsb-dahr",
            "post_uid": "steel-guitar-rag-ucsb-dahr",
            "source_system": "curated_reference",
        },
        {
            "score": 0.96,
            "excerpt": (
                "Guy Cundell's provenance article discusses McAuliffe's Steel Guitar Rag, "
                "Sylvester Weaver's Guitar Rag, and the tune's Western swing setting."
            ),
            "forum_name": "Curated external reference",
            "thread_title": "Guy Cundell, Steel Guitar Blag",
            "thread_url": "https://b0b.com/wp/wp-content/uploads/2022/08/Steel-Guitar-Blag.pdf",
            "chunk_id": "steel-guitar-rag-cundell",
            "post_uid": "steel-guitar-rag-cundell",
            "source_system": "curated_reference",
        },
        {
            "score": 0.94,
            "excerpt": (
                "SecondHandSongs lists Steel Guitar Rag as adapted from Guitar Rag, "
                "with Sara Martin and Sylvester Weaver connected to the earlier work."
            ),
            "forum_name": "SecondHandSongs",
            "thread_title": "Steel Guitar Rag work page",
            "thread_url": "https://secondhandsongs.com/work/129616/all",
            "chunk_id": "steel-guitar-rag-secondhandsongs",
            "post_uid": "steel-guitar-rag-secondhandsongs",
            "source_system": "curated_reference",
        },
        {
            "score": 0.92,
            "excerpt": (
                "Easy Song lists modern copyright/licensing information for Steel Guitar Rag, "
                "which is useful attribution context for a teaching transcription or arrangement."
            ),
            "forum_name": "Easy Song",
            "thread_title": "Steel Guitar Rag copyright and licensing listing",
            "thread_url": "https://www.easysong.com/search/songs/song-copyright-holder-information.aspx?s=50588",
            "chunk_id": "steel-guitar-rag-easysong",
            "post_uid": "steel-guitar-rag-easysong",
            "source_system": "curated_reference",
        },
    )


def steel_guitar_rag_answer_for_question(question: str) -> str | None:
    q = (question or "").lower()
    if "steel guitar rag" not in q:
        return None

    if re.search(r"\bwho\s+wrote\b|\bcomposer\b|\bauthor\b|\bcredit", q):
        return (
            "“Steel Guitar Rag” is most strongly associated with Leon McAuliffe and the Bob Wills/Texas Playboys Western-swing recording world, but the authorship story is more nuanced.\n\n"
            "The curated reference connects the tune to Sylvester Weaver’s earlier “Guitar Rag,” and notes that later licensing records commonly list Cliffie Stone, Leon McAuliffe, and Merle Travis. For citation-level work, treat the exact recording, chart, or licensing record as the authority."
        )

    if re.search(r"\btab\b|\btablature\b|\bteach\b|\bhow\s+do\s+i\s+play\b|\blearn\b", q):
        teaching_tab = _steel_guitar_rag_teaching_tab()
        return (
            "I can teach Steel Guitar Rag as a faithful transcription, an E9 adaptation, or a simplified arrangement. The study below is labeled as a compact original teaching version; identify the recording and section when you want note-for-note comparison.\n\n"
            "Use it to learn swing eighths, I-IV-V motion, slides, and clean blocking.\n\n"
            f"{teaching_tab}\n\n"
            "Practice it slowly first. Keep the melody clear, let the bar movement sound intentional, and add ornaments only after the time feels steady."
        )

    if re.search(r"\bvariation|\bversions?\b|\barrangements?\b|\bform\b", q):
        return (
            "Common Steel Guitar Rag variations usually come from arrangement choices, not one fixed modern pedal-steel tab.\n\n"
            "The curated reference describes the famous 1936 Western-swing setting as three distinct 16-bar sections: A, B, and C. Players may adapt it as a lap-steel/non-pedal piece, a C6 steel version, an E9 teaching arrangement, or a more modern solo feature. Listening references in the curated file include Bob Wills/Texas Playboys, Leon McAuliffe, Buddy Emmons, Speedy West, and Merle Travis-related examples."
        )

    if re.search(r"\bwhat\s+key\b|\bkey\s+is\b", q):
        return (
            "“Steel Guitar Rag” is often taught and played in E, but the key can vary by arrangement, player, or band.\n\n"
            "If you are working from a specific recording, chart, or bandstand version, use that version’s key as the authority."
        )

    if "song or the app" in q or ("app" in q and "song" in q):
        return (
            "“Steel Guitar Rag” is a classic steel-guitar tune. This app’s user-facing name is The Turnaround.\n\n"
            "Some project docs may still use Steel Guitar RAG as a technical description, but the song and the app are not the same thing."
        )

    return (
        "“Steel Guitar Rag” is a landmark steel-guitar instrumental tied to Western swing and early electric-steel vocabulary.\n\n"
        "The famous 1936 Bob Wills/Texas Playboys recording featuring Leon McAuliffe helped make it a standard. The tune is useful to study because it combines ragtime bounce, I-IV-V harmony, steel-specific slides and sustain, and a form that goes beyond a single lick."
    )


def _steel_guitar_rag_teaching_tab() -> str:
    reference = load_steel_guitar_rag_reference()
    section_match = re.search(
        r"## 10\. E9 Pedal-Steel Teaching Version: Short Original Study(?P<section>.*?)(?:\n## |\Z)",
        reference,
        re.S,
    )
    section = section_match.group("section") if section_match else reference
    code_match = re.search(r"```text\n.*?\n```", section, re.S)
    if code_match:
        return code_match.group(0)
    return "```text\nSteel Guitar Rag original E9 teaching study unavailable.\n```"
