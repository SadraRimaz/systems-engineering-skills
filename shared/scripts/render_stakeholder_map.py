#!/usr/bin/env python3
"""Stakeholder map: stakeholders grouped by class, filterable by payer and influence."""
import sysreq_lib as L


def ready(ws, args):
    return L.need(ws, "stakeholders", ("has at least one stakeholder", lambda o: bool(o.get("stakeholders"))))


def render(ws, args):
    o = L.load(ws, "stakeholders")
    classes = {c["id"]: c["name"] for c in L.data("stakeholder-classes")}
    groups = {}
    for s in o["stakeholders"]:
        groups.setdefault(s["class"], []).append(s)
    lc = L.load(ws, "lifecycle")
    phases = {p["id"]: p for p in (lc or {}).get("phases", [])}
    active_in = {}
    for p in phases.values():
        for sid in p.get("stakeholder_ids", []):
            active_in.setdefault(sid, []).append(p["domain_label"])
    body = ['<div class="bar"><button class="on" data-f="all">All</button><button data-f="pays">Pays</button>'
            '<button data-f="high">High influence</button></div>']
    for cid, items in groups.items():
        label = classes.get(cid, cid.replace("other:", "Other: "))
        body.append(f"<h2>{L.e(label)}</h2>")
        for s in items:
            tags = f'<span class="tag">influence: {L.e(s["influence"])}</span>'
            if s["pays"]:
                tags += '<span class="tag ok">pays</span>'
            if s.get("represented_by"):
                tags += f'<span class="tag">represented by {L.e(s["represented_by"])}</span>'
            phs = "".join(f'<span class="tag">{L.e(p)}</span>' for p in active_in.get(s["id"], []))
            objs = "".join(f"<li>{L.e(x)}</li>" for x in s["objectives"])
            cons = "".join(f"<li>{L.e(x)}</li>" for x in s.get("jurisdiction_constraints", []))
            body.append(
                f'<div class="card sh" data-pays="{str(s["pays"]).lower()}" data-inf="{L.e(s["influence"])}">'
                f'<b>{L.e(s["name"])}</b> <span class="mut">{L.e(s["id"])}</span><br>{tags}'
                f'<p>{L.e(s["needs_summary"])}</p><p class="mut">Interacts with the system: {L.e(s["interaction_with_system"])}</p>'
                f'<details><summary>Objectives, constraints, evidence</summary><ul>{objs}</ul>'
                f'{"<b>Constraints</b><ul>"+cons+"</ul>" if cons else ""}<p class="mut">Evidence: {L.e(s["evidence"])}</p></details>'
                f'{"<div>Active in: "+phs+"</div>" if phs else ""}</div>')
    none = o.get("class_coverage", [])
    if none:
        body.append("<h2>Classes with no stakeholder</h2><ul>" + "".join(
            f"<li>{L.e(classes.get(c['class'], c['class']))}: {L.e(c['reason'])}</li>" for c in none) + "</ul>")
    script = ("document.querySelectorAll('[data-f]').forEach(function(b){b.addEventListener('click',function(){"
              "document.querySelectorAll('[data-f]').forEach(function(x){x.classList.toggle('on',x===b)});var f=b.dataset.f;"
              "document.querySelectorAll('.sh').forEach(function(c){var show=f==='all'||(f==='pays'&&c.dataset.pays==='true')||(f==='high'&&c.dataset.inf==='high');"
              "c.classList.toggle('hide',!show)})})});")
    return L.page("Stakeholder map", f"{len(o['stakeholders'])} stakeholders in {len(groups)} classes · {L.meta_line(o)}", "".join(body), script)


if __name__ == "__main__":
    L.run_renderer("render_stakeholder_map.py", "stakeholder-map.html", ready, render, "Show stakeholders grouped by class.")
