"""
Production API for Render — Zomato CSV retrieval (Phase 1/2) + Groq ranking (Phase 3).

Endpoints:
  GET  /health
  GET  /locations
  POST /recommend

Run locally:
  cd <repo-root>
  export GROQ_API_KEY=...
  uvicorn backend.app:app --reload --port 5000

Render start:
  gunicorn backend.app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1 --timeout 120
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any, List, Optional, Union

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Repo root on PYTHONPATH (Render: working dir is usually repo root)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from phase3.orchestrator import RecommendationOrchestrator
from phase3.prompt_builder import UserPreferences
from phase4.csv_candidates import load_dataset_cities, load_search_results
from phase4.ui_components import UIComponents

# --- Configuration ---

def _csv_path() -> Path:
    raw = os.getenv("DATA_CSV_PATH", "phase1/data/processed/restaurants_processed.csv")
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    return path


def _allowed_origins() -> List[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or ["*"]


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
SHORTLIST_FOR_LLM = int(os.getenv("SHORTLIST_FOR_LLM", "15"))
TOP_RECOMMENDATIONS = int(os.getenv("TOP_RECOMMENDATIONS", "5"))

# --- Request / response models ---


class RecommendRequest(BaseModel):
    location: str = Field(..., min_length=1, description="Dataset `city` value")
    cuisine: str = Field(..., min_length=1)
    min_rating: float = Field(..., ge=0, le=5)
    budget: Union[int, float, str] = Field(
        ...,
        description="Max cost_for_two (₹). Number or numeric string.",
    )
    additional_preferences: Optional[str] = Field(
        default=None,
        description="Optional free-text preferences for Groq ranking",
    )


def _parse_budget(value: Union[int, float, str]) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        raise ValueError("budget is required")
    try:
        return float(s)
    except ValueError as exc:
        raise ValueError(
            f"Invalid budget '{value}'. Use a number (max ₹ for two), e.g. 1000."
        ) from exc


# --- App ---

app = FastAPI(
    title="Restaurant Recommendation API",
    description="AI-powered recommendations (Hugging Face Zomato data + Groq)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

_ui = UIComponents()


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "restaurant-recommendation-api",
        "docs": "/docs",
        "health": "/health",
        "locations": "/locations",
        "recommend": "POST /recommend",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    csv_path = _csv_path()
    return {
        "status": "healthy",
        "service": "restaurant-recommendation-api",
        "version": "1.0.0",
        "llm_provider": LLM_PROVIDER,
        "dataset_available": csv_path.is_file(),
        "dataset_path": str(csv_path),
    }


@app.get("/locations")
def locations() -> dict[str, List[str]]:
    csv_path = _csv_path()
    if not csv_path.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"Dataset not found at {csv_path}. Run Phase 1 build or set DATA_CSV_PATH.",
        )
    cities = list(load_dataset_cities(str(csv_path)))
    return {"locations": cities}


@app.post("/recommend")
def recommend(body: RecommendRequest) -> dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY (or LLM_API_KEY) is not configured on the server.",
        )

    csv_path = _csv_path()
    if not csv_path.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"Dataset not found at {csv_path}.",
        )

    try:
        max_cost = _parse_budget(body.budget)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    city = body.location.strip()
    cuisine = body.cuisine.strip()
    if not city or not cuisine:
        raise HTTPException(status_code=400, detail="location and cuisine are required")

    started = time.perf_counter()

    candidates, rows = load_search_results(
        csv_path,
        city=city,
        cuisine_substr=cuisine,
        min_rating=body.min_rating,
        max_cost_for_two=max_cost,
        max_rows=SHORTLIST_FOR_LLM,
    )

    if not candidates:
        return {
            "success": True,
            "data": {
                "summary": "No restaurants found matching your criteria.",
                "total_results": 0,
                "rankings": [],
                "suggestions": [
                    "Try another location from GET /locations",
                    "Lower minimum rating or increase budget",
                    "Try a broader cuisine term",
                ],
            },
            "meta": {
                "processing_time_ms": int((time.perf_counter() - started) * 1000),
                "candidates_filtered": 0,
            },
        }

    extra = (body.additional_preferences or "").strip() or None
    preferences = UserPreferences(
        location=city,
        budget=(
            f"Up to ₹{int(max_cost)} for two (dataset: cost_for_two). "
            "Every candidate already satisfies this cap."
        ),
        cuisine=cuisine,
        min_rating=body.min_rating,
        additional_preferences=extra,
    )

    orchestrator = RecommendationOrchestrator(llm_provider=LLM_PROVIDER)
    ok, err = orchestrator.validate_input_data(preferences, candidates)
    if not ok:
        raise HTTPException(status_code=400, detail=err or "Invalid input")

    try:
        response = asyncio.run(
            orchestrator.generate_recommendations(preferences, candidates)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Recommendation service error: {exc}",
        ) from exc

    payload = _ui.render_json(response)
    data = payload.get("data") or {}
    rankings = data.get("rankings") or []

    # Cap at top N; add aliases + dataset fields for clients
    by_name = {row["name"]: row for row in rows}
    trimmed: List[dict[str, Any]] = []
    for item in rankings[:TOP_RECOMMENDATIONS]:
        name = item.get("restaurant_name") or item.get("name")
        meta = by_name.get(name) if name else None
        enriched = {
            **item,
            "name": name,
            "score": item.get("relevance_score") or item.get("score"),
        }
        if meta:
            enriched["rating"] = meta.get("rating")
            enriched["cost_for_two"] = meta.get("cost_for_two")
            enriched["cuisines"] = meta.get("cuisines")
            enriched["locality"] = meta.get("locality")
            enriched["votes"] = meta.get("votes")
        trimmed.append(enriched)

    data["rankings"] = trimmed
    data["total_results"] = len(trimmed)
    payload["data"] = data
    payload["meta"] = {
        "processing_time_ms": int((time.perf_counter() - started) * 1000),
        "candidates_filtered": len(candidates),
        "location": city,
    }
    return payload


# WSGI alias for plain gunicorn (optional)
application = app
