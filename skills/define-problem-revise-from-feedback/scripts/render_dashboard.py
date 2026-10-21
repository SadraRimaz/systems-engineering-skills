#!/usr/bin/env python3
"""Pipeline status dashboard: artifact versions, approval, stale flags, open issues, validation."""
import sysreq_lib as L
from status import summarize


def ready(ws, args):
    return [] if any(L.load(ws, n) is not None for n in L.artifact_names()) else ["workspace has no artifacts yet"]


def render(ws, args):
    s = summarize(ws)
    done = sum(1 for r in s["artifacts"] if r["done"])
    total = len(s["artifacts"])
    rows = ""
    for i, r in enumerate(s["artifacts"]):
        if not r["present"]:
            state = '<span class="mut">not started</span>'
            extra = ""
        else:
            state = ('<span class="ok">approved</span>' if r["status"] == "approved" and r["version"] >= 1 else '<span class="warn">draft</span>')
            if r["stale"]:
                state += ' <span class="bad">STALE (' + L.e(", ".join(r["stale"])) + ")</span>"
            extra = (f"v{r['version']} · {r['open_issues']} open issues · "
                     f"<span class=\"{'bad' if r['validation_errors'] else 'ok'}\">{r['validation_errors']} errors</span> · {r['validation_warnings']} warnings")
        nxt = ' <span class="tag">next</span>' if r["skill"] == s["next_skill"] else ""
        rows += f"<tr><td>{i}</td><td><b>{L.e(r['title'])}</b>{nxt}<br><span class='mut'>{L.e(r['skill'])}</span></td><td>{state}</td><td>{extra}</td></tr>"
    pct = int(100 * done / total) if total else 0
    bar = f'<div class="card"><b>{done} of {total}</b> artifacts approved and current<div style="background:var(--soft);border-radius:6px;height:10px;margin-top:8px"><div style="width:{pct}%;background:var(--acc2);height:10px;border-radius:6px"></div></div></div>'
    nxt = f'<p>Next skill to run: <b>{L.e(s["next_skill"])}</b></p>' if s["next_skill"] else "<p class=ok>All artifacts are approved and current.</p>"
    return L.page("Pipeline status", f"Workspace {ws}", f"{bar}{nxt}<table><tr><th>#</th><th>Skill</th><th>State</th><th>Detail</th></tr>{rows}</table>")


if __name__ == "__main__":
    L.run_renderer("render_dashboard.py", "dashboard.html", ready, render, "Show pipeline status.")
