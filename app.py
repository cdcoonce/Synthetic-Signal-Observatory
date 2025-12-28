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

import streamlit as st

from synthetic_signal_observatory.app_services import (
    generate_and_persist_events,
    get_events_for_chart,
    get_events_for_rolling_window,
    get_latest_events,
    get_total_event_count,
    reset_database,
    should_enable_db_reset,
)
from synthetic_signal_observatory.analytics import compute_rolling_metrics
from synthetic_signal_observatory.config import AppConfig, load_app_config
from synthetic_signal_observatory.viz import (
    build_signal_chart_rows,
    build_signal_over_time_chart,
)

logger = logging.getLogger(__name__)


def _generate_batch(config: AppConfig) -> int:
    """Generate and persist a batch of synthetic events.

    Parameters
    ----------
    config:
        Application configuration.

    Returns
    -------
    int
        Number of events inserted.
    """
    now_utc = datetime.now(tz=UTC)
    run_id = now_utc.strftime("run-%Y%m%d-%H%M%S")

    return generate_and_persist_events(
        db_path=config.db_path,
        count=config.batch_size,
        start_ts=now_utc,
        run_id=run_id,
        seed=config.seed,
        source_ids=["source-1"],
        signal_names=["alpha", "beta", "gamma", "delta"],
        step=timedelta(seconds=1),
    )


