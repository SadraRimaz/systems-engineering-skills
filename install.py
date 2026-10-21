#!/usr/bin/env python3
"""Install the skills for your coding agent (Windows, macOS and Linux).

Run it and answer the prompts:

    python install.py

Or skip the prompts:

    python install.py --agent claude --scope project --project-dir /path/to/your/project --yes

Agents: claude (Claude Code), codex (Codex), antigravity (Antigravity), opencode (OpenCode).
Scope: project (skills live in one project) or global (skills available everywhere for your user).
Needs only Python 3.8+ (with the standard 'venv' module). The installer creates a virtual environment next to the skills
folder (for example .claude/.sysreq-venv), installs the helper-script requirements into it, and points every installed
skill at it, so the skills always run with the right packages. Use --no-venv to skip this.
"""
import argparse
import os
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


def venv_python(venv):
    return venv / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")


def make_venv(venv):
    """Create the virtual environment (if needed) and install the requirements. Returns its Python or None."""
    py = venv_python(venv)
    try:
        if not py.is_file():
            print(f"Creating virtual environment in {venv}")
            subprocess.check_call([sys.executable, "-m", "venv", str(venv)])
        print("Installing requirements into it")
        subprocess.check_call([str(py), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "-r", str(ROOT / "shared" / "scripts" / "requirements.txt")])
        return py
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"warning: could not set up the virtual environment ({exc}).")
        print("  On Debian/Ubuntu install the 'python3-venv' package, then run this installer again.")
        return None


def link_venv(dest, names, py):
    for n in names:
        (dest / n / ".venv-python").write_text(str(py) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", choices=sorted(AGENTS))
    ap.add_argument("--scope", choices=["project", "global"])
    ap.add_argument("--project-dir", help="project folder for --scope project (default: current folder)")
    ap.add_argument("--yes", action="store_true", help="do not ask for confirmation (replace existing skills)")
    ap.add_argument("--no-venv", action="store_true", help="do not create a virtual environment (skills then use the system Python)")
    ap.add_argument("--venv-dir", help="use this folder for the virtual environment (default: .sysreq-venv beside the skills folder)")
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
        if not names:
            continue
        print(f"Installed {len(names)} skills into {dest}")
        installed = names
        if not a.no_venv:
            venv = Path(a.venv_dir).expanduser().resolve() if a.venv_dir else dest.parent / ".sysreq-venv"
            py = make_venv(venv)
            if py:
                link_venv(dest, names, py)
    if not installed:
        return
    if a.no_venv:
        print("No virtual environment created. Install the requirements yourself: pip install -r shared/scripts/requirements.txt")
    info = AGENTS[agent]
    print(f"\nDone. Open {info['label']} and start with:\n  " + info["use"].format(name=FIRST))
    print("Then follow the order in README.md.")


if __name__ == "__main__":
    main()
