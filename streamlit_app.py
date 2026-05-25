"""
Streamlit UI for the Zomato-style restaurant recommender (problem statement workflow).

1. Collect Location, Budget, Cuisine, Minimum rating
2. Filter the Hugging Face / Phase 1 processed dataset
3. Rank a shortlist with Groq (Phase 3)
4. Show the top 5 recommendations with explanations

Run from repo root:
  pip install -r streamlit-requirements.txt
  python3 -m streamlit run streamlit_app.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

import streamlit as st

from phase3.orchestrator import RecommendationOrchestrator
from phase3.prompt_builder import UserPreferences
from phase4.csv_candidates import load_dataset_cities, load_search_results

CSV_PATH = ROOT / "phase1" / "data" / "processed" / "restaurants_processed.csv"
SHORTLIST_FOR_LLM = 15
TOP_RECOMMENDATIONS = 5

st.set_page_config(
    page_title="Restaurant recommendations",
    page_icon="🍽️",
    layout="centered",
)

st.title("Find your next meal")
st.markdown(
    "Tell us **where** you want to eat, your **budget**, preferred **cuisine**, and **minimum rating**. "
    "We filter the Zomato dataset (Hugging Face) and use **Groq** to pick and explain the **top 5** matches."
)

if not CSV_PATH.is_file():
    st.error(
        f"Processed dataset not found at `{CSV_PATH}`. "
        "Run Phase 1 ingestion first (`python phase1/build_store.py`)."
    )
    st.stop()

@st.cache_data(show_spinner=False)
def get_dataset_cities(csv_path: str) -> list[str]:
    return list(load_dataset_cities(csv_path))


dataset_cities = get_dataset_cities(str(CSV_PATH))
if not dataset_cities:
    st.error("No locations found in the processed dataset `city` column.")
    st.stop()

groq_key = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
if not groq_key:
    st.warning("Set `GROQ_API_KEY` (or `LLM_API_KEY`) in `.env` to generate AI recommendations.")

with st.form("preferences_form", clear_on_submit=False):
    st.subheader("Your preferences")
    col1, col2 = st.columns(2)
    with col1:
        location = st.selectbox(
            "Location",
            options=dataset_cities,
            index=dataset_cities.index("Bellandur") if "Bellandur" in dataset_cities else 0,
            help="Areas from the Hugging Face Zomato export (`city` in the processed CSV).",
        )
        cuisine = st.text_input(
            "Cuisine",
            value="North Indian",
            placeholder="e.g. North Indian, Chinese, Italian",
        )
    with col2:
        budget = st.number_input(
            "Budget (max ₹ for two)",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
            help="Uses the dataset **cost_for_two** field (approximate meal cost for two people).",
        )
        min_rating = st.slider(
            "Minimum rating",
            min_value=1.0,
            max_value=5.0,
            value=4.0,
            step=0.1,
        )

    additional_preferences = st.text_area(
        "Additional preferences (optional)",
        value="",
        placeholder="e.g. family-friendly, outdoor seating, vegetarian options, quick service, romantic ambience…",
        help="Free text passed to Groq when ranking—use for anything not covered above.",
        height=80,
    )

    submitted = st.form_submit_button("Get recommendations", type="primary", use_container_width=True)

if not submitted:
    st.info("Fill in the criteria above (additional preferences are optional), then click **Get recommendations**.")
    st.caption(
        "Data: [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) "
        "→ `phase1/data/processed/restaurants_processed.csv`"
    )
    st.stop()

city = location
cuisine_value = cuisine.strip()
if not city or not cuisine_value:
    st.warning("Location and cuisine are required.")
    st.stop()

if not groq_key:
    st.error("Groq API key missing. Add `GROQ_API_KEY` to `.env` and restart the app.")
    st.stop()

with st.spinner("Filtering restaurants from the dataset…"):
    candidates, rows = load_search_results(
        CSV_PATH,
        city=city,
        cuisine_substr=cuisine_value,
        min_rating=min_rating,
        max_cost_for_two=float(budget),
        max_rows=SHORTLIST_FOR_LLM,
    )

if not candidates:
    st.info(
        "No restaurants matched these filters. Try another **location** from the dataset, "
        "a broader **cuisine**, a lower **minimum rating**, or a higher **budget**."
    )
    st.stop()

extra_prefs = additional_preferences.strip()
success_bits = (
    f"Found **{len(candidates)}** candidate(s) in **{city}** "
    f"(cuisine includes **{cuisine_value}**, rating ≥ **{min_rating}**, cost for two ≤ **₹{int(budget)}**"
)
if extra_prefs:
    success_bits += f", plus your notes: *{extra_prefs}*"
success_bits += ")."
st.success(success_bits)

by_name: Dict[str, dict] = {row["name"]: row for row in rows}

preferences = UserPreferences(
    location=city,
    budget=f"Up to ₹{int(budget)} for two (dataset: cost_for_two). Every candidate already meets this cap.",
    cuisine=cuisine_value,
    min_rating=min_rating,
    additional_preferences=extra_prefs or None,
)

with st.spinner("Ranking with Groq and writing explanations…"):
    orchestrator = RecommendationOrchestrator(llm_provider="groq")
    ok, err = orchestrator.validate_input_data(preferences, candidates)
    if not ok:
        st.error(err)
        st.stop()

    response = asyncio.run(orchestrator.generate_recommendations(preferences, candidates))

st.subheader(f"Top {TOP_RECOMMENDATIONS} recommendations")
if response.summary:
    st.write(response.summary)

rankings = response.rankings[:TOP_RECOMMENDATIONS]
if not rankings:
    st.warning("Groq did not return ranked results. Try again or relax your filters.")
    if response.suggestions:
        for tip in response.suggestions:
            st.caption(f"• {tip}")
    st.stop()

for ranking in rankings:
    meta: Optional[dict] = by_name.get(ranking.restaurant_name)
    cuisines_text = meta["cuisines"] if meta else "—"
    rating_text = f"{meta['rating']:.1f}/5" if meta else "—"
    cost_text = f"₹{meta['cost_for_two']:,} for two" if meta else "—"
    locality = meta.get("locality") if meta else None

    with st.container(border=True):
        st.markdown(f"### #{ranking.rank} · {ranking.restaurant_name}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Rating", rating_text)
        c2.metric("Est. cost", cost_text.replace(" for two", ""))
        c3.metric("Match score", f"{ranking.relevance_score}/100")
        st.markdown(f"**Cuisine:** {cuisines_text}")
        if locality:
            st.caption(locality)
        st.markdown(ranking.explanation)
        if ranking.highlights:
            st.markdown("**Highlights:** " + " · ".join(ranking.highlights))

if len(response.rankings) > TOP_RECOMMENDATIONS:
    st.caption(f"Showing {TOP_RECOMMENDATIONS} of {len(response.rankings)} ranked results from Groq.")
