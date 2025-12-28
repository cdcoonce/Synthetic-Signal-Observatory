"""Synthetic event generator.

The generator is intentionally deterministic and side-effect free.

Design goals
------------
- Pure functions only (no I/O, no globals).
- Deterministic output given the same inputs (especially `seed`).
- Emits `SyntheticEvent` objects that satisfy architecture invariants.

Notes
-----
- Persistence is handled separately (DuckDB helpers).
- Orchestration/UI (Streamlit) should call these functions, not embed logic.
"""

from __future__ import annotations

import logging
import random
import hashlib
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from uuid import UUID

from synthetic_signal_observatory.duckdb_persistence import SyntheticEvent

logger = logging.getLogger(__name__)


def _require_timezone_aware(timestamp: datetime, *, field_name: str) -> None:
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _deterministic_uuid(rng: random.Random) -> str:
    """Generate a deterministic UUID string from a Random instance."""

    return str(UUID(int=rng.getrandbits(128)))


def _stable_signal_base(signal_name: str) -> float:
    """Return a stable base value for a signal name.

    Notes
    -----
    Python's built-in `hash()` is intentionally randomized between processes.
    We use a stable hash (sha256) to keep generation deterministic across runs.
    """

    digest = hashlib.sha256(signal_name.encode("utf-8")).digest()
    return float(int.from_bytes(digest[:2], byteorder="big") % 10)


def generate_synthetic_events(
    *,
    count: int,
    start_ts: datetime,
    run_id: str,
    seed: int,
    source_ids: list[str],
    signal_names: list[str],
    step: timedelta,
) -> list[SyntheticEvent]:
    """Generate a batch of synthetic events.

    Parameters
    ----------
    count:
        Number of events to generate.
    start_ts:
        Timestamp for the first event; MUST be timezone-aware.
    run_id:
        Identifier for the generator run/session.
    seed:
        RNG seed for deterministic generation.
    source_ids:
        Candidate source IDs to sample from.
    signal_names:
        Candidate signal names to sample from.
    step:
        Time delta between sequential events.

    Returns
    -------
    list[SyntheticEvent]
        A list of generated events.

    Raises
    ------
    ValueError
        If inputs are invalid (e.g., start_ts naive, empty lists).
    """

    if count < 0:
        raise ValueError("count must be >= 0")

    _require_timezone_aware(start_ts, field_name="start_ts")

    if not run_id:
        raise ValueError("run_id must be a non-empty string")

    if not source_ids:
        raise ValueError("source_ids must be non-empty")

    if not signal_names:
        raise ValueError("signal_names must be non-empty")

    if step.total_seconds() <= 0:
        raise ValueError("step must be positive")

    rng = random.Random(seed)

    start_ts_utc = start_ts.astimezone(UTC)

    events: list[SyntheticEvent] = []
    current_ts = start_ts_utc

    for _ in range(count):
        event_id = _deterministic_uuid(rng)
        source_id = rng.choice(source_ids)
        signal_name = rng.choice(signal_names)

        # Simple, stable signal: base per signal + noise
        base = _stable_signal_base(signal_name)
        noise = rng.normalvariate(0.0, 1.0)
        signal_value = base + noise

        # Quality score strictly in [0, 1]
        quality_score = rng.random()

        events.append(
            SyntheticEvent(
                event_id=event_id,
                event_ts=current_ts,
                source_id=source_id,
                signal_name=signal_name,
                signal_value=signal_value,
                quality_score=quality_score,
                run_id=run_id,
            )
        )
        current_ts = current_ts + step

    # Debug logging for dev; avoid logging per-event in production paths.
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Generated %s synthetic events (seed=%s): %s",
            len(events),
            seed,
            [asdict(event) for event in events[:3]],
        )

    return events
