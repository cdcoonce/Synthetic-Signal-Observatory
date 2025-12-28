"""Application service layer.

This module wires pure generation logic to persistence.

It exists so that Streamlit (UI/orchestration) remains thin while the behavior
is testable using pytest.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from synthetic_signal_observatory.duckdb_persistence import (
    NormalizedSyntheticEvent,
    SyntheticEvent,
    append_synthetic_events,
    fetch_synthetic_events,
)
from synthetic_signal_observatory.generator import generate_synthetic_events

logger = logging.getLogger(__name__)


def generate_and_persist_events(
    *,
    db_path: Path,
    count: int,
    start_ts: datetime,
    run_id: str,
    seed: int,
    source_ids: list[str],
    signal_names: list[str],
    step: timedelta,
) -> int:
    """Generate synthetic events and append them to DuckDB.

    Parameters
    ----------
    db_path:
        Path to the DuckDB database file.
    count:
        Number of events to generate.
    start_ts:
        Timestamp for the first event; MUST be timezone-aware.
    run_id:
        Identifier for the generator run/session.
    seed:
        RNG seed for deterministic generation.
    source_ids:
        Candidate source IDs.
    signal_names:
        Candidate signal names.
    step:
        Time delta between sequential events.

    Returns
    -------
    int
        Number of events appended.
    """

    events: list[SyntheticEvent] = generate_synthetic_events(
        count=count,
        start_ts=start_ts,
        run_id=run_id,
        seed=seed,
        source_ids=source_ids,
        signal_names=signal_names,
        step=step,
    )

    inserted = append_synthetic_events(db_path, events)
    logger.info("Inserted %s events into %s", inserted, db_path)
    return inserted


def get_latest_events(db_path: Path, *, limit: int) -> list[NormalizedSyntheticEvent]:
    """Fetch the most recent synthetic events.

    Parameters
    ----------
    db_path:
        Path to the DuckDB database file.
    limit:
        Maximum number of rows to return.

    Returns
    -------
    list[NormalizedSyntheticEvent]
        Latest events, newest first.
    """

    return fetch_synthetic_events(db_path, limit=limit)


def get_total_event_count(db_path: Path) -> int:
    """Return the total number of stored events.

    Notes
    -----
    This intentionally uses `fetch_synthetic_events` for now to avoid adding new
    query helpers prematurely. It can be optimized later.
    """

    return len(fetch_synthetic_events(db_path))
