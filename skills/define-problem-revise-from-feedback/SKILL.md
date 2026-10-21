---
name: define-problem-revise-from-feedback
description: Ingest stakeholder feedback on the produced documents (meeting notes, comments, emails, approvals, feasibility results), triage each item with the user, revise the affected artifacts in dependency order, clear stale downstream artifacts, record approval or disapproval, and show a status dashboard and revision diffs. Use when stakeholders have reviewed or commented on the artifacts, when results come back, or when the user wants to change anything already approved.
license: MIT
compatibility: Requires Python 3.9+ and the jsonschema package (pip install -r scripts/requirements.txt).
metadata:
  "opencode/slash": "true"
  stage: define-problem
  order: "9"
---

# Revise from Stakeholder Feedback

Stage: Requirements and Design Problem Definition, step 9 of 9. Produces `feedback.json` and new versions of any artifact it changes.

**Workspace:** the folder path the user gave after the skill name, else `./sysreq`.
**Inputs:** an existing workspace, plus the feedback itself: pasted text or file paths (notes, emails, comments, results). If no feedback was given, ask for it. Follow `references/interview-protocol.md` for the whole interview.

## Why this matters

Requirements are never right the first time; the stakeholders' needs sharpen as they see the documents. Capture every comment, trace it to the exact artifact items it touches, and keep all artifacts consistent. The real exit of this whole stage is the stakeholders' approval of how the system will be accepted.

## Your job

Question bank: `references/question-bank.md`.

1. **Status.** Run `python3 scripts/status.py --workspace <ws>`. Note which artifacts are approved, draft or stale.
2. **Ingest.** Split the feedback into items. For each item, keep the `raw_text`, the `source`, the `received` date and who it came from (`from_stakeholder_id` if known). Never paraphrase the raw text.
3. **Map and classify.** Link each item to the IDs it touches (`targets`: STK-, LC-, SCN-, MSN-, EXT-, IF-, CTL-, BD-, OBJ-, REQ-, FQ-, AN-, PT-, UT-, ES-) and classify it: `clarification`, `change_request`, `new_requirement`, `conflict`, `approval` or `rejection`. Ask when a target is unclear.
4. **Triage with the user** in rounds. For each item propose a disposition with a recommended answer: `accepted`, `rejected`, `deferred` (both need a rationale) or `needs_clarification`. Conflicts between stakeholders are put to the user explicitly; do not resolve them silently.
5. **Apply accepted items, upstream first.** Use the dependency order of the artifacts (concept brief, stakeholders, lifecycle, scenarios, boundary, objectives, requirements, feasibility plan). For each changed artifact: edit it, validate it, show the user the change, get approval, stamp it (`--approve`). Record `applied_in` (artifact and new version) on each accepted item.
6. **Clear stale artifacts.** Run `python3 scripts/validate.py --workspace <ws>`. For every artifact reported stale, compare with the previous version (`scripts/diff_versions.py`), review with the user what the upstream change affects, update it, and stamp it again. Repeat until nothing is stale. For missing items an upstream change calls for (a new stakeholder needing scenarios, an interface needing a requirement), say which skill covers them and offer to run it.
7. **Approvals.** Ask the stakeholders' decision on the acceptance requirements (or the whole set): record in `approvals` the stakeholder IDs, `scope`, `decision` (`approved` or `disapproved`), date and any conditions.
8. **Challenge.** Test: does any accepted change contradict another artifact? Did a "clarification" quietly change a requirement? Is any approval conditional on something unrecorded?
9. **Play-back and exit gate.**

## Artifact: `feedback.json`

Shape: `assets/templates/feedback.template.json`. Authority: `assets/schemas/feedback.schema.json`. IDs `FB-001`..., never reused. Add new items on later rounds and keep old ones.

## Exit checklist

- [ ] Every item has a disposition; rejected and deferred have a rationale; accepted have `applied_in`.
- [ ] No artifact is stale.
- [ ] An approval decision is recorded for the acceptance requirements.
- [ ] The user approved the play-back.

## Visuals

| Visual | Generator |
|---|---|
| Pipeline status dashboard | `python3 scripts/render_dashboard.py --workspace <ws>` |
| Revision diff for an artifact (needs two stamped versions) | `python3 scripts/diff_versions.py --workspace <ws> --artifact <name>` |

## Finish

Validate, stamp (artifact name `feedback`), report. Then:
- If approved with nothing open: the stage is complete. Say so and point to the dashboard.
- If disapproved or changes remain: name the earliest affected skill and give its slash form to re-run it.

## Gotchas

- Stamping an upstream artifact makes downstream ones stale. That is intended: it tells you what to re-confirm.
- Do not edit artifacts the feedback does not touch. Do not "improve" them while you are there.
