**Live Demo:** TODO - Add deployed URL

# AI Website Audit Tool

A lightweight AI-powered website audit tool designed for structured, grounded analysis of marketing and UX signals.

## Architecture Overview

- **Extraction Layer**: [app/services/scraper.py](app/services/scraper.py) uses requests + BeautifulSoup to collect factual metrics (word count, headings, CTA count, link counts, images, meta tags) and visible page text.
- **AI Layer**: [app/services/ai_analyzer.py](app/services/ai_analyzer.py) consumes only the extracted facts and text. It uses Gemini with a strict JSON schema to avoid hallucination and to return structured insights.
- **UI Layer**: [app_ui.py](app_ui.py) provides a clean Streamlit interface that runs the scraper, displays metrics, and renders AI insights and recommendations.

## Key Features

- Predictive Impact Scoring with Plotly charts (current vs potential SEO/UX).
- 4-Tab Enterprise Dashboard layout (Metrics, Insights, Growth, Logs).
- Transparent Prompt Logging with full system/user prompts and raw model output.

## AI Design Decisions

- **Pydantic schemas** ([app/models.py](app/models.py)) enforce strict structure for both scraped metrics and AI responses.
- **Schema-forced JSON** via `responseMimeType` and `responseSchema` makes the model produce a validated, typed response rather than free-form text.
- **No hallucinations**: the system prompt explicitly instructs the model to ground every insight and recommendation in the provided metrics and page text.

## Trade-Offs

- **BeautifulSoup vs Playwright**: BeautifulSoup is fast and lightweight, but it only sees server-rendered HTML. JavaScript-heavy sites may hide content that a browser engine like Playwright could render.
- **Text truncation**: The page text is truncated before sending to the model for performance and token safety.

## Run Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure `GEMINI_API_KEY` is set in your `.env` file.
3. Start the app:
   ```bash
   streamlit run app_ui.py
   ```
4. Open the provided local URL in your browser.

## Prompt Logging

Every AI call appends the system prompt, user prompt, structured inputs, and raw JSON output to:

- [logs/prompt_logs.json](logs/prompt_logs.json)

The log entry includes the parsed metrics object and the page text used to build the prompt.

## What I Would Improve With More Time

- Add a Playwright-backed optional scraper for JS-heavy pages.
- Improve CTA heuristics with pattern checks for common intent keywords and visual hierarchy.
- Add model fallback selection and graceful retry logic for API errors.
- Provide a richer UI summary card for the top 3 recommendations.
