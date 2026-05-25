## Phase 2 — Retrieval Layer (filtering + shortlist)

This folder implements **Phase 2** from `d/phasedarchitecture.md`:

- Parse and validate user preferences (location, budget, cuisine, minimum rating)
- Apply **rules-based filtering** (hard constraints)
- Produce a deterministic **shortlist** for the LLM (Phase 3)
- Provide clear behavior when results are empty (optional relaxation)

### Inputs

- `phase1/data/processed/restaurants.sqlite` (created by Phase 1)

### Output

- JSON printed to stdout containing:
  - Normalized preferences
  - Applied filters (including any relaxations)
  - Shortlisted restaurants

### Run

```bash
python3 phase2/retrieve.py --location Bangalore --cuisine Italian --min-rating 4.0 --budget medium --top 10
```

### Budget formats

- `low|medium|high` (mapped to dataset cost tertiles)
- A number (max cost), e.g. `--budget 800`
- A range `min-max`, e.g. `--budget 400-900`

### Notes

- Location is treated as a **hard constraint** by default (exact string match after normalization).
- `--relax` enables a best-effort strategy when there are zero matches.

