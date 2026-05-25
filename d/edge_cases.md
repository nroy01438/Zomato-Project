## Detailed edge cases (phase-wise)

This checklist is derived from `d/problemstatment.md` and `d/phasedarchitecture.md`.

---

## Phase 0 — Foundations (setup)

- **Missing/invalid env vars**: LLM key absent, wrong key, wrong provider selected.
- **Network constraints**: dataset/LLM calls blocked, intermittent connectivity, DNS failures.
- **Timezone/locale issues**: numeric parsing differs (`,` vs `.`), currency symbols in cost fields.
- **Logging safety**: prompts/responses accidentally logged with API keys or sensitive user text.

---

## Phase 1 — Data layer (ingestion + preprocessing)

- **Schema drift**: dataset columns renamed/removed, new nested structures, unexpected nullability.
- **Corrupt or partial download**: truncated rows, decoding errors, gzip/parquet read failures.
- **Missing critical fields**: no rating/cost/cuisine for many rows; empty strings vs `null`.
- **Inconsistent location granularity**: “Bangalore” vs “Bengaluru”, neighborhoods vs cities, mixed casing.
- **Cuisine formatting**: comma-separated strings, inconsistent delimiters (`/`, `&`, `,`), duplicates (“North Indian, North Indian”).
- **Cost anomalies**: cost as string (“₹500 for two”), ranges (“300-600”), zeros/negative, extreme outliers.
- **Rating anomalies**: “NEW”, “-”, “Not rated”, values outside 0–5, text embedded (“4.2/5”).
- **Duplicate restaurants**: same name+address repeated; chains with many branches (need stable IDs).
- **Non-ASCII text**: special characters in names/cuisines causing prompt formatting or UI rendering issues.
- **Processed store integrity**: mismatched types between runs, non-deterministic ordering, inconsistent normalization results.

---

## Phase 2 — Retrieval layer (preference parsing + filtering + shortlist)

- **Empty or incomplete preferences**: user provides only city; omits budget/cuisine/rating.
- **Invalid values**
  - Location not in dataset
  - Rating outside allowed range (e.g., 6 or -1)
  - Budget string not recognized (“mid”, “cheap-ish”)
- **Ambiguous location input**: “Delhi NCR”, “New Delhi”, “NCR”, “Bangalore/Delhi”.
- **Cuisine synonyms/typos**: “Itallian”, “Chineese”, “South-Indian”, “Pan Asian” vs “Asian”.
- **Over-constrained filters**: no matches when combining location+cuisine+min rating+budget.
- **Relaxation strategy pitfalls**: relaxing constraints returns irrelevant results (e.g., wrong city) or violates “hard constraints” unintentionally.
- **Case-sensitivity and whitespace**: “ Delhi ” fails exact match if not normalized.
- **Shortlist bias**
  - All top \(N\) from a single chain
  - All very expensive/very cheap due to skew
  - No diversity in cuisines if user asked broad cuisine
- **Tie-breaking**: same rating/cost across many items; unstable ordering across runs.
- **Performance**: filtering slow on large dataset; repeated computations without caching.

---

## Phase 3 — LLM orchestration (ranking + explanations)

- **Prompt too large**: shortlist \(N\) + fields exceed token limits; truncation drops important fields.
- **Hallucination**
  - Adds restaurants not in shortlist
  - Invents ratings/costs/locations
  - Claims features not present (e.g., “family-friendly” without evidence)
- **Schema violations**: returns prose when JSON expected; missing fields; wrong types.
- **Inconsistent ranking logic**: ignores hard constraints (e.g., recommends below min rating).
- **Contradictory explanations**: says “budget friendly” for high-cost item; mismatched cuisine.
- **Model refusal/safety**: refuses due to misunderstood policy; overly cautious.
- **Provider instability**: timeouts, rate limits, 5xx errors, slow responses.
- **Retry loops**: validator keeps retrying due to minor formatting issues → cost blow-up.
- **Determinism**: same input yields different rankings; hard to test/regress without temperature control.

---

## Phase 4 — Presentation layer (UI/API)

- **Empty results UI**: show helpful message + suggested relaxations instead of blank screen.
- **Partial data display**: missing cost/rating should render gracefully (“N/A”) without breaking layout.
- **Formatting issues**: currency display, rounding ratings, long restaurant names overflowing UI.
- **User input injection**: user types prompt-injection text into “additional preferences”.
- **Concurrency**: multiple users hit `/recommend` simultaneously; shared cache collisions if keys not normalized.

---

## Phase 5 — Evaluation & observability

- **Golden tests fragile**: LLM text changes break tests; should test structure/constraints rather than exact wording.
- **Constraint satisfaction checks**: ensure every recommended item actually meets hard filters.
- **Coverage gaps**: tests only for popular cities/cuisines; misses long-tail and missing-field scenarios.
- **Logging volume/cost**: storing full prompts/responses too large; needs sampling/redaction.
- **Debuggability**: can’t reproduce a bad result because prompt version / dataset version wasn’t logged.

---

## Phase 6 — Production hardening (optional)

- **Cache correctness**
  - Different inputs normalize to same key incorrectly (collision)
  - Dataset refresh makes cached recommendations stale/inconsistent
- **Rate limiting edge cases**: bursts from one user; fairness across users.
- **Fallback behavior**: LLM down → rule-based ranking still must be sensible and explainable.
- **Dataset refresh failures**: new dataset breaks preprocessing; must roll back to last good processed snapshot.
- **Cost control**: runaway token usage from large shortlists or repeated retries.
