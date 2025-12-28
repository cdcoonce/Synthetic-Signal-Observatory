# REALTIME_DISPLAY_PLAN.md
## Faux Real-Time Display for Synthetic Signal Observatory

This document outlines a plan to transform the current **manual-click** generation
model into a **faux real-time** display that continuously generates and visualizes
synthetic events without requiring repeated user interaction.

---

## 1. Goal

Make the dashboard feel like a live monitoring system:
- Events appear to stream in automatically.
- Charts and tables update in place without full-page reloads.
- The user can still pause/resume or adjust parameters on the fly.

This is "faux" real-time because the data is synthetic and generated client-side
(or on the Streamlit server process), not pushed from an external source.

---

## 2. Current State

| Aspect | Current Behavior |
|--------|------------------|
| Generation trigger | Manual button click ("Generate a small batch") |
| Batch size | Configurable via `SSO_BATCH_SIZE` (default 100) |
| Update cadence | Only on user interaction or explicit `st.rerun()` |
| Chart refresh | Full rerun of script on each interaction |

---

## 3. Proposed UX

### 3.1 Auto-Run Mode Toggle

Add a toggle (checkbox or switch) labeled **"Auto-generate"** or **"Live mode"**.

- **Off (default)**: Behaves as today—manual button to generate.
- **On**: Automatically generates a small batch at a configurable interval and
  refreshes the display.

### 3.2 Configurable Refresh Interval

Expose a slider or number input for refresh interval (e.g., 1–10 seconds).
Default: 2 seconds.

### 3.3 Pause / Resume

When auto-run is enabled, the toggle acts as pause/resume. Turning it off stops
new generation but keeps existing data visible.

### 3.4 Visual Feedback

- Show a small "streaming" indicator (e.g., spinner or blinking dot) when live
  mode is active.
- Optionally display a "Last updated: X seconds ago" timestamp.

---

## 4. Chosen Implementation: `st.fragment` with `run_every`

Streamlit 1.33+ supports `@st.fragment(run_every=timedelta(...))` to re-execute
only a portion of the app on a timer without a full rerun. This is the approach
we will use.

### Why This Approach

| Benefit | Description |
|---------|-------------|
| Partial refresh | Only the fragment re-executes; rest of page stays stable |
| Smoother UX | No full-page flicker or blocked UI |
| No external deps | Built into Streamlit ≥ 1.33 |
| Fine-grained control | Fragment can be conditionally enabled via toggle |

### Implementation Pattern

```python
from datetime import timedelta
import streamlit as st

# Toggle in main app body (outside fragment)
live_mode = st.toggle("Live mode", value=False)
refresh_interval = st.slider("Refresh interval (s)", 1, 10, 2)

@st.fragment(run_every=timedelta(seconds=refresh_interval) if live_mode else None)
def live_panel():
    """Fragment that auto-refreshes when live_mode is enabled."""
    if live_mode:
        generate_and_persist_events(...)
    # Render chart / table / metrics
    ...

live_panel()
```

### Key Considerations

- **Version requirement**: Streamlit ≥ 1.33 (verify in `pyproject.toml`).
- **Fragment boundaries**: State inside the fragment resets on each run; keep
  controls (toggle, sliders) outside the fragment.
- **Conditional `run_every`**: Pass `None` to disable auto-refresh when live
  mode is off.

## 5. Implementation Steps

1. **Add config knob** `SSO_AUTO_REFRESH_INTERVAL` (seconds, default 2).
2. **Add UI toggle** for live mode in the sidebar or header.
3. **Wrap generation + display in a fragment** decorated with `run_every`.
4. **Gate fragment execution** on the live-mode toggle state.
5. **Add visual indicator** (spinner / timestamp) when live.
6. **Write tests** for the new config parsing and any pure helpers.
7. **Update STATUS.md / TODO.md** to reflect the new capability.

## 6. Configuration Additions

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SSO_AUTO_REFRESH_INTERVAL` | int (seconds) | `2` | Interval between auto-generation cycles |
| `SSO_AUTO_RUN_DEFAULT` | bool | `false` | Whether live mode is on by default |

---

## 7. UI Sketch

```
┌─────────────────────────────────────────────────────────┐
│  Synthetic Signal Observatory           [Live ●]  2s ▼ │
├─────────────────────────────────────────────────────────┤
│  Total stored events: 1,420   Anomalies in view: 3     │
├─────────────────────────────────────────────────────────┤
│  [Chart: Signal over time — auto-updating]             │
│  ...                                                    │
├─────────────────────────────────────────────────────────┤
│  Latest events (table)                                  │
│  ...                                                    │
└─────────────────────────────────────────────────────────┘
```

- **[Live ●]**: Toggle; green dot pulses when active.
- **2s ▼**: Dropdown/slider for refresh interval.

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Database grows unbounded | Add a cap or rolling window purge (future TODO) |
| Browser tab left open accumulates data | Same as above; warn in docs |
| Streamlit version too old | Require ≥ 1.33 in `pyproject.toml`; document in README |
| Flicker during refresh | Use `st.empty()` containers for in-place updates |

---

## 9. Tasks Breakdown

- [ ] Verify/pin Streamlit ≥ 1.33 in `pyproject.toml`
- [ ] Add `SSO_AUTO_REFRESH_INTERVAL` and `SSO_AUTO_RUN_DEFAULT` to config
- [ ] Add Live Mode toggle + interval slider to UI (outside fragment)
- [ ] Create `@st.fragment(run_every=...)` wrapper for chart/table section
- [ ] Conditionally generate events inside fragment when live mode enabled
- [ ] Add visual indicator (spinner / timestamp) for streaming state
- [ ] Write/adjust tests for new config and any helpers
- [ ] Update `.env.example`, `STATUS.md`, `TODO.md`
- [ ] (Optional) Add data-retention/purge logic to prevent unbounded growth

---

## 10. Success Criteria

- Dashboard updates automatically when Live Mode is enabled.
- User can pause/resume without losing data.
- Refresh interval is configurable via UI and/or environment.
- No full-page flicker on each update (if using fragments).
- All existing tests still pass.

---

**This plan is directional. Implementation details may evolve.**
