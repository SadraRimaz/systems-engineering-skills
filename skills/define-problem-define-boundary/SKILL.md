---
name: define-problem-define-boundary
description: Interview the user to draw the system boundary: derive external systems, enabling systems, context, interfaces and controls from the operational scenarios, then generate external-systems diagrams per lifecycle phase and a context map. Use after scenarios exist, or when someone asks where the system starts and stops, what its interfaces are, or what is in or out of scope.
license: MIT
compatibility: Requires Python 3.9+ and the jsonschema package (pip install -r scripts/requirements.txt).
metadata:
  "opencode/slash": "true"
  stage: define-problem
  order: "5"
---

# Define System Boundary

Stage: Requirements and Design Problem Definition, step 5 of 9. Produces `boundary.json`.

**Workspace:** the folder path the user gave after the skill name, else `./sysreq`.
**Inputs:** `concept-brief`, `lifecycle`, `scenarios` (all approved). Follow `references/interview-protocol.md` for the whole interview.

## Why this matters

Everything inside the boundary can change; everything outside is a constraint. The boundary decides which inputs and outputs the requirements must cover, and it has cost and schedule consequences. It is nearly always harder to settle than people expect, so draw it early and in the open.

## Your job

Question bank: `references/question-bank.md`.

1. **Derive a draft.** Run `python3 scripts/derive_boundary.py --workspace <ws> --write`. It turns every actor in the scenario exchanges into an external system and every exchange into an interface, with placeholder values ('external', 'TO CONFIRM'). Re-run it after scenarios change; it only adds what is missing.
2. **Probe.** For each external system confirm with the user:
   - `kind`: `external` (interacts with the system), `enabling` (provides services to field, support or run it in that phase), or `context` (can affect the system but cannot be affected by it).
   - `role` in one line, whether it is `legacy`, and in which phases it is present.
   - Interfaces: direction `input`, `output` or `control` (a policy, rule or constraint rather than data). Keep or merge as the user prefers.
3. **Controls.** Ask for regulations, policies, standards and constraints that govern each phase and record them in `controls`.
4. **Boundary decisions.** For each judgment call about what is in or out, record who decided and the cost or schedule implication. The party that procures or pays has a major say; all stakeholders should see the consequences of each option.
5. **Challenge.** Test each context item (does the system really have no effect on it?), each enabling system (must it be built too?), and each system output that goes nowhere.
6. **Play-back and exit gate.**

## Artifact: `boundary.json`

Shape: `assets/templates/boundary.template.json`. Authority: `assets/schemas/boundary.schema.json`.

- IDs: `EXT-001`, `IF-001`, `CTL-001`, `BD-001`, never reused.
- Validity rules, enforced by `scripts/validate.py`: every scenario exchange maps to an interface; every external or enabling system receives at least one system output in each phase it is present; a context system receives none.

## Exit checklist

- [ ] No placeholder `TO CONFIRM` remains.
- [ ] Every scenario exchange has an interface.
- [ ] Every non-context system receives an output in each of its phases.
- [ ] Controls are recorded or noted as none per phase.
- [ ] Boundary decisions have a decider and an implication.
- [ ] The user approved the play-back.

## Visuals

| Visual | Generator |
|---|---|
| External-systems diagram per phase (inputs left, outputs right, controls top, enabling below) | `python3 scripts/render_external_systems.py --workspace <ws>` |
| Context map, now from the boundary model | `python3 scripts/render_context_map.py --workspace <ws>` |

## Finish

Validate, stamp (artifact name `boundary`), report. If a missing interface sent the user back to scenarios, say which scenario to revise. Next skill: `define-problem-build-objectives`.

## Gotchas

- A system that only sends outputs to nobody is not an external system, it is context. A system the system sends outputs to is not context.
- Do not stop at the operating phase. Every active phase has its own external systems.
