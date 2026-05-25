"""Load restaurant candidates from Phase 1 processed CSV (shared by CLI and Streamlit)."""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from phase3.prompt_builder import RestaurantCandidate


@lru_cache(maxsize=4)
def load_dataset_cities(csv_path: str) -> tuple[str, ...]:
    """Distinct non-empty values from the dataset `city` column (Hugging Face → Phase 1)."""
    path = Path(csv_path)
    if not path.is_file():
        return ()
    cities: set[str] = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            city = (row.get("city") or "").strip()
            if city:
                cities.add(city)
    return tuple(sorted(cities, key=str.casefold))


def load_search_results(
    csv_path: Path,
    *,
    city: str,
    cuisine_substr: str,
    min_rating: float,
    max_cost_for_two: float,
    max_rows: int,
) -> Tuple[List[RestaurantCandidate], List[dict]]:
    """
    One pass: candidates for Phase 3 + display dicts (includes locality) for UI tables.
    """
    cuisine_need = cuisine_substr.strip()
    seen: set[tuple[str, int]] = set()
    candidates: List[RestaurantCandidate] = []
    display_rows: List[dict] = []

    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("city", "").strip() != city:
                continue
            cuisines_raw = row.get("cuisines") or ""
            parts = [p.strip() for p in cuisines_raw.split("|") if p.strip()]
            if not any(
                cuisine_need.casefold() == p.casefold() or cuisine_need.casefold() in p.casefold()
                for p in parts
            ):
                if cuisine_need not in cuisines_raw:
                    continue
            try:
                rating = float(row["rating"]) if row.get("rating") not in (None, "", "nan") else None
            except ValueError:
                rating = None
            if rating is None or rating < min_rating:
                continue
            try:
                cost = float(row["cost_for_two"]) if row.get("cost_for_two") not in (None, "") else None
            except ValueError:
                cost = None
            if cost is None or cost > max_cost_for_two:
                continue
            try:
                votes = int(float(row["votes"])) if row.get("votes") not in (None, "") else 0
            except ValueError:
                votes = 0
            name = row.get("name") or ""
            key = (name, int(round(cost)))
            if key in seen:
                continue
            seen.add(key)
            c = RestaurantCandidate(
                name=name,
                cuisines=parts,
                rating=float(rating),
                cost_for_two=int(round(cost)),
                location=city,
                votes=votes,
            )
            candidates.append(c)
            display_rows.append(
                {
                    "name": name,
                    "locality": (row.get("locality") or "")[:200],
                    "cuisines": ", ".join(parts[:10]),
                    "rating": float(rating),
                    "cost_for_two": int(round(cost)),
                    "votes": votes,
                }
            )

    order = sorted(range(len(candidates)), key=lambda i: (candidates[i].rating, candidates[i].votes), reverse=True)
    candidates = [candidates[i] for i in order][:max_rows]
    display_rows = [display_rows[i] for i in order][:max_rows]
    return candidates, display_rows


def load_candidates_from_csv(
    csv_path: Path,
    *,
    city: str,
    cuisine_substr: str,
    min_rating: float,
    max_cost_for_two: float,
    max_rows: int,
) -> List[RestaurantCandidate]:
    cands, _ = load_search_results(
        csv_path,
        city=city,
        cuisine_substr=cuisine_substr,
        min_rating=min_rating,
        max_cost_for_two=max_cost_for_two,
        max_rows=max_rows,
    )
    return cands
