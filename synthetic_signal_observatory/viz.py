"""Visualization helpers.

This module provides small, testable helpers for building Vega-Lite/Altair
inputs. It intentionally avoids Streamlit so it can be unit-tested.

Notes
-----
Altair's inline data (`alt.Data(values=...)`) is serialized to JSON.
Timezone-aware Python `datetime` objects are not reliably JSON-serializable in
that path and can lead to charts rendering blank.

To keep chart rendering stable, we convert timestamps to ISO-8601 strings.
"""

from __future__ import annotations

from datetime import UTC
from typing import Any, Mapping, Sequence

import altair as alt

from synthetic_signal_observatory.analytics import RollingMetricRow


def build_signal_chart_rows(metrics: Sequence[RollingMetricRow]) -> list[dict[str, Any]]:
    """Build JSON-serializable rows for the signal-over-time chart.

    Parameters
    ----------
    metrics:
        Rolling metric rows (typically from `compute_rolling_metrics`).

    Returns
    -------
    list[dict[str, Any]]
        JSON-serializable rows sorted by timestamp.

    Notes
    -----
    - `event_ts` is emitted as an ISO-8601 string in UTC.
    - Sorting is performed by the underlying datetime (not the string), then
      serialized.
    """

    ordered = sorted(metrics, key=lambda row: row.event_ts_utc)

    return [
        {
            "event_ts": row.event_ts_utc.astimezone(UTC).isoformat(),
            "source_id": row.source_id,
            "signal_name": row.signal_name,
            "signal_value": row.signal_value,
            "is_anomaly": row.is_anomaly,
            "z_score": row.z_score,
        }
        for row in ordered
    ]


def build_signal_over_time_chart(chart_rows: Sequence[Mapping[str, Any]]) -> alt.Chart:
    """Build the layered Altair chart used in the Streamlit dashboard.

    Parameters
    ----------
    chart_rows:
        Rows as produced by `build_signal_chart_rows`.

    Returns
    -------
    alt.Chart
        A layered Altair chart (line + points) suitable for Streamlit.
    """

    base = (
        alt.Chart(alt.Data(values=list(chart_rows)))
        .encode(
            x=alt.X("event_ts:T", title="Event timestamp (UTC)"),
            y=alt.Y("signal_value:Q", title="Signal value"),
            # Explicit order avoids jumbled line connections.
            order=alt.Order("event_ts:T"),
            detail=["source_id:N", "signal_name:N"],
            tooltip=[
                alt.Tooltip("event_ts:T"),
                alt.Tooltip("source_id:N"),
                alt.Tooltip("signal_name:N"),
                alt.Tooltip("signal_value:Q", format=".3f"),
                alt.Tooltip("is_anomaly:N"),
                alt.Tooltip("z_score:Q", format=".3f"),
            ],
        )
    )

    line = base.mark_line().encode(color=alt.Color("signal_name:N"))
    points = base.mark_point().encode(
        color=alt.Color("signal_name:N"),
        opacity=alt.condition("datum.is_anomaly", alt.value(1.0), alt.value(0.3)),
        size=alt.condition("datum.is_anomaly", alt.value(120), alt.value(30)),
    )

    return (line + points).interactive()
