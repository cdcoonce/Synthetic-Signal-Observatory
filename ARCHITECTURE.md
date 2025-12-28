# ARCHITECTURE.md — System Architecture & Boundaries

This document defines the **stable architecture** of this repository.

It exists to:
- Preserve system intent across time and agents
- Prevent silent re-architecture
- Provide a shared mental model for contributors

---

## How to use this file (IMPORTANT)

- This file describes **what the system is**, not what is currently being worked on
- This file is a **living document** (edits are allowed when correcting inaccuracies)
- Prefer **additive updates** when describing new components or boundaries
- When architecture changes materially:
  - Update the relevant sections
  - Add a dated note in the architecture log
  - Reference the motivating decision in `DECISIONS.md`

If unsure whether something is “architecture”:
→ If changing it would break assumptions elsewhere, it belongs here.

---

## What belongs in this file

- System boundaries and responsibilities
- Data flow (high-level, end-to-end)
- Stable folder/package roles
- Technology responsibilities (what each tool is allowed to do)
- Testing and environment boundaries

---

## ARCHITECTURE LOG (append below)

<!--
Append new architecture sections below.
Use clear headings and bullet points.
Prefer constraints over prose.
-->

## 2025-12-27 — Synthetic event data model (raw)

- **Entity name**: `synthetic_events` (raw, event-style)
- **Grain**: 1 row = 1 generated event
- **Primary key**: `event_id` (unique per event)
- **Time semantics**:
  - `event_ts` is UTC
  - Derived partition key is `event_date` = `event_ts` truncated to date (UTC)

### Schema (initial)

- `event_id`: string
  - Unique identifier for the event (UUID recommended)
- `event_ts`: datetime
  - Event timestamp in UTC
- `source_id`: string
  - Synthetic “device/user/sensor” identifier (small cardinality)
- `signal_name`: string
  - Name of the synthetic signal (e.g., "alpha", "beta")
- `signal_value`: float
  - Numeric signal value
- `quality_score`: float
  - Range: [0.0, 1.0]
- `run_id`: string
  - Identifier for the generator run/session (groups events produced together)

### Invariants

- `event_id` MUST be globally unique.
- `event_ts` MUST be timezone-aware and normalized to UTC.
- `quality_score` MUST be clamped to [0.0, 1.0].

### Notes

- This is the raw event table; derived features/metrics belong in separate models/tables.

## 2025-12-27 — Analytics layer (rolling metrics + anomaly flag)

- Analytics is computed as a **pure function** over event data.
- Metrics are computed **per group**: (`source_id`, `signal_name`).
- Rolling stats use a **lookback window** of prior values (excluding the current event).
- Rolling stats are only emitted once a **full window** exists; earlier rows have `None` stats.
- An anomaly is flagged when `abs(z_score) >= threshold` and rolling std > 0.