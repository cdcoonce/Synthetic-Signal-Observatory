# DECISIONS.md — Architectural & Design Decisions

This file is the **decision log** for this repository.

It records decisions that are:
- Hard to reverse
- Cross-cutting
- Important for future agents to respect

---

## How to use this file (IMPORTANT)

- This file is **append-only**
- NEVER edit or delete existing decisions
- Every irreversible or opinionated choice MUST be recorded
- If a decision is temporary, mark it as **Proposed**

If a change conflicts with a prior decision:
→ Stop and escalate before proceeding.

---

## Decision format (REQUIRED)

Each decision MUST include:

- **ID** (monotonic, e.g. D-0006)
- **Status**: Proposed | Accepted | Superseded
- **Context**: Why this decision was needed
- **Decision**: What was chosen
- **Consequences**: What this enables / restricts

Use bullets. Be explicit.

---

## DECISION LOG (append below)

<!--
### D-000X — Short title

- Status:
- Date:

#### Context
- ...

#### Decision
- ...

#### Consequences
- ...
-->

### D-0001 — Select dashboard framework (Streamlit)

- Status: Proposed
- Date: 2025-12-27

#### Context
- The project requires a Python-native, deployable, interactive dashboard with live/auto-refresh behavior.
- We want a simple, single-process app that is easy to run locally and easy to host as a portfolio artifact.
- Early phases benefit from fast iteration and a low ceremony UI layer.

#### Decision
- Use Streamlit as the dashboard framework for the initial implementation.

#### Consequences
- UI will be implemented as a Streamlit app (single Python process).
- Live updates will use Streamlit-native patterns (e.g., periodic refresh) rather than a separate frontend.
- Hosting options include Streamlit Community Cloud or container/VM deployment.

### D-0002 — Use uv for environment and dependency management

- Status: Accepted
- Date: 2025-12-27

#### Context
- The repo needs a reproducible, low-friction way to manage Python versions, dependencies, and execution.
- The project aims to be easy for agents and humans to run locally and in CI.

#### Decision
- Use `uv` for dependency management and running project commands.

#### Consequences
- Project dependencies will live in `pyproject.toml`.
- Lockfile-based reproducibility is expected (`uv.lock`).
- Documentation should prefer `uv run ...` for execution.

### D-0003 — Confirm Streamlit as dashboard framework

- Status: Accepted
- Date: 2025-12-27

#### Context
- D-0001 proposed Streamlit to unblock Phase 0 implementation.
- The repository now uses `uv` and already includes `streamlit` in dependencies.

#### Decision
- Confirm Streamlit as the dashboard framework for the initial implementation.

#### Consequences
- Proceed with a Streamlit-based app entrypoint and UI.
- Future changes to the dashboard framework require a new decision entry.

### D-0004 — Use DuckDB for persistent storage (raw events)

- Status: Accepted
- Date: 2025-12-27

#### Context
- The project needs persistent local storage between runs for raw event data.
- We want a lightweight, single-process-friendly store that supports easy querying for dashboards and analytics.

#### Decision
- Use DuckDB as the persistence layer for the raw `synthetic_events` data.

#### Consequences
- A local DuckDB database file will be created/updated during runs.
- The dashboard and analytics steps can query DuckDB directly.
- If we also write Parquet, it is an optimization/interop choice, not the system of record.

### D-0005 — Database reset semantics (drop events table)

- Status: Accepted
- Date: 2025-12-28

#### Context
- The Streamlit dashboard is used interactively and can accumulate event rows quickly.
- A "reset" control is useful during development and demos.
- Reset is destructive and must be hard to trigger accidentally.

#### Decision
- Define "Reset database" as: `DROP TABLE IF EXISTS synthetic_events`.
- Do NOT delete the DuckDB file.
- Gate the UI control behind `SSO_ALLOW_DB_RESET` (default disabled) and a UI confirmation checkbox.

#### Consequences
- Reset is idempotent and fast.
- Other potential tables (if added later) are preserved by reset unless explicitly included.
- Users must opt in via an environment variable to expose destructive controls.

### D-0006 — Faux real-time display via st.fragment

- Status: Accepted
- Date: 2025-12-28

#### Context
- The dashboard currently requires manual button clicks to generate new events.
- A "live" or "streaming" feel is desirable for portfolio demos.
- Streamlit 1.33+ provides `@st.fragment(run_every=...)` for partial-page auto-refresh.

#### Decision
- Implement faux real-time display using `st.fragment` with a configurable `run_every` interval.
- Add a Live Mode toggle (off by default) and an interval slider.
- Require Streamlit ≥ 1.33; do not implement fallback patterns.

#### Consequences
- Charts and tables update automatically when Live Mode is enabled.
- Only the fragment re-executes; the rest of the page remains stable.
- Database may grow unbounded if left running; future work may add retention/purge logic.
- See `docs/planning/REALTIME_DISPLAY_PLAN.md` for full implementation details.
