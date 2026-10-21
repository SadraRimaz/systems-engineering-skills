#!/usr/bin/env python3
"""Draft requirement skeletons so nothing is forgotten: one input/output/interface requirement per
interface and one performance requirement per objective measure that has none yet. Safe to re-run:
only missing ones are added. Every drafted item is flagged tbd with a 'TO CONFIRM' rationale and must be
rewritten with the user.

Usage: python scripts/draft_requirements.py --workspace ./sysreq [--write]
Without --write the draft is printed and nothing is saved. Exit codes: 0 ok | 2 missing input
"""
import argparse
from pathlib import Path

import sysreq_lib as L


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", default="./sysreq")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    ws = Path(a.workspace)
    brief = L.load(ws, "concept-brief", required=True)
    lc = L.load(ws, "lifecycle", required=True)
    sc = L.load(ws, "scenarios", required=True)
    bd = L.load(ws, "boundary", required=True)
    ob = L.load(ws, "objectives", required=True)
    sysname = L.system_name(brief)
    rq = L.load(ws, "requirements") or {"meta": {"artifact": "requirements", "version": 0, "status": "draft", "built_from": {}, "changelog": []},
                                        "requirements": [], "partition_notes": [], "open_issues": [], "decisions_log": []}
    ext = L.by_id(bd["external_systems"])
    covered_if = {i for q in rq["requirements"] for i in q["sources"].get("interface_ids", [])}
    covered_obj = {i for q in rq["requirements"] for i in q["sources"].get("objective_ids", [])}
    added = []

    def new(**kw):
        q = {"id": f"REQ-{len(rq['requirements']) + 1:03d}", "kind": "constraint", "rationale": "TO CONFIRM: why do the stakeholders need this?", "status": "proposed", "tbd": True}
        q.update(kw)
        rq["requirements"].append(q)
        added.append(q["id"])

    for i in bd["interfaces"]:
        if i["id"] in covered_if:
            continue
        x = ext[i["external_id"]]
        scs = [s["id"] for s in sc["scenarios"] if s["phase_id"] == i["phase_id"] and any(e["item"].lower() == i["item"].lower() for e in s["exchanges"])]
        cat = {"input": "input", "output": "output", "control": "external_interface"}[i["direction"]]
        verb, prep = ("accept", "from") if i["direction"] != "output" else ("provide", "to")
        new(statement=f"The {sysname} shall {verb} {i['item'].lower()} {prep} {x['name'].lower()}.", phase_id=i["phase_id"], category=cat,
            sources={"scenario_ids": scs[:1], "interface_ids": [i["id"]]}, qualification_method="demonstration")
    hier = L.by_id(ob["hierarchies"])
    first_phase = (L.active_phases(lc) or [{"id": ""}])[0]["id"]
    for n in ob["nodes"]:
        if n["level"] != "measure" or n["id"] in covered_obj:
            continue
        ph = hier[n["hierarchy_id"]].get("scope_phase_id") or first_phase
        unit = n.get("unit", "")
        new(statement=f"The {sysname} shall achieve {n['name'].lower()} of {n['threshold']:g} {unit} or better, with a design goal of {n['goal']:g} {unit}.".replace("  ", " "),
            phase_id=ph, category="output", kind="performance", threshold=n["threshold"], goal=n["goal"], unit=unit,
            sources={"scenario_ids": n.get("scenario_ids", [])[:1], "objective_ids": [n["id"]], "stakeholder_ids": n.get("stakeholder_ids", [])[:1]},
            qualification_method="instrumented_test")
    if a.write:
        L.write_json(L.artifact_path(ws, "requirements"), rq)
    L.emit({"written": a.write, "added": added})


if __name__ == "__main__":
    main()
