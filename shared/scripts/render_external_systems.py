#!/usr/bin/env python3
"""External-systems diagram per lifecycle phase: inputs enter from the left, outputs leave to the
right, controls come from the top, enabling systems support from below, context is dashed."""
import sysreq_lib as L


def ready(ws, args):
    miss = L.need(ws, "boundary", ("has external systems", lambda o: bool(o.get("external_systems"))),
                  ("has interfaces", lambda o: bool(o.get("interfaces"))))
    miss += L.need(ws, "lifecycle", ("has phases", lambda o: bool(o.get("phases"))))
    miss += L.need(ws, "concept-brief", ("has a system name", lambda o: bool(L.system_name(o))))
    return miss


def diagram(sysname, phase, bd):
    ext = L.by_id(bd["external_systems"])
    ifs = [i for i in bd["interfaces"] if i["phase_id"] == phase["id"]]
    left = [i for i in ifs if i["direction"] == "input"]
    right = [i for i in ifs if i["direction"] == "output"]
    top = [i for i in ifs if i["direction"] == "control"]
    ctl = [c for c in bd.get("controls", []) if phase["id"] in c["applies_to_phases"]]
    enabling = [x for x in bd["external_systems"] if x["kind"] == "enabling" and phase["id"] in x["phase_ids"]]
    rows = max(len(left), len(right), 2)
    tops = [(ext[i["external_id"]]["name"], i["item"]) for i in top] + [(c["name"], c["kind"]) for c in ctl]
    top_h = 170 if tops else 30
    W = 1000
    bx, bw = 360, 280
    by, bh = top_h, rows * 64 + 20
    H = by + bh + (110 if enabling else 30)
    o = [f'<svg viewBox="0 0 {W} {H}" style="max-width:{W}px" role="img" aria-label="External systems diagram">{L.ARROW_DEFS}']
    o.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="12" class="sys"/>')
    t, _ = L.svg_text(bx + bw / 2, by + bh / 2 - 6, sysname, 22, 17)
    o.append(t)
    t, _ = L.svg_text(bx + bw / 2, by + bh / 2 + 20, f"in {phase['domain_label']}", 28, 11, cls="mut")
    o.append(t)

    def ebox(x, y, x_ext, label, kind):
        dash = ' stroke-dasharray="5 4"' if kind == "context" else ""
        cls = "sys" if kind == "enabling" else "box"
        s = f'<rect x="{x}" y="{y-20}" width="170" height="40" rx="8" class="{cls}"{dash}/>'
        t, _ = L.svg_text(x + 85, y - 2, label, 22, 12)
        return s + t

    for k, i in enumerate(left):
        y = by + 40 + k * 64
        x = ext[i["external_id"]]
        o.append(ebox(20, y, 20, x["name"], x["kind"]))
        dash_attr = ' stroke-dasharray="5 4"' if x["kind"] == "context" else ""
        o.append(f'<line x1="190" y1="{y}" x2="{bx}" y2="{y}" class="line" marker-end="url(#ah)"{dash_attr}/>')
        t, _ = L.svg_text(275, y - 8, i["item"], 18, 11, cls="mut lbl")
        o.append(t)
    for k, i in enumerate(right):
        y = by + 40 + k * 64
        x = ext[i["external_id"]]
        o.append(ebox(810, y, 810, x["name"], x["kind"]))
        o.append(f'<line x1="{bx+bw}" y1="{y}" x2="810" y2="{y}" class="line" marker-end="url(#ah)"/>')
        t, _ = L.svg_text(725, y - 8, i["item"], 18, 11, cls="mut lbl")
        o.append(t)
    for k, (name, item) in enumerate(tops[:5]):
        x = bx + 30 + k * (bw - 60) / max(len(tops[:5]) - 1, 1) if len(tops[:5]) > 1 else bx + bw / 2
        o.append(f'<rect x="{x-62:.0f}" y="16" width="124" height="44" rx="8" class="box"/>')
        t, _ = L.svg_text(f"{x:.0f}", 34, name, 18, 11)
        o.append(t)
        o.append(f'<line x1="{x:.0f}" y1="60" x2="{x:.0f}" y2="{by}" class="line" marker-end="url(#ah)"/>')
        t, _ = L.svg_text(f"{x+6:.0f}", 120, item, 16, 10, anchor="start", cls="mut")
        o.append(t)
    for k, x in enumerate(enabling):
        xx = bx + 20 + k * (bw - 40) / max(len(enabling), 1)
        y = by + bh + 70
        o.append(f'<rect x="{xx:.0f}" y="{y-20}" width="{(bw-40)/max(len(enabling),1)-8:.0f}" height="40" rx="8" class="sys"/>')
        t, _ = L.svg_text(f"{xx + ((bw-40)/max(len(enabling),1)-8)/2:.0f}", y - 2, x["name"], 16, 11)
        o.append(t)
        o.append(f'<line x1="{xx + ((bw-40)/max(len(enabling),1)-8)/2:.0f}" y1="{y-20}" x2="{xx + ((bw-40)/max(len(enabling),1)-8)/2:.0f}" y2="{by+bh}" class="line" marker-end="url(#ah)"/>')
    o.append("</svg>")
    return "".join(o)


def render(ws, args):
    bd, lc, brief = L.load(ws, "boundary"), L.load(ws, "lifecycle"), L.load(ws, "concept-brief")
    sysname = L.system_name(brief)
    phases = [p for p in L.active_phases(lc) if any(i["phase_id"] == p["id"] for i in bd["interfaces"])]
    tabs = '<div class="tabs bar">' + "".join(
        f'<button class="{"on" if i == 0 else ""}" data-group="ph" data-tab="{L.e(p["id"])}">{L.e(p["domain_label"])}</button>' for i, p in enumerate(phases)) + "</div>"
    panels = ""
    for i, p in enumerate(phases):
        here = [x for x in bd["external_systems"] if p["id"] in x["phase_ids"]]
        table = "<table><tr><th>System</th><th>Kind</th><th>Role</th></tr>" + "".join(
            f"<tr><td>{L.e(x['name'])}{' <span class=tag>legacy</span>' if x.get('legacy') else ''}</td><td>{L.e(x['kind'])}</td><td>{L.e(x['role'])}</td></tr>" for x in here) + "</table>"
        panels += f'<div data-group="ph" data-panel="{L.e(p["id"])}" class="{"" if i == 0 else "hide"}"><div class="card">{diagram(sysname, p, bd)}</div><div class="card">{table}</div></div>'
    dec = "".join(f"<li>{L.e(d['decision'])} <span class='mut'>(decided by {L.e(d['decided_by'])}: {L.e(d['implication'])})</span></li>" for d in bd.get("boundary_decisions", []))
    legend = '<p class="mut">Inputs enter from the left, outputs leave to the right, controls (policies, regulations, constraints) enter from the top, enabling systems support from below. Dashed boxes are context: they affect the system but are not affected by it.</p>'
    body = f"{tabs}{legend}{panels}<h2>Boundary decisions</h2><ul>{dec or '<li class=mut>none recorded</li>'}</ul>"
    return L.page(f"External systems: {sysname}", f"One diagram per lifecycle phase · {L.meta_line(bd)}", body, L.tab_script())


if __name__ == "__main__":
    L.run_renderer("render_external_systems.py", "external-systems.html", ready, render, "Draw the external-systems diagram for each lifecycle phase.")
