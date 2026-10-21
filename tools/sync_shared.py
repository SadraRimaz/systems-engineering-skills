#!/usr/bin/env python3
"""Copy shared files into every skill folder so each skill is self-contained and installable.

The single source for scripts, data, schemas and the interview protocol is shared/. Never edit the
copies inside skills/. Which scripts a skill receives is read from the script names mentioned in its
SKILL.md (plus the scripts they import). Artifact templates are generated from the JSON schemas.

Usage:
  python tools/sync_shared.py          copy files (run after changing anything in shared/)
  python tools/sync_shared.py --check  report drift and exit 1 if skills/ is out of date
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "shared"
SKILLS = ROOT / "skills"
MARKER = ".synced"
ALWAYS = ["sysreq_lib.py", "validate.py", "stamp.py", "status.py", "lint_requirements.py", "requirements.txt"]


def script_closure(names):
    have, todo = set(), list(names)
    while todo:
        n = todo.pop()
        if n in have:
            continue
        have.add(n)
        p = SHARED / "scripts" / n
        if p.suffix == ".py" and p.exists():
            for m in re.finditer(r"^(?:import|from)\s+(\w+)", p.read_text(encoding="utf-8"), re.M):
                dep = f"{m.group(1)}.py"
                if (SHARED / "scripts" / dep).exists():
                    todo.append(dep)
    return sorted(have)


def placeholder(schema):
    t = schema.get("type")
    if "enum" in schema:
        return " | ".join(str(x) for x in schema["enum"])
    if isinstance(t, list):
        return None
    if t == "object":
        return {k: placeholder(v) for k, v in schema.get("properties", {}).items()}
    if t == "array":
        return [placeholder(schema.get("items", {}))]
    if t == "string":
        m = re.match(r"^\^([A-Z]+(?:-H)?)-?\\d", schema.get("pattern", ""))
        if m:
            return f"{m.group(1)}-H1" if m.group(1).endswith("-H") else f"{m.group(1)}-001"
        return ""
    if t == "integer":
        return 1
    if t == "number":
        return 0
    if t == "boolean":
        return False
    return None


def template(artifact):
    schema = json.loads((SHARED / "schemas" / f"{artifact}.schema.json").read_text(encoding="utf-8"))
    obj = placeholder(schema)
    obj["meta"] = {"artifact": artifact, "version": 0, "status": "draft", "built_from": {}, "changelog": []}
    ordered = {"meta": obj.pop("meta"), **obj}
    return json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"


def wanted(skill_dir, artifact):
    """Return {relative path: bytes} the skill should contain from shared/."""
    out = {}
    body = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    named = set(re.findall(r"scripts/([A-Za-z0-9_\-]+\.py)", body))
    missing = [n for n in named if not (SHARED / "scripts" / n).exists()]
    if missing:
        sys.exit(f"error: {skill_dir.name}/SKILL.md mentions scripts that do not exist in shared/scripts: {missing}")
    for n in script_closure(ALWAYS + sorted(named)):
        out[f"scripts/{n}"] = (SHARED / "scripts" / n).read_bytes()
    out["references/interview-protocol.md"] = (SHARED / "protocols" / "interview-protocol.md").read_bytes()
    for p in sorted((SHARED / "data").glob("*.json")):
        out[f"assets/data/{p.name}"] = p.read_bytes()
    for p in sorted((SHARED / "schemas").glob("*.json")):
        out[f"assets/schemas/{p.name}"] = p.read_bytes()
    if artifact:
        out[f"assets/templates/{artifact}.template.json"] = template(artifact).encode("utf-8")
    return out


def pipeline():
    d = json.loads((SHARED / "data" / "pipeline.json").read_text(encoding="utf-8"))
    return {s["skill"]: s["artifact"] for st in d["stages"] for s in st["skills"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only report drift")
    a = ap.parse_args()
    arts = pipeline()
    drift = []
    for skill, artifact in arts.items():
        d = SKILLS / skill
        if not (d / "SKILL.md").exists():
            drift.append(f"{skill}: folder or SKILL.md missing")
            continue
        want = wanted(d, artifact)
        marker = d / MARKER
        old = marker.read_text(encoding="utf-8").split() if marker.exists() else []
        for rel in old:
            if rel not in want and (d / rel).exists():
                drift.append(f"{skill}/{rel}: no longer shared") if a.check else (d / rel).unlink()
        for rel, data in want.items():
            f = d / rel
            if not f.exists() or f.read_bytes() != data:
                if a.check:
                    drift.append(f"{skill}/{rel}: out of date")
                else:
                    f.parent.mkdir(parents=True, exist_ok=True)
                    f.write_bytes(data)
        if not a.check:
            marker.write_text("\n".join(sorted(want)) + "\n", encoding="utf-8")
    extra = [p.name for p in SKILLS.iterdir() if p.is_dir() and p.name not in arts and (p / "SKILL.md").exists()]
    if extra:
        print(f"note: skills not listed in shared/data/pipeline.json were skipped: {extra}")
    if a.check:
        if drift:
            print("\n".join(drift))
            print("Run: python tools/sync_shared.py")
            sys.exit(1)
        print("skills/ is in sync with shared/")
    else:
        print(f"synced {len(arts)} skills")


if __name__ == "__main__":
    main()
