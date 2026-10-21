#!/usr/bin/env python3
"""Draft the boundary model from the scenarios: every actor that exchanges something with the
system becomes an external system, and every exchange becomes an interface. Safe to re-run:
existing entries are kept and only missing ones are added.

Usage: python scripts/derive_boundary.py --workspace ./sysreq [--write]
Without --write the draft is printed to stdout and nothing is saved.
Draft values (kind 'external', role 'TO CONFIRM') must be confirmed with the user.
Exit codes: 0 ok | 2 missing input
"""
import argparse
from pathlib import Path

import sysreq_lib as L


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", default="./sysreq")
    ap.add_argument("--write", action="store_true", help="save to boundary.json (merging with what exists)")
    a = ap.parse_args()
    ws = Path(a.workspace)
    brief = L.load(ws, "concept-brief", required=True)
    sc = L.load(ws, "scenarios", required=True)
    sysname = L.system_name(brief).lower()
    bd = L.load(ws, "boundary") or {"meta": {"artifact": "boundary", "version": 0, "status": "draft", "built_from": {}, "changelog": []},
                                    "external_systems": [], "interfaces": [], "controls": [], "boundary_decisions": [], "open_issues": [], "decisions_log": []}
    ext = {x["name"].lower(): x for x in bd["external_systems"]}
    n_ext = len(bd["external_systems"])
    n_if = len(bd["interfaces"])
    have = {(i["phase_id"], i["external_id"], i["direction"], i["item"].lower()) for i in bd["interfaces"]}
    for s in sc["scenarios"]:
        for x in s["exchanges"]:
            out = x["from"].lower() == sysname
            actor = x["to"] if out else x["from"]
            if actor.lower() == sysname:
                continue
            e = ext.get(actor.lower())
            if e is None:
                e = {"id": f"EXT-{len(bd['external_systems']) + 1:03d}", "name": actor, "kind": "external", "legacy": False, "phase_ids": [], "role": "TO CONFIRM"}
                bd["external_systems"].append(e)
                ext[actor.lower()] = e
            if s["phase_id"] not in e["phase_ids"]:
                e["phase_ids"].append(s["phase_id"])
            key = (s["phase_id"], e["id"], "output" if out else "input", x["item"].lower())
            if key not in have:
                have.add(key)
                bd["interfaces"].append({"id": f"IF-{len(bd['interfaces']) + 1:03d}", "phase_id": s["phase_id"], "external_id": e["id"],
                                         "direction": key[2], "item": x["item"], "item_kind": x["item_kind"]})
    if a.write:
        L.write_json(L.artifact_path(ws, "boundary"), bd)
    L.emit({"written": a.write, "added_external_systems": len(bd["external_systems"]) - n_ext,
            "added_interfaces": len(bd["interfaces"]) - n_if, "draft": bd})


if __name__ == "__main__":
    main()
