from __future__ import annotations

from datetime import UTC, datetime

import pytest

from synthetic_signal_observatory.analytics import compute_rolling_metrics
from synthetic_signal_observatory.duckdb_persistence import NormalizedSyntheticEvent


def test_compute_rolling_metrics_requires_positive_window_size() -> None:
    with pytest.raises(ValueError, match="window_size"):
        compute_rolling_metrics([], window_size=0, z_threshold=3.0)


def test_compute_rolling_metrics_flags_simple_anomaly() -> None:
    # Window of 3: first three are baseline ~10, fourth is a spike.
    events = [
        NormalizedSyntheticEvent(
            event_id=f"e{i}",
            event_ts_utc=datetime(2025, 12, 27, 12, i, tzinfo=UTC),
            event_date=datetime(2025, 12, 27, tzinfo=UTC).date(),
            source_id="s1",
            signal_name="alpha",
            signal_value=value,
            quality_score=1.0,
            run_id="r1",
        )
        for i, value in enumerate([10.0, 10.5, 9.5, 30.0])
    ]

    metrics = compute_rolling_metrics(events, window_size=3, z_threshold=3.0)

    assert len(metrics) == 4

    # Last point should be an anomaly.
    assert metrics[-1].event_id == "e3"
    assert metrics[-1].is_anomaly is True

    # Earlier points should not be anomalies.
    assert any(m.is_anomaly for m in metrics[:-1]) is False


def test_compute_rolling_metrics_is_grouped_by_source_and_signal() -> None:
    events = [
        NormalizedSyntheticEvent(
            event_id="a1",
            event_ts_utc=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
            event_date=datetime(2025, 12, 27, tzinfo=UTC).date(),
            source_id="s1",
            signal_name="alpha",
            signal_value=0.0,
            quality_score=1.0,
            run_id="r1",
        ),
        NormalizedSyntheticEvent(
            event_id="b1",
            event_ts_utc=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
            event_date=datetime(2025, 12, 27, tzinfo=UTC).date(),
            source_id="s2",
            signal_name="alpha",
            signal_value=100.0,
            quality_score=1.0,
            run_id="r1",
        ),
        NormalizedSyntheticEvent(
            event_id="a2",
            event_ts_utc=datetime(2025, 12, 27, 12, 1, tzinfo=UTC),
            event_date=datetime(2025, 12, 27, tzinfo=UTC).date(),
            source_id="s1",
            signal_name="alpha",
            signal_value=0.0,
            quality_score=1.0,
            run_id="r1",
        ),
    ]

    metrics = compute_rolling_metrics(events, window_size=2, z_threshold=2.0)

    # Ensure metrics are returned for all events and include group keys.
    assert {(m.source_id, m.signal_name) for m in metrics} == {("s1", "alpha"), ("s2", "alpha")}
