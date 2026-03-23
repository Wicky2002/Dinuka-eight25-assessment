import json
import os

import pandas as pd
import plotly.express as px
import streamlit as st

from app.models import AIAnalysis, ScrapedMetrics
from app.services.ai_analyzer import AIAnalyzer
from app.services.scraper import WebScraper


st.set_page_config(page_title="AI Website Audit Tool", layout="wide")

st.markdown(
    """
<style>
[data-testid="metric-container"] {
  background: #1E1E1E;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
}
</style>
""",
    unsafe_allow_html=True,
)

st.title("AI-Powered Website Audit")
st.write("Lightweight, structured insights grounded in real page metrics.")

url_input = st.text_input("Website URL", placeholder="https://example.com")
run_clicked = st.button("Run Audit", type="primary", width="stretch")


def _normalize_url(raw_url: str) -> str:
    if raw_url.startswith("http://") or raw_url.startswith("https://"):
        return raw_url
    return f"https://{raw_url}"


if run_clicked and url_input:
    url = _normalize_url(url_input.strip())
    scraper = WebScraper()

    try:
        with st.spinner("Extracting factual metrics..."):
            result = scraper.extract_metrics(url)
    except Exception as exc:
        st.error(f"Scrape failed: {exc}")
        st.stop()

    page_text = str(result.pop("page_text", ""))
    metrics = ScrapedMetrics.model_validate(result)

    analyzer = AIAnalyzer()
    try:
        with st.spinner("Running AI analysis..."):
            analysis: AIAnalysis = analyzer.analyze(metrics.model_dump(), page_text)
    except Exception as exc:
        st.error(f"AI analysis failed: {exc}")
        st.stop()

    tabs = st.tabs(
        [
            "📊 Factual Metrics",
            "🧠 AI Insights & Action Plan",
            "🚀 Growth Projection",
            "🛠️ AI Orchestration (Logs)",
        ]
    )

    with tabs[0]:
        st.subheader("Factual Metrics")
        row1 = st.columns(4)
        row1[0].metric("Word Count", metrics.word_count)
        row1[1].metric("H1 Count", metrics.h1_count)
        row1[2].metric("H2 Count", metrics.h2_count)
        row1[3].metric("H3 Count", metrics.h3_count)

        row2 = st.columns(4)
        row2[0].metric("CTA Count", metrics.cta_count)
        row2[1].metric("Internal Links", metrics.internal_links)
        row2[2].metric("External Links", metrics.external_links)
        row2[3].metric("Image Count", metrics.image_count)

        row3 = st.columns(4)
        row3[0].metric("Missing Alt Text %", f"{metrics.missing_alt_text_percent}%")
        row3[1].metric("Meta Title Length", len(metrics.meta_title or ""))
        row3[2].metric("Meta Description Length", len(metrics.meta_description or ""))
        row3[3].metric("Total Links", metrics.internal_links + metrics.external_links)

        st.info(
            f"**Meta Title:** {metrics.meta_title or '(None)'}\n\n"
            f"**Meta Description:** {metrics.meta_description or '(None)'}"
        )

    with tabs[1]:
        st.subheader("Recommendations")
        if analysis.recommendations:
            for rec in analysis.recommendations:
                block = (
                    f"**Issue:** {rec.issue}\n\n"
                    f"**Action:** {rec.action}\n\n"
                    f"**Reasoning:** {rec.reasoning}\n\n"
                    f"**Expected Impact:** {rec.expected_impact}"
                )
                if rec.priority == "High":
                    st.error(block)
                elif rec.priority == "Medium":
                    st.warning(block)
                else:
                    st.success(block)
        else:
            st.write("No recommendations returned.")

        with st.expander("Detailed Insights", expanded=False):
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown(f"**SEO Structure:** {analysis.seo_structure}")
                st.markdown(f"**Messaging Clarity:** {analysis.messaging_clarity}")
                st.markdown(f"**CTA Usage:** {analysis.cta_usage}")
            with col_right:
                st.markdown(f"**Content Depth:** {analysis.content_depth}")
                st.markdown(f"**UX Concerns:** {analysis.ux_concerns}")

    with tabs[2]:
        st.subheader("Growth Projection")
        score_data = pd.DataFrame(
            {
                "Category": ["SEO", "UX"],
                "Current": [
                    analysis.scores.current_seo_score,
                    analysis.scores.current_ux_score,
                ],
                "Potential": [
                    analysis.scores.potential_seo_score,
                    analysis.scores.potential_ux_score,
                ],
            }
        )
        chart = px.bar(
            score_data,
            x="Category",
            y=["Current", "Potential"],
            barmode="group",
            range_y=[0, 100],
            title="Current vs Potential Scores",
        )
        st.plotly_chart(chart, width="stretch")

    with tabs[3]:
        st.subheader("AI Orchestration (Logs)")
        log_path = os.path.join("logs", "prompt_logs.json")
        if not os.path.exists(log_path):
            st.info("No prompt logs found yet. Run an analysis to generate them.")
        else:
            try:
                with open(log_path, "r", encoding="utf-8") as handle:
                    logs = json.load(handle)
            except (json.JSONDecodeError, OSError):
                logs = []

            if not logs:
                st.info("Prompt logs are empty. Run an analysis to generate entries.")
            else:
                latest = logs[-1]
                st.info(latest.get("system_prompt", "(Missing system prompt)"))
                st.code(latest.get("user_prompt", ""), language="markdown")
                st.code(latest.get("raw_json_output", ""), language="json")
