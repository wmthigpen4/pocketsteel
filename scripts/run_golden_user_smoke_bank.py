#!/usr/bin/env python3
"""Validate and score the golden adversarial user-smoke bank."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BANK = ROOT / "evals" / "golden_user_smoke_bank.yaml"

REQUIRED_PROMPT_KEYS = {
    "id",
    "category",
    "prompt",
    "expected_intent",
    "direct_answer_required",
    "requires_fretboard",
    "allow_source_cards",
    "allow_sgf_answer_body",
    "required_terms",
    "forbidden_terms",
    "severity_if_fail",
    "notes",
}
EXPECTED_GATES = {
    "SGF leakage",
    "direct answer first",
    "intent recognition",
    "fretboard expected/present",
    "source-card appropriateness",
    "off-domain guardrail",
    "web-required handling",
    "internal wording leakage",
}
INTERNAL_WORDING_TERMS = {"deterministic map", "rules engine", "payload", "classifier", "contract"}
SGF_FRAGMENT_RE = re.compile(
    r"(?:"
    r"Can someone please tell me|I know when I first started|lolol Thank God|"
    r"you desire more information|have a couple of students|beyond simply facilitating|"
    r"Further he went on to state|You can also build a 7 string instrument|"
    r"It seems that playing steel guitar has a lot in common|"
    r"^\s*-\s*(?:I|I've|I'm|We|My|Our|One\s+time)\b|"
    r"\b(?:forum thread|source support was weak|limited source support|treat it as a clue rather than consensus)\b"
    r")",
    re.I | re.M,
)
DIRECTNESS_BAD_START_RE = re.compile(
    r"^\s*(?:I found|The retrieved|Retrieved|Source|Forum|One related point|Related source detail|It depends)\b",
    re.I,
)
GUARDRAIL_TERMS_RE = re.compile(r"\b(?:steel guitar|pedal steel|I can help with|not something I can|outside)\b", re.I)
WEB_REQUIRED_RE = re.compile(r"\b(?:current|today|latest|right now|web|verify|up to date)\b", re.I)


@dataclass(frozen=True)
class GoldenPrompt:
    id: str
    category: str
    prompt: str
    expected_intent: str
    direct_answer_required: bool
    requires_fretboard: bool
    allow_source_cards: bool
    allow_sgf_answer_body: bool
    required_terms: tuple[str, ...] = field(default_factory=tuple)
    forbidden_terms: tuple[str, ...] = field(default_factory=tuple)
    severity_if_fail: str = "P1"
    notes: str = ""


@dataclass(frozen=True)
class GateFinding:
    gate: str
    severity: str
    message: str


def load_bank(path: Path = DEFAULT_BANK) -> tuple[dict[str, Any], list[GoldenPrompt]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("golden smoke bank must be a YAML mapping")
    prompt_rows = raw.get("prompts")
    if not isinstance(prompt_rows, list):
        raise ValueError("golden smoke bank must include a prompts list")
    report_gates = set(raw.get("global_rules", {}).get("report_gates", []))
    missing_gates = EXPECTED_GATES - report_gates
    if missing_gates:
        raise ValueError(f"golden smoke bank missing report gates: {sorted(missing_gates)}")

    prompts: list[GoldenPrompt] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(prompt_rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"prompt row {index} must be a mapping")
        missing = REQUIRED_PROMPT_KEYS - row.keys()
        if missing:
            raise ValueError(f"prompt row {index} missing keys: {sorted(missing)}")
        if row["id"] in seen_ids:
            raise ValueError(f"duplicate prompt id: {row['id']}")
        seen_ids.add(row["id"])
        prompts.append(
            GoldenPrompt(
                id=str(row["id"]),
                category=str(row["category"]),
                prompt=str(row["prompt"]),
                expected_intent=str(row["expected_intent"]),
                direct_answer_required=bool(row["direct_answer_required"]),
                requires_fretboard=bool(row["requires_fretboard"]),
                allow_source_cards=bool(row["allow_source_cards"]),
                allow_sgf_answer_body=bool(row["allow_sgf_answer_body"]),
                required_terms=tuple(str(term) for term in row.get("required_terms", [])),
                forbidden_terms=tuple(str(term) for term in row.get("forbidden_terms", [])),
                severity_if_fail=str(row.get("severity_if_fail") or "P1"),
                notes=str(row.get("notes") or ""),
            )
        )
    if not 250 <= len(prompts) <= 300:
        raise ValueError(f"golden smoke bank must contain 250-300 prompts; found {len(prompts)}")
    return raw, prompts


def mutate_prompt(prompt: str) -> list[str]:
    """Return deterministic natural-language variants for selected golden prompts."""
    variants = {
        prompt,
        prompt.lower(),
        prompt.rstrip("?") + " please?",
        "Hey, " + prompt[0].lower() + prompt[1:],
        prompt.rstrip("?") + "!",
    }
    replacements = [
        ("How do I play", "Where can I find"),
        ("Where can I play", "What frets give me"),
        ("Show me", "What does it look like when you show me"),
        ("chord", "chrd"),
        ("flat", "b"),
        ("sharp", "#"),
    ]
    for old, new in replacements:
        if old in prompt:
            variants.add(prompt.replace(old, new, 1))
    if re.search(r"\b[A-G]#", prompt):
        variants.add(prompt.replace("#", " sharp"))
    if re.search(r"\b[A-G]b\b", prompt):
        variants.add(prompt.replace("b", " flat", 1))
    if "?" in prompt:
        variants.add(prompt.replace("?", "??"))
    return sorted(variants)


def _payload_answer(payload: dict[str, Any]) -> str:
    return str(payload.get("answer") or payload.get("text") or payload.get("response", {}).get("answer") or "")


def _payload_sources(payload: dict[str, Any]) -> list[Any]:
    sources = payload.get("sources")
    if sources is None and isinstance(payload.get("response"), dict):
        sources = payload["response"].get("sources")
    return sources if isinstance(sources, list) else []


def _payload_fretboard(payload: dict[str, Any]) -> Any:
    if "fretboard" in payload:
        return payload.get("fretboard")
    if isinstance(payload.get("response"), dict):
        return payload["response"].get("fretboard")
    return None


def score_payload(prompt: GoldenPrompt, payload: dict[str, Any]) -> list[GateFinding]:
    answer = _payload_answer(payload)
    answer_lower = answer.lower()
    sources = _payload_sources(payload)
    fretboard = _payload_fretboard(payload)
    findings: list[GateFinding] = []

    forbidden_hits = [term for term in prompt.forbidden_terms if term.lower() in answer_lower]
    if not prompt.allow_sgf_answer_body and (forbidden_hits or SGF_FRAGMENT_RE.search(answer)):
        findings.append(
            GateFinding("SGF leakage", prompt.severity_if_fail, f"answer body contains SGF/forum leakage: {forbidden_hits[:3]}")
        )
    internal_hits = [term for term in INTERNAL_WORDING_TERMS if term in answer_lower]
    if internal_hits:
        findings.append(GateFinding("internal wording leakage", "P1", f"answer leaked internal wording: {sorted(internal_hits)}"))
    if prompt.direct_answer_required and DIRECTNESS_BAD_START_RE.search(answer):
        findings.append(GateFinding("direct answer first", prompt.severity_if_fail, "answer starts with source framing instead of a direct answer"))
    missing_terms = [term for term in prompt.required_terms if term.lower() not in answer_lower]
    if missing_terms:
        findings.append(GateFinding("intent recognition", prompt.severity_if_fail, f"answer missing required terms: {missing_terms[:5]}"))
    if prompt.requires_fretboard and not fretboard:
        findings.append(GateFinding("fretboard expected/present", prompt.severity_if_fail, "expected fretboard payload is missing"))
    if not prompt.requires_fretboard and fretboard:
        findings.append(GateFinding("fretboard expected/present", "P2", "fretboard payload appeared where it was not expected"))
    if not prompt.allow_source_cards and sources:
        findings.append(GateFinding("source-card appropriateness", prompt.severity_if_fail, "source cards appeared where they are not allowed"))
    if prompt.category == "off-domain guardrails" and (sources or fretboard or not GUARDRAIL_TERMS_RE.search(answer)):
        findings.append(GateFinding("off-domain guardrail", "P1", "off-domain answer did not cleanly guardrail without sources/fretboard"))
    if prompt.category == "web-required/current-info prompts" and (sources or fretboard or not WEB_REQUIRED_RE.search(answer)):
        findings.append(GateFinding("web-required handling", "P1", "web/current-info answer did not clearly require current verification"))
    return findings


def score_responses(prompts: list[GoldenPrompt], responses: dict[str, dict[str, Any]]) -> dict[str, Any]:
    by_id = {prompt.id: prompt for prompt in prompts}
    results = []
    gate_counts: Counter[str] = Counter()
    for prompt_id, payload in responses.items():
        if prompt_id not in by_id:
            raise ValueError(f"response references unknown prompt id: {prompt_id}")
        findings = score_payload(by_id[prompt_id], payload)
        for finding in findings:
            gate_counts[finding.gate] += 1
        results.append(
            {
                "id": prompt_id,
                "prompt": by_id[prompt_id].prompt,
                "status": "pass" if not findings else "fail",
                "findings": [finding.__dict__ for finding in findings],
            }
        )
    return {
        "total_scored": len(results),
        "pass_count": sum(1 for result in results if result["status"] == "pass"),
        "fail_count": sum(1 for result in results if result["status"] == "fail"),
        "gate_counts": dict(gate_counts),
        "results": results,
    }


def load_response_file(path: Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "responses" in raw:
        raw = raw["responses"]
    if isinstance(raw, list):
        return {str(item["id"]): dict(item.get("payload") or item) for item in raw}
    if isinstance(raw, dict):
        return {str(key): dict(value) for key, value in raw.items()}
    raise ValueError("responses JSON must be an object, a {responses: ...} object, or a list of id/payload rows")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument("--responses", type=Path, help="Optional JSON response payloads keyed by golden prompt id.")
    parser.add_argument("--json-output", type=Path, help="Optional output path for gate-level JSON results.")
    parser.add_argument("--print-variants", action="store_true", help="Print deterministic prompt variants for the first 20 prompts.")
    args = parser.parse_args(argv)

    bank, prompts = load_bank(args.bank)
    categories = Counter(prompt.category for prompt in prompts)
    print(f"Loaded {len(prompts)} golden prompts across {len(categories)} categories from {args.bank}")
    for category, count in sorted(categories.items()):
        print(f"- {category}: {count}")

    if args.print_variants:
        for prompt in prompts[:20]:
            print(f"{prompt.id}: {mutate_prompt(prompt.prompt)}")

    if args.responses:
        report = score_responses(prompts, load_response_file(args.responses))
        print("Gate results:")
        for gate, count in sorted(report["gate_counts"].items()):
            print(f"- {gate}: {count}")
        print(f"Pass: {report['pass_count']}  Fail: {report['fail_count']}")
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    elif args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(
                {
                    "total_prompts": len(prompts),
                    "category_counts": dict(sorted(categories.items())),
                    "report_gates": bank.get("global_rules", {}).get("report_gates", []),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
