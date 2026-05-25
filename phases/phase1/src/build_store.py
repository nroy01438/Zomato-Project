from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _bump_csv_field_limit() -> None:
    """
    The raw dataset can contain very large text fields.
    Python's csv module defaults to a ~128KB field limit which can raise:
    `_csv.Error: field larger than field limit (131072)`.
    """

    try:
        csv.field_size_limit(1024 * 1024 * 50)  # 50MB
    except (OverflowError, AttributeError):
        pass


RAW_URL = "https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation/resolve/main/zomato.csv?download=true"

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "phase1" / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

RAW_CSV_PATH = RAW_DIR / "zomato.csv"
PROCESSED_CSV_PATH = PROCESSED_DIR / "restaurants_processed.csv"
SQLITE_PATH = PROCESSED_DIR / "restaurants.sqlite"


def download_with_resume(url: str, dest: Path, chunk_size: int = 1024 * 1024) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)

    existing = dest.stat().st_size if dest.exists() else 0
    mode = "wb"

    if existing > 0:
        mode = "ab"

    req = Request(url, method="GET")
    if existing > 0:
        req.add_header("Range", f"bytes={existing}-")

    try:
        with urlopen(req, timeout=60) as resp:
            with open(dest, mode) as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
    except HTTPError as e:
        if existing > 0 and e.code in {416, 400}:
            dest.unlink(missing_ok=True)
            download_with_resume(url, dest, chunk_size=chunk_size)
            return
        raise
    except URLError:
        raise


def normalize_text(value):
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def normalize_city(value):
    s = normalize_text(value)
    if not s:
        return None
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_rating(value):
    s = normalize_text(value)
    if not s:
        return None
    s_upper = s.upper()
    if s_upper in {"NEW", "NOT RATED", "-", "N/A"}:
        return None
    m = re.search(r"(\d+(\.\d+)?)", s)
    if not m:
        return None
    try:
        rating = float(m.group(1))
    except ValueError:
        return None
    if rating < 0 or rating > 5:
        return None
    return rating


def parse_int(value):
    s = normalize_text(value)
    if not s:
        return None
    s = re.sub(r"[^\d]", "", s)
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def parse_cost_for_two(value):
    s = normalize_text(value)
    if not s:
        return None
    s = s.replace(",", "")
    m = re.search(r"(\d+(\.\d+)?)", s)
    if not m:
        return None
    try:
        cost = float(m.group(1))
    except ValueError:
        return None
    if cost <= 0:
        return None
    return cost


def normalize_cuisines(value):
    s = normalize_text(value)
    if not s:
        return None
    parts = re.split(r"\s*,\s*|\s*/\s*|\s*&\s*", s)
    cleaned = []
    seen = set()
    for p in parts:
        p = p.strip()
        if not p:
            continue
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(p)
    return "|".join(cleaned) if cleaned else None


def stable_id(row: dict) -> str:
    basis = "|".join(
        [
            str(row.get("name") or ""),
            str(row.get("city") or ""),
            str(row.get("locality") or ""),
            str(row.get("cuisines") or ""),
        ]
    ).encode("utf-8")
    return hashlib.sha1(basis).hexdigest()[:16]


def pick_column_from_fieldnames(fieldnames: Iterable[str], candidates) -> Optional[str]:
    cols = {c.lower(): c for c in fieldnames}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None


def preprocess_row(raw: Dict[str, str], colmap: Dict[str, Optional[str]]) -> Optional[Dict[str, object]]:
    name = normalize_text(raw.get(colmap["name"]) if colmap["name"] else None)
    if not name:
        return None

    city = normalize_city(raw.get(colmap["city"]) if colmap["city"] else None)
    locality = normalize_text(raw.get(colmap["locality"]) if colmap["locality"] else None)
    cuisines = normalize_cuisines(raw.get(colmap["cuisines"]) if colmap["cuisines"] else None)
    cost_for_two = parse_cost_for_two(raw.get(colmap["cost_for_two"]) if colmap["cost_for_two"] else None)
    rating = parse_rating(raw.get(colmap["rating"]) if colmap["rating"] else None)
    votes = parse_int(raw.get(colmap["votes"]) if colmap["votes"] else None)

    row = {
        "name": name,
        "city": city,
        "locality": locality,
        "cuisines": cuisines,
        "cost_for_two": cost_for_two,
        "rating": rating,
        "votes": votes,
        "raw_url": RAW_URL,
    }
    row["id"] = stable_id(row)
    return row


