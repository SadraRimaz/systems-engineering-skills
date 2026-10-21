---
name: define-problem-write-requirements
description: Interview the user to write stakeholder requirements per lifecycle phase, partitioned into input/output, system-wide and technology, trade-off, and qualification categories, with "shall" grammar, thresholds, goals, rationale and traceability, then generate the partition tree, traceability matrix and a requirement lint report. Use after objectives are built, or when someone wants to write, check or organize requirements.
license: MIT
compatibility: Requires Python 3.9+ and the jsonschema package (pip install -r scripts/requirements.txt).
metadata:
  "opencode/slash": "true"
  stage: define-problem
  order: "7"
---

# Write Stakeholder Requirements

Stage: Requirements and Design Problem Definition, step 7 of 9. Produces `requirements.json`.

**Workspace:** the folder path the user gave after the skill name, else `./sysreq`.
**Inputs:** `stakeholders`, `lifecycle`, `scenarios`, `boundary`, `objectives` (all approved). Follow `references/interview-protocol.md` for the whole interview.

## Why this matters

Stakeholder requirements state what the stakeholders need in their own terms, leaving design freedom. They must be complete enough that the stakeholders are happy with whatever is built, and loose enough that many designs remain feasible. Requirements in one phase often constrain the design in another, so they are written per phase.

## Your job

Question bank and writing rules: `references/question-bank.md`.

1. **Draft the skeleton.** Run `python3 scripts/draft_requirements.py --workspace <ws> --write`. It adds one input/output/interface requirement per interface and one performance requirement per objective measure, all flagged `tbd` with a placeholder rationale. Re-run after upstream changes; it only adds what is missing. Rewrite each drafted item with the user.
2. **Probe** per active phase, one group at a time. The categories are in `assets/data/requirement-categories.json`, with typical dimensions for each:
   - **Input/output:** inputs, outputs, external interface constraints, and the two to six first-level functions stated as what the system must deliver, not how. Stakeholders should not care how functions are done as long as inputs and outputs satisfy them.
   - **Technology and system-wide:** technology constraints (each needs a justification, such as interoperability), quality (usability, reliability, safety, security and so on), cost per phase, schedule per phase. Regulation belongs here once, not duplicated in input/output.
   - **Trade-off:** performance, cost and cost-performance trade-offs, taken from the objectives weights and value curves and from willingness to pay. Add exactly one overall cross-phase cost-performance requirement with `phase_id` `ALL`.
   - **Qualification:** observance (which data is collected, by which method), verification, validation (traced to scenarios) and acceptance (criteria and who decides). Set `qualification_method` on every performance requirement.
3. **Write each statement** by the rules in the question bank: "The <system> shall <verb> <object> <condition>"; one `shall` each; thresholds with units; a design goal where it applies; no vague words; positive statements. Ask for the rationale of each; trying to write one often reveals the real requirement.
4. **Lint.** Run `python3 scripts/lint_requirements.py --workspace <ws> --json` and rewrite flagged statements with the user.
5. **Challenge.** Test each requirement for hidden solutions, over-constraint (does it exclude designs stakeholders would accept?), conflicts with other requirements, and whether one design exists that could meet all of them (feasibility is planned in the next skill).
6. **Play-back and exit gate.**

## Artifact: `requirements.json`

Shape: `assets/templates/requirements.template.json`. Authority: `assets/schemas/requirements.schema.json`.

- `id` is `REQ-001`..., never reused. Each requirement has exactly one `phase_id` and one `category`.
- `sources` trace to stakeholders, scenarios, interfaces, objectives and mission requirements; at least one stakeholder, scenario or mission is required.
- `threshold` and `goal` for an objective measure must match `objectives.json`.
- A group that does not apply in a phase goes in `partition_notes` with a reason.

## Exit checklist

- [ ] Every active phase has all four groups, or a `partition_notes` reason.
- [ ] Every interface has an input, output or interface requirement.
- [ ] Every objective measure has a requirement with threshold and goal.
- [ ] Exactly one overall cross-phase trade-off requirement and at least one acceptance requirement.
- [ ] Linter shows no errors and the user has seen every warning.
- [ ] No placeholder rationale remains and no `tbd` is unexplained.
- [ ] The user approved the play-back.

## Visuals

| Visual | Generator |
|---|---|
| Requirements partition by phase, group and category | `python3 scripts/render_tree.py --workspace <ws> --mode partition` |
| Requirement levels (mission, stakeholder, derived later) | `python3 scripts/render_tree.py --workspace <ws> --mode levels` |
| Traceability and qualification matrix, with coverage gaps | `python3 scripts/render_traceability.py --workspace <ws>` |
| Requirement lint report | `python3 scripts/lint_requirements.py --workspace <ws>` |

## Finish

Validate, stamp (artifact name `requirements`), report. Next skill: `define-problem-plan-feasibility`.

## Gotchas

- Real approval of the acceptance requirements by the stakeholders is recorded by the last skill, not here. Say so to the user.
- Do not write requirements for functions. Write them for what crosses the boundary.
