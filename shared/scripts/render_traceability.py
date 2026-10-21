#!/usr/bin/env python3
"""Traceability and qualification matrix: every requirement against its sources and its qualification
method, plus coverage gaps (scenarios, interfaces and objectives that no requirement traces to)."""
import sysreq_lib as L

METHODS = [("demonstration", "Demonstration"), ("analysis_simulation", "Analysis / simulation"), ("inspection", "Inspection"), ("instrumented_test", "Instrumented test")]


def ready(ws, args):
    miss = L.need(ws, "requirements", ("has requirements", lambda o: bool(o.get("requirements"))))
    return miss


def chips(ids):
    return "".join(f'<span class="tag">{L.e(i)}</span>' for i in ids) or '<span class="mut">–</span>'


def render(ws, args):
    o = L.load(ws, "requirements")
    cats = {c["id"]: c["name"] for c in L.data("requirement-categories")["categories"]}
    lc = L.load(ws, "lifecycle")
    phases = {p["id"]: p["domain_label"] for p in (lc or {}).get("phases", [])}
    phases["ALL"] = "All phases"
    rows, used = "", {"scenario_ids": set(), "interface_ids": set(), "objective_ids": set(), "stakeholder_ids": set()}
    for q in o["requirements"]:
        s = q["sources"]
        for k in used:
            used[k].update(s.get(k, []))
        method = q.get("qualification_method")
        cells = "".join(f'<td style="text-align:center">{"●" if method == m else ""}</td>' for m, _ in METHODS)
        rows += (f'<tr data-phase="{L.e(q["phase_id"])}" data-cat="{L.e(q["category"])}"><td><b>{L.e(q["id"])}</b></td>'
                 f'<td>{L.e(q["statement"])}</td><td>{L.e(phases.get(q["phase_id"], q["phase_id"]))}</td><td>{L.e(cats.get(q["category"], q["category"]))}</td>'
                 f'<td>{chips(s.get("stakeholder_ids", []))}</td><td>{chips(s.get("scenario_ids", []) + s.get("mission_ids", []))}</td>'
                 f'<td>{chips(s.get("interface_ids", []))}</td><td>{chips(s.get("objective_ids", []))}</td>{cells}</tr>')
    head = "".join(f"<th>{L.e(n)}</th>" for _, n in METHODS)
    opts_p = '<option value="">All phases</option>' + "".join(f'<option value="{L.e(k)}">{L.e(v)}</option>' for k, v in phases.items() if any(q["phase_id"] == k for q in o["requirements"]))
    opts_c = '<option value="">All categories</option>' + "".join(f'<option value="{L.e(k)}">{L.e(v)}</option>' for k, v in cats.items() if any(q["category"] == k for q in o["requirements"]))
    gaps = ""
    sc, bd, ob = L.load(ws, "scenarios"), L.load(ws, "boundary"), L.load(ws, "objectives")
    if sc:
        miss = [s for s in sc["scenarios"] if s["id"] not in used["scenario_ids"]]
        gaps += f"<h3>Scenarios not referenced by any requirement ({len(miss)})</h3><div>{chips([s['id'] + ' ' + s['title'] for s in miss])}</div>"
    if bd:
        miss = [i for i in bd["interfaces"] if i["id"] not in used["interface_ids"]]
        gaps += f"<h3>Interfaces without a requirement ({len(miss)})</h3><div>{chips([i['id'] + ' ' + i['item'] for i in miss])}</div>"
    if ob:
        miss = [n for n in ob["nodes"] if n["level"] == "measure" and n["id"] not in used["objective_ids"]]
        gaps += f"<h3>Objective measures without a requirement ({len(miss)})</h3><div>{chips([n['id'] + ' ' + n['name'] for n in miss])}</div>"
    script = ("function f(){var p=document.getElementById('fp').value,c=document.getElementById('fc').value;"
              "document.querySelectorAll('tbody tr').forEach(function(r){r.classList.toggle('hide',(p&&r.dataset.phase!==p)||(c&&r.dataset.cat!==c))})}"
              "document.getElementById('fp').onchange=f;document.getElementById('fc').onchange=f;")
    body = (f'<div class="bar"><select id="fp">{opts_p}</select><select id="fc">{opts_c}</select></div>'
            f'<div class="card" style="overflow-x:auto"><table><thead><tr><th>ID</th><th>Requirement</th><th>Phase</th><th>Category</th><th>Stakeholders</th><th>Scenarios / missions</th><th>Interfaces</th><th>Objectives</th>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
            f"<h2>Coverage gaps</h2>{gaps or '<p class=mut>No upstream artifacts to compare against.</p>'}")
    return L.page("Traceability and qualification matrix", f"{len(o['requirements'])} requirements · {L.meta_line(o)}", body, script)


if __name__ == "__main__":
    L.run_renderer("render_traceability.py", "traceability.html", ready, render, "Show requirement traceability and qualification methods.")
