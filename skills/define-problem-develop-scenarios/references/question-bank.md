# Question bank: scenarios

Scenario kinds and prompts are in `assets/data/scenario-kinds.json`.

## Starting a phase
- Who is the key stakeholder here, and what are they trying to get done?
- Describe the most common successful interaction, step by step, as things crossing the boundary: who gives what to whom?
- What does each party see, hear or receive at each step?

## Widening
- Who else is involved in this phase, and what do they do with or to the system?
- What changes with different kinds of people (ability, experience, language) or contexts (place, season, load)?
- What does the system do at the busiest and the quietest times?
- What does a maintainer, supplier or support person do, and what keeps working meanwhile?

## Complexity
- What other system can fail or misbehave around it? What should the system do?
- How should it fail when something inside it breaks, so the surroundings suffer least?
- What are the extremes of the environment: cold, noise, overload, hostile users?
- How does it start up, and how is it shut down safely?

## Writing exchanges
- Who is the sender and who the receiver? What exactly is passed (data, energy, matter)?
- Is that the system's input or output? If it describes how the system works inside, restate what comes in and goes out.
- What feedback does each party need at each step to know what is happening?

## Mission requirements
- What do the stakeholders ultimately want to achieve with it, measured outside the system?
- What measure would they use to say the mission succeeded?
- Is there a tail they care about (the worst case, not only the average)?

## User stories
- "As a <stakeholder in this phase>, I want <output or capability>, so that <objective>." What goes in each blank?

## Challenge prompts
- "In step <n> the system 'decides' or 'computes'. What does the outside world see instead?"
- "This phase has no failure scenario. What could go wrong, and who notices?"
- "<Stakeholder> is active in this phase but has no scenario. What do they do?"
