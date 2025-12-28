"""Analytics / modeling layer.

This module contains pure, deterministic analytics functions.

Current scope
-------------
- Rolling mean / stddev per (source_id, signal_name)
- Simple anomaly flagging based on z-score threshold

Design constraints
------------------
- Pure functions only (no I/O).
- Group-aware: metrics are computed independently per source/signal.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime
from math import sqrt
from typing import Iterable

from synthetic_signal_observatory.duckdb_persistence import NormalizedSyntheticEvent


@dataclass(frozen=True, slots=True)
class RollingMetricRow:
    """Rolling metrics for a single event."""

    event_id: str
    event_ts_utc: datetime
    event_date: object
    source_id: str
    signal_name: str
    signal_value: float
    quality_score: float
    run_id: str
    rolling_mean: float | None
    rolling_std: float | None
    z_score: float | None
    is_anomaly: bool


def compute_rolling_metrics(
    events: Iterable[NormalizedSyntheticEvent],
    *,
    window_size: int,
    z_threshold: float,
) -> list[RollingMetricRow]:
    """Compute rolling metrics and anomaly flags per (source_id, signal_name).

    Parameters
    ----------
    events:
        Events to process.
    window_size:
        Rolling window size (must be >= 1). Rolling statistics are computed using
        the preceding window (excluding the current event).
    z_threshold:
        Z-score threshold for anomaly detection.

    Returns
    -------
    list[RollingMetricRow]
        Metrics ordered by event_ts ascending.

    Notes
    -----
    - The first event(s) in each group will have `None` rolling stats until
      enough history exists.
    - An anomaly is flagged when std > 0 and abs(z_score) >= z_threshold.
    """

    if window_size < 1:
        raise ValueError("window_size must be >= 1")

    # Normalize order: analytics should be stable regardless of input ordering.
    ordered_events = sorted(events, key=lambda e: e.event_ts_utc)

    # Maintain rolling windows per group.
    windows: dict[tuple[str, str], deque[float]] = defaultdict(
        lambda: deque(maxlen=window_size)
    )

    results: list[RollingMetricRow] = []

    for event in ordered_events:
        # Ensure we consistently treat timestamps as UTC.
        event_ts_utc = event.event_ts_utc.astimezone(UTC)

        key = (event.source_id, event.signal_name)
        window = windows[key]

        # Require a full lookback window before producing rolling stats.
        # This keeps early points from being flagged due to tiny sample sizes.
        if len(window) < window_size:
            rolling_mean = None
            rolling_std = None
            z_score = None
            is_anomaly = False
        else:
            rolling_mean = sum(window) / len(window)
            variance = sum((x - rolling_mean) ** 2 for x in window) / len(window)
            rolling_std = sqrt(variance)

            if rolling_std == 0.0:
                z_score = 0.0
                is_anomaly = False
            else:
                z_score = (event.signal_value - rolling_mean) / rolling_std
                is_anomaly = abs(z_score) >= z_threshold

        results.append(
            RollingMetricRow(
                event_id=event.event_id,
                event_ts_utc=event_ts_utc,
                event_date=event.event_date,
                source_id=event.source_id,
                signal_name=event.signal_name,
                signal_value=float(event.signal_value),
                quality_score=float(event.quality_score),
                run_id=event.run_id,
                rolling_mean=rolling_mean,
                rolling_std=rolling_std,
                z_score=z_score,
                is_anomaly=is_anomaly,
            )
        )

        # Update rolling window *after* computing stats for the current event.
        window.append(float(event.signal_value))

    return results