PROCESSED_COLUMNS = [
    "id",
    "name",
    "city",
    "locality",
    "cuisines",
    "cost_for_two",
    "rating",
    "votes",
    "raw_url",
]


def write_outputs_streaming(raw_csv_path: Path, limit: Optional[int]) -> Tuple[int, int]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if SQLITE_PATH.exists():
        SQLITE_PATH.unlink()

    con = sqlite3.connect(str(SQLITE_PATH))
    created = 0
    kept = 0

    try:
        con.execute(
            """
            CREATE TABLE restaurants (
              id TEXT PRIMARY KEY,
              name TEXT,
              city TEXT,
              locality TEXT,
              cuisines TEXT,
              cost_for_two REAL,
              rating REAL,
              votes INTEGER,
              raw_url TEXT
            )
            """
        )
        con.execute("CREATE INDEX idx_restaurants_city ON restaurants(city)")
        con.execute("CREATE INDEX idx_restaurants_rating ON restaurants(rating)")
        con.execute("CREATE INDEX idx_restaurants_cost_for_two ON restaurants(cost_for_two)")

        with open(raw_csv_path, "r", encoding="utf-8", errors="replace", newline="") as f_in, open(
            PROCESSED_CSV_PATH, "w", encoding="utf-8", newline=""
        ) as f_out:
            reader = csv.DictReader(f_in)
            writer = csv.DictWriter(f_out, fieldnames=PROCESSED_COLUMNS)
            writer.writeheader()

            if reader.fieldnames is None:
                raise SystemExit("Raw CSV appears to have no header row.")

            colmap = {
                "name": pick_column_from_fieldnames(reader.fieldnames, ["name", "restaurant name", "restaurant_name"]),
                "city": pick_column_from_fieldnames(reader.fieldnames, ["city", "listed_in(city)", "location"]),
                "locality": pick_column_from_fieldnames(reader.fieldnames, ["locality", "address", "location"]),
                "cuisines": pick_column_from_fieldnames(reader.fieldnames, ["cuisines", "cuisine"]),
                "cost_for_two": pick_column_from_fieldnames(
                    reader.fieldnames, ["approx_cost(for two people)", "cost_for_two", "average_cost_for_two"]
                ),
                "rating": pick_column_from_fieldnames(reader.fieldnames, ["rate", "rating"]),
                "votes": pick_column_from_fieldnames(reader.fieldnames, ["votes", "vote"]),
            }

            insert_sql = """
              INSERT OR REPLACE INTO restaurants
              (id, name, city, locality, cuisines, cost_for_two, rating, votes, raw_url)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            for raw_row in reader:
                created += 1
                processed = preprocess_row(raw_row, colmap)
                if not processed:
                    continue
                kept += 1

                writer.writerow(processed)
                con.execute(
                    insert_sql,
                    (
                        processed["id"],
                        processed["name"],
                        processed["city"],
                        processed["locality"],
                        processed["cuisines"],
                        processed["cost_for_two"],
                        processed["rating"],
                        processed["votes"],
                        processed["raw_url"],
                    ),
                )

                if limit is not None and kept >= limit:
                    break

            con.commit()
    finally:
        con.close()

    return created, kept


def main():
    _bump_csv_field_limit()

    parser = argparse.ArgumentParser(description="Phase 1: Build processed restaurant store.")
    parser.add_argument("--limit", type=int, default=None, help="Only process first N rows (for quick iteration).")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading raw dataset (assumes phase1/data/raw/zomato.csv exists).",
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not args.skip_download:
        download_with_resume(RAW_URL, RAW_CSV_PATH)
    if not RAW_CSV_PATH.exists():
        raise SystemExit(f"Raw CSV not found at {RAW_CSV_PATH}")

    created, kept = write_outputs_streaming(RAW_CSV_PATH, args.limit)

    print("Phase 1 build complete")
    print(f"- rows read: {created}")
    print(f"- rows kept: {kept}")
    print(f"- raw: {RAW_CSV_PATH}")
    print(f"- processed csv: {PROCESSED_CSV_PATH}")
    print(f"- sqlite: {SQLITE_PATH}")


if __name__ == "__main__":
    main()

