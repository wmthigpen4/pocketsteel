#!/usr/bin/env python3
"""Streamlit app for Steel Guitar RAG Electronics RAG v0."""

from __future__ import annotations

import os

from rag_answer import answer_question
from rag_common import APP_DISPLAY_NAME, DEFAULT_CHAT_MODEL, DEFAULT_EMBEDDING_MODEL, excerpt


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise SystemExit("Missing dependency: streamlit. Install it with `pip install streamlit`.") from exc

    st.set_page_config(page_title=f"{APP_DISPLAY_NAME} RAG v0", layout="wide")
    st.title(f"{APP_DISPLAY_NAME} RAG v0")
    st.caption("Electronics forum only")

    with st.sidebar:
        st.header("Filters")
        forum_name = st.text_input("Forum name", value="Electronics")
        date_filter = st.text_input("Date contains", placeholder="e.g. 2015 or 14 Mar 2015")
        thread_title = st.text_input("Thread title contains")
        top_k = st.slider("Retrieved chunks", min_value=3, max_value=12, value=6)
        embedding_model = st.text_input("Embedding model", value=os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL))
        chat_model = st.text_input("Chat model", value=os.environ.get("CHAT_MODEL", DEFAULT_CHAT_MODEL))

    question = st.text_area("Question", placeholder="Why does my amp buzz until I touch the changer?", height=100)
    ask = st.button("Ask", type="primary", disabled=not question.strip())

    if ask:
        with st.spinner("Retrieving sources and asking the local model..."):
            answer, rows, weak = answer_question(
                question,
                top_k=top_k,
                chroma_path="rag-data/electronics/chroma",
                collection_name="electronics",
                model=embedding_model,
                chat_model=chat_model,
                forum_name=forum_name.strip() or None,
                thread_title=thread_title.strip() or None,
                date=date_filter.strip() or None,
            )
        if weak:
            st.warning(answer)
        else:
            st.markdown(answer)

        st.subheader("Retrieved Sources")
        if not rows:
            st.write("No retrieved sources.")
        for index, row in enumerate(rows, 1):
            metadata = row["metadata"]
            title = metadata.get("thread_title") or "(untitled thread)"
            url = metadata.get("source_url") or metadata.get("thread_url") or ""
            user = metadata.get("username") or ""
            date = metadata.get("post_date") or metadata.get("post_date_raw") or ""
            with st.expander(f"{index}. {title}", expanded=True):
                st.write(url)
                if user or date:
                    st.caption(f"{user} {date}".strip())
                st.write(excerpt(row["text"], width=700))


if __name__ == "__main__":
    main()
