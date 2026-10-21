# Systems Engineering Skills

Agent skills that turn a rough system idea into a well-defined design problem. Each skill is an interview: it asks you focused questions, challenges vague or solution-biased answers, and writes a structured artifact only when you agree with it. Each artifact feeds the next skill, and every skill can generate interactive HTML visuals (diagrams, matrices, hierarchies) from the data you have agreed on.

Works with Claude Code, Codex, Antigravity and OpenCode. Runs on Windows, macOS and Linux.

## Install

You need Python 3.9+ and one of the agents above.

```
git clone <this repository>
cd systems-engineering-skills
python install.py
```

The installer asks which agent you use and whether to install for one project or for your whole user account, then copies the skills to the right place for that agent. It also creates a virtual environment (`.sysreq-venv`, next to the skills folder), installs the dependencies into it, and links every skill to it, so the skills use that environment automatically and nothing is installed into your system Python. Run it again after updating the repository.

Options: `--no-venv` skips the environment, and `--venv-dir <folder>` puts it elsewhere. Run `python install.py --help` for all options.

## Use

1. Open your agent in the folder where your project lives.
2. Run the skills in the order below. Pass the folder where the results should be kept; `./sysreq` is the default and is created for you.
3. Answer the questions. Each round gives you a recommended answer, so replying "yes" accepts it.
4. When the skill offers a visual, say yes or no.
5. Approve the result when asked. The skill then tells you which skill to run next.

How to start a skill, by agent:

| Agent | Command |
|---|---|
| Claude Code | `/define-problem-scope-concept ./sysreq` |
| OpenCode | `/define-problem-scope-concept ./sysreq` |
| Codex | `$define-problem-scope-concept ./sysreq` (or `/skills` to pick it) |
| Antigravity | "Use the define-problem-scope-concept skill on ./sysreq" |

Replace the skill name to run the others. A skill that is missing something it needs tells you which skill to run first.

## Define Problem

Requirements and design problem definition. Run in this order.

### 1. Scope System Concept
- **Run:** `define-problem-scope-concept`
- **Needs:** your raw idea.
- **Produces:** `concept-brief.json`; optional context map.
- **Ends when:** the problem is stated without a solution, the system is named, the boundary unknowns have owners, and you approve.
- **Next:** `define-problem-identify-stakeholders`

### 2. Identify Stakeholders
- **Run:** `define-problem-identify-stakeholders`
- **Needs:** the concept brief.
- **Produces:** `stakeholders.json`; optional stakeholder map.
- **Ends when:** every kind of stakeholder is named or ruled out with a reason, someone pays, and you approve.
- **Next:** `define-problem-define-lifecycle`

### 3. Define System Lifecycle
- **Run:** `define-problem-define-lifecycle`
- **Needs:** concept brief, stakeholders.
- **Produces:** `lifecycle.json`; optional stakeholder-by-phase matrix and phase timeline.
- **Ends when:** every lifecycle phase is active, not applicable (with reason) or merged, each active phase has its stakeholders, and you approve. It may add stakeholders it discovers.
- **Next:** `define-problem-develop-scenarios`

### 4. Develop Operational Scenarios
- **Run:** `define-problem-develop-scenarios`
- **Needs:** concept brief, stakeholders, lifecycle.
- **Produces:** `scenarios.json` (user stories, inputs and outputs, mission requirements); optional user-story and sequence-diagram views across phases.
- **Ends when:** every active phase has scenarios for each of its stakeholders, every scenario kind is covered or ruled out, and you approve.
- **Next:** `define-problem-define-boundary`

### 5. Define System Boundary
- **Run:** `define-problem-define-boundary`
- **Needs:** concept brief, lifecycle, scenarios.
- **Produces:** `boundary.json` (external systems, interfaces, controls, boundary decisions); optional external-systems diagrams per phase and context map.
- **Ends when:** every scenario exchange has an interface, nothing is left "TO CONFIRM", and you approve.
- **Next:** `define-problem-build-objectives`

### 6. Build Objectives Hierarchy
- **Run:** `define-problem-build-objectives`
- **Needs:** stakeholders, lifecycle, scenarios.
- **Produces:** `objectives.json` (measures with thresholds, goals, weights, value curves); optional hierarchy visual.
- **Ends when:** weights sum to 1, every leaf is measurable, no objective is a means, and you approve.
- **Next:** `define-problem-write-requirements`

### 7. Write Stakeholder Requirements
- **Run:** `define-problem-write-requirements`
- **Needs:** stakeholders, lifecycle, scenarios, boundary, objectives.
- **Produces:** `requirements.json` (per phase: input/output, system-wide, trade-off, qualification); optional partition tree, requirement levels, traceability matrix, lint report.
- **Ends when:** every phase and interface is covered, every objective measure has a requirement, the linter reports no errors, and you approve.
- **Next:** `define-problem-plan-feasibility`

### 8. Plan Feasibility Analysis
- **Run:** `define-problem-plan-feasibility`
- **Needs:** stakeholders, scenarios, requirements.
- **Produces:** `feasibility-plan.json` (questions, analyses, prototype tasks and steps, usability tests, decision criteria); optional plan view. Planning only: nothing is run or built.
- **Ends when:** every feasibility question has work and decision criteria, and you approve.
- **Next:** `define-problem-revise-from-feedback`

### 9. Revise from Stakeholder Feedback
- **Run:** `define-problem-revise-from-feedback`
- **Needs:** the workspace, plus feedback (paste it or give file paths). Run it whenever stakeholders comment, results come in, or you want to change something approved.
- **Produces:** `feedback.json` and new versions of the artifacts it changes; optional status dashboard and revision diffs.
- **Ends when:** every feedback item has a decision, no artifact is out of date, and an approval decision is recorded.
- **Next:** none if approved (the stage is complete); otherwise it names the earliest skill to run again.

## What is saved

```
sysreq/
  concept-brief.json  stakeholders.json  lifecycle.json  scenarios.json
  boundary.json  objectives.json  requirements.json  feasibility-plan.json  feedback.json
  views/      generated HTML visuals (open in a browser; regenerate, do not edit)
  history/    every approved version of every artifact
```

The JSON files are the single source of truth. Changing an earlier artifact marks the later ones that were built from it as out of date, and the skills help you bring them back in line.

## Troubleshooting

- **A script reports a missing package or environment:** run `python install.py` again. It recreates the virtual environment and relinks the skills. On Debian or Ubuntu, install `python3-venv` first.
- **`python3` not found (Windows):** the skills use `python`; either way the virtual environment is used.
- **Skills not listed in the agent:** restart the agent after installing, and check you installed for the right agent and scope.

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md) to add skills or stages. Released under the [MIT License](LICENSE).
