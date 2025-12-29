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


def _compute_centered_domain_iso(
    *, center_ts_utc: datetime, window_seconds: int
) -> tuple[str, str]:
    """Compute an ISO-8601 x-domain centered on a timestamp.

    Parameters
    ----------
    center_ts_utc:
        Center timestamp for the domain. Must be timezone-aware.
    window_seconds:
        Total window width in seconds.

    Returns
    -------
    tuple[str, str]
        ``(domain_start, domain_end)`` as ISO-8601 UTC strings.
    """

    if center_ts_utc.tzinfo is None:
        raise ValueError("center_ts_utc must be timezone-aware")
    if window_seconds <= 0:
        raise ValueError("window_seconds must be > 0")

    half_window = timedelta(seconds=window_seconds / 2)
    start_ts = (center_ts_utc - half_window).astimezone(UTC)
    end_ts = (center_ts_utc + half_window).astimezone(UTC)
    return start_ts.isoformat(), end_ts.isoformat()


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
        "and shows rolling metrics."
    )

    config = load_app_config()
    db_path = config.db_path

    # -------------------------------------------------------------------------
    # Sidebar Controls (inputs live here)
    # -------------------------------------------------------------------------
    # Pull available filter options outside the fragment so the controls remain
    # stable across auto-refresh reruns.
    events_for_filter_options = get_events_for_chart(db_path, limit=None)
    available_sources = sorted({event.source_id for event in events_for_filter_options})
    available_signals = sorted({event.signal_name for event in events_for_filter_options})
    source_options = ["(all)", *available_sources]
    signal_options = ["(all)", *available_signals]
    filters_disabled = not bool(events_for_filter_options)

    selected_source = st.session_state.get("chart_source_filter", "(all)")
    selected_signal = st.session_state.get("chart_signal_filter", "(all)")
    if selected_source not in source_options:
        selected_source = "(all)"
    if selected_signal not in signal_options:
        selected_signal = "(all)"

    with st.sidebar:
        st.subheader("Live Mode")

        initial_live_mode = bool(
            st.session_state.get("live_mode", config.auto_run_default)
        )
        live_mode_label = "🟢 Live Mode" if initial_live_mode else "🔴 Live Mode"
        live_mode = st.toggle(
            label=live_mode_label,
            value=initial_live_mode,
            key="live_mode",
            help="Auto-generate events at the configured interval",
        )

        refresh_interval = int(
            st.number_input(
                label="Refresh interval (seconds)",
                min_value=1,
                max_value=60,
                value=int(config.auto_refresh_interval),
                step=1,
                disabled=not live_mode,
                help="How often the live panel refreshes and generates new events",
            )
        )

        st.selectbox(
            label="Source",
            options=source_options,
            index=source_options.index(selected_source),
            key="chart_source_filter",
            disabled=filters_disabled,
        )

        st.selectbox(
            label="Signal",
            options=signal_options,
            index=signal_options.index(selected_signal),
            key="chart_signal_filter",
            disabled=filters_disabled,
        )

        st.subheader("Analytics (rolling metrics)")
        st.slider(
            label="Rolling window size",
            min_value=2,
            max_value=100,
            value=5,
            step=1,
            key="rolling_window_size",
        )
        st.slider(
            label="Z-score threshold",
            min_value=0.5,
            max_value=10.0,
            value=3.0,
            step=0.5,
            key="z_threshold",
        )

        st.subheader("Database")
        if not config.allow_db_reset:
            st.info(
                "Database reset is disabled. Set `SSO_ALLOW_DB_RESET=1` to enable it."
            )
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

    # -------------------------------------------------------------------------
    # Signal over time (chart directly under Live Mode controls)
    # -------------------------------------------------------------------------
    st.subheader("Signal over time")

    # Chart navigation + manual generation controls (kept outside fragment so
    # clicks are handled predictably even when the fragment auto-refreshes).
    nav_cols = st.columns(4)
    with nav_cols[0]:
        back_clicked = st.button(
            "◀ Back",
            help="Shift view window backward",
            key="chart_nav_back",
        )
    with nav_cols[1]:
        recenter_clicked = st.button(
            "Recenter on latest",
            help="Resume auto-centering on newly generated data",
            key="chart_nav_recenter",
        )
    with nav_cols[2]:
        generate_clicked = False
        if not live_mode:
            generate_clicked = st.button(
                "Generate a batch",
                key="chart_nav_generate",
            )
        else:
            st.write("")
    with nav_cols[3]:
        forward_clicked = st.button(
            "Forward ▶",
            help="Shift view window forward",
            key="chart_nav_forward",
        )

    if generate_clicked:
        inserted = _generate_batch(config)
        st.success(f"Inserted {inserted} events")

    # Server-driven chart window state. This is outside the fragment so the
    # controls are stable across auto-refresh.
    if "chart_window_seconds" not in st.session_state:
        st.session_state["chart_window_seconds"] = 300
    if "follow_latest" not in st.session_state:
        st.session_state["follow_latest"] = bool(live_mode)
    if "chart_center_ts_utc" not in st.session_state:
        st.session_state["chart_center_ts_utc"] = datetime.now(tz=UTC)

    nav_step_seconds = max(1, int(st.session_state["chart_window_seconds"] / 2))

    if back_clicked:
        st.session_state["follow_latest"] = False
        st.session_state["chart_center_ts_utc"] = st.session_state[
            "chart_center_ts_utc"
        ] - timedelta(seconds=nav_step_seconds)
    if forward_clicked:
        st.session_state["follow_latest"] = False
        st.session_state["chart_center_ts_utc"] = st.session_state[
            "chart_center_ts_utc"
        ] + timedelta(seconds=nav_step_seconds)
    if recenter_clicked:
        st.session_state["follow_latest"] = True

    # -------------------------------------------------------------------------
    # Live Panel Fragment — auto-refreshes when live_mode is enabled
    # -------------------------------------------------------------------------
    @st.fragment(
        run_every=timedelta(seconds=refresh_interval) if live_mode else None
    )
    def live_panel() -> None:
        """Fragment that displays metrics/chart/table and optionally generates events."""
        window_size = int(st.session_state.get("rolling_window_size", 5))
        z_threshold = float(st.session_state.get("z_threshold", 3.0))

        # Generate events when in live mode
        if live_mode:
            _generate_batch(config)

        # Chart
        selected_source = st.session_state.get("chart_source_filter", "(all)")
        selected_signal = st.session_state.get("chart_signal_filter", "(all)")
        chart_source = None if selected_source == "(all)" else selected_source
        chart_signal = None if selected_signal == "(all)" else selected_signal

        chart_events = get_events_for_chart(
            db_path,
            source_id=chart_source,
            signal_name=chart_signal,
            limit=None,
        )

        latest_chart_ts_utc = (
            max((event.event_ts_utc for event in chart_events), default=None)
            if chart_events
            else None
        )
        if st.session_state.get("follow_latest") and latest_chart_ts_utc is not None:
            st.session_state["chart_center_ts_utc"] = latest_chart_ts_utc

        chart_metrics = compute_rolling_metrics(
            chart_events[::-1],
            window_size=window_size,
            z_threshold=z_threshold,
        )

        chart_rows = build_signal_chart_rows(chart_metrics)
        if not chart_rows:
            st.info("No data to chart yet (generate events first).")
        else:
            domain_start, domain_end = _compute_centered_domain_iso(
                center_ts_utc=st.session_state["chart_center_ts_utc"],
                window_seconds=int(st.session_state["chart_window_seconds"]),
            )
            chart = build_signal_over_time_chart(
                chart_rows,
                x_domain=(domain_start, domain_end),
            )
            st.altair_chart(chart, width='stretch')

        # Metrics (below the chart)
        total_rows = get_total_event_count(db_path)
        st.metric(label="Total stored events", value=total_rows)

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

        # (Removed latest-events table: UI now relies on rolling metrics only)

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

    logger.info("Streamlit app rendered")


if __name__ == "__main__":
    render_app()
