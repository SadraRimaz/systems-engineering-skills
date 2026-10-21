#!/usr/bin/env python3
"""User stories and sequence diagrams mapped across lifecycle phases."""
import sysreq_lib as L


def ready(ws, args):
    miss = L.need(ws, "scenarios", ("has at least one scenario", lambda o: bool(o.get("scenarios"))))
    miss += L.need(ws, "lifecycle", ("has phases", lambda o: bool(o.get("phases"))))
    miss += L.need(ws, "concept-brief", ("has a system name", lambda o: bool(L.system_name(o))))
    return miss


def sequence(sysname, exchanges):
    actors = []
    for x in exchanges:
        for a in (x["from"], x["to"]):
            if a not in actors:
                actors.append(a)
    if sysname in actors:  # put the system last so it reads as the focus lifeline
        actors.remove(sysname)
        actors.append(sysname)
    cw, top, rh = 170, 56, 46
    W = max(len(actors) * cw, 560)
    H = top + 30 + len(exchanges) * rh + 20
    off = (W - len(actors) * cw) / 2
    xs = {a: off + cw / 2 + i * cw for i, a in enumerate(actors)}
    out = [f'<svg viewBox="0 0 {W} {H}" style="max-width:{W}px" role="img" aria-label="Sequence diagram">{L.ARROW_DEFS}']
    for a in actors:
        bold = a == sysname
        out.append(f'<rect x="{xs[a]-62}" y="8" width="124" height="38" rx="6" class="{"sys" if bold else "box"}"/>')
        t, _ = L.svg_text(xs[a], 24, a, 18, 12)
        out.append(t)
        out.append(f'<line x1="{xs[a]}" y1="46" x2="{xs[a]}" y2="{H-10}" class="line" stroke-width="{3 if bold else 1}" stroke-dasharray="{"" if bold else "4 4"}"/>')
    dashes = {"data": "", "energy": "8 3", "matter": "2 4"}
    for i, x in enumerate(exchanges):
        y = top + 30 + i * rh
        x1, x2 = xs[x["from"]], xs[x["to"]]
        sx, ex = (x1 + 4, x2 - 4) if x2 > x1 else (x1 - 4, x2 + 4)
        out.append(f'<line x1="{sx}" y1="{y}" x2="{ex}" y2="{y}" class="line" stroke-width="1.6" stroke-dasharray="{dashes[x["item_kind"]]}" marker-end="url(#ah)"/>')
        t, _ = L.svg_text((x1 + x2) / 2, y - 6, f"{i+1}. {x['item']}", 28, 11, cls="lbl")
        out.append(t)
    out.append("</svg>")
    return "".join(out)


def render(ws, args):
    sc, lc, brief = L.load(ws, "scenarios"), L.load(ws, "lifecycle"), L.load(ws, "concept-brief")
    st = L.load(ws, "stakeholders")
    stk = L.by_id((st or {}).get("stakeholders", []))
    sysname = L.system_name(brief)
    phases = [p for p in lc["phases"] if p["status"] == "active" and any(s["phase_id"] == p["id"] for s in sc["scenarios"])]
    tabs = '<div class="tabs bar">' + "".join(
        f'<button class="{"on" if i == 0 else ""}" data-group="ph" data-tab="{L.e(p["id"])}">{L.e(p["domain_label"])}</button>' for i, p in enumerate(phases)) + "</div>"
    panels = ""
    for i, p in enumerate(phases):
        cards = ""
        for s in [x for x in sc["scenarios"] if x["phase_id"] == p["id"]]:
            u = s["user_story"]
            who = "".join(f'<span class="tag">{L.e(stk.get(k, {}).get("name", k))}</span>' for k in s["stakeholder_ids"])
            pre = "".join(f"<li>{L.e(x)}</li>" for x in s.get("preconditions", []))
            env = "".join(f"<li>{L.e(x)}</li>" for x in s.get("environment_conditions", []))
            var = "".join(f"<li>{L.e(x)}</li>" for x in s.get("variations", []))
            cards += (
                f'<div class="card scn" data-kind="{L.e(s["kind"])}"><b>{L.e(s["title"])}</b> <span class="mut">{L.e(s["id"])}</span> '
                f'<span class="tag">{L.e(s["kind"])}</span> {who}'
                f'<p><i>As a {L.e(u["as_a"])}, I want {L.e(u["i_want"])}, so that {L.e(u["so_that"])}.</i></p>'
                f'<p>Goal: {L.e(s["goal"])}</p>{sequence(sysname, s["exchanges"])}'
                f'{"<details><summary>Preconditions</summary><ul>"+pre+"</ul></details>" if pre else ""}'
                f'{"<details><summary>Environment and failure conditions</summary><ul>"+env+"</ul></details>" if env else ""}'
                f'{"<details><summary>Variations</summary><ul>"+var+"</ul></details>" if var else ""}</div>')
        panels += f'<div data-group="ph" data-panel="{L.e(p["id"])}" class="{"" if i == 0 else "hide"}"><p class="mut">{L.e(p["description"])}</p>{cards}</div>'
    msn = "".join(f"<li><b>{L.e(m['id'])}</b> {L.e(m['statement'])} <span class='mut'>(measure: {L.e(m['measure'])})</span></li>" for m in sc.get("mission_requirements", []))
    kinds = sorted({s["kind"] for s in sc["scenarios"]})
    matrix = "<table><tr><th>Phase</th>" + "".join(f"<th>{L.e(k)}</th>" for k in kinds) + "</tr>"
    for p in phases:
        matrix += f"<tr><td>{L.e(p['domain_label'])}</td>" + "".join(
            f"<td>{sum(1 for s in sc['scenarios'] if s['phase_id'] == p['id'] and s['kind'] == k) or '<span class=mut>–</span>'}</td>" for k in kinds) + "</tr>"
    matrix += "</table>"
    legend = '<p class="mut">Arrows: solid = data, dashed = energy, dotted = matter. Time runs downward; order is what matters, not spacing. The system is the bold lifeline.</p>'
    body = (f'<h2>Mission requirements</h2><ul>{msn or "<li class=mut>none recorded</li>"}</ul>'
            f'<h2>Coverage across phases</h2><div class="card" style="overflow-x:auto">{matrix}</div>'
            f"<h2>Scenarios by phase</h2>{tabs}{legend}{panels}")
    return L.page(f"Operational scenarios: {sysname}", f"{len(sc['scenarios'])} scenarios · {L.meta_line(sc)}", body, L.tab_script())


if __name__ == "__main__":
    L.run_renderer("render_scenarios.py", "scenarios.html", ready, render, "Show user stories and sequence diagrams across lifecycle phases.")
