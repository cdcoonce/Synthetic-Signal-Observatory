# AGENTS.md — Repository Agent Operating System

This file defines **how humans and AI agents work together** in this repository.

It is not a style guide.  
It is a **cognition, context, and execution control system**.

Failure to follow this file is considered a process failure, even if code “works”.

---

## 0. Prime Directive

> **Humans think.  
> Agents execute.  
> Context is finite.**

AI systems are **amplifiers**, not thinkers.  
This repository is designed to prevent amplified mistakes.

---

## 1. Role & Authority Model (HUMAN-IN-THE-LOOP)

### Authority Split

| Stage | Responsibility |
|-------|----------------|
| Reasoning | Human |
| Planning | Human + Agent |
| Approval | Human |
| Execution | Agent |
| Validation | Human |
| Memory | Documentation |

Agents have **zero decision authority**.

---

## 2. Context Is a Degradable Resource (CRITICAL)

### The Dumb Zone Rule (ENFORCED)

The final ~60% of a long context window is the **Dumb Zone**.

Once in the Dumb Zone, models:

- Hallucinate constraints
- Argue with instructions
- Repeat themselves
- Produce verbose but incorrect output

**Do NOT argue. Do NOT prompt harder.**

**Correct action:**

- STOP
- NUKE the chat
- Restart with a clean context
- Reload only compressed summaries

Continuing in degraded context is considered a failure mode.

### docs/ — Compressed Context Cache

The `docs/` directory contains **human-curated, high-signal summaries**.

Agents MUST:

- Prefer `docs/` over raw files when available
`docs/` exists to keep live context small and correct.

---

## 3. Context Hierarchy & Compression Strategy

Agents MUST retrieve context **progressively**, not exhaustively.

### Context Levels (Highest Signal → Lowest)

1. `AGENTS.md` — Rules & enforcement
2. `STATUS.md` / `TODO.md` — Current truth
3. `docs/context-summary.md` — Supporting knowledge
4. `ARCHITECTURE.md` — System shape
5. `DECISIONS.md` — Frozen intent
6. `LEARNINGS.md` — Failure memory
7. Source code — Implementation details

### Rules

- Start at the highest level
- Go deeper **only if required**
- More context is NOT better context

When deeper context is consulted, agents MUST:

- Summarize findings in **≤5 bullets**
- Explain *why* deeper context was needed
- Never paste large raw excerpts forward

---

## 4. Sub-Agents (STRICTLY FOR CONTEXT COMPRESSION)

Sub-agents exist **only** to protect the main context window.

### Allowed Sub-Agent Behavior

A sub-agent MAY:

- Read many files in isolation
- Extract factual information
- Return compressed summaries

A sub-agent MUST return:

- ≤1 sentence per file
- No opinions
- No plans
- No code
- No suggestions

### Forbidden Sub-Agent Behavior

Sub-agents MUST NOT:

- Make decisions
- Review plans
- Generate code
- Act as “QA”, “Architect”, or “Reviewer”

Sub-agents are **not teammates**.  
They are **context compressors**.

---

## 5. Execution Workflow (NON-NEGOTIABLE)

This repository allows **ONE workflow only**:

> **RESEARCH → PLAN → IMPLEMENT**

Any deviation is a process failure.

---

### 5.1 RESEARCH (Ground Truth Only)

Purpose: establish reality.

Agents MUST:

- Read the actual code
- Inspect tests
- Consult architecture and decisions
- Use sub-agents ONLY for compression

Outputs:

- Facts
- Constraints
- Unknowns

Forbidden:

- Planning
- Proposing changes
- Writing code

---

### 5.2 PLAN (Alignment Phase)

Purpose: achieve mental alignment **before tokens are spent**.

Agents MUST produce a plan containing:

- Exact files to change
- Exact changes per file
- Tests to add or modify
- Documentation updates required
- Explicit non-goals
- Risks and assumptions

**No code is allowed in the Plan.**

Humans review and approve the PLAN, not the implementation.

---

### 5.3 IMPLEMENT (Execution Only)

Purpose: mechanical execution of an approved plan.

Agents MUST:

- Follow the approved plan exactly
- Avoid interpretation or creativity
- Stop immediately if ambiguity appears

Implementation without an approved plan is forbidden.

---

## 6. AI Is an Amplifier (SAFETY RULE)

AI systems do not improve thinking.

They amplify:

- Bad plans
- Missing constraints
- Ambiguous intent

Therefore:

- Thinking is a human responsibility
- Planning is a shared responsibility
- Execution is the agent’s responsibility

Agents MUST refuse to implement weak or unclear plans.

---

## 7. Review Philosophy (PLAN > PR)

Human review effort MUST focus on **plans**, not code diffs.

- Plans are reviewed synchronously
- Implementations are reviewed asynchronously
- Mental alignment happens at the plan level

If the plan is correct, implementation errors are mechanical.  
If the plan is wrong, no PR review will save it.

---

## 8. Documentation as Long-Term Memory (REQUIRED)

Agents do not retain memory across sessions.  
Documentation **is** memory.

### Mandatory Update Rules

At the end of every task, the agent MUST ask:

- Did this change architecture? → `ARCHITECTURE.md`
- Did this introduce or rely on a decision? → `DECISIONS.md`
- Did this change project state? → `STATUS.md`
- Did this advance or complete work? → `TODO.md`
- Did this expose a pitfall or failure? → `LEARNINGS.md`

If yes, documentation MUST be updated **in the same change set**.

---

## 9. Tooling Stability & Reps

This repository values **reps over novelty**.

- Do NOT chase new AI tools
- Do NOT optimize prematurely
- Learn the failure modes of the chosen setup

Consistency beats optimization.

---

## 10. Safe Defaults

If anything is unclear:

- STOP
- Ask one focused question
- Do NOT guess
- Do NOT proceed “to be helpful”

Silence is NOT approval.

---

## Final Rule

> **Protect context.  
> Debate plans.  
> Execute deliberately.  
> Reset aggressively.**

Code solves today’s problem.  
Process prevents tomorrow’s catastrophe.
