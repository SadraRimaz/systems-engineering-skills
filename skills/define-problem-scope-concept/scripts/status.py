#!/usr/bin/env python3
"""Print the pipeline status of a workspace as JSON: per artifact version, approval,
stale flags, open issues, validation result, and the next skill to run.

Usage: python scripts/status.py --workspace ./sysreq
Exit codes: 0 ok | 2 workspace folder not found
"""
import argparse
import sys
from pathlib import Path

import sysreq_lib as L
from validate import validate_artifact


def summarize(ws):
    ws = Path(ws)
    stale = L.stale_report(ws)
    rows, nxt = [], None
    for s in L.ordered_skills():
        name = s["artifact"]
        obj = L.load(ws, name)
        row = {"skill": s["skill"], "title": s["title"], "artifact": name, "present": obj is not None}
        if obj is not None:
            m = L.meta_of(obj)
            rep = validate_artifact(ws, name)
            issues = [i for i in obj.get("open_issues", []) if i.get("status") == "open"]
            row.update({
                "version": int(m.get("version", 0) or 0), "status": m.get("status", "draft"),
                "stale": [x["upstream"] for x in stale if x["artifact"] == name],
                "open_issues": len(issues), "validation_errors": len(rep.errors), "validation_warnings": len(rep.warnings),
                "built_from": m.get("built_from", {}),
            })
            done = row["version"] >= 1 and row["status"] == "approved" and not row["stale"]
        else:
            done = False
        row["done"] = done
        if not done and nxt is None:
            nxt = s["skill"]
        rows.append(row)
    return {"artifacts": rows, "next_skill": nxt, "complete": nxt is None}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", default="./sysreq", help="project workspace folder (default ./sysreq)")
    a = ap.parse_args()
    if not Path(a.workspace).is_dir():
        L.fail(f"workspace folder '{a.workspace}' not found. Run the scope-concept skill first.", 2)
    L.emit(summarize(a.workspace))


if __name__ == "__main__":
    main()
