---
name: define-problem-scope-concept
description: Interview the user about a raw system, product or service idea and turn it into a clear, agreed Concept Brief (problem, purpose, boundary hypothesis, domain vocabulary). Use first, before any requirements work, whenever someone has an idea they want to mature, scope, or define as a design problem, even if they do not say "concept" or "scope".
license: MIT
compatibility: Requires Python 3.9+ and the jsonschema package (pip install -r scripts/requirements.txt).
metadata:
  "opencode/slash": "true"
  stage: define-problem
  order: "1"
---

# Scope System Concept

Stage: Requirements and Design Problem Definition, step 1 of 9. Produces `concept-brief.json`, the foundation every later skill reads.

**Workspace:** the folder path the user gave after the skill name, else `./sysreq`. Create it if it does not exist.
**Inputs:** none. The user presents the raw idea. Follow `references/interview-protocol.md` for the whole interview.

## Your job

Mature the idea into a statement of the problem and a first view of the system's place in the world, without choosing a solution. Question bank: `references/question-bank.md`.

1. **Seed.** Let the user describe the idea in their own words. Store it verbatim in `raw_idea`.
2. **Probe** in this order, one round at a time:
   - The problem, who has it, how it is handled today, and the larger purpose behind it.
   - Mission objectives, the value proposition, and a "day in the life" story.
   - The system of interest: its name and a black-box description (what goes in, what comes out).
   - The boundary hypothesis: what is inside, what is clearly outside and how it relates, what is still unknown and who will find out.
   - Constraints, assumptions, non-goals.
   - Domain: the sector, then a glossary mapping the generic lifecycle terms in `assets/data/baseline-lifecycle.json` to the user's terms (for example "manufacturing" to "build and packaging" in software).
3. **Challenge.** Test the problem statement for hidden solutions ("we need an app", "use AI"), for the right level of problem (is there a larger purpose that changes the answer?), and for terms that could be read two ways. Record each challenge in `solution_bias_flags` with how it was resolved.
4. **Play-back and exit gate.**

## Artifact: `concept-brief.json`

Shape: `assets/templates/concept-brief.template.json`. Authority: `assets/schemas/concept-brief.schema.json`.

- `problem_statement` names a need, never a solution or technology.
- `system_of_interest.name` is used verbatim by every later skill as the system's name in scenarios. Choose it carefully with the user.
- `boundary_hypothesis.unknown` items each need an `owner`.
- `domain_profile.glossary` keeps `baseline_term` so the generic and domain terms stay linked.
- Record every decision in `decisions_log` and every unresolved item in `open_issues`.

## Exit checklist

- [ ] The problem statement contains no solution.
- [ ] At least one mission objective, tied to the larger purpose.
- [ ] The system has a name and a black-box description.
- [ ] Every boundary unknown has an owner.
- [ ] Sector and glossary are set.
- [ ] The user approved the play-back.

## Visuals

Offer them with the visual gate in the protocol.

| Visual | Generator |
|---|---|
| Context map (draft from the boundary hypothesis) | `python3 scripts/render_context_map.py --workspace <ws>` |

## Finish

Validate, stamp (artifact name `concept-brief`) and report as the protocol says. Next skill: `define-problem-identify-stakeholders`.

## Gotchas

- Users often arrive with a solution. Do not reject it. Ask what need it serves and write the need.
- Do not ask for stakeholders or lifecycle phases here. The next skills cover them. A passing mention is fine; record it in `open_issues`.
