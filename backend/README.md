# Backend API (Render)

Production REST API for the restaurant recommender. See **`d/deployment-render-vercel.md`** for full deploy steps.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health + dataset availability |
| GET | `/locations` | All `city` values from processed CSV |
| POST | `/recommend` | Filter dataset + Groq top 5 |

## Local run

```bash
cd "/path/to/basic"
pip install -r backend/requirements.txt
export GROQ_API_KEY=your_key
export ALLOWED_ORIGINS=http://localhost:3000

uvicorn backend.app:app --reload --port 5000
# or
python -m uvicorn backend.app:app --host 0.0.0.0 --port 5000
```

**Render (recommended start command):**
```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port $PORT
```

## Environment variables

| Variable | Required | Default |
|----------|----------|---------|
| `GROQ_API_KEY` | Yes* | — |
| `LLM_PROVIDER` | No | `groq` |
| `DATA_CSV_PATH` | No | `phase1/data/processed/restaurants_processed.csv` |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000,...` |
| `SHORTLIST_FOR_LLM` | No | `15` |
| `TOP_RECOMMENDATIONS` | No | `5` |

\*Or `LLM_API_KEY`

## Example request

```bash
curl -X POST http://localhost:5000/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "location": "Bellandur",
    "cuisine": "North Indian",
    "min_rating": 4,
    "budget": 1000,
    "additional_preferences": "family-friendly"
  }'
```

## Render

Connect the repo and use root-level **`render.yaml`**, or set:

- **Build:** `pip install -r backend/requirements.txt`
- **Start:** `gunicorn backend.app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1 --timeout 120`
