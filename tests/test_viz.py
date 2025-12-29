from __future__ import annotations

from datetime import UTC, datetime

from synthetic_signal_observatory.analytics import RollingMetricRow
from synthetic_signal_observatory.viz import (
    build_signal_chart_rows,
    build_signal_over_time_chart,
)


def test_build_signal_over_time_chart_applies_x_domain_when_provided() -> None:
    chart_rows = build_signal_chart_rows(
        [
            RollingMetricRow(
                event_id="e1",
                event_ts_utc=datetime(2025, 12, 27, 12, 0, 1, tzinfo=UTC),
                event_date=object(),
                source_id="s1",
                signal_name="alpha",
                signal_value=1.0,
                quality_score=1.0,
                run_id="r1",
                rolling_mean=None,
                rolling_std=None,
                z_score=None,
                is_anomaly=False,
            )
        ]
    )

    domain_start = "2025-12-27T11:59:31+00:00"
    domain_end = "2025-12-27T12:00:31+00:00"

    chart = build_signal_over_time_chart(chart_rows, x_domain=(domain_start, domain_end))
    spec = chart.to_dict()

    # For layered charts, encoding is usually present per-layer.
    first_layer = spec["layer"][0]
    x_encoding = first_layer["encoding"]["x"]
    assert x_encoding["scale"]["domain"] == [domain_start, domain_end]


def test_build_signal_chart_rows_emits_iso_timestamps_and_sorts() -> None:
    rows = build_signal_chart_rows(
        [
            RollingMetricRow(
                event_id="e2",
                event_ts_utc=datetime(2025, 12, 27, 12, 0, 2, tzinfo=UTC),
                event_date=object(),
                source_id="s1",
                signal_name="alpha",
                signal_value=2.0,
                quality_score=1.0,
                run_id="r1",
                rolling_mean=None,
                rolling_std=None,
                z_score=None,
                is_anomaly=False,
            ),
            RollingMetricRow(
                event_id="e1",
                event_ts_utc=datetime(2025, 12, 27, 12, 0, 1, tzinfo=UTC),
                event_date=object(),
                source_id="s1",
                signal_name="alpha",
                signal_value=1.0,
                quality_score=1.0,
                run_id="r1",
                rolling_mean=None,
                rolling_std=None,
                z_score=None,
                is_anomaly=False,
            ),
        ]
    )

    assert rows[0]["event_ts"].endswith("+00:00")
    assert isinstance(rows[0]["event_ts"], str)
    assert rows[0]["event_ts"] < rows[1]["event_ts"]


def test_build_signal_over_time_chart_serializes_inline_data() -> None:
    chart_rows = build_signal_chart_rows(
        [
            RollingMetricRow(
                event_id="e1",
                event_ts_utc=datetime(2025, 12, 27, 12, 0, 1, tzinfo=UTC),
                event_date=object(),
                source_id="s1",
                signal_name="alpha",
                signal_value=1.0,
                quality_score=1.0,
                run_id="r1",
                rolling_mean=None,
                rolling_std=None,
                z_score=None,
                is_anomaly=False,
            )
        ]
    )

    chart = build_signal_over_time_chart(chart_rows)
    spec = chart.to_dict()

    # Layered chart: ensure values are present and JSON-serializable.
    assert "layer" in spec

    # Vega-Lite commonly hoists inline data to the top-level for layered charts.
    values = None
    if "data" in spec and isinstance(spec["data"], dict):
        values = spec["data"].get("values")
    if values is None:
        first_layer = spec["layer"][0]
        if "data" in first_layer and isinstance(first_layer["data"], dict):
            values = first_layer["data"].get("values")

    assert isinstance(values, list)
    assert values[0]["event_ts"] == chart_rows[0]["event_ts"]
