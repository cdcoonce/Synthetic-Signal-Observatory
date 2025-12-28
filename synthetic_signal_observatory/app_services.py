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


def _require_timezone_aware(timestamp: datetime, *, field_name: str) -> None:
    """Raise if a timestamp is naive.

    Parameters
    ----------
    timestamp:
        Timestamp to validate.
    field_name:
        Field name for error messages.

    Raises
    ------
    ValueError
        If the timestamp is naive.
    """

    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _choose_effective_start_ts(
    *,
    db_path: Path,
    requested_start_ts: datetime,
    step: timedelta,
) -> datetime:
    """Choose a start timestamp that avoids collisions with persisted data.

    Motivation
    ----------
    Streamlit charts (Vega-Lite) effectively operate at millisecond precision.
    If multiple batches are generated near the same wall clock time, timestamps
    that differ only in microseconds can collapse to the same rendered instant,
    making time-series lines look "jumbled".

    Strategy
    --------
    If the database already has events, advance the start timestamp to be at
    least one `step` after the latest persisted event.
    """

    _require_timezone_aware(requested_start_ts, field_name="start_ts")
    requested_start_ts_utc = requested_start_ts.astimezone(UTC).replace(microsecond=0)

    latest = fetch_synthetic_events(db_path, limit=1)
    if not latest:
        return requested_start_ts_utc

    latest_ts = latest[0].event_ts_utc.replace(microsecond=0)
    if requested_start_ts_utc <= latest_ts:
        return latest_ts + step

    return requested_start_ts_utc


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

    effective_start_ts = _choose_effective_start_ts(
        db_path=db_path,
        requested_start_ts=start_ts,
        step=step,
    )

    events: list[SyntheticEvent] = generate_synthetic_events(
        count=count,
        start_ts=effective_start_ts,
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


def get_events_for_chart(
    db_path: Path,
    *,
    source_id: str | None = None,
    signal_name: str | None = None,
    limit: int | None = None,
) -> list[NormalizedSyntheticEvent]:
    """Fetch events intended for charting.

    Parameters
    ----------
    db_path:
        Path to the DuckDB database file.
    source_id:
        Optional source filter. When provided, only events for this source are
        returned.
    signal_name:
        Optional signal filter. When provided, only events for this signal are
        returned.
    limit:
        Optional maximum number of rows to return. Use ``None`` to fetch all
        persisted events.

    Returns
    -------
    list[NormalizedSyntheticEvent]
        Events ordered newest-first (as stored query ordering).

    Notes
    -----
    This is intentionally a thin wrapper around persistence so Streamlit can
    fetch full history for pan/zoom exploration without duplicating filtering
    logic in the UI layer.
    """

    events = fetch_synthetic_events(db_path, limit=limit)
    if source_id is not None:
        events = [event for event in events if event.source_id == source_id]
    if signal_name is not None:
        events = [event for event in events if event.signal_name == signal_name]
    return events


def get_events_for_rolling_window(
    db_path: Path,
    *,
    window_limit: int,
    window_size: int,
    max_fetch_limit: int = 5_000,
) -> tuple[list[NormalizedSyntheticEvent], list[NormalizedSyntheticEvent]]:
    """Return (window_events, lookback_events) for rolling analytics.

    Parameters
    ----------
    db_path:
        Path to the DuckDB database file.
    window_limit:
        Number of latest events to display in the UI window (newest first).
    window_size:
        Rolling window size used by analytics.
    max_fetch_limit:
        Safety cap for how many rows to fetch while searching for sufficient
        lookback history.

    Returns
    -------
    tuple[list[NormalizedSyntheticEvent], list[NormalizedSyntheticEvent]]
        - window_events: latest N events (newest first)
        - lookback_events: a superset of events that includes enough prior
          history (when available) so rolling metrics are computed for every
          event in the window.

    Notes
    -----
    Rolling metrics for an event require `window_size` prior values in the same
    (source_id, signal_name) group. This function will progressively fetch more
    recent history until either:
    - every window event has sufficient prior history within the fetched set, or
    - the database does not contain enough data, or
    - max_fetch_limit is reached.
    """

    if window_limit <= 0:
        return ([], [])
    if window_size < 1:
        raise ValueError("window_size must be >= 1")

    window_events = fetch_synthetic_events(db_path, limit=window_limit)
    if not window_events:
        return ([], [])

    window_event_ids = {event.event_id for event in window_events}

    def lookback_satisfied(events: list[NormalizedSyntheticEvent]) -> bool:
        ordered = sorted(events, key=lambda e: e.event_ts_utc)
        index_by_id: dict[str, int] = {}
        group_positions: dict[tuple[str, str], int] = {}

        for event in ordered:
            key = (event.source_id, event.signal_name)
            group_positions[key] = group_positions.get(key, 0) + 1
            # Position is 1-based count within group; prior count is pos-1.
            index_by_id[event.event_id] = group_positions[key] - 1

        for event_id in window_event_ids:
            prior_count = index_by_id.get(event_id)
            if prior_count is None:
                return False
            if prior_count < window_size:
                return False
        return True

    fetch_limit = min(max_fetch_limit, window_limit + window_size * 10)
    while True:
        lookback_events = fetch_synthetic_events(db_path, limit=fetch_limit)
        if len(lookback_events) <= window_limit:
            return (window_events, lookback_events)

        if lookback_satisfied(lookback_events):
            return (window_events, lookback_events)

        if fetch_limit >= max_fetch_limit:
            return (window_events, lookback_events)

        fetch_limit = min(max_fetch_limit, fetch_limit * 2)


def get_total_event_count(db_path: Path) -> int:
    """Return the total number of stored events.

    Notes
    -----
    This intentionally uses `fetch_synthetic_events` for now to avoid adding new
    query helpers prematurely. It can be optimized later.
    """

    return len(fetch_synthetic_events(db_path))
