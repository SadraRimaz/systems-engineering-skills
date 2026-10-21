# Question bank and writing rules: requirements

Category definitions and typical dimensions: `assets/data/requirement-categories.json`.

## Writing rules
- Form: `The <system or phase system> shall <verb> <object> <condition at the end>.` `shall` states a requirement, `will` a fact, `should` a goal.
- One requirement, one `shall`. Split compound predicates ("shall fit, weigh and cost").
- State what the system does, not what it must not do. Rewrite "shall not" positively.
- No "and/or"; say which. No vague verbs (maximize, minimize, accommodate, handle, support) and no vague adjectives (adequate, flexible, rapid, robust, user-friendly).
- Give a minimum acceptable threshold with its unit, and a design goal where stakeholders value more.
- Do not specify a solution. A technology constraint belongs in the technology category with a justification.
- Each requirement is verifiable by a finite, affordable process and traceable to a stakeholder, scenario or mission.
- Write a rationale. If you cannot, the requirement may not be real.

## Input and output
- What must the system receive in this phase? What accuracy, rate, timing, and what bounds on inputs? What must it do with unexpected or unwanted inputs?
- What must it produce? For each output: quality (accuracy, correctness, security), quantity (intensity, throughput, coverage), timing (response time, update rate, availability).
- What does each external interface force: format, timing, physical fit?
- What are the two to six top-level things the system does, stated as what it delivers?

## System-wide and technology
- Which laws or standards apply? (Put each once, here.)
- Is any technology or platform mandated? Why (compatibility, existing product line, cost)?
- Which qualities matter in this phase: usability, availability, reliability, maintainability, supportability, safety, security, trainability, testability, extensibility, size or weight?
- What are the cost limits and schedule limits for this phase? What is the operational life?

## Trade-off
- Which performance measures matter most, and how do stakeholders trade one against another? (Use the objectives hierarchy.)
- How should costs in different phases and by different payers be compared?
- How much would stakeholders pay for a given performance gain? Can that be written into the contract?
- Overall across phases: how are alternative designs compared end to end?

## Qualification
- For each input/output and system-wide requirement: how will we know it is met (demonstration, analysis and simulation, inspection, instrumented test)?
- Verification: how will the data show the real system matches its design? What is pass and fail?
- Validation: how will the data show it satisfies the stakeholders' needs? Which scenarios are replayed?
- Acceptance: what makes the stakeholders accept it, who decides, and by when?
- Does the qualification system itself need requirements (test equipment, facilities, simulators)?

## Challenge prompts
- "Does this rule out a design the stakeholders would be happy with?"
- "Is this a need or a means? What need does it serve?"
- "Could two readers disagree on whether this is met?"
- "Which other requirement could conflict with this one?"
