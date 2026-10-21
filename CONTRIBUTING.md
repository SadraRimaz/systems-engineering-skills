# Contributing

## Layout

```
shared/      single source for scripts, data, schemas and the interview protocol
skills/      one self-contained folder per skill (shared files are copied in)
tools/       sync_shared.py, validate_skills.py
install.py   cross-platform installer
```

Never edit shared files inside `skills/`. Edit `shared/`, then run `python tools/sync_shared.py`.

## Add a skill to an existing stage

1. Create `skills/<stage>-<action>/SKILL.md`. The folder name equals the `name` field: lowercase letters, digits and single hyphens, at most 64 characters. Use the stage prefix (for example `define-problem-`).
2. Frontmatter: `name`, `description` (what it does and when to use it, at most 1024 characters, imperative and specific), `license`, `compatibility`, and `metadata` with `"opencode/slash": "true"`, `stage` and `order`.
3. Keep `SKILL.md` under 500 lines. Put question banks in `references/`.
4. Follow `shared/protocols/interview-protocol.md`: the skill interviews, challenges, plays back, and writes only after approval.
5. Add the skill to `shared/data/pipeline.json` with its artifact name and upstream artifacts, and add `shared/schemas/<artifact>.schema.json` and a validator function in `shared/scripts/validate.py`.
6. Mention the scripts it uses in `SKILL.md` as `scripts/<name>.py`; the sync tool copies exactly those (plus their imports).
7. Add its section to `README.md` in run order.

## Add a new stage

Add a new stage entry to `shared/data/pipeline.json`, use a new skill prefix, and add a section to `README.md`. Stages reuse the shared library and the same workspace conventions.

## Script rules

- Never prompt. Take input from flags and files, write JSON to stdout and diagnostics to stderr.
- Provide `--help`, clear error messages that say what to do next, and these exit codes: 0 ok, 1 invalid content, 2 usage or missing file, 3 not ready.
- Standard library only, plus the packages in `shared/scripts/requirements.txt`.
- Import `sysreq_lib` before any third-party package: it re-runs the script in the installer's virtual environment (the skill's `.venv-python` file points to it; `SYSREQ_NO_VENV=1` disables this).
- Visual generators write one self-contained HTML file and support `--check-ready`.

## Before you commit

```
python tools/sync_shared.py
python tools/validate_skills.py
```
