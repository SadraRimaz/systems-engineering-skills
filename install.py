#!/usr/bin/env python3
"""Install the skills for your coding agent (Windows, macOS and Linux).

Run it and answer the prompts:

    python install.py

Or skip the prompts:

    python install.py --agent claude --scope project --project-dir /path/to/your/project --yes

Agents: claude (Claude Code), codex (Codex), antigravity (Antigravity), opencode (OpenCode).
Scope: project (skills live in one project) or global (skills available everywhere for your user).
Needs only Python 3.8+. The skills' helper scripts need the 'jsonschema' package; this installer offers to install it.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILLS = ROOT / "skills"
HOME = Path.home()

AGENTS = {
    "claude": {"label": "Claude Code", "project": [".claude/skills"], "global": [HOME / ".claude" / "skills"],
               "use": "/{name} ./sysreq"},
    "codex": {"label": "Codex", "project": [".agents/skills"], "global": [HOME / ".agents" / "skills"],
              "use": "${name} ./sysreq   (or type /skills to pick it)"},
    "antigravity": {"label": "Antigravity", "project": [".agents/skills"], "global": [HOME / ".gemini" / "config" / "skills"],
                    "use": "Ask: use the {name} skill on ./sysreq   (in the CLI, /skills lists installed skills)"},
    "opencode": {"label": "OpenCode", "project": [".opencode/skills"], "global": [HOME / ".config" / "opencode" / "skills"],
                 "use": "/{name} ./sysreq"},
}
FIRST = "define-problem-scope-concept"


def ask_choice(title, options):
    print(f"\n{title}")
    for i, (_, label) in enumerate(options, 1):
        print(f"  {i}. {label}")
    while True:
        raw = input("Enter a number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1][0]
        print("Please enter one of the numbers above.")


def ask_yes(question, default=True):
    raw = input(f"{question} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    return default if not raw else raw.startswith("y")


def targets(agent, scope, project_dir):
    info = AGENTS[agent]
    if scope == "project":
        return [Path(project_dir) / rel for rel in info["project"]]
    out = list(info["global"])
    if agent == "antigravity" and (HOME / ".gemini" / "antigravity-cli").is_dir():
        out.append(HOME / ".gemini" / "antigravity-cli" / "skills")
    return out


def copy_skills(dest, assume_yes):
    names = sorted(p.name for p in SKILLS.iterdir() if (p / "SKILL.md").exists())
    existing = [n for n in names if (dest / n).exists()]
    if existing and not assume_yes:
        if not ask_yes(f"{len(existing)} of these skills already exist in {dest}. Replace them?", True):
            print("Skipped.")
            return []
    dest.mkdir(parents=True, exist_ok=True)
    for n in names:
        target = dest / n
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(SKILLS / n, target, ignore=shutil.ignore_patterns("__pycache__", ".synced", "*.pyc"))
    return names


def deps_ok():
    try:
        import jsonschema  # noqa: F401
        return True
    except ImportError:
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", choices=sorted(AGENTS))
    ap.add_argument("--scope", choices=["project", "global"])
    ap.add_argument("--project-dir", help="project folder for --scope project (default: current folder)")
    ap.add_argument("--yes", action="store_true", help="do not ask for confirmation (replace existing skills)")
    ap.add_argument("--install-deps", action="store_true", help="pip install the helper-script requirements")
    a = ap.parse_args()
    interactive = sys.stdin.isatty()
    if not SKILLS.is_dir():
        sys.exit("error: skills/ folder not found. Run this script from the repository.")
    if (not a.agent or not a.scope) and not interactive:
        sys.exit("error: not an interactive terminal. Pass --agent and --scope (see --help).")
    agent = a.agent or ask_choice("Which coding agent do you use?", [(k, v["label"]) for k, v in AGENTS.items()])
    scope = a.scope or ask_choice("Where should the skills be installed?", [
        ("project", "Only in one project (recommended if you will work on one system)"),
        ("global", "Everywhere for my user account")])
    project_dir = a.project_dir
    if scope == "project" and not project_dir:
        raw = input(f"Project folder [{Path.cwd()}]: ").strip() if interactive else ""
        project_dir = raw or str(Path.cwd())
    installed = []
    for dest in targets(agent, scope, project_dir):
        names = copy_skills(dest, a.yes)
        if names:
            print(f"Installed {len(names)} skills into {dest}")
            installed = names
    if not installed:
        return
    if not deps_ok():
        want = a.install_deps or (interactive and not a.yes and ask_yes("The helper scripts need the 'jsonschema' package. Install it now with pip?", True))
        if want:
            subprocess.call([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "shared" / "scripts" / "requirements.txt")])
        else:
            print(f"Later, run: {sys.executable} -m pip install -r shared/scripts/requirements.txt")
    info = AGENTS[agent]
    print(f"\nDone. Open {info['label']} and start with:\n  " + info["use"].format(name=FIRST))
    print("Then follow the order in README.md.")


if __name__ == "__main__":
    main()
