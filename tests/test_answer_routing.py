from __future__ import annotations

from steel_guitar_rag.answer_routing import (
    contextual_entity_probe_question,
    corpus_promoted_decision,
    entity_anchors,
    evaluate_corpus_entity_evidence,
    is_corpus_entity_candidate,
    select_answer_route,
)


GUARDED_UNKNOWN = {
    "domain": "off_domain",
    "intent": "unknown",
    "needs_sources": False,
    "needs_fretboard": False,
    "needs_copedent": False,
    "retrieval_allowed": False,
    "allowed_answer_shape": "guardrail_refusal",
}


def sgf_result(title: str, excerpt: str, thread_id: str) -> dict[str, object]:
    return {
        "thread_title": title,
        "excerpt": excerpt,
        "thread_id": thread_id,
        "thread_url": f"https://bb.steelguitarforum.com/viewtopic.php?t={thread_id}",
        "source_system": "sgf_phpbb_current",
    }


def test_unknown_person_and_product_are_corpus_candidates_without_name_whitelist() -> None:
    assert is_corpus_entity_candidate("Who is Travis Toy?", GUARDED_UNKNOWN)
    assert entity_anchors("Who is Travis Toy?") == ("travis", "toy")
    assert is_corpus_entity_candidate("What is Acme Steel Lessons?", GUARDED_UNKNOWN)


def test_contextual_entity_probe_uses_prior_user_question_not_assistant_claim() -> None:
    context = [
        "User: Who is Travis Toy?",
        "Assistant: Travis Toy is a pedal-steel guitarist.",
    ]

    assert contextual_entity_probe_question(
        "What is he especially known for?", context
    ) == "Who is Travis Toy?"
    assert contextual_entity_probe_question(
        "What is he especially known for?",
        ["Assistant: Travis Toy is a pedal-steel guitarist."],
    ) is None


def test_public_player_relation_establishes_context_without_name_whitelist() -> None:
    evidence = evaluate_corpus_entity_evidence(
        "Who is Acme Person?",
        [
            sgf_result(
                "Patty Loveless tour",
                "Acme Person, who plays steel and dobro, joined the touring band.",
                "303",
            )
        ],
    )

    assert evidence.strong is True


def test_private_placeholder_is_never_a_corpus_entity_candidate() -> None:
    assert not is_corpus_entity_candidate("Who is <private_player>?", GUARDED_UNKNOWN)


def test_exact_public_sgf_match_establishes_steel_context() -> None:
    evidence = evaluate_corpus_entity_evidence(
        "Who is Travis Toy?",
        [
            sgf_result(
                "Travis Toy interview",
                "Travis Toy discusses pedal steel technique and touring.",
                "101",
            )
        ],
    )

    assert evidence.strong is True
    assert evidence.reason == "exact_sgf_match"
    assert evidence.distinct_threads == 1


def test_repeated_partial_sgf_matches_establish_product_context() -> None:
    evidence = evaluate_corpus_entity_evidence(
        "What is Acme Player Course?",
        [
            sgf_result("Acme course", "The Player curriculum starts with grips.", "101"),
            sgf_result("Player lessons", "Members compared the Acme material.", "202"),
        ],
    )

    assert evidence.strong is True
    assert evidence.reason == "repeated_sgf_matches"


def test_non_sgf_or_single_weak_match_does_not_establish_context() -> None:
    evidence = evaluate_corpus_entity_evidence(
        "Who is Taylor Swift?",
        [
            {
                "thread_title": "Taylor Swift",
                "excerpt": "Pop artist biography.",
                "thread_url": "https://example.com/taylor",
            },
            sgf_result("Unrelated singer thread", "A Taylor guitar was mentioned.", "303"),
        ],
    )

    assert evidence.strong is False


def test_promoted_tutorial_uses_source_backed_lesson_route() -> None:
    decision = corpus_promoted_decision("What is Travis Toy Tutorials?")

    assert decision["domain"] == "steel_guitar"
    assert decision["intent"] == "lesson_lookup"
    assert select_answer_route(decision) == "source_backed_rag"
    assert select_answer_route(decision, deterministic_available=True) == "hybrid"


def test_three_public_routes_are_explicit() -> None:
    deterministic = {
        **GUARDED_UNKNOWN,
        "domain": "steel_guitar",
        "intent": "copedent_position",
        "allowed_answer_shape": "copedent_position",
    }
    source_backed = corpus_promoted_decision("Who is Example Player?")

    assert select_answer_route(deterministic) == "deterministic"
    assert select_answer_route(source_backed) == "source_backed_rag"
    assert select_answer_route(source_backed, deterministic_available=True) == "hybrid"
    assert select_answer_route(GUARDED_UNKNOWN) == "guardrail"
