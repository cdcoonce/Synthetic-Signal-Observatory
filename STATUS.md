# STATUS.md — Current Project State

This document describes the **current operational state** of the repository.

It answers:
- What works today?
- What is blocked?
- What risks exist right now?

---

## How to use this file (IMPORTANT)

- This file reflects **current state only**
- It MAY be updated, but prefer appending dated sections
- Do NOT delete historical status without reason
- When major milestones complete, note them

This is the fastest way for a new agent to orient.

---

## What belongs in this file

- High-level project health
- CI status
- Major completed milestones
- Active blockers or risks
- Environment readiness

---

## CURRENT STATUS (append below)

<!--
## Status as of YYYY-MM-DD

### Working
- ...

### In progress
- ...

### Blocked / Risks
- ...
-->

## Status as of 2025-12-27

### Working
- Repository documentation “memory” files exist (`AGENTS.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `STATUS.md`, `TODO.md`, `LEARNINGS.md`).
- Git remote `origin` is configured.

### In progress
- Phase 0 (Foundation) kickoff.
- Dashboard framework confirmed: Streamlit (D-0003: Accepted).

### Completed (foundation)
- DuckDB persistence helpers implemented with pytest coverage.
- Pure synthetic event generator implemented with pytest coverage.
- Streamlit app wired to generate + persist + display latest events.
- Rolling analytics (mean/std + anomaly flag) implemented with pytest coverage and displayed.
- App service layer advances `start_ts` when appending batches to avoid timestamp overlaps that can collapse at chart precision.

### Decisions locked in
- Environment/dependency management: `uv` (D-0002: Accepted).
- Persistence layer for raw events: DuckDB (D-0004: Accepted).

### Blocked / Risks
- No technical blockers yet.
- No open decision blockers.

## Status as of 2025-12-27 (latest)

### Working
- Streamlit dashboard generates events, persists to DuckDB, and renders tables + chart.
- Chart rendering is guarded by tests (Altair inline-data timestamps are serialized as ISO-8601 strings).
- New events are snapped to whole-second UTC timestamps and batches advance `start_ts` to avoid overlaps.
- Rolling analytics for the displayed window uses DuckDB lookback; metrics are only `None` when the database lacks sufficient history.
- Chart supports filtering by `source_id` and `signal_name` to reduce overplotting.
- Chart supports pan/zoom and plots full persisted history for exploration.
- Database reset control exists but is disabled by default; enable with `SSO_ALLOW_DB_RESET=1` and confirm in UI.
- **Live Mode** toggle and interval slider for faux real-time auto-generation (D-0006).
- Config supports `SSO_AUTO_REFRESH_INTERVAL` and `SSO_AUTO_RUN_DEFAULT`.
- `.env.example` documents all environment variables.

### In progress
- Add lightweight logging configuration for local runs.

### Blocked / Risks
- None currently; primary risk is query + chart performance as data volume grows (full-history plots).
- Live mode may cause unbounded DB growth if left running; retention/purge logic is a future TODO.

### Completed
- Centralized app configuration (db path, batch size, seed) via `synthetic_signal_observatory.config`.
- Faux real-time display using `st.fragment(run_every=...)` (D-0006: Accepted). Toggle enables auto-generation with configurable interval.

## Status as of 2025-12-28

### Working
- Signal-over-time chart uses a server-driven x-domain window centered on the latest data (future padding) during Live Mode.
- Back/Forward buttons pause auto-centering (`follow_latest=False`) without stopping Live Mode generation.
- Recenter button resumes auto-centering on new data (`follow_latest=True`).

### In progress
- Add lightweight logging configuration for local runs.

### Blocked / Risks
- Streamlit/Altair pan/zoom remains client-side only; it does not update server state without a custom component (expected limitation).
