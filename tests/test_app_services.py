from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from synthetic_signal_observatory.app_services import (
    generate_and_persist_events,
    get_events_for_chart,
    get_events_for_rolling_window,
    get_total_event_count,
    reset_database,
    should_enable_db_reset,
)

from synthetic_signal_observatory.analytics import compute_rolling_metrics


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

    latest = get_events_for_chart(db_path, limit=3)
    assert len(latest) == 3
    assert latest[0].event_ts_utc >= latest[-1].event_ts_utc


def test_generate_and_persist_advances_start_ts_to_avoid_overlaps(tmp_path: Path) -> None:
    db_path = tmp_path / "sso.duckdb"

    start_ts = datetime(2025, 12, 27, 12, 0, tzinfo=UTC)
    step = timedelta(seconds=1)

    generate_and_persist_events(
        db_path=db_path,
        count=5,
        start_ts=start_ts,
        run_id="run-1",
        seed=123,
        source_ids=["s1"],
        signal_names=["alpha"],
        step=step,
    )
    generate_and_persist_events(
        db_path=db_path,
        count=5,
        start_ts=start_ts,
        run_id="run-2",
        seed=123,
        source_ids=["s1"],
        signal_names=["alpha"],
        step=step,
    )

    events = get_events_for_chart(db_path, limit=50)
    run1 = [event for event in events if event.run_id == "run-1"]
    run2 = [event for event in events if event.run_id == "run-2"]

    assert len(run1) == 5
    assert len(run2) == 5

    max_run1_ts = max(event.event_ts_utc for event in run1)
    min_run2_ts = min(event.event_ts_utc for event in run2)

    assert min_run2_ts > max_run1_ts


def test_get_events_for_rolling_window_fetches_sufficient_lookback(tmp_path: Path) -> None:
    db_path = tmp_path / "sso.duckdb"

    # Generate enough history so rolling stats exist for all window events.
    generate_and_persist_events(
        db_path=db_path,
        count=20,
        start_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
        run_id="run-1",
        seed=123,
        source_ids=["s1"],
        signal_names=["alpha"],
        step=timedelta(seconds=1),
    )

    window_limit = 10
    window_size = 5
    window_events, lookback_events = get_events_for_rolling_window(
        db_path,
        window_limit=window_limit,
        window_size=window_size,
    )

    assert len(window_events) == window_limit
    assert len(lookback_events) >= window_limit + window_size

    metrics_all = compute_rolling_metrics(
        lookback_events[::-1],
        window_size=window_size,
        z_threshold=3.0,
    )
    window_ids = {event.event_id for event in window_events}
    window_metrics = [row for row in metrics_all if row.event_id in window_ids]

    # Because the DB has enough history, rolling stats should be present.
    assert all(row.rolling_mean is not None for row in window_metrics)
    assert all(row.rolling_std is not None for row in window_metrics)


def test_get_events_for_chart_can_fetch_full_history_and_filter(tmp_path: Path) -> None:
    db_path = tmp_path / "sso.duckdb"

    generate_and_persist_events(
        db_path=db_path,
        count=10,
        start_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
        run_id="run-1",
        seed=123,
        source_ids=["s1", "s2"],
        signal_names=["alpha", "beta"],
        step=timedelta(seconds=1),
    )

    all_events = get_events_for_chart(db_path, limit=None)
    assert len(all_events) == 10

    s1_events = get_events_for_chart(db_path, source_id="s1", limit=None)
    assert s1_events
    assert all(event.source_id == "s1" for event in s1_events)

    beta_events = get_events_for_chart(db_path, signal_name="beta", limit=None)
    assert beta_events
    assert all(event.signal_name == "beta" for event in beta_events)


def test_reset_database_clears_events(tmp_path: Path) -> None:
    db_path = tmp_path / "sso.duckdb"

    generate_and_persist_events(
        db_path=db_path,
        count=5,
        start_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
        run_id="run-1",
        seed=123,
        source_ids=["s1"],
        signal_names=["alpha"],
        step=timedelta(seconds=1),
    )
    assert get_total_event_count(db_path) == 5

    reset_database(db_path)
    assert get_total_event_count(db_path) == 0


def test_should_enable_db_reset_requires_env_and_confirmation() -> None:
    assert should_enable_db_reset(allow_db_reset=False, confirm_reset=False) is False
    assert should_enable_db_reset(allow_db_reset=False, confirm_reset=True) is False
    assert should_enable_db_reset(allow_db_reset=True, confirm_reset=False) is False
    assert should_enable_db_reset(allow_db_reset=True, confirm_reset=True) is True
