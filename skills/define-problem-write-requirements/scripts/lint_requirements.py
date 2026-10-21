#!/usr/bin/env python3
"""Lint requirement statements against writing rules and report findings.

Rules: one 'shall' per requirement; 'will' states facts and 'should' states goals;
subject first, conditions last; no negative or compound predicates; no 'and/or';
no vague words; no solution leakage outside the technology category.

Usage:
  python scripts/lint_requirements.py --workspace ./sysreq [--json] [--out FILE] [--check-ready]
Exit codes: 0 no errors | 1 errors found | 3 requirements.json not ready
"""
import argparse
import re
import sys
from pathlib import Path

import sysreq_lib as L

_TERMS = L.data("vague-terms")
_GROUPS = {c["id"]: c["group"] for c in L.data("requirement-categories")["categories"]}
_VERBS = r"(?:provide|display|send|store|accept|receive|support|allow|notify|record|report|produce|deliver|stop|start|indicate|log|show|transmit)"


def lint_requirement(text, req=None):
    out = []

    def add(rule, severity, message):
        out.append({"rule": rule, "severity": severity, "message": message})

    t = " ".join(str(text).split())
    low = t.lower()
    shalls = len(re.findall(r"\bshall\b", low))
    category = (req or {}).get("category", "")
    if shalls == 0:
        add("modal", "error", "use 'shall' for a requirement ('will' states facts, 'should' states goals)")
    if shalls > 1:
        add("single-requirement", "warn", f"{shalls} uses of 'shall': split into one requirement per statement")
    if not re.match(r"^(the|each|every|all)\b", low):
        add("subject-first", "warn", "start with the system of interest as the subject ('The <system> shall ...')")
    if re.search(r"\bshall not\b", low):
        add("negative-predicate", "warn", "restate positively: say what the system shall do")
    if "and/or" in low:
        add("and-or", "error", "'and/or' gives the designer a choice: say 'and' or 'or'")
    if re.search(rf"\bshall\s+\w+[^.;]*?\band\s+(?:also\s+)?{_VERBS}\b", low):
        add("compound-predicate", "warn", "two actions joined by 'and': split so each can be traced and verified")
    if re.match(r"^if\b", low):
        add("condition-last", "warn", "put the condition at the end ('The system shall ... when ...')")
    for w in _TERMS["vague_verbs"]:
        if re.search(rf"\bshall\s+(?:also\s+)?{re.escape(w)}\b", low):
            add("vague-term", "warn", f"verb '{w}' is open to interpretation: say what the system does, with a measurable threshold")
    for w in _TERMS["vague_adjectives"]:
        if re.search(rf"\b{re.escape(w)}\b", low):
            add("vague-term", "warn", f"'{w}' is open to interpretation: use a measurable threshold")
    for w in _TERMS["placeholders"]:
        if re.search(rf"\b{re.escape(w)}\b", low):
            add("placeholder", "warn", f"'{w}': replace with a value or record an open issue")
    if _GROUPS.get(category) in ("io", "system_wide") and category != "technology" and re.search(r"\b(using|implemented (?:with|in|using)|based on|via)\b", low):
        add("solution-leakage", "warn", "may prescribe a solution: state the need, not the means (or use the technology category with a justification)")
    if len(t.split()) > 45:
        add("concise", "warn", "over 45 words: remove unnecessary information")
    return out


def _ready(ws):
    o = L.load(ws, "requirements")
    return [] if o and o.get("requirements") else ["requirements.json has no requirements yet"]


def _html(ws, rows, summary):
    body = [f'<div class="card"><b>{summary["errors"]}</b> errors · <b>{summary["warnings"]}</b> warnings across '
            f'<b>{summary["requirements"]}</b> requirements · <b>{summary["clean"]}</b> clean</div>',
            "<table><tr><th>ID</th><th>Statement</th><th>Findings</th></tr>"]
    for r in rows:
        f = "".join(f'<div class="{"bad" if x["severity"] == "error" else "warn"}">{L.e(x["rule"])}: {L.e(x["message"])}</div>' for x in r["findings"]) or '<span class="ok">clean</span>'
        body.append(f"<tr><td>{L.e(r['id'])}</td><td>{L.e(r['statement'])}</td><td>{f}</td></tr>")
    body.append("</table>")
    return L.page("Requirement lint report", "Writing-rule findings per requirement statement", "".join(body))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", default="./sysreq")
    ap.add_argument("--out", help="HTML report path (default <workspace>/views/lint-report.html)")
    ap.add_argument("--json", action="store_true", help="print findings as JSON and skip HTML")
    ap.add_argument("--check-ready", action="store_true")
    a = ap.parse_args()
    ws = Path(a.workspace)
    missing = _ready(ws)
    if a.check_ready:
        L.emit({"ready": not missing, "missing": missing})
        sys.exit(3 if missing else 0)
    if missing:
        L.emit({"ready": False, "missing": missing})
        sys.exit(3)
    reqs = L.load(ws, "requirements")["requirements"]
    rows = [{"id": q["id"], "statement": q["statement"], "findings": lint_requirement(q["statement"], q)} for q in reqs]
    errs = sum(1 for r in rows for f in r["findings"] if f["severity"] == "error")
    warns = sum(1 for r in rows for f in r["findings"] if f["severity"] == "warn")
    summary = {"requirements": len(rows), "errors": errs, "warnings": warns, "clean": sum(1 for r in rows if not r["findings"])}
    if a.json:
        L.emit({"summary": summary, "rows": rows})
    else:
        out = Path(a.out) if a.out else ws / "views" / "lint-report.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_html(ws, rows, summary), encoding="utf-8")
        L.emit({"ready": True, "out": str(out), "summary": summary})
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
