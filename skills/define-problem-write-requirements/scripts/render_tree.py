#!/usr/bin/env python3
"""Generic hierarchy renderer with three modes:
  objectives  objectives hierarchy with weights, thresholds, goals and value curves
  partition   requirements partitioned by phase, group and category
  levels      requirement levels (mission, stakeholder, derived)"""
import sysreq_lib as L

NODE_W, NODE_H, COL, ROW = 240, 84, 300, 100


def ready(ws, args):
    if args.mode == "objectives":
        return L.need(ws, "objectives", ("has nodes", lambda o: bool(o.get("nodes"))))
    return L.need(ws, "requirements", ("has requirements", lambda o: bool(o.get("requirements"))))


def curve_svg(x, y, w, h, shape, points, thr, goal):
    pts = []
    if shape == "piecewise" and points:
        lo, hi = min(thr, goal), max(thr, goal)
        span = (hi - lo) or 1
        pts = [((px - lo) / span, pv) for px, pv in points]
        if goal < thr:
            pts = [(1 - a, b) for a, b in pts]
        pts.sort()
    else:
        for i in range(0, 21):
            t = i / 20
            v = {"linear": t, "concave": 1 - (1 - t) ** 2, "convex": t ** 2, "s_curve": t * t * (3 - 2 * t)}.get(shape, t)
            pts.append((t, v))
    path = " ".join(f"{x + a * w:.1f},{y + h - b * h:.1f}" for a, b in pts)
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="var(--line)"/>'
            f'<polyline points="{path}" fill="none" stroke="var(--acc)" stroke-width="1.6"/>')


def layout(node, depth, state):
    kids = node.get("children", [])
    if not kids:
        node["_y"] = state["y"]
        state["y"] += ROW
    else:
        for k in kids:
            layout(k, depth + 1, state)
        node["_y"] = (kids[0]["_y"] + kids[-1]["_y"]) / 2
    node["_d"] = depth
    state["maxd"] = max(state["maxd"], depth)


