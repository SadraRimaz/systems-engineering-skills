#!/usr/bin/env python3
"""Context map: the system of interest, its external and enabling systems, and the
wider context. Draft from the concept brief's boundary hypothesis; refined from the
boundary model when boundary.json exists."""
import math

import sysreq_lib as L


def ready(ws, args):
    b = L.load(ws, "concept-brief")
    if not b:
        return ["concept-brief.json does not exist"]
    miss = []
    if not b.get("system_of_interest", {}).get("name"):
        miss.append("concept-brief: system_of_interest.name is empty")
    bd = L.load(ws, "boundary")
    if not (bd and bd.get("external_systems")) and not b.get("boundary_hypothesis", {}).get("outside"):
        miss.append("concept-brief: boundary_hypothesis.outside has no entries (and no boundary.json yet)")
    return miss


def collect(ws):
    brief = L.load(ws, "concept-brief")
    bd = L.load(ws, "boundary")
    nodes = []
    if bd and bd.get("external_systems"):
        for x in bd["external_systems"]:
            ifs = [i for i in bd.get("interfaces", []) if i["external_id"] == x["id"]]
            nodes.append({
                "name": x["name"], "kind": x["kind"], "label": x["role"],
                "in": any(i["direction"] in ("input", "control") for i in ifs),
                "out": any(i["direction"] == "output" for i in ifs),
                "legacy": x.get("legacy", False),
            })
        source = "boundary model"
    else:
        for x in brief["boundary_hypothesis"]["outside"]:
            nodes.append({"name": x["name"], "kind": "external", "label": x["relation"], "in": True, "out": True, "legacy": False})
        source = "boundary hypothesis (draft)"
    return brief, nodes, source


def render(ws, args):
    brief, nodes, source = collect(ws)
    W, H, cx, cy = 980, 640, 490, 320
    parts = [f'<svg viewBox="0 0 {W} {H}" style="max-width:{W}px" role="img" aria-label="Context map">{L.ARROW_DEFS}',
             f'<rect x="10" y="10" width="{W-20}" height="{H-20}" rx="24" class="box" stroke-dasharray="6 5"/>',
             f'<text x="30" y="36" font-size="13" class="mut">Context</text>']
    n = max(len(nodes), 1)
    rx, ry = 360, 210
    for i, nd in enumerate(nodes):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        x, y = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
        dash = ' stroke-dasharray="5 4"' if nd["kind"] == "context" else ""
        cls = "sys" if nd["kind"] == "enabling" else "box"
        x1, y1 = cx + 120 * math.cos(ang), cy + 70 * math.sin(ang)
        x2, y2 = x - 62 * math.cos(ang), y - 24 * math.sin(ang)
        marks = ""
        if nd["kind"] == "context":
            marks = 'marker-end="url(#ah)"'
            ax1, ay1, ax2, ay2 = x2, y2, x1, y1
        else:
            ax1, ay1, ax2, ay2 = x1, y1, x2, y2
            marks = ('marker-end="url(#ah)" ' if nd["out"] else "") + ('marker-start="url(#ah)"' if nd["in"] else "")
        parts.append(f'<line x1="{ax1:.0f}" y1="{ay1:.0f}" x2="{ax2:.0f}" y2="{ay2:.0f}" class="line"{dash} {marks}/>')
        parts.append(f'<rect x="{x-70:.0f}" y="{y-30:.0f}" width="140" height="60" rx="8" class="{cls}"{dash}/>')
        t, _ = L.svg_text(f"{x:.0f}", f"{y-12:.0f}", nd["name"], 18, 13)
        parts.append(t)
        t, _ = L.svg_text(f"{x:.0f}", f"{y+22:.0f}", f"{nd['kind']}{' · legacy' if nd['legacy'] else ''}", 24, 11, cls="mut")
        parts.append(t)
        if nd["label"]:
            lx, ly = (x1 + x2) / 2, (y1 + y2) / 2
            t, _ = L.svg_text(f"{lx:.0f}", f"{ly-4:.0f}", nd["label"], 26, 11, cls="mut lbl")
            parts.append(t)
    parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="130" ry="76" class="sys"/>')
    t, _ = L.svg_text(cx, cy - 8, L.system_name(brief), 22, 16)
    parts.append(t)
    t, _ = L.svg_text(cx, cy + 22, "system of interest", 22, 11, cls="mut")
    parts.append(t)
    parts.append("</svg>")
    unknown = brief["boundary_hypothesis"].get("unknown", [])
    inside = brief["boundary_hypothesis"].get("inside", [])
    extra = ""
    if inside:
        extra += "<h2>Assumed inside the boundary</h2><div>" + "".join(f'<span class="tag">{L.e(i)}</span>' for i in inside) + "</div>"
    if unknown:
        extra += "<h2>Boundary still unknown</h2><ul>" + "".join(f"<li>{L.e(u['item'])} <span class='mut'>(owner: {L.e(u['owner'])})</span></li>" for u in unknown) + "</ul>"
    legend = ('<p class="mut">Solid box: external system · filled: enabling system · dashed: context (affects the system, is not affected by it). '
              'Arrowheads show the direction of inputs and outputs.</p>')
    return L.page(f"Context map: {L.system_name(brief)}", f"Source: {source}", f'<div class="card">{"".join(parts)}</div>{legend}{extra}')


if __name__ == "__main__":
    L.run_renderer("render_context_map.py", "context-map.html", ready, render, "Draw the system in its context.")
