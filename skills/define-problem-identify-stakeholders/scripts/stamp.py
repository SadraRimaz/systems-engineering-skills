#!/usr/bin/env python3
"""Finish an artifact: validate, bump its version, record upstream versions, snapshot it.

Run only after the user has confirmed the read-back of the artifact.

Usage:
  python scripts/stamp.py --workspace ./sysreq --artifact stakeholders --summary "Initial register" --approve

--approve marks the artifact approved (the user confirmed it). Without it the artifact stays draft.
Exit codes: 0 stamped | 1 validation errors (nothing written) | 2 usage
Output (stdout): JSON with the new version, status, downstream artifacts now stale, and the next skill.
"""
import argparse
import copy
import sys
from pathlib import Path

import sysreq_lib as L
from validate import validate_artifact


def strip_meta(o):
    return {k: v for k, v in o.items() if k != "meta"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", default="./sysreq", help="project workspace folder (default ./sysreq)")
    ap.add_argument("--artifact", required=True, help="artifact name, e.g. stakeholders")
    ap.add_argument("--summary", required=True, help="one-line change summary for the changelog")
    ap.add_argument("--approve", action="store_true", help="mark approved (user confirmed)")
    a = ap.parse_args()
    ws = Path(a.workspace)
    name = a.artifact
    if name not in L.artifact_names():
        L.fail(f"unknown artifact '{name}'. Known: {', '.join(L.artifact_names())}", 2)
    obj = L.load(ws, name, required=True)
    hist = ws / "history"
    cur = int(L.meta_of(obj).get("version", 0) or 0)
    snap = hist / f"{name}.v{cur}.json"
    if cur >= 1 and snap.exists():
        prev = L.read_json(snap)
        if strip_meta(prev) == strip_meta(obj):
            if a.approve and L.meta_of(obj).get("status") != "approved":
                obj["meta"]["status"] = "approved"
                obj["meta"].setdefault("changelog", []).append({"version": cur, "date": L.today(), "summary": f"Approved without content change. {a.summary}"})
                L.write_json(L.artifact_path(ws, name), obj)
                L.write_json(snap, obj)
                L.emit({"artifact": name, "version": cur, "status": "approved", "note": "no content change; status set to approved"})
                return
            L.emit({"artifact": name, "version": cur, "note": "no changes since last stamp; nothing written"})
            return
    new = copy.deepcopy(obj)
    m = new.setdefault("meta", {})
    m["artifact"] = name
    m["version"] = cur + 1
    m["status"] = "approved" if a.approve else "draft"
    m["built_from"] = {up: L.version_of(L.load(ws, up)) for up in L.upstream_of(name) if L.load(ws, up) is not None}
    m.setdefault("changelog", []).append({"version": m["version"], "date": L.today(), "summary": a.summary})
    L.write_json(L.artifact_path(ws, name), new)  # validators read from the workspace
    rep = validate_artifact(ws, name)
    if rep.errors:
        L.write_json(L.artifact_path(ws, name), obj)  # restore the unstamped draft
        L.emit({"artifact": name, "stamped": False, "errors": rep.errors, "warnings": rep.warnings})
        sys.stderr.write("error: validation failed; nothing was stamped. Fix the errors and run again.\n")
        sys.exit(1)
    L.write_json(hist / f"{name}.v{m['version']}.json", new)
    stale = [s for s in L.stale_report(ws) if s["upstream"] == name]
    nxt = L.next_skill(name)
    L.emit({
        "artifact": name, "stamped": True, "version": m["version"], "status": m["status"],
        "warnings": rep.warnings,
        "downstream_now_stale": [s["artifact"] for s in stale],
        "next_skill": nxt["skill"] if nxt else None,
        "next_title": nxt["title"] if nxt else None,
    })


if __name__ == "__main__":
    main()
