#!/usr/bin/env python3
"""Show what changed between two stamped versions of an artifact (JSON + HTML view).

Usage:
  python scripts/diff_versions.py --workspace ./sysreq --artifact requirements [--from 1] [--to 2] [--out FILE] [--check-ready]
Defaults: the two most recent stamped versions. Exit codes: 0 ok | 3 fewer than two versions | 2 usage
"""
import argparse
import re
import sys
from pathlib import Path

import sysreq_lib as L


def versions(ws, name):
    out = []
    for p in (Path(ws) / "history").glob(f"{name}.v*.json"):
        m = re.search(r"\.v(\d+)\.json$", p.name)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def flatten(obj, path=""):
    flat = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "meta" and not path:
                continue
            flat.update(flatten(v, f"{path}.{k}" if path else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            key = v["id"] if isinstance(v, dict) and "id" in v else (v["question_id"] if isinstance(v, dict) and "question_id" in v else i)
            flat.update(flatten(v, f"{path}[{key}]"))
    else:
        flat[path] = obj
    return flat


def diff(old, new):
    a, b = flatten(old), flatten(new)
    added = {k: b[k] for k in b if k not in a}
    removed = {k: a[k] for k in a if k not in b}
    changed = {k: (a[k], b[k]) for k in a if k in b and a[k] != b[k]}
    return added, removed, changed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", default="./sysreq")
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--from", dest="v_from", type=int)
    ap.add_argument("--to", dest="v_to", type=int)
    ap.add_argument("--out")
    ap.add_argument("--check-ready", action="store_true")
    a = ap.parse_args()
    ws = Path(a.workspace)
    vs = versions(ws, a.artifact)
    missing = [] if len(vs) >= 2 else [f"{a.artifact}: fewer than two stamped versions (found {vs})"]
    if a.check_ready:
        L.emit({"ready": not missing, "missing": missing, "versions": vs})
        sys.exit(3 if missing else 0)
    if missing:
        L.emit({"ready": False, "missing": missing})
        sys.exit(3)
    v_to = a.v_to or vs[-1]
    v_from = a.v_from or [v for v in vs if v < v_to][-1]
    old = L.read_json(ws / "history" / f"{a.artifact}.v{v_from}.json")
    new = L.read_json(ws / "history" / f"{a.artifact}.v{v_to}.json")
    added, removed, changed = diff(old, new)
    log = [c for c in L.meta_of(new).get("changelog", []) if v_from < c.get("version", 0) <= v_to]

    def short(v):
        s = str(v)
        return s if len(s) < 140 else s[:137] + "..."

    rows = "".join(f'<tr><td><code>{L.e(k)}</code></td><td class="ok">added</td><td>{L.e(short(v))}</td></tr>' for k, v in added.items())
    rows += "".join(f'<tr><td><code>{L.e(k)}</code></td><td class="bad">removed</td><td>{L.e(short(v))}</td></tr>' for k, v in removed.items())
    rows += "".join(f'<tr><td><code>{L.e(k)}</code></td><td class="warn">changed</td><td>{L.e(short(o))} &rarr; {L.e(short(n))}</td></tr>' for k, (o, n) in changed.items())
    notes = "".join(f"<li>v{c['version']} ({L.e(c['date'])}): {L.e(c['summary'])}</li>" for c in log)
    body = (f'<div class="card"><b>{len(added)}</b> added · <b>{len(removed)}</b> removed · <b>{len(changed)}</b> changed</div>'
            f"<h2>Changelog</h2><ul>{notes or '<li class=mut>none</li>'}</ul><h2>Differences</h2>"
            f"<table><tr><th>Field</th><th>Change</th><th>Detail</th></tr>{rows or '<tr><td colspan=3 class=mut>no differences</td></tr>'}</table>")
    out = Path(a.out) if a.out else ws / "views" / f"{a.artifact}-diff-v{v_from}-v{v_to}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(L.page(f"Revision diff: {a.artifact}", f"version {v_from} to version {v_to}", body), encoding="utf-8")
    L.emit({"ready": True, "out": str(out), "added": len(added), "removed": len(removed), "changed": len(changed)})


if __name__ == "__main__":
    main()
