---
name: define-problem-build-objectives
description: Interview the user to build an objectives hierarchy: stakeholders' fundamental objectives decomposed into measurable value objectives with thresholds, goals, weights and value curves, then generate the hierarchy visual. Use after scenarios and boundary are defined, or when someone needs to define measures of effectiveness or performance, priorities, trade-offs, or what "good" means for a system.
license: MIT
compatibility: Requires Python 3.9+ and the jsonschema package (pip install -r scripts/requirements.txt).
metadata:
  "opencode/slash": "true"
  stage: define-problem
  order: "6"
---

# Build Objectives Hierarchy

Stage: Requirements and Design Problem Definition, step 6 of 9. Produces `objectives.json`.

**Workspace:** the folder path the user gave after the skill name, else `./sysreq`.
**Inputs:** `stakeholders`, `lifecycle`, `scenarios` (all approved). The boundary is not required but is helpful: if `boundary` is approved, use it to name the measured outputs. Follow `references/interview-protocol.md` for the whole interview.

## Why this matters

The stakeholders' values, not the engineers' guesses, must drive the trade-offs between competing performance, cost and schedule. The hierarchy records what stakeholders would pay more to improve. It is the basis for every later comparison of alternatives. Each stakeholder group and phase can have its own hierarchy.

## Your job

Question bank: `references/question-bank.md`.

1. **Seed.** Ask, per stakeholder group and phase that matters: what would you pay more for, or pay less to avoid?
2. **Probe.**
   - **Fundamental objective:** the aggregate the stakeholders care about (root, level `fundamental`).
   - **Value objectives:** the natural subdivisions of it (level `value`), each something stakeholders value for its own sake. Keep depth between 2 and 5 levels. Carrying the decomposition too far is a mistake.
   - **Measures** (leaves, level `measure`): one measurable quantity each, with `measure_kind` (`effectiveness`, measured outside the system in a defined environment, or `performance`, a property measured of the system), `unit`, `direction`, `threshold` (minimum acceptable), `goal` (the level beyond which stakeholders see no added value), and `conditions` from the scenarios (peak and off-peak, for example).
   - **Weights:** for sibling objectives ask which improvement from threshold to goal is worth the most and score it 100, then score the others relative to it. Convert with `python3 scripts/swing_weights.py 100 60 30` and write the result. Sibling weights must sum to 1.
   - **Value curves:** ask how value grows between threshold and goal (steady, diminishing returns, accelerating, S-shaped, or points) and set `value_curve`.
3. **Challenge.** Reject means objectives: ways to achieve a result (a technology, a component's speed, "use a controller") are not value. Each node must have `design_independent: true`; if the honest answer is no, rewrite it as the value it serves or drop it. Also test: are objectives double-counted, do any measures overlap, is every measure's threshold/goal swing real?
4. **Play-back and exit gate.**

## Artifact: `objectives.json`

Shape: `assets/templates/objectives.template.json`. Authority: `assets/schemas/objectives.schema.json`.

- IDs: hierarchy `OBJ-H1`, node `OBJ-001`..., never reused. One root per hierarchy.
- Only leaves carry `threshold`, `goal`, `unit`, `direction` and `value_curve`. `goal` lies beyond `threshold` in the `direction` of improvement.
- Link nodes to `stakeholder_ids` and `scenario_ids` so each objective is traceable.
- Thresholds and goals live here and only here. The requirements skill copies them into requirement statements and the validator checks they agree.

## Exit checklist

- [ ] One root per hierarchy, depth 2 to 5.
- [ ] Every leaf is a measure with unit, direction, threshold, goal and value curve.
- [ ] Sibling weights sum to 1.
- [ ] No means objectives remain.
- [ ] Each hierarchy is linked to its stakeholders.
- [ ] The user approved the play-back.

## Visuals

| Visual | Generator |
|---|---|
| Objectives hierarchy with weights, thresholds, goals and value curves | `python3 scripts/render_tree.py --workspace <ws> --mode objectives` |

## Finish

Validate, stamp (artifact name `objectives`), report. Next skill: `define-problem-write-requirements`.

## Gotchas

- Weights compare swings (threshold to goal), not the importance of the topic. "Safety matters more than speed" is not an answer; "going from 90 to 99 percent availability matters twice as much as going from 5 to 1 second response" is.
- Stakeholders disagree. Record whose values these are in `stakeholder_ids`. If groups disagree, make separate hierarchies and note the conflict as an open issue.
