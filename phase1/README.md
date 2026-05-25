## Phase 1 — Data Layer (ingestion + preprocessing)

This folder implements **Phase 1** from `d/phasedarchitecture.md`: ingest the Hugging Face Zomato dataset, clean/normalize key fields, and write a reproducible **processed store**.

### What it produces

- `phase1/data/raw/zomato.csv` (downloaded, large)
- `phase1/data/processed/restaurants_processed.csv` (normalized, smaller schema)
- `phase1/data/processed/restaurants.sqlite` (SQLite table for fast querying)

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r phase1/requirements.txt
```

Note: Phase 1 uses only the Python standard library, so the requirements file is intentionally empty.

### Build the processed store

```bash
python phase1/build_store.py
```

### Optional: build a smaller sample (faster iteration)

```bash
python phase1/build_store.py --limit 5000
```

### Output schema (processed)

The processed dataset is written with this stable schema:

- `id` (string): stable row id
- `name` (string)
- `city` (string)
- `locality` (string)
- `cuisines` (string): pipe-separated cuisines (e.g., `Italian|Pizza`)
- `cost_for_two` (number): numeric estimate when available
- `rating` (number)
- `votes` (integer)
- `raw_url` (string): source dataset url

