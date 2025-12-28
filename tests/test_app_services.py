from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from synthetic_signal_observatory.app_services import (
    generate_and_persist_events,
    get_latest_events,
    get_total_event_count,
)


def test_generate_and_persist_and_read_back(tmp_path: Path) -> None:
    db_path = tmp_path / "sso.duckdb"

    inserted = generate_and_persist_events(
        db_path=db_path,
        count=5,
        start_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
        run_id="run-1",
        seed=123,
        source_ids=["s1"],
        signal_names=["alpha"],
        step=timedelta(seconds=1),
    )

    assert inserted == 5
    assert get_total_event_count(db_path) == 5

    latest = get_latest_events(db_path, limit=3)
    assert len(latest) == 3
    assert latest[0].event_ts_utc >= latest[-1].event_ts_utc
