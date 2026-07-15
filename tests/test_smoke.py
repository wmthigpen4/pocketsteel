from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import rag_app
import rag_search
from rag_common import APP_DISPLAY_NAME


class Context:
    def __init__(self, calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]], name: str, *args: Any) -> None:
        self.calls = calls
        self.name = name
        self.args = args

    def __enter__(self) -> "Context":
        self.calls.append((f"{self.name}.__enter__", self.args, {}))
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.calls.append((f"{self.name}.__exit__", (), {}))


class FakeStreamlit:
    def __init__(self, *, question: str = "", ask: bool = False) -> None:
        self.question = question
        self.ask = ask
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.sidebar = Context(self.calls, "sidebar")

    def _record(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append((name, args, kwargs))

    def set_page_config(self, **kwargs: Any) -> None:
        self._record("set_page_config", **kwargs)

    def title(self, *args: Any, **kwargs: Any) -> None:
        self._record("title", *args, **kwargs)

    def caption(self, *args: Any, **kwargs: Any) -> None:
        self._record("caption", *args, **kwargs)

    def header(self, *args: Any, **kwargs: Any) -> None:
        self._record("header", *args, **kwargs)

    def text_input(self, label: str, value: str = "", **kwargs: Any) -> str:
        self._record("text_input", label, value, **kwargs)
        return value

    def slider(self, label: str, **kwargs: Any) -> int:
        self._record("slider", label, **kwargs)
        return int(kwargs.get("value", kwargs.get("min_value", 0)))

    def text_area(self, *args: Any, **kwargs: Any) -> str:
        self._record("text_area", *args, **kwargs)
        return self.question

    def button(self, *args: Any, **kwargs: Any) -> bool:
        self._record("button", *args, **kwargs)
        return self.ask

    def spinner(self, *args: Any, **kwargs: Any) -> Context:
        self._record("spinner", *args, **kwargs)
        return Context(self.calls, "spinner", *args)

    def warning(self, *args: Any, **kwargs: Any) -> None:
        self._record("warning", *args, **kwargs)

    def markdown(self, *args: Any, **kwargs: Any) -> None:
        self._record("markdown", *args, **kwargs)

    def subheader(self, *args: Any, **kwargs: Any) -> None:
        self._record("subheader", *args, **kwargs)

    def write(self, *args: Any, **kwargs: Any) -> None:
        self._record("write", *args, **kwargs)

    def expander(self, *args: Any, **kwargs: Any) -> Context:
        self._record("expander", *args, **kwargs)
        return Context(self.calls, "expander", *args)


def install_fake_streamlit(monkeypatch: Any, fake: FakeStreamlit) -> None:
    monkeypatch.setitem(sys.modules, "streamlit", fake)


def call_args(fake: FakeStreamlit, name: str) -> list[tuple[Any, ...]]:
    return [args for call_name, args, _kwargs in fake.calls if call_name == name]


def sample_row(text: str = "A forum user suggested checking the guitar ground path first.") -> dict[str, Any]:
    return {
        "text": text,
        "metadata": {
            "forum_name": "Electronics",
            "thread_title": "Hum that goes away when touching changer",
            "source_url": "https://bb.steelguitarforum.com/viewtopic.php?t=123",
            "username": "Alice",
            "post_date": "Mar 12, 2018",
        },
        "distance": 0.12,
        "slug": "electronics",
    }


def test_homepage_loads(monkeypatch: Any) -> None:
    fake = FakeStreamlit()
    install_fake_streamlit(monkeypatch, fake)

    rag_app.main()

    assert any(APP_DISPLAY_NAME in args[0] for args in call_args(fake, "title"))
    assert any(args[0] == "Question" for args in call_args(fake, "text_area"))
    assert any(args[0] == "Ask" for args in call_args(fake, "button"))


def test_user_can_enter_a_question(monkeypatch: Any) -> None:
    fake = FakeStreamlit(question="Why does my amp buzz?", ask=True)
    install_fake_streamlit(monkeypatch, fake)
    captured: dict[str, Any] = {}

    def fake_answer_question(question: str, **kwargs: Any) -> tuple[str, list[dict[str, Any]], bool]:
        captured["question"] = question
        captured["kwargs"] = kwargs
        return "Forum users point to grounding first. [1]", [sample_row()], False

    monkeypatch.setattr(rag_app, "answer_question", fake_answer_question)

    rag_app.main()

    assert captured["question"] == "Why does my amp buzz?"
    assert captured["kwargs"]["forum_name"] == "Electronics"
    assert any(args[0] == "Forum users point to grounding first. [1]" for args in call_args(fake, "markdown"))


def test_search_api_returns_source_results(monkeypatch: Any) -> None:
    class FakeCollection:
        def query(self, **kwargs: Any) -> dict[str, Any]:
            assert kwargs["query_embeddings"] == [[0.1, 0.2, 0.3]]
            assert kwargs["n_results"] == 2
            return {
                "documents": [["Check guitar ground continuity before replacing parts."]],
                "metadatas": [
                    [
                        {
                            "forum_name": "Electronics",
                            "thread_title": "Grounding a pedal steel",
                            "source_url": "https://example.test/thread",
                            "post_dates_raw": '["Mar 12, 2018"]',
                        }
                    ]
                ],
                "distances": [[0.08]],
            }

    monkeypatch.setattr(rag_search, "chroma_collection", lambda *_args, **_kwargs: FakeCollection())
    monkeypatch.setattr(rag_search, "ollama_embed", lambda *_args, **_kwargs: [[0.1, 0.2, 0.3]])

    rows = rag_search.search_chunks("ground buzz", top_k=2)

    assert rows == [
        {
            "text": "Check guitar ground continuity before replacing parts.",
            "metadata": {
                "forum_name": "Electronics",
                "thread_title": "Grounding a pedal steel",
                "source_url": "https://example.test/thread",
                "post_dates_raw": ["Mar 12, 2018"],
            },
            "distance": 0.08,
            "slug": "",
        }
    ]


def test_answer_page_shows_citations(monkeypatch: Any) -> None:
    fake = FakeStreamlit(question="Why does touching the changer reduce hum?", ask=True)
    install_fake_streamlit(monkeypatch, fake)
    monkeypatch.setattr(
        rag_app,
        "answer_question",
        lambda *_args, **_kwargs: ("Check the guitar ground path before replacing parts. [1]", [sample_row()], False),
    )

    rag_app.main()

    assert any("[1]" in args[0] for args in call_args(fake, "markdown"))
    assert any(args[0] == "Retrieved Sources" for args in call_args(fake, "subheader"))
    assert any("Hum that goes away" in args[0] for args in call_args(fake, "expander"))
    assert any("https://bb.steelguitarforum.com/viewtopic.php?t=123" in args[0] for args in call_args(fake, "write"))


def test_empty_result_state_works(monkeypatch: Any) -> None:
    fake = FakeStreamlit(question="What is this unknown part?", ask=True)
    install_fake_streamlit(monkeypatch, fake)
    monkeypatch.setattr(
        rag_app,
        "answer_question",
        lambda *_args, **_kwargs: ("The retrieved forum corpus did not provide enough evidence to answer that reliably.", [], True),
    )

    rag_app.main()

    assert any("did not provide enough evidence" in args[0] for args in call_args(fake, "warning"))
    assert any(args[0] == "No retrieved sources." for args in call_args(fake, "write"))


def test_app_does_not_expose_raw_source_dumps(monkeypatch: Any) -> None:
    raw_source_dump = " ".join(f"raw-source-token-{index}" for index in range(200))
    fake = FakeStreamlit(question="Why does my amp buzz?", ask=True)
    install_fake_streamlit(monkeypatch, fake)
    monkeypatch.setattr(
        rag_app,
        "answer_question",
        lambda *_args, **_kwargs: ("A concise cited answer. [1]", [sample_row(raw_source_dump)], False),
    )

    rag_app.main()

    written_strings = [args[0] for args in call_args(fake, "write") if isinstance(args[0], str)]
    assert raw_source_dump not in written_strings
    assert all(len(value) <= 700 for value in written_strings)
    assert any(value.endswith(" ...") for value in written_strings)


def test_mobile_layout_is_usable() -> None:
    html = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    shell_css = Path("ui/workspace-shell.css").read_text(encoding="utf-8")

    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in html
    assert "@media (max-width: 699px)" in shell_css
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in shell_css
    assert ".home-product-grid" in shell_css and "grid-template-columns: 1fr;" in shell_css
    assert "overflow-x: clip;" in shell_css
    assert ".home-explorer-stage" in shell_css and "overflow-x: auto;" in shell_css
    assert "min-height: 44px;" in shell_css
    assert "background-attachment: scroll;" in shell_css
    assert ".page.is-answering main" in html and "width: calc(100% - 28px);" in html
    assert "textarea {" in html and "min-height: 152px;" in html