def draw(node, out, with_curves):
    x, y = 20 + node["_d"] * COL, node["_y"] + 10
    for k in node.get("children", []):
        kx, ky = 20 + k["_d"] * COL, k["_y"] + 10 + NODE_H / 2
        out.append(f'<path d="M{x+NODE_W} {y+NODE_H/2} C{x+NODE_W+30} {y+NODE_H/2} {kx-30} {ky} {kx} {ky}" class="line"/>')
        draw(k, out, with_curves)
    cls = node.get("cls", "box")
    out.append(f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" rx="8" class="{cls}"/>')
    c = node.get("curve") if with_curves else None
    t, n = L.svg_text(x + 10, y + 20, node["label"], 21 if c else 30, 12, anchor="start")
    out.append(t)
    if node.get("sub"):
        t, _ = L.svg_text(x + 10, y + 26 + 15 * n, node["sub"], 24 if c else 34, 11, anchor="start", cls="mut")
        out.append(t)
    if c:
        out.append(curve_svg(x + NODE_W - 62, y + 10, 52, 34, *c))


def tree_svg(root, with_curves=False):
    state = {"y": 0, "maxd": 0}
    layout(root, 0, state)
    w = 40 + (state["maxd"] + 1) * COL
    out = [f'<svg viewBox="0 0 {w} {state["y"]+30}" style="max-width:{w}px" role="img">']
    draw(root, out, with_curves)
    out.append("</svg>")
    return "".join(out)


def objectives_view(ws):
    o = L.load(ws, "objectives")
    nodes = o["nodes"]
    kids = {}
    for n in nodes:
        kids.setdefault(n["parent_id"], []).append(n)

    def build(n):
        sub = []
        if n.get("weight") is not None:
            sub.append(f"weight {n['weight']:g}")
        if n["level"] == "measure" and n.get("threshold") is not None:
            sub.append(f"{n['threshold']:g} → {n['goal']:g} {n.get('unit','')}".strip())
        if n.get("conditions"):
            sub.append(", ".join(n["conditions"]))
        d = {"label": n["name"], "sub": " · ".join(sub), "children": [build(k) for k in kids.get(n["id"], [])],
             "cls": "sys" if n["level"] == "fundamental" else "box"}
        if n["level"] == "measure" and n.get("value_curve") and n.get("threshold") is not None:
            vc = n["value_curve"]
            d["curve"] = (vc["shape"], vc.get("points", []), n["threshold"], n["goal"])
        return d

    body = ""
    for h in o["hierarchies"]:
        roots = [n for n in kids.get(None, []) if n["hierarchy_id"] == h["id"]]
        if roots:
            body += f'<h2>{L.e(h["name"])}</h2><div class="card" style="overflow-x:auto">{tree_svg(build(roots[0]), True)}</div>'
    note = ('<p class="mut">Each leaf shows threshold → goal (the swing from minimally acceptable to the level beyond which stakeholders see no added value) '
            'and a value curve over that range. Sibling weights express relative value of the swing and sum to 1.</p>')
    return L.page("Objectives hierarchy", f"{len(nodes)} objectives · {L.meta_line(o)}", note + body)


def partition_view(ws):
    o = L.load(ws, "requirements")
    cats = {c["id"]: c for c in L.data("requirement-categories")["categories"]}
    groups = {g["id"]: g["name"] for g in L.data("requirement-categories")["groups"]}
    lc = L.load(ws, "lifecycle")
    phases = {p["id"]: p["domain_label"] for p in L.active_phases(lc)} if lc else {}
    phases["ALL"] = "All phases"
    root = {"label": "Stakeholder requirements", "sub": f"{len(o['requirements'])} requirements", "cls": "sys", "children": []}
    for pid, plabel in phases.items():
        pq = [q for q in o["requirements"] if q["phase_id"] == pid]
        if not pq:
            continue
        pn = {"label": plabel, "sub": f"{len(pq)} requirements", "children": []}
        for gid, gname in groups.items():
            gq = [q for q in pq if cats[q["category"]]["group"] == gid]
            if not gq:
                continue
            gn = {"label": gname, "sub": f"{len(gq)}", "children": []}
            for cid in cats:
                cq = [q for q in gq if q["category"] == cid]
                if cq:
                    gn["children"].append({"label": cats[cid]["name"], "sub": ", ".join(q["id"] for q in cq[:4]) + (f" +{len(cq) - 4} more" if len(cq) > 4 else ""), "children": []})
            pn["children"].append(gn)
        root["children"].append(pn)
    notes = "".join(f"<li>{L.e(phases.get(n['phase_id'], n['phase_id']))} / {L.e(groups.get(n['group'], n['group']))}: n/a, {L.e(n['reason'])}</li>" for n in o.get("partition_notes", []))
    body = (f'<div class="card" style="overflow-x:auto">{tree_svg(root)}</div>'
            f"<h2>Groups marked not applicable</h2><ul>{notes or '<li class=mut>none</li>'}</ul>")
    return L.page("Requirements partition", f"By lifecycle phase, then requirement group and category · {L.meta_line(o)}", body)


def levels_view(ws):
    o = L.load(ws, "requirements")
    sc = L.load(ws, "scenarios") or {}
    n_m, n_s = len(sc.get("mission_requirements", [])), len(o["requirements"])
    rows = [("Mission requirements", f"{n_m} · objectives of stakeholders in the wider system", 0.34, "sys"),
            ("Stakeholder requirements", f"{n_s} · written in stakeholders' language, design-independent", 0.62, "sys"),
            ("System requirements", "derived later, in engineering terms", 0.86, "box"),
            ("Component and item requirements", "derived later during architecture and design", 1.0, "box")]
    out = ['<svg viewBox="0 0 700 330" role="img">']
    for i, (a, b, f, cls) in enumerate(rows):
        w = 640 * f
        dash = ' stroke-dasharray="5 4"' if cls == "box" else ""
        out.append(f'<rect x="{350-w/2:.0f}" y="{10+i*78}" width="{w:.0f}" height="68" rx="10" class="{cls}"{dash}/>')
        t, _ = L.svg_text(350, 38 + i * 78, a, 40, 14)
        out.append(t)
        t, _ = L.svg_text(350, 58 + i * 78, b, 70, 11, cls="mut")
        out.append(t)
    out.append("</svg>")
    note = '<p class="mut">This phase produces the top two levels. Derived levels (dashed) are produced by later stages.</p>'
    return L.page("Requirement levels", L.meta_line(o), f'<div class="card">{"".join(out)}</div>{note}')


def add_args(ap):
    ap.add_argument("--mode", required=True, choices=["objectives", "partition", "levels"], help="which hierarchy to draw")


def render(ws, args):
    return {"objectives": objectives_view, "partition": partition_view, "levels": levels_view}[args.mode](ws)


if __name__ == "__main__":
    L.run_renderer("render_tree.py", "tree-{mode}.html", ready, render, "Draw a hierarchy (objectives, requirements partition, or requirement levels).", add_args)
