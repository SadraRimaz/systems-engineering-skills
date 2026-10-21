---
name: define-problem-plan-feasibility
description: Interview the user to produce a Feasibility Analysis Plan from their stakeholder requirements: the feasibility questions, analyses, prototyping tasks and steps, usability tests, elicitation sessions and decision criteria needed to show a workable design can exist. Use after requirements are written, or when someone asks whether requirements are achievable, what to prototype, or how to test feasibility. Planning only; never runs the analyses or writes code.
license: MIT
compatibility: Requires Python 3.9+ and the jsonschema package (pip install -r scripts/requirements.txt).
metadata:
  "opencode/slash": "true"
  stage: define-problem
  order: "8"
---

# Plan Feasibility Analysis

Stage: Requirements and Design Problem Definition, step 8 of 9. Produces `feasibility-plan.json`.

**Workspace:** the folder path the user gave after the skill name, else `./sysreq`.
**Inputs:** `stakeholders`, `scenarios`, `requirements` (all approved). Follow `references/interview-protocol.md` for the whole interview.

**This skill plans only.** Do not run analyses, build prototypes, write code or contact stakeholders. The output is a plan the user can execute later.

## Why this matters

Hundreds of requirements together can leave no solution at an affordable cost and schedule, and that is often found too late. The plan says what must be shown, how, and what result would force a requirement to change.

## Your job

Question bank: `references/question-bank.md`.

1. **Find the risky requirements.** Read `requirements.json` and propose feasibility questions for: requirements flagged `tbd`; demanding thresholds near the edge of what is known; requirement sets that may conflict; things never done before (new technology, new user behavior); cost and schedule risks. Each question links to its requirement IDs, a `concern` (conflict, demanding, unproven, cost, schedule) and a `priority`.
2. **Probe** the work that answers each question, in this order:
   - **Analyses:** performance, cost, schedule or quality analyses, varying the surrounding system's parameters to see their effect.
   - **Prototype tasks:** `throwaway` (to learn) or `evolutionary` (grows into the system); `fidelity` (paper, mockup, subscale, working); what it will teach; ordered steps; effort; owner; dependencies on other prototype tasks.
   - **Usability tests** on prototypes: user segments by domain knowledge, computer experience and system experience, drawn from actual users of the system; tasks taken from scenarios; metrics for learnability, efficiency, memorability, error rate (classify errors minor, major, catastrophic; separate random errors from system-caused ones) and satisfaction (subjective, categorical).
   - **Elicitation sessions:** interviews (best for quiet people), facilitated groups (to surface disagreement), observation (for stressful periods), questionnaires only as a last resort.
3. **Decision criteria.** For every question: what result means feasible, infeasible, or a reason to change a requirement. The user, not you, sets these.
4. **Challenge.** Test: is any high-priority question answered only by opinion? Does each prototype teach something a cheaper analysis could not? Are the test users the system's real users?
5. **Play-back and exit gate.**

## Artifact: `feasibility-plan.json`

Shape: `assets/templates/feasibility-plan.template.json`. Authority: `assets/schemas/feasibility-plan.schema.json`.

- IDs: `FQ-001`, `AN-001`, `PT-001`, `UT-001`, `ES-001`, never reused.
- `results` stays empty until the work is done; later, record results as `pending` or `done` with a summary (the last skill ingests outcomes).
- Prototype steps are numbered 1..n; `depends_on` must not form a cycle.

## Exit checklist

- [ ] Every question links to existing requirements and has decision criteria.
- [ ] Every question is addressed by at least one analysis, prototype task or elicitation session.
- [ ] Each prototype task has steps, effort, an owner and what it will teach.
- [ ] Usability tests name segments, tasks from scenarios, and metrics with targets.
- [ ] Every `tbd` requirement is covered or the gap is an open issue.
- [ ] The user approved the play-back.

## Visuals

| Visual | Generator |
|---|---|
| Feasibility plan: questions, work, prototype flow, tests, criteria | `python3 scripts/render_feasibility.py --workspace <ws>` |

## Finish

Validate, stamp (artifact name `feasibility-plan`), report. Next skill: `define-problem-revise-from-feedback`, to run when stakeholders have reviewed the artifacts or when plan results come in.

## Gotchas

- A plan is not a schedule. Record effort and dependencies, not calendar dates, unless the user gives them.
- "Feasible" means one design can meet all requirements at once, within cost and schedule. Testing one requirement alone does not show that.
