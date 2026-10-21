---
name: define-problem-identify-stakeholders
description: Interview the user to identify every stakeholder of a system (payers, developers, producers, testers, deployers, trainers, operators, users, affected non-users, maintainers, sustainers, improvers, decommissioners) and produce a complete Stakeholder Register. Use after the Concept Brief exists, or whenever someone asks who the stakeholders, users, customers or affected parties of a system are.
license: MIT
compatibility: Requires Python 3.9+ and the jsonschema package (pip install -r scripts/requirements.txt).
metadata:
  "opencode/slash": "true"
  stage: define-problem
  order: "2"
---

# Identify Stakeholders

Stage: Requirements and Design Problem Definition, step 2 of 9. Produces `stakeholders.json`.

**Workspace:** the folder path the user gave after the skill name, else `./sysreq`.
**Inputs:** `concept-brief` (approved). Check with the protocol's required-inputs step. Follow `references/interview-protocol.md` for the whole interview.

## Why this matters

Anyone with a need in any lifecycle phase has a right to have requirements considered, and anyone who pays has the strongest say. A system seen only through its users is judged a failure by everyone else. Missing a stakeholder class here means missing requirements later.

## Your job

Question bank: `references/question-bank.md`.

1. **Seed.** Read the concept brief, then ask the user who they think is involved, in their own words.
2. **Probe.** Walk through the classes in `assets/data/stakeholder-classes.json`, a few at a time. For each class, word the class prompt in the user's sector terms (use the glossary in the concept brief) and ask who fits. Then:
   - Split any group whose members differ in needs, abilities or priorities (for example novice and expert users).
   - Ask who pays, in which phases. Different phases can have different payers.
   - For groups too large to interview, record a `represented_by` surrogate.
   - Ask who regulates or has jurisdiction, and who is harmed if the system fails or misbehaves without ever using it.
3. **Challenge.** Test each class you got no answer for (is "none" really right?), each stakeholder described only by their solution wishes (what need is behind it?), and the payers (is the real payer named?).
4. **Play-back and exit gate.**

## Artifact: `stakeholders.json`

Shape: `assets/templates/stakeholders.template.json`. Authority: `assets/schemas/stakeholders.schema.json`.

- `id` is `STK-001`, `STK-002`, ... never reused.
- `class` is a class id from `assets/data/stakeholder-classes.json`, or `other:<label>` for a class not on the list.
- `needs_summary` and `objectives` are in the stakeholder's language and independent of any solution.
- `interaction_with_system` states what they give to and get from the system as a black box.
- `evidence` says how we know this stakeholder exists (who named them, which document).
- A class with no stakeholder goes in `class_coverage` with a reason. Do not leave a class unaddressed.
- Which phases a stakeholder is active in is **not** stored here. The lifecycle skill records it once, on the phase.

## Exit checklist

- [ ] Every class has at least one stakeholder or a `class_coverage` reason.
- [ ] At least one stakeholder has `pays: true`.
- [ ] Large groups have a `represented_by` surrogate or an open issue.
- [ ] Every stakeholder has evidence and a solution-independent need.
- [ ] The user approved the play-back.

## Visuals

| Visual | Generator |
|---|---|
| Stakeholder map grouped by class (filter by payer and influence) | `python3 scripts/render_stakeholder_map.py --workspace <ws>` |

## Finish

Validate, stamp (artifact name `stakeholders`), report. Next skill: `define-problem-define-lifecycle`. Tell the user the lifecycle skill may add stakeholders it discovers.

## Gotchas

- "The user" is rarely one stakeholder. Ask who else touches the system before it is used and after.
- Victims are easy to forget: people exposed to side effects, neighbors, bystanders, downstream systems' owners.
