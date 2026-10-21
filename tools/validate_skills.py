#!/usr/bin/env python3
"""Check every skill folder against the Agent Skills format rules.

Checks: SKILL.md exists; frontmatter has name and description; name is 1-64 chars of lowercase letters,
digits and single hyphens and matches the folder; description is 1-1024 chars; compatibility is at most 500
chars; the body is under 500 lines; every scripts/..., references/... and assets/... path mentioned in SKILL.md
exists; shared copies are in sync.

Usage: python tools/validate_skills.py        Exit codes: 0 ok | 1 problems found
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fm = {}
    for line in m.group(1).splitlines():
        k = re.match(r"^([A-Za-z\"/_-]+):\s*(.*)$", line)
        if k and not line.startswith(" "):
            fm[k.group(1)] = k.group(2).strip()
    return fm, text[m.end():]


def main():
    problems = []
    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        f = d / "SKILL.md"
        if not f.exists():
            problems.append(f"{d.name}: SKILL.md missing")
            continue
        text = f.read_text(encoding="utf-8")
        fm, body = frontmatter(text)
        if fm is None:
            problems.append(f"{d.name}: frontmatter missing")
            continue
        name, desc = fm.get("name", ""), fm.get("description", "")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
            problems.append(f"{d.name}: invalid name '{name}'")
        if name != d.name:
            problems.append(f"{d.name}: name '{name}' must match the folder")
        if not 1 <= len(desc) <= 1024:
            problems.append(f"{d.name}: description length {len(desc)} (must be 1-1024)")
        if len(fm.get("compatibility", "")) > 500:
            problems.append(f"{d.name}: compatibility over 500 chars")
        if len(body.splitlines()) >= 500:
            problems.append(f"{d.name}: body has {len(body.splitlines())} lines (keep under 500)")
        for rel in sorted(set(re.findall(r"(?:scripts|references|assets)/[A-Za-z0-9_./\-<>]+", body))):
            rel = rel.rstrip(".,)")
            if "<" in rel or "*" in rel:
                continue
            if not (d / rel).exists():
                problems.append(f"{d.name}: SKILL.md mentions {rel} which does not exist")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_shared.py"), "--check"], capture_output=True, text=True)
    if r.returncode:
        problems.append(r.stdout.strip() or r.stderr.strip())
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print(f"{len(list(SKILLS.iterdir()))} skills valid")


if __name__ == "__main__":
    main()
