# Synthetic Signal Observatory

Portfolio project: a Python-native, deployable, interactive dashboard that continuously generates synthetic signals, persists them locally, runs a lightweight analytics step, and visualizes results with interactive controls.

**Project plan**
- See [docs/planning/SETUP_INSTRUCTIONS.md](docs/planning/SETUP_INSTRUCTIONS.md) for the high-level intent and phases.

**Repo memory (read first)**
- [AGENTS.md](AGENTS.md): agent rules and collaboration constraints
- [DECISIONS.md](DECISIONS.md): append-only decision log (e.g., framework choice)
- [ARCHITECTURE.md](ARCHITECTURE.md): architecture boundaries, data model, and invariants (living doc)
- [STATUS.md](STATUS.md): current state snapshot
- [TODO.md](TODO.md): work queue
- [LEARNINGS.md](LEARNINGS.md): “do not repeat” pitfalls and environment quirks

## Repo layout

- `app.py`: Streamlit entrypoint (UI/orchestration only)
- `synthetic_signal_observatory/`: business logic (pure functions) + service layer + viz helpers
- `tests/`: pytest suite

## Quickstart (local)

This repo uses `uv` for Python dependency management.

- Create/sync the environment: `uv sync`
- Run a one-off command: `uv run python -c "import sys; print(sys.version)"`

Run the dashboard:

- `uv run streamlit run app.py`

The Streamlit entrypoint is `app.py`.

## Tests

- `uv sync --group dev`
- `uv run pytest`

