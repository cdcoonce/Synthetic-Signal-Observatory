from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from synthetic_signal_observatory.duckdb_persistence import SyntheticEvent
from synthetic_signal_observatory.generator import generate_synthetic_events


def test_generate_synthetic_events_returns_expected_count() -> None:
    events = generate_synthetic_events(
        count=3,
        start_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
        run_id="run-1",
        seed=123,
        source_ids=["s1"],
        signal_names=["alpha"],
        step=timedelta(seconds=1),
    )

    assert len(events) == 3
    assert all(isinstance(event, SyntheticEvent) for event in events)


def test_generate_synthetic_events_produces_utc_timezone_aware_timestamps() -> None:
    events = generate_synthetic_events(
        count=2,
        start_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
        run_id="run-1",
        seed=123,
        source_ids=["s1"],
        signal_names=["alpha"],
        step=timedelta(seconds=30),
    )

    assert events[0].event_ts.tzinfo is UTC
    assert events[1].event_ts.tzinfo is UTC
    assert events[1].event_ts > events[0].event_ts


def test_generate_synthetic_events_snaps_to_whole_seconds() -> None:
    events = generate_synthetic_events(
        count=3,
        start_ts=datetime(2025, 12, 27, 12, 0, 0, 123456, tzinfo=UTC),
        run_id="run-1",
        seed=123,
        source_ids=["s1"],
        signal_names=["alpha"],
        step=timedelta(seconds=1),
    )

    assert all(event.event_ts.microsecond == 0 for event in events)
    assert events[0].event_ts == datetime(2025, 12, 27, 12, 0, 0, tzinfo=UTC)
    assert events[1].event_ts == datetime(2025, 12, 27, 12, 0, 1, tzinfo=UTC)


def test_generate_synthetic_events_quality_score_in_range() -> None:
    events = generate_synthetic_events(
        count=50,
        start_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
        run_id="run-1",
        seed=999,
        source_ids=["s1", "s2"],
        signal_names=["alpha", "beta"],
        step=timedelta(seconds=1),
    )

    assert all(0.0 <= event.quality_score <= 1.0 for event in events)


def test_generate_synthetic_events_is_deterministic_given_seed() -> None:
    params = dict(
        count=10,
        start_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
        run_id="run-1",
        seed=42,
        source_ids=["s1", "s2"],
        signal_names=["alpha", "beta"],
        step=timedelta(seconds=5),
    )

    events_a = generate_synthetic_events(**params)
    events_b = generate_synthetic_events(**params)

    assert [event.event_id for event in events_a] == [event.event_id for event in events_b]
    assert [event.signal_value for event in events_a] == [event.signal_value for event in events_b]
    assert [event.source_id for event in events_a] == [event.source_id for event in events_b]
    assert [event.signal_name for event in events_a] == [event.signal_name for event in events_b]


def test_generate_synthetic_events_varies_across_run_ids() -> None:
    """Different run_ids should produce different sequences.

    This prevents the Streamlit Live Mode from looking like it is repeating the
    exact same batch over and over when the base seed is constant.
    """

    base_params = dict(
        count=25,
        start_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
        seed=42,
        source_ids=["s1"],
        signal_names=["alpha"],
        step=timedelta(seconds=1),
    )

    events_a = generate_synthetic_events(run_id="run-a", **base_params)
    events_b = generate_synthetic_events(run_id="run-b", **base_params)

    assert [event.signal_value for event in events_a] != [
        event.signal_value for event in events_b
    ]


def test_generate_synthetic_events_requires_timezone_aware_start_ts() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        generate_synthetic_events(
            count=1,
            start_ts=datetime(2025, 12, 27, 12, 0),
            run_id="run-1",
            seed=1,
            source_ids=["s1"],
            signal_names=["alpha"],
            step=timedelta(seconds=1),
        )


def test_generate_synthetic_events_rejects_empty_source_or_signal_lists() -> None:
    with pytest.raises(ValueError, match="source_ids"):
        generate_synthetic_events(
            count=1,
            start_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
            run_id="run-1",
            seed=1,
            source_ids=[],
            signal_names=["alpha"],
            step=timedelta(seconds=1),
        )

    with pytest.raises(ValueError, match="signal_names"):
        generate_synthetic_events(
            count=1,
            start_ts=datetime(2025, 12, 27, 12, 0, tzinfo=UTC),
            run_id="run-1",
            seed=1,
            source_ids=["s1"],
            signal_names=[],
            step=timedelta(seconds=1),
        )
