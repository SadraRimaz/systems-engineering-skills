---
name: define-problem-define-lifecycle
description: Interview the user to define every lifecycle stage of their system (development, production, deployment, training, operation and support, refinement, retirement, adapted to their industry) and who is active in each, so requirements can be captured systematically per stage. Use after stakeholders are identified, or whenever someone asks what lifecycle phases or stages a system goes through.
license: MIT
compatibility: Requires Python 3.9+ and the jsonschema package (pip install -r scripts/requirements.txt).
metadata:
  "opencode/slash": "true"
  stage: define-problem
  order: "3"
---

# Define System Lifecycle

Stage: Requirements and Design Problem Definition, step 3 of 9. Produces `lifecycle.json`.

**Workspace:** the folder path the user gave after the skill name, else `./sysreq`.
**Inputs:** `concept-brief`, `stakeholders` (both approved). Follow `references/interview-protocol.md` for the whole interview.

## Why this matters

A separate system exists to support each phase (a development system, a production system, a training system, and so on), and each has its own stakeholders, scenarios and requirements. Requirements for one phase often constrain the design for another, so every phase must be considered up front, even if some are later marked not applicable.

## Your job

Question bank: `references/question-bank.md`.

1. **Seed.** Show the generic phases from `assets/data/baseline-lifecycle.json`, rewritten in the user's sector terms using the concept brief's glossary. Ask which ring true.
2. **Probe.** For each phase decide with the user:
   - `active`, `not_applicable` (with a reason) or `merged` into another phase (with a reason).
   - Domain label and description, adapted to the sector (for software, production might become "build and packaging").
   - The enabling system that exists in this phase (people, tools, facilities).
   - Which stakeholders are active in it (this is where that relation is recorded).
   - Overlaps with other phases (`concurrency_notes`), risks to capture, and which scenario kinds from `assets/data/scenario-kinds.json` to seed.
   - Add custom phases only when the generic list truly does not fit; set `baseline_ref` to `custom`.
3. **Back edge.** If the user names a stakeholder who is not in the register, add them to `stakeholders.json`, validate and stamp `stakeholders` (this raises its version), then continue. Never store the phase relation on the stakeholder.
4. **Challenge.** For each `not_applicable` phase: is it truly absent, or only out of scope for now? For each active phase: who else is there? Does something in this phase constrain the design in another?
5. **Play-back and exit gate.**

## Artifact: `lifecycle.json`

Shape: `assets/templates/lifecycle.template.json`. Authority: `assets/schemas/lifecycle.schema.json`.

- `id` is `LC-001`, `LC-002`, ... in lifecycle order, never reused.
- `baseline_ref` is a baseline phase id or `custom`. Every baseline phase must appear at least once.
- Active phases need `stakeholder_ids` that exist in `stakeholders.json`.

## Exit checklist

- [ ] Every baseline phase is active, not applicable with a reason, or merged with a reason.
- [ ] Every active phase has an enabling system and at least one stakeholder.
- [ ] Overlaps between phases are noted.
- [ ] Every stakeholder is active in at least one phase (or the gap is an open issue).
- [ ] The user approved the play-back.

## Visuals

| Visual | Generator |
|---|---|
| Stakeholder × lifecycle matrix and phase timeline with overlaps | `python3 scripts/render_lifecycle.py --workspace <ws>` |

## Finish

Validate, stamp (artifact name `lifecycle`), report. If stakeholders changed, say so. Next skill: `define-problem-develop-scenarios`.

## Gotchas

- Phases are not strictly sequential: development of a refinement can run while the system operates. Capture that in `concurrency_notes`, not by reordering.
- Training is often skipped by mistake. Ask who must learn something, even if informally.
