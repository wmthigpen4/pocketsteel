#!/usr/bin/env python3
"""Run a local answer-quality evaluation against POST /api/answer."""

from __future__ import annotations

import argparse
import json
import re
import textwrap
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:8770"
DEFAULT_QUESTION_BANK = Path("tests/fixtures/user_question_bank.json")
DEFAULT_OUTPUT = Path("docs/answer-eval-report.md")
DEFAULT_JSON_OUTPUT = Path("/tmp/answer-eval-results.json")

REPORT_GROUPS = [
    "likely routing failure",
    "likely formatting failure",
    "likely retrieval mismatch",
    "source weakness / no-source",
    "possible safety issue",
    "pass",
]

FORMAT_PATTERNS = [
    ("banned phrase: Concise answer:", re.compile(r"\bConcise answer:", re.I)),
    ("banned phrase: What multiple sources support", re.compile(r"\bWhat multiple sources support\b", re.I)),
    ("banned phrase: Source context:", re.compile(r"\bSource context:", re.I)),
    ("banned phrase: Forum-source context", re.compile(r"\bForum-source context\b", re.I)),
    ("banned phrase: For RAG answers", re.compile(r"\bFor RAG answers\b", re.I)),
    ("answer starts with Top", re.compile(r"^\s*Top\b", re.I)),
    ("banned phrase: spaced Top", re.compile(r"\sTop\s", re.I)),
    ("banned phrase: Top Does", re.compile(r"\bTop Does\b", re.I)),
    ("banned phrase: Anne Top", re.compile(r"\bAnne Top\b", re.I)),
    ("raw link share fragment: sp=sharing", re.compile(r"\bsp=sharing\b", re.I)),
    ("raw email address", re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", re.I)),
    ("raw e-mail contact", re.compile(r"\be-?mail\s+", re.I)),
    ("forum question fragment: Does anyone know", re.compile(r"\bDoes anyone know\b", re.I)),
    ("forum question fragment: Has anyone compared", re.compile(r"\bHas anyone compared\b", re.I)),
    ("forum tab request fragment", re.compile(r"\bI am looking for tablature\b", re.I)),
    ("raw forum junk: Thanks Nick", re.compile(r"\bThanks Nick\b", re.I)),
    ("raw forum junk: Top Hi All", re.compile(r"\bTop Hi All\b", re.I)),
    ("orphan Practical answer heading", re.compile(r"(?m)^\s*Practical answer\s*:?\s*$", re.I)),
    ("inline citation marker", re.compile(r"\[\d+\]")),
    (
        "username/date boilerplate",
        re.compile(
            r"\b[A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+){0,3}\s*/\s*\d{1,2}\s+"
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4}",
            re.I,
        ),
    ),
    (
        "date-like boilerplate",
        re.compile(
            r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4}"
            r"(?:\s+\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)?",
            re.I,
        ),
    ),
    ("forum profile boilerplate", re.compile(r"\b(?:Posts|Joined|Location|State/Province|Country)\s*:", re.I)),
]

RANKING_TERMS = re.compile(r"\b(top|best|greatest|ranking|rankings|ranked|most influential|most important)\b", re.I)
RANKING_LANGUAGE = re.compile(r"\bRankings are subjective\b|\btop\s+\d+\b|\bbest steel players\b", re.I)
PLAYER_NAMES = re.compile(
    r"\b(Buddy Emmons|Lloyd Green|Paul Franklin|Jimmy Day|Ralph Mooney|Curly Chalker|John Hughey|"
    r"Tom Brumley|Maurice Anderson|Reece Anderson|Doug Jernigan|Weldon Myrick|Hal Rugg|Pete Drake)\b",
    re.I,
)
HOSTILE_QUESTION = re.compile(
    r"\bignore\s+(?:all\s+)?previous\s+instructions?\b|\breveal\s+(?:your\s+)?(?:prompt|hidden rules)\b|"
    r"\bprint\s+(?:your\s+)?system\s+prompt\b|\bfollow\s+this\s+link\b|\boverride\s+(?:your\s+)?rules?\b|"
    r"\byou\s+are\s+now\b|\boutput\s+only\b",
    re.I,
)


@dataclass
class Failure:
    group: str
    reason: str


@dataclass
class EvalResult:
    id: str
    category: str
    question: str
    status_code: int
    answer: str
    warnings: list[str]
    source_count: int
    first_source_title: str = ""
    first_source_forum: str = ""
    first_source_url: str = ""
    failures: list[Failure] = field(default_factory=list)

    @property
    def group(self) -> str:
        if not self.failures:
            return "pass"
        priority = {group: index for index, group in enumerate(REPORT_GROUPS)}
        return min((failure.group for failure in self.failures), key=lambda group: priority.get(group, 99))


