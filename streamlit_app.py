"""Streamlit Cloud entrypoint — uses the same service layer as the FastAPI backend."""

from __future__ import annotations

import os
from contextlib import contextmanager

import streamlit as st

_SECRET_KEYS = (
    "DATABASE_URL",
    "REDIS_URL",
    "GOOGLE_API_KEY",
    "GEMINI_ENRICHMENT_MODEL",
    "GEMINI_RAG_MODEL",
    "GEMINI_EMBEDDING_MODEL",
    "VECTOR_DIMENSION",
    "REQUIRE_ADMIN_API_KEY",
)


def _bootstrap_secrets() -> None:
    """Map Streamlit Cloud secrets into env vars before settings/database import."""
    try:
        secrets = st.secrets
    except Exception:
        return
    for key in _SECRET_KEYS:
        if key in secrets:
            os.environ[key] = str(secrets[key])


_bootstrap_secrets()

from config.settings import get_settings  # noqa: E402

get_settings.cache_clear()

from src.cache.insight_cache import insight_list_cache  # noqa: E402
from src.insights.schemas import VALID_INSIGHT_TYPES  # noqa: E402
from src.insights.service import InsightService  # noqa: E402
from src.rag.schemas import AskRequest  # noqa: E402
from src.rag.service import RagService  # noqa: E402
from src.retrieval.schemas import SearchFilters, SearchQuery  # noqa: E402
from src.retrieval.semantic_search import SemanticSearchService  # noqa: E402
from src.security.sanitize import sanitize_query  # noqa: E402
from src.storage.database import SessionLocal, check_db_connection  # noqa: E402
from src.storage.models import InsightCache  # noqa: E402


@contextmanager
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


st.set_page_config(
    page_title="Review Discovery Engine",
    page_icon="🎧",
    layout="wide",
)

st.title("Review Discovery Engine")
st.caption("Spotify review research — semantic search, RAG Q&A, and insights")

with st.sidebar:
    st.subheader("Status")
    if check_db_connection():
        st.success("Database connected")
    else:
        st.error("Database unreachable — check `DATABASE_URL` in Streamlit secrets")
    if get_settings().google_api_key and get_settings().google_api_key != "placeholder":
        st.success("Gemini API key set")
    else:
        st.warning("Set `GOOGLE_API_KEY` in Streamlit secrets for Ask/search")

tab_search, tab_ask, tab_insights = st.tabs(["Search", "Ask", "Insights"])

with tab_search:
    st.subheader("Semantic Search")
    query = st.text_input("Search query", placeholder="e.g. users complaining about shuffle")
    col1, col2, col3 = st.columns(3)
    with col1:
        platform = st.text_input("Platform filter", value="")
    with col2:
        sentiment = st.selectbox(
            "Sentiment",
            options=["", "positive", "negative", "neutral", "mixed"],
            format_func=lambda x: x or "Any",
        )
    with col3:
        min_rating = st.number_input("Min rating", min_value=1, max_value=5, value=1)
    top_k = st.slider("Results", min_value=5, max_value=30, value=10)

    if st.button("Search", type="primary", key="search_btn"):
        cleaned = sanitize_query(query)
        if not cleaned:
            st.error("Enter a search query.")
        else:
            filters = SearchFilters(
                platform=platform or None,
                sentiment=sentiment or None,
                min_rating=min_rating if min_rating > 1 else None,
            )
            with db_session() as db:
                service = SemanticSearchService(db)
                try:
                    results = service.search(cleaned, filters, top_k=top_k, hybrid=True)
                except ValueError as exc:
                    st.error(str(exc))
                    results = []

            st.write(f"**{len(results)}** results for: _{cleaned}_")
            for item in results:
                with st.expander(
                    f"★ {item.rating or '—'} · {item.platform} · score {item.score:.2f}",
                    expanded=False,
                ):
                    st.write(item.excerpt)
                    if item.summary:
                        st.info(item.summary)
                    st.caption(
                        f"ID: `{item.review_id}` · {item.review_date} · "
                        f"sentiment: {item.sentiment or '—'}"
                    )

with tab_ask:
    st.subheader("Ask a Question (RAG)")
    question = st.text_area(
        "Question",
        placeholder="What are the top complaints about Spotify's free tier?",
        height=100,
    )
    ask_top_k = st.slider("Evidence reviews", min_value=5, max_value=25, value=15, key="ask_top_k")

    if st.button("Get Answer", type="primary", key="ask_btn"):
        cleaned = sanitize_query(question)
        if not cleaned:
            st.error("Enter a question.")
        else:
            with st.spinner("Retrieving evidence and generating answer…"):
                with db_session() as db:
                    service = RagService(db)
                    try:
                        response = service.ask(
                            AskRequest(question=cleaned, top_k=ask_top_k, include_insights=True)
                        )
                    except ValueError as exc:
                        st.error(str(exc))
                        response = None

            if response:
                confidence_color = {
                    "high": "green",
                    "medium": "orange",
                    "low": "red",
                }.get(response.confidence, "gray")
                st.markdown(f"**Confidence:** :{confidence_color}[{response.confidence}]")
                st.markdown(response.answer)
                if response.related_insights:
                    st.markdown("**Related insights:** " + ", ".join(response.related_insights))
                st.markdown(f"**Citations** ({response.retrieval_count} reviews retrieved)")
                for cite in response.citations:
                    with st.expander(f"{cite.source} · relevance {cite.relevance_score:.2f}"):
                        st.write(cite.excerpt)
                        st.caption(f"Review ID: `{cite.review_id}`")

with tab_insights:
    st.subheader("Cached Insights")
    refresh = st.button("Refresh from database")

    with db_session() as db:
        if refresh:
            insight_list_cache.invalidate()
        cached = insight_list_cache.get()
        if cached:
            rows = cached.get("insights", [])
        else:
            db_rows = (
                db.query(InsightCache)
                .order_by(InsightCache.insight_type.asc(), InsightCache.generated_at.desc())
                .all()
            )
            rows = [
                {
                    "insight_type": row.insight_type,
                    "title": row.title,
                    "summary": row.summary,
                    "metrics": row.metrics or {},
                    "generated_at": row.generated_at.isoformat(),
                }
                for row in db_rows
            ]

    if not rows:
        st.info(
            "No cached insights yet. Run insight generation locally, "
            "or pick a type below to generate one."
        )
    else:
        for item in rows:
            with st.expander(item["title"], expanded=False):
                st.write(item["summary"])
                if item.get("metrics"):
                    st.json(item["metrics"])
                st.caption(f"Type: {item['insight_type']} · {item['generated_at']}")

    st.divider()
    st.markdown("**Generate a single insight** (uses Gemini quota)")
    insight_type = st.selectbox("Insight type", options=sorted(VALID_INSIGHT_TYPES))
    if st.button("Generate", key="gen_insight"):
        with st.spinner(f"Generating {insight_type}…"):
            with db_session() as db:
                service = InsightService(db)
                try:
                    insight = service.generate(insight_type)
                except Exception as exc:
                    st.error(str(exc))
                    insight = None
            if insight:
                st.success(insight.title)
                st.write(insight.summary)
                if insight.metrics:
                    st.json(insight.metrics)
