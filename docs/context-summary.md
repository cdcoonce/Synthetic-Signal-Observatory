# Synthetic Signal Observatory — Context Summary (Repo Map)

This file is a **repo map** intended to onboard a new agent quickly.
It focuses on **what each file/directory is for**, where key logic lives, and how to run/test.

## Quickstart

- Create/sync environment: `uv sync`
- Run dashboard: `uv run streamlit run app.py`
- Run tests: `uv sync --group dev` then `uv run pytest`

## Where to Start Reading (in order)

1. `README.md` — what the project is + how to run.
2. `STATUS.md` — what works today + current risks.
3. `TODO.md` — the execution queue.
4. `ARCHITECTURE.md` — stable boundaries, data model, invariants.
5. `DECISIONS.md` — append-only decision log (what must be respected).
6. `LEARNINGS.md` — known pitfalls / anti-patterns to avoid.
7. `AGENTS.md` — process rules and collaboration constraints (governing document).

## Top-Level Repo Map

- `app.py`
  - Streamlit entrypoint (UI + orchestration). Calls service layer and pure helpers.
  - Implements Live Mode (auto-generation via `st.fragment`) and chart-window navigation.
- `pyproject.toml`
  - Project metadata + runtime deps (DuckDB, Streamlit) and dev deps (pytest).
  - Requires Python `>=3.12`.
- `uv.lock`
  - Dependency lockfile for reproducible installs with `uv`.

- `README.md`
  - User-facing overview + quickstart commands.
- `STATUS.md`
  - Current operational state (what works, what’s in progress, risks).
- `TODO.md`
  - Work queue: NOW / NEXT / LATER.
- `ARCHITECTURE.md`
  - Architecture log and stable invariants (raw event schema + analytics constraints).
- `DECISIONS.md`
  - Append-only decision log (e.g., Streamlit + DuckDB + Live Mode design).
- `LEARNINGS.md`
  - “Do not repeat” pitfalls (notably Altair inline data + datetimes).
- `AGENTS.md`
  - Repository agent operating system (workflow + authority model).

- `.env.example`
  - Example configuration for local runs (documents all supported env vars).
- `.env`
  - Local-only runtime overrides (auto-loaded unless disabled); should not be committed.
- `.gitignore`
  - Git ignore rules (e.g., `.venv/`, caches).

- `data/`
  - Local persistence assets.
  - `data/sso.duckdb` is the DuckDB system-of-record for raw events.
- `docs/`
  - Documentation home.
  - Currently contains this file; other docs may be added over time.

- `synthetic_signal_observatory/`
  - Core package: business logic and helpers (kept testable; minimal side effects).
- `tests/`
  - Pytest suite for core logic + service behavior.

- `.venv/`, `__pycache__/`, `.pytest_cache/`
  - Local/ephemeral environment and caches (not part of the system design).

## Package Map: `synthetic_signal_observatory/`

- `__init__.py`
  - Package marker (currently minimal).

- `config.py`
  - Centralized config loader.
  - Reads env vars and optionally repo-root `.env` (no `python-dotenv` dependency).
  - Defines `AppConfig` and the supported environment variables.

- `generator.py`
  - Pure synthetic event generator.
  - Deterministic given `(seed, run_id, start_ts)` by deriving an RNG seed.
  - Snaps timestamps to whole-second UTC to avoid chart precision issues.

- `duckdb_persistence.py`
  - DuckDB system-of-record for raw events (`synthetic_events`).
  - Normalizes events (UTC timestamps, quality score clamping) and handles create/append/fetch/reset.
  - Reset semantics: drop the table, keep the DB file.

- `analytics.py`
  - Pure analytics/modeling layer.
  - Rolling mean/std + z-score anomaly flagging per `(source_id, signal_name)`.

- `app_services.py`
  - Application service layer (glue between generator and persistence).
  - Implements “effective start timestamp” logic to avoid timestamp collisions across batches.
  - Provides query helpers used by the UI (fetch for chart, rolling window lookback strategy).

- `viz.py`
  - Visualization helpers (Altair chart builder + JSON-serializable chart rows).
  - Converts timestamps to ISO-8601 strings for stable Vega-Lite/Altair rendering.

## Tests Map: `tests/`

- `conftest.py`
  - Adds repo root to `sys.path` so tests can import project modules without an editable install.
  - This is a known improvement target (see `TODO.md`).

- `test_config.py`
  - Validates config parsing and env var precedence.
- `test_generator.py`
  - Validates generator determinism and input validation.
- `test_duckdb_persistence.py`
  - Validates DuckDB schema/normalization/append/fetch/reset behavior.
- `test_analytics.py`
  - Validates rolling metrics/anomaly rules and edge cases.
- `test_app_services.py`
  - Validates orchestration rules (e.g., timestamp continuity, lookback fetching strategy).
- `test_viz.py`
  - Regression tests for Altair chart serialization stability (no datetime objects in inline values).

## Data Model & Invariants (High Signal)

- Raw table: `synthetic_events` in DuckDB.
- `event_ts` is timezone-aware and normalized to UTC.
- New events are snapped to whole-second UTC (`microsecond=0`).
- Rolling metrics are group-aware per `(source_id, signal_name)` and use a lookback window.

## Operational Notes / Gotchas

- Streamlit reruns scripts on interaction; keep side effects out of module scope.
- Altair inline data + Python `datetime` objects can render blank; `viz.py` uses ISO-8601 strings.
- Live Mode continuously appends to DuckDB; without retention/purge logic, DB growth is unbounded.
- Destructive DB reset is env-gated (`SSO_ALLOW_DB_RESET=1`) and requires an in-UI confirmation.
