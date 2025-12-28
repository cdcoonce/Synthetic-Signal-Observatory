# Development Learnings & Anti-Patterns

This document captures **failed approaches, environment-specific pitfalls,
and tooling behaviors** that SHOULD NOT be retried.

It exists to prevent agents from repeating costly mistakes.

---

## Purpose

- Preserve **negative knowledge** (what not to do)
- Prevent repeated experimentation with known failures
- Document OS, shell, and tooling edge cases
- Provide future agents with clear guardrails

This file is **not** for architectural decisions (see `DECISIONS.md`)
or current work tracking (see `STATUS.md` / `TODO.md`).

---

## What Belongs Here

Use this file for:

- CLI / shell issues
- OS-specific behavior (especially Windows)
- Tooling quirks (uv, git, dbt, dlt, Dagster, DuckDB)
- Encoding, line endings, path handling
- Environment or filesystem constraints
- “This *should* work, but doesn’t” situations

---

## Entry Format (Required)

```markdown
## YYYY-MM-DD — Short, Action-Oriented Title

**Context**
What was being attempted?

**What Failed**
What specifically did not work?
Include exact errors or symptoms.

**Root Cause**
Why it failed (OS behavior, tool limitation, misassumption).

**Resolution / Workaround**
What actually works instead.

**Do Not Repeat**
Explicit instruction for future agents.

---

## Learnings (Most Recent First)

<!-- Add new entries below this line -->

## 2025-12-27 — Altair Inline Data + Python datetimes Can Render Blank

**Context**
Streamlit renders the time-series chart using Altair with inline data (`alt.Data(values=...)`).

**What Failed**
Charts intermittently rendered with no marks even though data existed.

**Root Cause**
Timezone-aware Python `datetime` objects in inline `values` are not reliably JSON-serializable
through Altair/Vega-Lite, and the resulting spec can collapse or fail silently.

**Resolution / Workaround**
- Convert timestamps to ISO-8601 strings (UTC) before passing them to Altair inline `values`, or
- Use a DataFrame-based chart path that handles datetime conversion explicitly.
- Add a unit test that calls `chart.to_dict()` and asserts `data.values` contains string timestamps.

**Do Not Repeat**
Do NOT pass Python `datetime` objects directly into `alt.Data(values=...)`.

## 2025-01-02 — Windows Line Endings Break CLI Scripts

**Context**
Attempted to run bash-style CLI commands from documentation on Windows.

**What Failed**
Scripts failed with unexpected parsing errors and invisible character issues.

**Root Cause**
Windows uses CRLF line endings by default.
Some CLI tools and scripts expect LF only.

**Resolution / Workaround**
- Avoid bash scripts for cross-platform workflows
- Prefer Python entrypoints or documented `uv run ...` commands
- If needed, normalize line endings explicitly

**Do Not Repeat**
Do NOT assume shell scripts are portable across OSes.
