"""Synthetic Signal Observatory Streamlit app.

This is intentionally minimal: it proves the dashboard entrypoint runs and gives
us a place to iteratively wire in synthetic data generation, persistence, and
analytics.

Notes
-----
Streamlit reruns the script on interaction, so keep side effects out of module
scope and prefer pure functions (called from within the app body).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

import streamlit as st

from synthetic_signal_observatory.app_services import (
    generate_and_persist_events,
    get_latest_events,
    get_total_event_count,
)
from synthetic_signal_observatory.analytics import compute_rolling_metrics

logger = logging.getLogger(__name__)


def render_app() -> None:
    """Render the minimal Streamlit UI.

    This function is the UI entrypoint. It contains no business logic; it should
    only orchestrate layout and call pure helper functions as the project grows.
    """

    # Keep the UI intentionally minimal for Phase 0.
    st.set_page_config(page_title="Synthetic Signal Observatory", layout="centered")

    st.title("Synthetic Signal Observatory")
    st.markdown(
        "This dashboard generates synthetic signals, persists them in DuckDB, "
        "and shows the latest events."
    )

    db_path = Path("data/sso.duckdb")

    col_left, col_right = st.columns(2)

    with col_left:
        if st.button("Generate a small batch"):
            now_utc = datetime.now(tz=UTC)
            run_id = now_utc.strftime("run-%Y%m%d-%H%M%S")

            inserted = generate_and_persist_events(
                db_path=db_path,
                count=25,
                start_ts=now_utc,
                run_id=run_id,
                seed=42,
                source_ids=["source-1", "source-2", "source-3"],
                signal_names=["alpha", "beta"],
                step=timedelta(seconds=1),
            )
            st.success(f"Inserted {inserted} events")

    with col_right:
        total_rows = get_total_event_count(db_path)
        st.metric(label="Total stored events", value=total_rows)

    latest_events = get_latest_events(db_path, limit=20)
    st.subheader("Latest events")
    st.dataframe(
        [
            {
                "event_id": event.event_id,
                "event_ts": event.event_ts_utc,
                "event_date": event.event_date,
                "source_id": event.source_id,
                "signal_name": event.signal_name,
                "signal_value": event.signal_value,
                "quality_score": event.quality_score,
                "run_id": event.run_id,
            }
            for event in latest_events
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Analytics (rolling metrics)")

    window_size = st.slider(
        label="Rolling window size",
        min_value=2,
        max_value=25,
        value=5,
        step=1,
    )
    z_threshold = st.slider(
        label="Z-score threshold",
        min_value=0.5,
        max_value=10.0,
        value=3.0,
        step=0.5,
    )

    metrics = compute_rolling_metrics(
        latest_events[::-1],
        window_size=window_size,
        z_threshold=z_threshold,
    )
    anomaly_count = sum(1 for row in metrics if row.is_anomaly)
    st.metric(label="Anomalies in view", value=anomaly_count)
    st.dataframe(
        [
            {
                "event_ts": row.event_ts_utc,
                "source_id": row.source_id,
                "signal_name": row.signal_name,
                "signal_value": row.signal_value,
                "rolling_mean": row.rolling_mean,
                "rolling_std": row.rolling_std,
                "z_score": row.z_score,
                "is_anomaly": row.is_anomaly,
            }
            for row in metrics
        ],
        use_container_width=True,
        hide_index=True,
    )

    logger.info("Streamlit app rendered")


if __name__ == "__main__":
    render_app()
