# Interview protocol

Every skill in this repository follows this protocol. A skill is an expert interview, not a form to fill in or a one-shot generator. Keep going until you and the user share one understanding, then write the artifact.

## Ground rules

- **Read before asking.** Load the workspace artifacts you need and never ask for what is already recorded.
- **Never invent facts.** If data is missing, ask the user. If the user cannot answer now, record an open issue (`kind` TBD, TBR or question, with an `owner`) and move on.
- **Problems, not solutions.** Capture needs in the user's own terms and keep them independent of how the system will be built. When a statement names a technology, product or design, ask what need it serves.
- **Black box.** Describe the system only by what crosses its boundary: what goes in, what comes out. Do not describe internal processing.
- **Use the user's vocabulary.** The concept brief holds a domain profile with a glossary. Word questions and artifact text in the user's sector terms and keep the `baseline_ref` that points to the generic term.
- **Be direct.** Short questions. No lectures. Explain a concept in one sentence only when the user needs it to answer.

## Phases

### 1. Seed
Ask the user for an open narrative first, or reuse what the workspace already holds. Do not ask questions yet unless the narrative is empty.

### 2. Probe
Ask in rounds. A round contains every question you can ask now, meaning every question whose answer does not depend on an answer still open in the same round. Hold the rest for later rounds. Use at most 4 questions per round. Format each question like this, so a plain "yes" accepts your recommendation:

```
❓ **Q1** - **<short title>**: <the question, with options if there are any>

➡️ <your recommended answer, grounded in what you already know>
```

Look up facts yourself (files, the workspace, the data files) instead of asking the user. Ask only for decisions and for knowledge only the user has. After the user answers, save the draft artifact (see Saving drafts), then compute the next round.

### 3. Challenge
Before closing, test the draft: name any solution hidden in a need, any over-constraint that removes design freedom, any term that two people could read differently, and anything that is true only for the happy path. Put each challenge to the user as a question with a recommended resolution.

### 4. Play-back
Show the draft in plain language: a short list or table, not raw JSON. Include the open issues. Ask what is wrong or missing. Repeat Probe and Challenge until the user has no corrections.

### 5. Exit gate
Run the skill's exit checklist. Tell the user which items pass and which do not. Ask for explicit approval ("Approve this and save it?"). Only after the user says yes, finish (see Finishing).

## Saving drafts and resuming

- After each Probe round write the artifact file in the workspace with `meta.status` set to `draft` and `meta.version` unchanged. Use `assets/templates/<artifact>.template.json` as the starting shape; `assets/schemas/<artifact>.schema.json` is the authority.
- At the start of a skill, check whether the artifact file exists. If it is a draft, summarize it in three lines and resume. If it is approved and current, ask what the user wants to change and work in revision mode. If it is flagged stale (see `scripts/validate.py` output), review what changed upstream with the user and update only what it affects.
- IDs are stable. Never renumber or reuse an ID. Add new IDs at the end.

## Required inputs

Run `python3 scripts/validate.py --workspace <ws> --require <list>` for the artifacts the skill needs. If anything is missing, unfinished or not approved, tell the user which skill to run first (the output names it in `run_first`) and stop. Do not build on unapproved inputs and do not make up the missing data.

## Visual gate

Each skill lists the visuals it can generate. For each one, in this order:

1. Run the generator with `--check-ready`. Exit code 3 means data is missing: tell the user what is missing and do not ask.
2. If it is ready, name the visual and ask exactly: **"Based on the data gathered so far, I can generate this. Would you like me to generate it for you?"**
3. Generate only if the user says yes. Report the output path. Visuals are derived from the artifacts and are never edited by hand: to change one, change the artifact and regenerate.

## Finishing

1. Run `python3 scripts/validate.py --workspace <ws> --artifact <name>`. Fix every error with the user.
2. After the user approves the read-back, run `python3 scripts/stamp.py --workspace <ws> --artifact <name> --summary "<one line>" --approve`.
3. Tell the user, in at most four lines: what was produced and where, how many open issues remain, which downstream artifacts are now stale (if any), and which skill to run next. The stamp output names the next skill. Show its slash form: `/<next-skill> <workspace>`.

## Conventions

- Run scripts from this skill's folder. Resolve the workspace to an absolute path first, because the working directory may differ. Use `python` where `python3` does not exist.
- If a script reports a missing package, run `pip install -r scripts/requirements.txt`.
- Scripts never prompt. They read files and flags and write JSON to stdout, diagnostics to stderr.
- Exit codes: 0 ok, 1 invalid content, 2 usage or missing file, 3 not ready.
