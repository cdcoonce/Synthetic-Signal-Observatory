"""DuckDB persistence helpers.

The project uses DuckDB as the system of record for raw synthetic events.

This module intentionally keeps responsibilities narrow:
- Validate/normalize events to match architecture invariants.
- Create/ensure the `synthetic_events` table.
- Append and fetch events.

Business logic should remain pure; these functions accept explicit inputs
(e.g., db_path) and avoid hidden globals.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, date
from pathlib import Path
from typing import Iterable, Sequence

import duckdb

logger = logging.getLogger(__name__)


TABLE_NAME = "synthetic_events"


@dataclass(frozen=True, slots=True)
class SyntheticEvent:
    """A single raw synthetic event.

    Parameters
    ----------
    event_id:
        Unique identifier for the event.
    event_ts:
        Timezone-aware event timestamp.
    source_id:
        Synthetic source identifier (e.g., sensor/device/user).
    signal_name:
        Name of the synthetic signal.
    signal_value:
        Numeric value for the signal.
    quality_score:
        Quality score in [0.0, 1.0] (will be clamped on normalization).
    run_id:
        Identifier for the generator run/session.
    """

    event_id: str
    event_ts: datetime
    source_id: str
    signal_name: str
    signal_value: float
    quality_score: float
    run_id: str


@dataclass(frozen=True, slots=True)
class NormalizedSyntheticEvent:
    """A normalized synthetic event ready for persistence."""

    event_id: str
    event_ts_utc: datetime
    event_date: date
    source_id: str
    signal_name: str
    signal_value: float
    quality_score: float
    run_id: str


def normalize_synthetic_event(event: SyntheticEvent) -> NormalizedSyntheticEvent:
    """Validate and normalize a raw event.

    This function enforces architecture invariants:
    - `event_ts` MUST be timezone-aware and normalized to UTC.
    - `quality_score` MUST be clamped to [0.0, 1.0].

    Parameters
    ----------
    event:
        Raw event.

    Returns
    -------
    NormalizedSyntheticEvent
        Normalized event with UTC timestamp and derived UTC event_date.

    Raises
    ------
    ValueError
        If required fields are missing/invalid or event_ts is naive.
    """

    if not event.event_id:
        raise ValueError("event_id must be a non-empty string")

    if event.event_ts.tzinfo is None or event.event_ts.utcoffset() is None:
        raise ValueError("event_ts must be timezone-aware")

    event_ts_utc = event.event_ts.astimezone(UTC)
    event_date = event_ts_utc.date()

    quality_score = min(1.0, max(0.0, float(event.quality_score)))

    return NormalizedSyntheticEvent(
        event_id=str(event.event_id),
        event_ts_utc=event_ts_utc,
        event_date=event_date,
        source_id=str(event.source_id),
        signal_name=str(event.signal_name),
        signal_value=float(event.signal_value),
        quality_score=quality_score,
        run_id=str(event.run_id),
    )


def _ensure_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Ensure the `synthetic_events` table exists."""

    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            event_id VARCHAR,
            event_ts TIMESTAMPTZ,
            event_date DATE,
            source_id VARCHAR,
            signal_name VARCHAR,
            signal_value DOUBLE,
            quality_score DOUBLE,
            run_id VARCHAR
        )
        """
    )


def _table_exists(connection: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    """Return whether a table exists in the current DuckDB database.

    Parameters
    ----------
    connection:
        An open DuckDB connection.
    table_name:
        Table name to check.

    Returns
    -------
    bool
        True if the table exists, else False.
    """

    result = connection.execute(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name = ?
        LIMIT 1
        """.strip(),
        [table_name],
    ).fetchone()
    return result is not None


def append_synthetic_events(db_path: Path, events: Sequence[SyntheticEvent]) -> int:
    """Append synthetic events to DuckDB.

    Parameters
    ----------
    db_path:
        Path to the DuckDB database file.
    events:
        Events to append.

    Returns
    -------
    int
        Number of events appended.

    Notes
    -----
    - This function creates the database/table if needed.
    - Events are normalized before persistence.
    """

    if not isinstance(db_path, Path):
        raise TypeError("db_path must be a pathlib.Path")

    if not events:
        return 0

    normalized_events = [normalize_synthetic_event(event) for event in events]

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(db_path)) as connection:
        _ensure_table(connection)

        rows = [
            (
                event.event_id,
                event.event_ts_utc,
                event.event_date,
                event.source_id,
                event.signal_name,
                event.signal_value,
                event.quality_score,
                event.run_id,
            )
            for event in normalized_events
        ]

        connection.executemany(
            f"""
            INSERT INTO {TABLE_NAME} (
                event_id,
                event_ts,
                event_date,
                source_id,
                signal_name,
                signal_value,
                quality_score,
                run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """.strip(),
            rows,
        )

    logger.info("Appended %s events to %s", len(events), db_path)
    return len(events)


def fetch_synthetic_events(
    db_path: Path,
    *,
    limit: int | None = None,
) -> list[NormalizedSyntheticEvent]:
    """Fetch normalized synthetic events from DuckDB.

    Parameters
    ----------
    db_path:
        Path to the DuckDB database file.
    limit:
        Optional maximum number of rows to return.

    Returns
    -------
    list[NormalizedSyntheticEvent]
        Events ordered by timestamp descending.
    """

    if not isinstance(db_path, Path):
        raise TypeError("db_path must be a pathlib.Path")

    if not db_path.exists():
        return []

    limit_sql = "" if limit is None else "LIMIT ?"

    with duckdb.connect(str(db_path), read_only=True) as connection:
        if not _table_exists(connection, TABLE_NAME):
            return []
        if limit is None:
            result = connection.execute(
                f"""
                SELECT
                    event_id,
                    event_ts,
                    event_date,
                    source_id,
                    signal_name,
                    signal_value,
                    quality_score,
                    run_id
                FROM {TABLE_NAME}
                ORDER BY event_ts DESC
                """.strip()
            ).fetchall()
        else:
            if limit <= 0:
                return []
            result = connection.execute(
                f"""
                SELECT
                    event_id,
                    event_ts,
                    event_date,
                    source_id,
                    signal_name,
                    signal_value,
                    quality_score,
                    run_id
                FROM {TABLE_NAME}
                ORDER BY event_ts DESC
                {limit_sql}
                """.strip(),
                [limit],
            ).fetchall()

    return [
        NormalizedSyntheticEvent(
            event_id=row[0],
            event_ts_utc=row[1].astimezone(UTC),
            event_date=row[2],
            source_id=row[3],
            signal_name=row[4],
            signal_value=float(row[5]),
            quality_score=float(row[6]),
            run_id=row[7],
        )
        for row in result
    ]
