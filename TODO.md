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

- [x] Add analytics controls in Streamlit (slider for `window_size`, slider for `z_threshold`)
- [x] Add at least one chart (signal over time) with anomalies visible
- [x] Ensure rolling metrics are available for all displayed window points (use DB lookback)
- [x] Prevent blank Altair charts (serialize timestamps; add regression tests)
- [x] Add chart filters (source/signal) to reduce overplotting
- [x] Make chart pan/zoom explore full DB history
- [x] Centralize app configuration (db path, batch size, seed) in one place
- [ ] Add lightweight logging configuration for local runs (avoid noisy reruns)
- [x] Add DB reset button (env-gated) to drop `synthetic_events`

### Faux Real-Time Display (D-0006) ✅ COMPLETED

- [x] Verify/pin Streamlit ≥ 1.33 in `pyproject.toml`
- [x] Add `SSO_AUTO_REFRESH_INTERVAL` and `SSO_AUTO_RUN_DEFAULT` to config
- [x] Add Live Mode toggle + interval slider to UI (outside fragment)
- [x] Create `@st.fragment(run_every=...)` wrapper for chart/table section
- [x] Conditionally generate events inside fragment when live mode enabled
- [x] Add visual indicator (spinner / timestamp) for streaming state
- [x] Write/adjust tests for new config options
- [x] Update `.env.example` with new config vars

## NEXT

<!-- Important but not urgent -->

- [ ] Add efficient DuckDB queries (e.g., `COUNT(*)`, latest N) without full-table fetch
- [ ] Add performance guardrails for full-history charting (cap/aggregation)
- [ ] Enforce/dedupe `event_id` on insert (document the approach; consider constraints vs merge)
- [ ] Add CI (GitHub Actions) to run `uv run pytest`
- [ ] Make imports work without `tests/conftest.py` sys.path tweak (package/editable install)
- [ ] Add data-retention/purge logic to prevent unbounded DB growth (live mode risk)

## LATER

<!-- Nice-to-have or exploratory -->

- [ ] Add deployment notes + screenshots/GIFs to README
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

