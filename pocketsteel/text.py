"""Text cleanup and chunking helpers for SGF corpus records."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser


BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "dd",
    "div",
    "dl",
    "dt",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def strip_html(value: str) -> str:
    """Convert a small HTML fragment to plain text using only the stdlib."""
    if "<" not in value or ">" not in value:
        return html.unescape(value)

    parser = _HTMLTextExtractor()
    try:
        parser.feed(value)
        parser.close()
        return html.unescape(parser.text())
    except Exception:
        return html.unescape(re.sub(r"<[^>]+>", " ", value))


def normalize_text(value: object) -> str:
    """Normalize SGF text while preserving paragraph breaks."""
    if value is None:
        return ""

    text = strip_html(str(value))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def compact_text(value: object) -> str:
    """Normalize text to a single line for metadata fields."""
    return re.sub(r"\s+", " ", normalize_text(value)).strip()


def split_paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()]


def split_sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return []
    return [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", compact)
        if part.strip()
    ]


def shorten(text: str, max_chars: int) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact
    cut = compact[: max_chars - 1].rsplit(" ", 1)[0]
    return f"{cut}..."

