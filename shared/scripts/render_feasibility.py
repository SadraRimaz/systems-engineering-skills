#!/usr/bin/env python3
"""Feasibility plan view: questions and the work that answers them, prototype dependency flow,
usability tests, elicitation sessions and decision criteria."""
import sysreq_lib as L


def ready(ws, args):
    return L.need(ws, "feasibility-plan", ("has feasibility questions", lambda o: bool(o.get("feasibility_questions"))),
                  ("has at least one analysis, prototype task or elicitation session",
                   lambda o: bool(o.get("analyses") or o.get("prototype_tasks") or o.get("elicitation_sessions"))))


def levels(protos):
    lv = {}

    def depth(pid, seen=()):
        if pid in lv:
            return lv[pid]
        deps = [d for d in protos[pid].get("depends_on", []) if d in protos and d not in seen]
        lv[pid] = 1 + max([depth(d, seen + (pid,)) for d in deps], default=-1)
        return lv[pid]

    for p in protos:
        depth(p)
    return lv


def flow_svg(prototypes, tests):
    if not prototypes:
        return ""
    protos = L.by_id(prototypes)
    lv = levels(protos)
    cols = {}
    for pid in protos:
        cols.setdefault(lv[pid], []).append(pid)
    pos = {}
    out = []
    for c, ids in cols.items():
        for r, pid in enumerate(ids):
            pos[pid] = (20 + c * 270, 20 + r * 100)
    W = 40 + (max(cols) + 1) * 270
    H = 40 + max(len(v) for v in cols.values()) * 100
    out.append(f'<svg viewBox="0 0 {W} {H}" style="max-width:{W}px" role="img" aria-label="Prototype flow">{L.ARROW_DEFS}')
    for pid, p in protos.items():
        x, y = pos[pid]
        for d in p.get("depends_on", []):
            if d in pos:
                dx, dy = pos[d]
                out.append(f'<line x1="{dx+230}" y1="{dy+36}" x2="{x}" y2="{y+36}" class="line" marker-end="url(#ah)"/>')
    for pid, p in protos.items():
        x, y = pos[pid]
        ut = [t["id"] for t in tests if t["prototype_id"] == pid]
        out.append(f'<rect x="{x}" y="{y}" width="230" height="72" rx="8" class="{"sys" if p["kind"] == "evolutionary" else "box"}"/>')
        t, _ = L.svg_text(x + 10, y + 20, f"{pid} {p['name']}", 30, 12, anchor="start")
        out.append(t)
        t, _ = L.svg_text(x + 10, y + 56, f"{p['kind']} · {p['fidelity']} · {len(p['steps'])} step{'s' if len(p['steps']) != 1 else ''}" + (f" · {', '.join(ut)}" if ut else ""), 40, 10, anchor="start", cls="mut")
        out.append(t)
    out.append("</svg>")
    return "".join(out)


def render(ws, args):
    o = L.load(ws, "feasibility-plan")
    reqs = L.by_id((L.load(ws, "requirements") or {}).get("requirements", []))
    crit = {c["question_id"]: c for c in o.get("decision_criteria", [])}
    work = {}
    for key, label in (("analyses", "analysis"), ("prototype_tasks", "prototype"), ("elicitation_sessions", "elicitation")):
        for w in o.get(key, []):
            for q in w.get("question_ids", []):
                work.setdefault(q, []).append(f"{w['id']} ({label})")
    rows = ""
    for q in o["feasibility_questions"]:
        c = crit.get(q["id"], {})
        rr = "".join(f'<span class="tag" title="{L.e(reqs.get(r, {}).get("statement", ""))}">{L.e(r)}</span>' for r in q["requirement_ids"])
        rows += (f"<tr><td><b>{L.e(q['id'])}</b><br><span class='tag'>{L.e(q['concern'])}</span><span class='tag'>{L.e(q['priority'])}</span></td>"
                 f"<td>{L.e(q['question'])}<br>{rr}</td><td>{'<br>'.join(L.e(x) for x in work.get(q['id'], [])) or '<span class=bad>none</span>'}</td>"
                 f"<td><div class='ok'>Feasible if: {L.e(c.get('feasible_if', ''))}</div><div class='bad'>Infeasible if: {L.e(c.get('infeasible_if', ''))}</div>"
                 f"<div class='warn'>Change requirement if: {L.e(c.get('change_requirement_if', ''))}</div></td></tr>")
    an = "".join(f"<li><b>{L.e(a['id'])} {L.e(a['name'])}</b> ({L.e(a['kind'])}): {L.e(a['method'])} &rarr; {L.e(a['deliverable'])}</li>" for a in o.get("analyses", []))
    steps = ""
    for p in o.get("prototype_tasks", []):
        s = "".join(f"<li>{L.e(x['action'])}</li>" for x in sorted(p["steps"], key=lambda z: z["order"]))
        steps += (f"<details><summary><b>{L.e(p['id'])} {L.e(p['name'])}</b> · {L.e(p['effort'])} · owner {L.e(p['owner'])}</summary>"
                  f"<p>Learns: {L.e('; '.join(p['learns']))}</p><ol>{s}</ol></details>")
    ut = ""
    for u in o.get("usability_tests", []):
        seg = "".join(f"<li>domain {L.e(x['domain_knowledge'])}, computer {L.e(x['computer_experience'])}, system {L.e(x['system_experience'])}" + (f", n={x['sample_size']}" if x.get("sample_size") else "") + "</li>" for x in u["user_segments"])
        met = "".join(f"<li>{L.e(m['element'])}: {L.e(m['measure'])} (target {L.e(m['target'])})</li>" for m in u["metrics"])
        ut += f"<div class='card'><b>{L.e(u['id'])}</b> on {L.e(u['prototype_id'])}; tasks from {L.e(', '.join(u['task_scenario_ids']))}<br>Segments:<ul>{seg}</ul>Metrics:<ul>{met}</ul></div>"
    es = "".join(f"<li><b>{L.e(x['id'])}</b> {L.e(x['method'].replace('_', ' '))} with {L.e(', '.join(x['participants']))}: {L.e(x['purpose'])}</li>" for x in o.get("elicitation_sessions", []))
    res = {r["ref_id"]: r for r in o.get("results", [])}
    done = sum(1 for r in res.values() if r["status"] == "done")
    body = (f'<div class="card">{len(o["feasibility_questions"])} questions · {len(o.get("analyses", []))} analyses · {len(o.get("prototype_tasks", []))} prototype tasks · '
            f'{len(o.get("usability_tests", []))} usability tests · {done} results recorded</div>'
            f'<h2>Questions, work and decision criteria</h2><div class="card" style="overflow-x:auto"><table><tr><th>Question</th><th>What is being asked</th><th>Answered by</th><th>Decision criteria</th></tr>{rows}</table></div>'
            f'<h2>Prototype flow</h2><div class="card" style="overflow-x:auto">{flow_svg(o.get("prototype_tasks", []), o.get("usability_tests", [])) or "<span class=mut>no prototype tasks</span>"}</div>{steps}'
            f'<h2>Analyses</h2><ul>{an or "<li class=mut>none</li>"}</ul><h2>Usability tests</h2>{ut or "<p class=mut>none</p>"}<h2>Elicitation sessions</h2><ul>{es or "<li class=mut>none</li>"}</ul>')
    return L.page("Feasibility analysis plan", L.meta_line(o) + " · plan only, nothing here has been executed unless a result is recorded", body)


if __name__ == "__main__":
    L.run_renderer("render_feasibility.py", "feasibility-plan.html", ready, render, "Show the feasibility analysis plan.")
