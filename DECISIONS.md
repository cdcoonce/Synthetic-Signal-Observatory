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
