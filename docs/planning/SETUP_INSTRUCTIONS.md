# PROJECT_PLAN.md
## Synthetic Signal Dashboard (Portfolio Project)

This document defines the **initial high-level plan** for this repository.

It is intended to be used by human contributors and AI agents working in **VS Code**, in conjunction with:
- `AGENTS.md`
- `DECISIONS.md`
- `TODO.md`
- `LEARNINGS.md`
- `STATUS.md`
- `ARCHITECTURE.md`

This plan describes *what this project is meant to become*, not how every detail must be implemented.

---

## 1. Project Intent

This repository will produce a **self-contained, deployable, interactive dashboard application** suitable for hosting on a personal portfolio website.

The application will:
- Generate **synthetic data**
- Process and persist that data locally
- Apply a lightweight **data science / analytics step**
- Visualize the results in real time
- Expose **interactive controls** for viewers

The data and insights are intentionally **meaningless**, but the system architecture and tooling are realistic and professional.

---

## 2. What This Project Demonstrates

This project exists to demonstrate:

- Data engineering workflow design
- State persistence (Parquet / DuckDB)
- Incremental data generation
- Feature engineering
- Basic analytical or modeling logic
- Live / auto-updating dashboards
- Documentation-driven development
- Good agent collaboration patterns

It is explicitly designed as a **portfolio artifact**, not a business solution.

---

## 3. Operating Model for This Repository

This repository follows a **documentation-first, agent-assisted workflow**.

### Required Behaviors

All contributors and agents must:

- Read and follow `AGENTS.md`
- Record architectural or tooling choices in `DECISIONS.md`
- Log failed attempts, surprises, or constraints in `LEARNINGS.md`
- Keep `STATUS.md` current as work progresses
- Treat this plan as *directional*, not immutable

Agents should prefer **incremental progress** over large rewrites.

---

## 4. High-Level System Description

The system will be a **single Python-native dashboard application** that:

1. Runs locally or in a hosted environment
2. Generates synthetic event-style data continuously
3. Persists data between runs
4. Applies analytics or modeling logic
5. Updates visualizations automatically
6. Allows user interaction via UI controls

All major components will run **within a single app process** for simplicity and deployability.

---

## 5. Key Constraints (Locked In)

The following constraints are intentional and should not be changed without documenting a decision:

- Python-native dashboard framework
- Live / auto-refreshing behavior
- Single-process architecture
- Persistent local storage
- Interactive UI controls
- Analytics / modeling component included
- Deployable as a standalone app

---

## 6. Conceptual Architecture (Initial)

At a conceptual level, the system includes:

- **Synthetic Data Generator**
  - Produces fake but structured signals/events
  - Runs continuously or on a timer
- **Processing / Feature Layer**
  - Transforms raw signals into analytics-ready data
- **Analytics / Modeling Layer**
  - Computes trends, rolling metrics, anomalies, or forecasts
- **Persistence Layer**
  - Stores raw and processed data between runs
- **Presentation Layer**
  - Interactive dashboard with live updates and controls

Details belong in `ARCHITECTURE.md` and may evolve.

---

## 7. Dashboard Characteristics

The dashboard should:

- Update automatically without requiring restarts
- Display multiple related visual elements
- Clearly label metrics and charts
- Provide controls such as sliders, toggles, or dropdowns
- Be understandable to a non-technical viewer
- Look polished enough for a portfolio site

Visual clarity is more important than analytical depth.

---

## 8. Development Phases

### Phase 0 — Foundation
- Repo initialized
- This plan committed
- Environment strategy chosen
- Dashboard framework selected and recorded

### Phase 1 — Data Generation
- Synthetic data schema defined
- Generator implemented
- Raw data persisted

### Phase 2 — Processing & Analytics
- Feature engineering implemented
- Analytical / modeling logic added
- Outputs persisted

### Phase 3 — Dashboard
- UI layout implemented
- Visualizations connected to data
- Controls wired to logic
- Live updates verified

### Phase 4 — Portfolio Polish
- README finalized
- Screenshots or GIFs captured
- Deployment instructions added
- Hosting verified

---

## 9. Non-Goals

This project is **not** intended to:

- Be production-grade
- Scale horizontally
- Use real user data
- Optimize aggressively for performance
- Include complex distributed systems

If any of these are explored, they must be framed as learning exercises.

---

## 10. How Agents Should Use This File

Agents should:

- Use this file to understand intent and constraints
- Avoid implementing beyond the current phase
- Ask for clarification rather than guessing direction
- Defer detailed decisions to `DECISIONS.md`

This file may be updated, but changes should be additive and intentional.

---

## 11. Next Immediate Step

After adding this file to the repo:

1. Ensure all template files exist
2. Choose the dashboard framework
3. Record that choice in `DECISIONS.md`
4. Begin Phase 0 implementation

---

**This project values clarity, intent, and learning over cleverness.**