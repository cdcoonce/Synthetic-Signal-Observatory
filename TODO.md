# TODO.md — Work Queue & Planning

This file tracks **actionable work items** for the repository.

It is intentionally lightweight and execution-focused.

---

## How to use this file (IMPORTANT)

- Prefer **small, testable tasks**
- Use checklists
- Reorder freely — this is not append-only
- If a task changes architecture or behavior:
  → Record a decision in `DECISIONS.md`

---

## Conventions

- `[ ]` = not started
- `[x]` = completed
- Keep items scoped so they can be finished in one PR

---

## NOW

<!-- Highest-priority work -->

- [ ] Add lightweight logging configuration for local runs (avoid noisy reruns)

## NEXT

<!-- Important but not urgent -->

- [ ] Add efficient DuckDB queries (e.g., `COUNT(*)`, latest N) without full-table fetch
- [ ] Add performance guardrails for full-history charting (cap/aggregation)
- [ ] Replace any remaining `use_container_width` usages (Streamlit deprecation)
- [ ] Enforce/dedupe `event_id` on insert (document the approach; consider constraints vs merge)
- [ ] Add CI (GitHub Actions) to run `uv run pytest`
- [ ] Make imports work without `tests/conftest.py` sys.path tweak (package/editable install)
- [ ] Add data-retention/purge logic to prevent unbounded DB growth (live mode risk)
- [ ] Add deployment notes + screenshots/GIFs to README

## LATER

<!-- Nice-to-have or exploratory -->

- [ ] Add Streamlit Community Cloud deployment notes (uv setup, Python version)
- [ ] Persist derived analytics outputs (optional; requires schema + decision)

## DONE

- [x] Confirm Streamlit framework (D-0003)
- [x] Set up `uv` project (`pyproject.toml`, `uv.lock`) and document test/run commands
- [x] Define initial raw event schema in ARCHITECTURE.md
- [x] Implement DuckDB persistence helpers + tests
- [x] Implement pure event generator + tests
- [x] Wire Streamlit to generate, persist, and display latest events
- [x] Implement rolling analytics + anomaly flag + tests; display in Streamlit
- [x] Stabilize chart rendering and ordering; add visualization helpers + tests
- [x] Add DB lookback strategy so rolling stats are only `None` when DB lacks history
- [x] Add chart filters for readability
- [x] Centralize app configuration (db path, batch size, seed) in one place
- [x] Add DB reset button (env-gated) to drop `synthetic_events`
- [x] Add analytics controls in Streamlit (slider for `window_size`, slider for `z_threshold`)
- [x] Add at least one chart (signal over time) with anomalies visible
- [x] Ensure rolling metrics are available for all displayed window points (use DB lookback)
- [x] Prevent blank Altair charts (serialize timestamps; add regression tests)
- [x] Make chart pan/zoom explore full DB history
- [x] Center chart window on latest data (future padding) with Back/Forward/Recenter controls
- [x] Faux Real-Time Display (D-0006): Live Mode toggle + auto-refresh fragment + config/tests

