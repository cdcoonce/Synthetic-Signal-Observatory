from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from synthetic_signal_observatory.duckdb_persistence import (
    SyntheticEvent,
    append_synthetic_events,
    fetch_synthetic_events,
    normalize_synthetic_event,
    reset_synthetic_events_table,
)


def test_normalize_requires_timezone_aware_timestamp() -> None:
    event = SyntheticEvent(
        event_id="e1",
        event_ts=datetime(2025, 12, 27, 12, 0, 0),
        source_id="s1",
        signal_name="alpha",
        signal_value=1.0,
        quality_score=0.5,
        run_id="r1",
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        normalize_synthetic_event(event)


def test_normalize_converts_to_utc_and_clamps_quality_score() -> None:
    # UTC-5 offset as a fixed offset timezone
    tz_minus_5 = timezone(timedelta(hours=-5))

    event = SyntheticEvent(
        event_id="e1",
        event_ts=datetime(2025, 12, 27, 23, 30, tzinfo=tz_minus_5),
        source_id="s1",
        signal_name="alpha",
        signal_value=1.0,
        quality_score=99.0,
        run_id="r1",
    )

    normalized = normalize_synthetic_event(event)

    assert normalized.event_ts_utc.tzinfo is UTC
    assert normalized.quality_score == 1.0
    assert normalized.event_date == normalized.event_ts_utc.date()


def test_append_and_fetch_round_trip(tmp_path: Path) -> None:
    db_path = tmp_path / "sso.duckdb"

    event_1 = SyntheticEvent(
        event_id="e1",
        event_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
        source_id="s1",
        signal_name="alpha",
        signal_value=1.0,
        quality_score=-1.0,
        run_id="r1",
    )

    event_2 = SyntheticEvent(
        event_id="e2",
        event_ts=datetime(2025, 12, 27, 12, 1, tzinfo=UTC),
        source_id="s1",
        signal_name="alpha",
        signal_value=2.0,
        quality_score=0.2,
        run_id="r1",
    )

    inserted = append_synthetic_events(db_path, [event_1, event_2])
    assert inserted == 2

    fetched = fetch_synthetic_events(db_path)

    # Ordered by event_ts DESC
    assert [e.event_id for e in fetched] == ["e2", "e1"]

    # Normalization applied
    assert fetched[-1].quality_score == 0.0
    assert fetched[-1].event_ts_utc.tzinfo is UTC


def test_reset_synthetic_events_table_drops_table_and_is_idempotent(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "sso.duckdb"

    inserted = append_synthetic_events(
        db_path,
        [
            SyntheticEvent(
                event_id="e1",
                event_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
                source_id="s1",
                signal_name="alpha",
                signal_value=1.0,
                quality_score=0.5,
                run_id="r1",
            )
        ],
    )
    assert inserted == 1
    assert fetch_synthetic_events(db_path)

    reset_synthetic_events_table(db_path)
    assert fetch_synthetic_events(db_path) == []

    # Idempotent: dropping twice should not raise.
    reset_synthetic_events_table(db_path)
    assert fetch_synthetic_events(db_path) == []
