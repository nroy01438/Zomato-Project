import argparse
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SQLITE_PATH = PROJECT_ROOT / "phase1" / "data" / "processed" / "restaurants.sqlite"


def norm_text(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = str(s).strip()
    s = re.sub(r"\s+", " ", s)
    return s if s else None


def norm_key(s: Optional[str]) -> Optional[str]:
    s = norm_text(s)
    return s.casefold() if s else None


@dataclass(frozen=True)
class Budget:
    kind: str  # "band" | "range" | "max" | "none"
    min_cost: Optional[float] = None
    max_cost: Optional[float] = None
    band: Optional[str] = None  # low|medium|high


def parse_budget(raw: Optional[str]) -> Budget:
    raw = norm_text(raw)
    if not raw:
        return Budget(kind="none")

    band = raw.casefold()
    if band in {"low", "medium", "high"}:
        return Budget(kind="band", band=band)

    m_range = re.fullmatch(r"(\d+(\.\d+)?)[\s]*-[\s]*(\d+(\.\d+)?)", raw)
    if m_range:
        a = float(m_range.group(1))
        b = float(m_range.group(3))
        lo, hi = (a, b) if a <= b else (b, a)
        return Budget(kind="range", min_cost=lo, max_cost=hi)

    m_num = re.fullmatch(r"(\d+(\.\d+)?)", raw)
    if m_num:
        return Budget(kind="max", max_cost=float(m_num.group(1)))

    raise SystemExit(
        "Invalid --budget. Use low|medium|high, a number (max), or a range like 400-900."
    )


def connect_db() -> sqlite3.Connection:
    if not SQLITE_PATH.exists():
        raise SystemExit(
            f"Missing Phase 1 store at {SQLITE_PATH}. Run: python3 phase1/build_store.py"
        )
    con = sqlite3.connect(str(SQLITE_PATH))
    con.row_factory = sqlite3.Row
    return con


def dataset_cost_tertiles(con: sqlite3.Connection) -> Tuple[float, float]:
    rows = con.execute(
        "SELECT cost_for_two FROM restaurants WHERE cost_for_two IS NOT NULL ORDER BY cost_for_two"
    ).fetchall()
    costs = [float(r["cost_for_two"]) for r in rows]
    if not costs:
        return (0.0, float("inf"))

    def q(p: float) -> float:
        idx = int(math.floor((len(costs) - 1) * p))
        return float(costs[idx])

    return (q(1 / 3), q(2 / 3))


def cuisine_match_sql(cuisine: str) -> Tuple[str, List[Any]]:
    c = cuisine.strip()
    if not c:
        return ("1=1", [])
    return (
        "(cuisines = ? OR cuisines LIKE ? OR cuisines LIKE ? OR cuisines LIKE ?)",
        [c, f"{c}|%", f"%|{c}|%", f"%|{c}"],
    )


def build_where(
    *,
    location: Optional[str],
    cuisine: Optional[str],
    min_rating: Optional[float],
    budget: Budget,
    tertiles: Tuple[float, float],
) -> Tuple[str, List[Any], Dict[str, Any]]:
    clauses: List[str] = []
    params: List[Any] = []
    applied: Dict[str, Any] = {"location": None, "cuisine": None, "min_rating": None, "budget": None}

    if location:
        clauses.append("city = ?")
        params.append(location)
        applied["location"] = location

    if cuisine:
        sql, p = cuisine_match_sql(cuisine)
        clauses.append(sql)
        params.extend(p)
        applied["cuisine"] = cuisine

    if min_rating is not None:
        clauses.append("rating IS NOT NULL AND rating >= ?")
        params.append(float(min_rating))
        applied["min_rating"] = float(min_rating)

    if budget.kind == "band":
        low_cut, high_cut = tertiles
        if budget.band == "low":
            clauses.append("cost_for_two IS NOT NULL AND cost_for_two <= ?")
            params.append(low_cut)
            applied["budget"] = {"band": "low", "max_cost": low_cut}
        elif budget.band == "medium":
            clauses.append("cost_for_two IS NOT NULL AND cost_for_two > ? AND cost_for_two <= ?")
            params.extend([low_cut, high_cut])
            applied["budget"] = {"band": "medium", "min_cost": low_cut, "max_cost": high_cut}
        else:
            clauses.append("cost_for_two IS NOT NULL AND cost_for_two > ?")
            params.append(high_cut)
            applied["budget"] = {"band": "high", "min_cost": high_cut}

    elif budget.kind == "range":
        clauses.append("cost_for_two IS NOT NULL AND cost_for_two >= ? AND cost_for_two <= ?")
        params.extend([float(budget.min_cost or 0), float(budget.max_cost or 0)])
        applied["budget"] = {"min_cost": budget.min_cost, "max_cost": budget.max_cost}

    elif budget.kind == "max":
        clauses.append("cost_for_two IS NOT NULL AND cost_for_two <= ?")
        params.append(float(budget.max_cost or 0))
        applied["budget"] = {"max_cost": budget.max_cost}

    where = " AND ".join(clauses) if clauses else "1=1"
    return where, params, applied


def fetch_candidates(
    con: sqlite3.Connection,
    *,
    where: str,
    params: Sequence[Any],
    pool: int,
) -> List[Dict[str, Any]]:
    rows = con.execute(
        f"""
        SELECT id, name, city, locality, cuisines, cost_for_two, rating, votes
        FROM restaurants
        WHERE {where}
        """,
        list(params),
    ).fetchall()

    def score(r: sqlite3.Row) -> Tuple[float, int, float]:
        rating = float(r["rating"]) if r["rating"] is not None else -1.0
        votes = int(r["votes"]) if r["votes"] is not None else 0
        cost = float(r["cost_for_two"]) if r["cost_for_two"] is not None else float("inf")
        return (rating, votes, -cost)

    rows_sorted = sorted(rows, key=score, reverse=True)
    rows_sorted = rows_sorted[: max(pool, 50)]
    return [dict(r) for r in rows_sorted]


def select_shortlist(
    candidates: List[Dict[str, Any]],
    *,
    top_n: int,
    prefer_diversity: bool,
) -> List[Dict[str, Any]]:
    if not prefer_diversity:
        return candidates[:top_n]

    chosen: List[Dict[str, Any]] = []
    seen_cuisine = set()

    def primary_cuisine(cuisines: Optional[str]) -> Optional[str]:
        if not cuisines:
            return None
        return cuisines.split("|", 1)[0].strip() or None

    for r in candidates:
        if len(chosen) >= top_n:
            break
        pc = norm_key(primary_cuisine(r.get("cuisines")))
        if pc and pc in seen_cuisine:
            continue
        if pc:
            seen_cuisine.add(pc)
        chosen.append(r)

    if len(chosen) < top_n:
        chosen_ids = {c["id"] for c in chosen}
        for r in candidates:
            if len(chosen) >= top_n:
                break
            if r["id"] in chosen_ids:
                continue
            chosen.append(r)

    return chosen


def relax_strategies(
    *,
    location: Optional[str],
    cuisine: Optional[str],
    min_rating: Optional[float],
    budget: Budget,
) -> List[Dict[str, Any]]:
    return [
        {"location": location, "cuisine": cuisine, "min_rating": min_rating, "budget": budget, "note": "no_relaxation"},
        {"location": location, "cuisine": None, "min_rating": min_rating, "budget": budget, "note": "dropped_cuisine"},
        {
            "location": location,
            "cuisine": cuisine,
            "min_rating": max(0.0, (min_rating or 0.0) - 0.5) if min_rating is not None else None,
            "budget": budget,
            "note": "lowered_min_rating",
        },
        {
            "location": location,
            "cuisine": None,
            "min_rating": max(0.0, (min_rating or 0.0) - 0.5) if min_rating is not None else None,
            "budget": budget,
            "note": "dropped_cuisine_and_lowered_min_rating",
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2: Retrieve shortlist from Phase 1 store.")
    parser.add_argument("--location", type=str, default=None, help="City/location (e.g., BTM)")
    parser.add_argument("--cuisine", type=str, default=None, help="Cuisine (e.g., Italian)")
    parser.add_argument("--min-rating", type=float, default=None, help="Minimum rating (0-5)")
    parser.add_argument("--budget", type=str, default=None, help="low|medium|high, number, or range (400-900)")
    parser.add_argument("--top", type=int, default=10, help="Number of recommendations to return")
    parser.add_argument("--pool", type=int, default=120, help="Candidate pool size before shortlist selection")
    parser.add_argument("--no-diversity", action="store_true", help="Disable cuisine diversity selection")
    parser.add_argument("--relax", action="store_true", help="Try relaxation strategy if no results")
    args = parser.parse_args()

    location = norm_text(args.location)
    cuisine = norm_text(args.cuisine)
    if args.min_rating is not None and (args.min_rating < 0 or args.min_rating > 5):
        raise SystemExit("--min-rating must be between 0 and 5")

    budget = parse_budget(args.budget)

    con = connect_db()
    try:
        tertiles = dataset_cost_tertiles(con)

        tries = relax_strategies(
            location=location, cuisine=cuisine, min_rating=args.min_rating, budget=budget
        )
        if not args.relax:
            tries = tries[:1]

        final = None
        for attempt in tries:
            where, params, applied = build_where(
                location=attempt["location"],
                cuisine=attempt["cuisine"],
                min_rating=attempt["min_rating"],
                budget=attempt["budget"],
                tertiles=tertiles,
            )
            candidates = fetch_candidates(con, where=where, params=params, pool=args.pool)
            if candidates:
                shortlist = select_shortlist(
                    candidates,
                    top_n=max(1, args.top),
                    prefer_diversity=not args.no_diversity,
                )
                final = {
                    "ok": True,
                    "applied_filters": applied,
                    "relaxation": attempt["note"],
                    "counts": {"candidates": len(candidates), "returned": len(shortlist)},
                    "restaurants": shortlist,
                }
                break

        if final is None:
            final = {
                "ok": True,
                "applied_filters": {
                    "location": location,
                    "cuisine": cuisine,
                    "min_rating": args.min_rating,
                    "budget": args.budget,
                },
                "relaxation": "none",
                "counts": {"candidates": 0, "returned": 0},
                "restaurants": [],
                "message": "No restaurants matched your filters. Try enabling --relax or loosening constraints.",
            }

        print(json.dumps(final, ensure_ascii=False, indent=2))
    finally:
        con.close()


if __name__ == "__main__":
    main()