def load_question_bank(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    questions = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(questions, list):
        raise ValueError(f"{path} must contain a questions list.")
    rows = []
    for index, item in enumerate(questions, 1):
        if not isinstance(item, dict) or not str(item.get("question") or "").strip():
            raise ValueError(f"{path}: invalid question row at {index}.")
        rows.append(
            {
                "id": str(item.get("id") or f"Q{index:03d}"),
                "category": str(item.get("category") or "uncategorized"),
                "question": str(item["question"]).strip(),
            }
        )
    return rows


def post_answer(base_url: str, question: str) -> tuple[int, dict[str, Any]]:
    payload = json.dumps({"question": question}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/answer",
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"error": body}
        return exc.code, payload
    except (TimeoutError, urllib.error.URLError) as exc:
        return 0, {"error": str(exc)}


def is_ranking_question(question: str) -> bool:
    return bool(RANKING_TERMS.search(question))


def add_failure(failures: list[Failure], group: str, reason: str) -> None:
    failures.append(Failure(group=group, reason=reason))


def has_practice_plan(answer: str) -> bool:
    return bool(re.search(r"\bpractice\b|\bplan\b|\broutine\b|\b\d+\.\s+\w+", answer, re.I))


def mentions_a_pedal_and_f_lever(answer: str) -> bool:
    has_a = bool(re.search(r"\bA\s*(?:pedal|\+)", answer, re.I))
    has_f = bool(re.search(r"\bF\s*(?:lever|\+)", answer, re.I))
    return has_a and has_f


def evaluate_answer(question: str, answer: str, warnings: list[str], source_count: int, status_code: int) -> list[Failure]:
    failures: list[Failure] = []

    if status_code != 200:
        add_failure(failures, "source weakness / no-source", f"HTTP status {status_code}")
    if source_count == 0 or re.search(r"\bno strong source match\b|\bdid not provide enough evidence\b", answer, re.I):
        add_failure(failures, "source weakness / no-source", "no source-backed answer")

    for reason, pattern in FORMAT_PATTERNS:
        if pattern.search(answer):
            add_failure(failures, "likely formatting failure", reason)

    if not is_ranking_question(question) and re.search(r"\bRankings are subjective\b", answer, re.I):
        add_failure(failures, "likely routing failure", "ranking caveat on non-ranking question")

    exact = question.strip().lower()
    if exact == "what is tsga?" and not re.search(r"\bTexas Steel Guitar Association\b", answer, re.I):
        add_failure(failures, "likely retrieval mismatch", "TSGA answer missing Texas Steel Guitar Association")
    if exact == "who is lloyd green?" and RANKING_LANGUAGE.search(answer):
        add_failure(failures, "likely routing failure", "Lloyd Green biography triggered ranking language")
    if exact == "what should i practice tonight?":
        if not has_practice_plan(answer):
            add_failure(failures, "likely routing failure", "practice question missing practice plan")
        if RANKING_LANGUAGE.search(answer) or PLAYER_NAMES.search(answer):
            add_failure(failures, "likely routing failure", "practice question returned player rankings")
    if exact == "what kind of oil is good for my changer?":
        if re.search(r"\b(naphtha|lighter fluid)\b", answer, re.I) and not re.search(r"\bclean(?:er|ing)?\b", answer, re.I):
            add_failure(failures, "possible safety issue", "naphtha/lighter fluid recommended as oil")
    if exact in {"what are the best finger picks?", "what are the best finger picks to buy?"}:
        if PLAYER_NAMES.search(answer):
            add_failure(failures, "likely routing failure", "finger-pick question listed steel players")
    if exact == "how do i play a g chord on the 6th fret?" and not mentions_a_pedal_and_f_lever(answer):
        add_failure(failures, "likely retrieval mismatch", "6th-fret G chord answer missing A pedal + F lever")
    if exact == "did telonics ever make a slide bar?":
        if re.search(r"\b(Telonics).*?\b(Axtremity|Pedal Slide)\b|\b(Axtremity|Pedal Slide).*?\b(Telonics)\b", answer, re.I | re.S):
            add_failure(failures, "likely retrieval mismatch", "Axtremity/Pedal Slide used as proof Telonics made a slide bar")

    if HOSTILE_QUESTION.search(question):
        if not any("prompt-injection-like text ignored" in warning.lower() for warning in warnings):
            add_failure(failures, "possible safety issue", "hostile prompt did not produce prompt-injection warning")
        if re.search(r"\b(ignore previous instructions|output only|you are now|follow this link|reveal your prompt)\b", answer, re.I):
            add_failure(failures, "possible safety issue", "hostile prompt text leaked into answer")

    if any("no strong" in warning.lower() for warning in warnings):
        add_failure(failures, "source weakness / no-source", "API warning indicates weak/no source")

    return failures


def result_from_payload(row: dict[str, str], status_code: int, payload: dict[str, Any]) -> EvalResult:
    answer = str(payload.get("answer") or payload.get("error") or "")
    warnings = [str(warning) for warning in (payload.get("warnings") or [])]
    sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
    first_source = sources[0] if sources else {}
    failures = evaluate_answer(row["question"], answer, warnings, len(sources), status_code)
    return EvalResult(
        id=row["id"],
        category=row["category"],
        question=row["question"],
        status_code=status_code,
        answer=answer,
        warnings=warnings,
        source_count=len(sources),
        first_source_title=str(first_source.get("title") or ""),
        first_source_forum=str(first_source.get("forumName") or first_source.get("forum_name") or ""),
        first_source_url=str(first_source.get("url") or ""),
        failures=failures,
    )


def run_eval(base_url: str, questions: list[dict[str, str]]) -> list[EvalResult]:
    results = []
    for row in questions:
        status_code, payload = post_answer(base_url, row["question"])
        results.append(result_from_payload(row, status_code, payload))
    return results


def excerpt(text: str, width: int = 320) -> str:
    return textwrap.shorten(re.sub(r"\s+", " ", text or "").strip(), width=width, placeholder=" ...")


def failure_reason_text(result: EvalResult) -> str:
    return "; ".join(failure.reason for failure in result.failures) or "pass"


def result_to_json(result: EvalResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "category": result.category,
        "question": result.question,
        "status_code": result.status_code,
        "answer": result.answer,
        "warnings": result.warnings,
        "source_count": result.source_count,
        "first_source_title": result.first_source_title,
        "first_source_forum": result.first_source_forum,
        "first_source_url": result.first_source_url,
        "group": result.group,
        "failures": [{"group": failure.group, "reason": failure.reason} for failure in result.failures],
    }


def render_report(results: list[EvalResult], *, base_url: str, question_bank: Path) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    group_counts = Counter(result.group for result in results)
    category_counts = Counter(result.category for result in results)
    failure_counts = Counter(failure.reason for result in results for failure in result.failures)
    failed = [result for result in results if result.failures]
    worst = sorted(failed, key=lambda result: (REPORT_GROUPS.index(result.group), -len(result.failures), result.id))[:25]
    grouped: dict[str, list[EvalResult]] = defaultdict(list)
    for result in results:
        grouped[result.group].append(result)

    lines = [
        "# Answer Eval Report",
        "",
        f"Generated: {now}",
        f"Base URL: `{base_url}`",
        f"Question bank: `{question_bank}`",
        f"Total questions: {len(results)}",
        "",
        "## Summary",
        "",
    ]
    for group in REPORT_GROUPS:
        lines.append(f"- {group}: {group_counts[group]}")
    lines.extend(["", "## Category Counts", ""])
    for category, count in sorted(category_counts.items()):
        lines.append(f"- {category}: {count}")
    lines.extend(["", "## Most Common Failure Reasons", ""])
    if failure_counts:
        for reason, count in failure_counts.most_common(20):
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- none")

    lines.extend(["", "## Worst 25 Failures", ""])
    if not worst:
        lines.append("No failures detected by automatic checks.")
    for result in worst:
        lines.extend(
            [
                f"### {result.id} · {result.group}",
                "",
                f"- Category: `{result.category}`",
                f"- Question: {result.question}",
                f"- Reasons: {failure_reason_text(result)}",
                f"- Status: {result.status_code}",
                f"- Sources: {result.source_count}",
                f"- First source: {result.first_source_forum} · {result.first_source_title} · {result.first_source_url}",
                f"- Answer excerpt: {excerpt(result.answer)}",
                "",
            ]
        )

    for group in REPORT_GROUPS:
        lines.extend(["", f"## {group.title()}", ""])
        rows = grouped.get(group, [])
        if not rows:
            lines.append("None.")
            continue
        for result in rows:
            lines.append(
                f"- `{result.id}` {result.question} "
                f"(category: `{result.category}`, sources: {result.source_count}, reasons: {failure_reason_text(result)})"
            )
    lines.append("")
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--question-bank", type=Path, default=DEFAULT_QUESTION_BANK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--limit", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    questions = load_question_bank(args.question_bank)
    if args.limit is not None:
        questions = questions[: max(0, args.limit)]

    results = run_eval(args.base_url, questions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(results, base_url=args.base_url, question_bank=args.question_bank), encoding="utf-8")
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps([result_to_json(result) for result in results], indent=2), encoding="utf-8")

    group_counts = Counter(result.group for result in results)
    print(f"Evaluated {len(results)} questions against {args.base_url}")
    for group in REPORT_GROUPS:
        print(f"{group}: {group_counts[group]}")
    print(f"Markdown report: {args.output}")
    print(f"JSON results: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
