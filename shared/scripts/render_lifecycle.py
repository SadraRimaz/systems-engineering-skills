#!/usr/bin/env python3
"""Lifecycle views: phase timeline with concurrency links, and a stakeholder x phase matrix."""
import sysreq_lib as L


def ready(ws, args):
    miss = L.need(ws, "lifecycle", ("has at least one active phase", lambda o: bool(L.active_phases(o))))
    miss += L.need(ws, "stakeholders", ("has stakeholders", lambda o: bool(o.get("stakeholders"))))
    return miss


def timeline(phases):
    bw, bh, gap = 150, 96, 22
    per_row = 5
    rows = (len(phases) + per_row - 1) // per_row
    W = per_row * (bw + gap) + gap
    H = rows * (bh + 90) + 20
    pos = {}
    out = [f'<svg viewBox="0 0 {W} {H}" style="max-width:{W}px" role="img" aria-label="Lifecycle timeline">{L.ARROW_DEFS}']
    for i, p in enumerate(phases):
        r, c = divmod(i, per_row)
        x, y = gap + c * (bw + gap), 50 + r * (bh + 90)
        pos[p["id"]] = (x + bw / 2, y, y + bh)
        cls = "sys" if p["status"] == "active" else "box"
        dash = "" if p["status"] == "active" else ' stroke-dasharray="4 4"'
        out.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="10" class="{cls}"{dash}/>')
        t, _ = L.svg_text(x + bw / 2, y + 24, p["domain_label"], 18, 13)
        out.append(t)
        sub = p["status"].replace("_", " ") + (f" → {p['merged_into']}" if p.get("merged_into") else "")
        t, _ = L.svg_text(x + bw / 2, y + bh - 12, f"{p['id']} · {sub}", 24, 10, cls="mut")
        out.append(t)
        if i:
            px, py = pos[phases[i - 1]["id"]][0], pos[phases[i - 1]["id"]][1]
            if r == (i - 1) // per_row:
                out.append(f'<line x1="{px + bw/2}" y1="{py + bh/2}" x2="{x}" y2="{y + bh/2}" class="line" marker-end="url(#ah)"/>')
    n = 0
    for p in phases:
        for note in p.get("concurrency_notes", []):
            if note["with_phase"] not in pos:
                continue
            n += 1
            x1, _, b1 = pos[p["id"]]
            x2, _, b2 = pos[note["with_phase"]]
            depth = 30 + 8 * (n % 4)
            out.append(f'<path d="M{x1} {b1} C{x1} {b1+depth} {x2} {b2+depth} {x2} {b2}" class="line" stroke-dasharray="4 3"/>')
            out.append(f'<text x="{(x1+x2)/2}" y="{b1+depth*0.75+10}" font-size="11" text-anchor="middle" class="mut">overlap {n}</text>')
    out.append("</svg>")
    legend = "".join(
        f"<li><b>overlap {i}</b>: {L.e(a)} ↔ {L.e(b)}: {L.e(t)}</li>"
        for i, (a, b, t) in enumerate(((p["domain_label"], next((q["domain_label"] for q in phases if q["id"] == n["with_phase"]), n["with_phase"]), n["note"])
                                         for p in phases for n in p.get("concurrency_notes", []) if n["with_phase"] in pos), 1))
    return "".join(out), legend


def render(ws, args):
    lc, st = L.load(ws, "lifecycle"), L.load(ws, "stakeholders")
    sc = L.load(ws, "scenarios")
    phases = lc["phases"]
    act = [p for p in phases if p["status"] == "active"]
    svg, legend = timeline(phases)
    counts = {}
    for s in (sc or {}).get("scenarios", []):
        for k in s["stakeholder_ids"]:
            counts[(k, s["phase_id"])] = counts.get((k, s["phase_id"]), 0) + 1
    head = "".join(f"<th>{L.e(p['domain_label'])}<br><span class='mut'>{L.e(p['id'])}</span></th>" for p in act)
    rows = ""
    for s in st["stakeholders"]:
        cells = ""
        for p in act:
            if s["id"] in p.get("stakeholder_ids", []):
                n = counts.get((s["id"], p["id"]), 0)
                cells += f'<td class="ok">●{f" · {n} scn" if sc else ""}</td>' if n or not sc else '<td class="warn">● · no scenario</td>'
            else:
                cells += '<td class="mut">–</td>'
        rows += f"<tr><td><b>{L.e(s['name'])}</b><br><span class='mut'>{L.e(s['id'])} · {L.e(s['class'])}</span></td>{cells}</tr>"
    detail = ""
    for p in phases:
        risks = "".join(f"<li>{L.e(r)}</li>" for r in p.get("key_risks_to_capture", []))
        detail += (f"<div class='card'><b>{L.e(p['domain_label'])}</b> <span class='mut'>{L.e(p['id'])} · baseline: {L.e(p['baseline_ref'])} · {L.e(p['status'])}</span>"
                   f"<p>{L.e(p['description'])}</p>"
                   f"{'<p class=mut>Reason: '+L.e(p['reason'])+'</p>' if p.get('reason') else ''}"
                   f"{'<p>Enabling system: '+L.e(p['enabling_system'])+'</p>' if p.get('enabling_system') else ''}"
                   f"{'<details><summary>Risks to capture</summary><ul>'+risks+'</ul></details>' if risks else ''}</div>")
    body = (f'<h2>Phase timeline</h2><div class="card">{svg}</div><ul>{legend}</ul>'
            f'<h2>Stakeholders by phase</h2><div class="card" style="overflow-x:auto"><table><tr><th>Stakeholder</th>{head}</tr>{rows}</table></div>'
            f"<h2>Phase details</h2>{detail}")
    return L.page("System lifecycle", f"{len(act)} active of {len(phases)} phases · {L.meta_line(lc)}", body)


if __name__ == "__main__":
    L.run_renderer("render_lifecycle.py", "lifecycle.html", ready, render, "Show lifecycle phases and who is active in each.")
