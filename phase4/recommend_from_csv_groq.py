"""
Load restaurant candidates from Phase 1 processed CSV, then rank via Phase 3 Groq.

Usage (from repo root `basic/`):
  export GROQ_API_KEY=...
  python3 phase4/recommend_from_csv_groq.py --location Bellandur --cuisine "North Indian" --min-rating 4 --budget 1000
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from phase3.orchestrator import RecommendationOrchestrator
from phase3.prompt_builder import UserPreferences
from phase4.csv_candidates import load_candidates_from_csv


async def main_async() -> None:
    root = Path(__file__).resolve().parents[1]
    default_csv = root / "phase1" / "data" / "processed" / "restaurants_processed.csv"

    parser = argparse.ArgumentParser(description="CSV shortlist + Groq ranking (Phase 3).")
    parser.add_argument("--location", default="Bellandur", help="Dataset city column (e.g. Bellandur)")
    parser.add_argument("--cuisine", default="North Indian")
    parser.add_argument("--min-rating", type=float, default=4.0)
    parser.add_argument("--budget", type=float, default=1000.0, help="Max cost_for_two (INR)")
    parser.add_argument("--csv", type=Path, default=default_csv)
    parser.add_argument("--top", type=int, default=12, help="Max candidates sent to the LLM")
    args = parser.parse_args()

    if not args.csv.is_file():
        raise SystemExit(f"CSV not found: {args.csv}")

    candidates = load_candidates_from_csv(
        args.csv,
        city=args.location.strip(),
        cuisine_substr=args.cuisine,
        min_rating=args.min_rating,
        max_cost_for_two=args.budget,
        max_rows=args.top,
    )

    preferences = UserPreferences(
        location=args.location,
        budget=f"Up to ₹{int(args.budget)} for two (dataset field cost_for_two)",
        cuisine=args.cuisine,
        min_rating=args.min_rating,
    )

    print("=== Retrieval (project CSV) ===")
    print(f"Location: {preferences.location} | Cuisine: {preferences.cuisine} | min_rating: {preferences.min_rating}")
    print(f"Budget filter: cost_for_two <= {int(args.budget)}")
    print(f"Candidates passed to Groq: {len(candidates)} (capped at --top {args.top})\n")

    for i, c in enumerate(candidates, 1):
        print(f"  {i}. {c.name} | {c.rating} | ₹{c.cost_for_two} for two | {c.votes} votes | {', '.join(c.cuisines[:4])}")

    if not candidates:
        print("\nNo candidates; skipping LLM.")
        return

    if not (os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")):
        print("\n[!] GROQ_API_KEY (or LLM_API_KEY) not set — set it in .env or the environment to call Groq.")
        return

    print("\n=== Groq (Phase 3) ===")
    orchestrator = RecommendationOrchestrator(llm_provider="groq")
    ok, err = orchestrator.validate_input_data(preferences, candidates)
    if not ok:
        raise SystemExit(err)

    response = await orchestrator.generate_recommendations(preferences, candidates)
    print(f"\nSummary: {response.summary}\n")
    for r in response.rankings:
        print(f"#{r.rank} {r.restaurant_name} — score {r.relevance_score}")
        print(f"   {r.explanation}")
        if r.highlights:
            print(f"   Highlights: {', '.join(r.highlights)}")
        print()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