def render_app() -> None:
    """Render the Streamlit UI.

    This function is the UI entrypoint. It contains no business logic; it should
    only orchestrate layout and call pure helper functions as the project grows.
    """
    st.set_page_config(page_title="Synthetic Signal Observatory", layout="centered")

    st.title("Synthetic Signal Observatory")
    st.markdown(
        "This dashboard generates synthetic signals, persists them in DuckDB, "
        "and shows the latest events."
    )

    config = load_app_config()
    db_path = config.db_path

    # -------------------------------------------------------------------------
    # Live Mode Controls (outside fragment so they persist across refreshes)
    # -------------------------------------------------------------------------
    st.subheader("Live Mode")

    col_live_toggle, col_interval = st.columns([1, 1])

    with col_live_toggle:
        live_mode = st.toggle(
            label="🟢 Live Mode",
            value=config.auto_run_default,
            help="Auto-generate events at the configured interval",
        )

    with col_interval:
        refresh_interval = st.slider(
            label="Refresh interval (seconds)",
            min_value=1,
            max_value=10,
            value=config.auto_refresh_interval,
            step=1,
            disabled=not live_mode,
        )

    if live_mode:
        st.info(f"🔴 Streaming — generating events every {refresh_interval}s")

    # -------------------------------------------------------------------------
    # Manual Generation (only when not in live mode)
    # -------------------------------------------------------------------------
    if not live_mode:
        col_left, col_right = st.columns(2)

        with col_left:
            if st.button("Generate a small batch"):
                inserted = _generate_batch(config)
                st.success(f"Inserted {inserted} events")

        with col_right:
            total_rows = get_total_event_count(db_path)
            st.metric(label="Total stored events", value=total_rows)

    # -------------------------------------------------------------------------
    # Analytics Controls (outside fragment so they persist)
    # -------------------------------------------------------------------------
    st.subheader("Analytics (rolling metrics)")

    col_window, col_z = st.columns(2)
    with col_window:
        window_size = st.slider(
            label="Rolling window size",
            min_value=2,
            max_value=100,
            value=5,
            step=1,
        )
    with col_z:
        z_threshold = st.slider(
            label="Z-score threshold",
            min_value=0.5,
            max_value=10.0,
            value=3.0,
            step=0.5,
        )

    # -------------------------------------------------------------------------
    # Signal over time
    # -------------------------------------------------------------------------
    st.subheader("Signal over time")

    # -------------------------------------------------------------------------
    # Live Panel Fragment — auto-refreshes when live_mode is enabled
    # -------------------------------------------------------------------------
    @st.fragment(
        run_every=timedelta(seconds=refresh_interval) if live_mode else None
    )
    def live_panel() -> None:
        """Fragment that displays metrics/chart/table and optionally generates events."""
        # Generate events when in live mode
        if live_mode:
            _generate_batch(config)

        # Metrics
        total_rows = get_total_event_count(db_path)
        st.metric(label="Total stored events", value=total_rows)

        # Chart (at the top of the fragment)
        chart_events_all = get_events_for_chart(db_path, limit=None)
        available_sources = sorted({event.source_id for event in chart_events_all})
        available_signals = sorted({event.signal_name for event in chart_events_all})

        source_options = ["(all)", *available_sources]
        signal_options = ["(all)", *available_signals]

        selected_source = st.session_state.get("chart_source_filter", "(all)")
        selected_signal = st.session_state.get("chart_signal_filter", "(all)")

        if selected_source not in source_options:
            selected_source = "(all)"
        if selected_signal not in signal_options:
            selected_signal = "(all)"

        chart_source = None if selected_source == "(all)" else selected_source
        chart_signal = None if selected_signal == "(all)" else selected_signal

        chart_events = get_events_for_chart(
            db_path,
            source_id=chart_source,
            signal_name=chart_signal,
            limit=None,
        )
        chart_metrics = compute_rolling_metrics(
            chart_events[::-1],
            window_size=window_size,
            z_threshold=z_threshold,
        )

        chart_rows = build_signal_chart_rows(chart_metrics)
        if not chart_rows:
            st.info("No data to chart yet (generate events first).")
        else:
            chart = build_signal_over_time_chart(chart_rows)
            st.altair_chart(chart, width='stretch')

        # Filters (below the chart, side-by-side)
        filters_disabled = not chart_events_all
        col_source, col_signal = st.columns(2)
        with col_source:
            st.selectbox(
                label="Source",
                options=source_options,
                index=source_options.index(selected_source),
                key="chart_source_filter",
                disabled=filters_disabled,
            )
        with col_signal:
            st.selectbox(
                label="Signal",
                options=signal_options,
                index=signal_options.index(selected_signal),
                key="chart_signal_filter",
                disabled=filters_disabled,
            )

        # Rolling metrics
        window_events, lookback_events = get_events_for_rolling_window(
            db_path,
            window_limit=20,
            window_size=window_size,
        )
        metrics_all = compute_rolling_metrics(
            lookback_events[::-1],
            window_size=window_size,
            z_threshold=z_threshold,
        )
        window_event_ids = {event.event_id for event in window_events}
        metrics = [row for row in metrics_all if row.event_id in window_event_ids]
        anomaly_count = sum(1 for row in metrics if row.is_anomaly)
        st.metric(label="Anomalies in view", value=anomaly_count)

        # Latest events table
        latest_events = get_latest_events(db_path, limit=20)
        st.markdown("**Latest events**")
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
            width='stretch',
            hide_index=True,
        )

        # Analytics table
        st.markdown("**Rolling metrics**")
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
            width='stretch',
            hide_index=True,
        )

        if live_mode:
            st.caption(f"Last updated: {datetime.now(tz=UTC).strftime('%H:%M:%S')} UTC")

    # Invoke the fragment
    live_panel()

    # -------------------------------------------------------------------------
    # Database Reset Controls (moved below chart)
    # -------------------------------------------------------------------------
    st.subheader("Database")
    if not config.allow_db_reset:
        st.info("Database reset is disabled. Set `SSO_ALLOW_DB_RESET=1` to enable it.")
    confirm_reset = st.checkbox(
        label="I understand this deletes all stored events",
        value=False,
        disabled=False,
    )
    reset_clicked = st.button(
        "Reset database",
        disabled=not should_enable_db_reset(
            allow_db_reset=config.allow_db_reset,
            confirm_reset=confirm_reset,
        ),
    )
    if reset_clicked:
        reset_database(db_path)
        st.success("Database reset: synthetic_events table dropped")
        st.rerun()

    logger.info("Streamlit app rendered")


if __name__ == "__main__":
    render_app()
