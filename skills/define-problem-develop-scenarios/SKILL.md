---
name: define-problem-develop-scenarios
description: Interview the user to develop operational scenarios for every lifecycle stage of their system, written as user stories with black-box input/output exchanges, plus mission requirements, and generate user-story and sequence-diagram views across stages. Use after the lifecycle is defined, or when someone wants to describe how a system will be used, a "day in the life", use cases, or an operational concept.
license: MIT
compatibility: Requires Python 3.9+ and the jsonschema package (pip install -r scripts/requirements.txt).
metadata:
  "opencode/slash": "true"
  stage: define-problem
  order: "4"
---

# Develop Operational Scenarios

Stage: Requirements and Design Problem Definition, step 4 of 9. Produces `scenarios.json` (the operational concept).

**Workspace:** the folder path the user gave after the skill name, else `./sysreq`.
**Inputs:** `concept-brief`, `stakeholders`, `lifecycle` (all approved). Follow `references/interview-protocol.md` for the whole interview.

## Why this matters

Scenarios build a shared vision of how the system will be used, deployed, supported and retired, from the stakeholders' point of view. They reveal the inputs and outputs that cross the boundary, which later define interfaces and requirements. A simple system typically needs 25 to 50 scenarios across all phases.

## Your job

Question bank: `references/question-bank.md`.

1. **Seed.** Ask the user to narrate, per active phase, how the key stakeholder uses or works with the system.
2. **Probe**, per active phase, in widening passes:
   - Pass 1: a few simple scenarios for the key stakeholder.
   - Pass 2: the other stakeholders active in that phase.
   - Pass 3: complexity. Walk the standard kinds in `assets/data/scenario-kinds.json`: initialization, normal operation in each context, extremes, maintenance, resupply, reaction to other systems' failures, degraded operation from internal failure, shutdown. Add environment conditions (weather, load, hostile conditions) and failure modes.
   - For each scenario capture the goal, a user story, preconditions, environment conditions, variations, and the ordered exchanges.
3. **Mission requirements.** Ask what the key needs are in terms of the stakeholders' own success measures, measured outside the system (for example "bring the astronauts home alive", "average wait under 30 seconds"). Record them as `mission_requirements`.
4. **Challenge.** Test every exchange for internal processing ("the system calculates...") and rewrite it as what the system takes in or gives out. Test each phase for a missing kind or stakeholder.
5. **Play-back and exit gate.**

## Artifact: `scenarios.json`

Shape: `assets/templates/scenarios.template.json`. Authority: `assets/schemas/scenarios.schema.json`.

- `id` is `SCN-001`... and mission requirements are `MSN-001`..., never reused.
- Each scenario belongs to one active phase (`phase_id`) and lists stakeholders (`stakeholder_ids`).
- `kind` is a scenario kind id, or `custom:<label>`.
- `exchanges` are ordered; each has `from`, `to`, `item`, `item_kind` (data, energy or matter). **One side is always the system**, named exactly as in `concept-brief.system_of_interest.name`. Name each external actor identically everywhere; these names become the external systems in the next skill. Order matters, time spacing does not.
- A kind not relevant to a phase goes in `coverage_notes` with a reason, so no kind is skipped silently.

## Exit checklist

- [ ] Every active phase has a scenario for each of its stakeholders.
- [ ] Every standard kind is covered or noted n/a per active phase.
- [ ] Every exchange involves the system and describes only inputs and outputs.
- [ ] Actor names are consistent across scenarios.
- [ ] Mission requirements exist or the gap is an open issue.
- [ ] The user approved the play-back.

## Visuals

| Visual | Generator |
|---|---|
| User stories and sequence diagrams per phase, with phase × kind coverage | `python3 scripts/render_scenarios.py --workspace <ws>` |

## Finish

Validate, stamp (artifact name `scenarios`), report. Next skill: `define-problem-define-boundary`.

## Gotchas

- Do not let scenarios turn into design: "the system queries the database" is internal. "The system returns the matching list" is an output.
- Phases other than operation need scenarios too: how is it shipped, how do people learn it, how is it retired?
