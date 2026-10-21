#!/usr/bin/env python3
"""Shared helpers for all skills: workspace I/O, data lookup, stale detection,
renderer wrapper, and HTML/SVG building blocks. Standard library only.

Exit codes used across the scripts:
  0 ok | 1 invalid content | 2 usage / missing file | 3 not ready (missing data)
"""
import argparse
import datetime
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _find_base():
    for base in (HERE.parent / "assets", HERE.parent):
        if (base / "data" / "pipeline.json").exists():
            return base
    sys.stderr.write("error: data files not found (expected assets/data or data next to scripts)\n")
    sys.exit(2)


BASE = _find_base()
DATA_DIR = BASE / "data"
SCHEMA_DIR = BASE / "schemas"


# ---------------------------------------------------------------- JSON I/O
def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}", 1)


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def data(name):
    return read_json(DATA_DIR / f"{name}.json")


def fail(message, code=1):
    sys.stderr.write(f"error: {message}\n")
    sys.exit(code)


def emit(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------- pipeline
PIPELINE = data("pipeline")


def ordered_skills():
    return [dict(s, stage=st["id"]) for st in PIPELINE["stages"] for s in st["skills"]]


def artifact_names():
    return [s["artifact"] for s in ordered_skills()]


def upstream_of(artifact):
    for s in ordered_skills():
        if s["artifact"] == artifact:
            return s["upstream"]
    return []


def skill_for(artifact):
    for s in ordered_skills():
        if s["artifact"] == artifact:
            return s
    return None


def next_skill(artifact):
    skills = ordered_skills()
    for i, s in enumerate(skills):
        if s["artifact"] == artifact:
            return skills[i + 1] if i + 1 < len(skills) else None
    return None


def artifact_for_id(identifier):
    prefix = str(identifier).split("-")[0]
    return PIPELINE["id_prefixes"].get(prefix)


# ---------------------------------------------------------------- workspace
def artifact_path(ws, name):
    return Path(ws) / f"{name}.json"


def load(ws, name, required=False):
    p = artifact_path(ws, name)
    if not p.exists():
        if required:
            fail(f"{p} not found. Run the skill that produces '{name}' first.", 2)
        return None
    return read_json(p)


def meta_of(obj):
    return (obj or {}).get("meta") or {}


def version_of(obj):
    return int(meta_of(obj).get("version", 0) or 0)


def stale_report(ws):
    """Artifacts built from an older version of an upstream artifact."""
    cache, out = {}, []
    for name in artifact_names():
        cache[name] = load(ws, name)
    for name, obj in cache.items():
        if obj is None or version_of(obj) < 1:
            continue
        built = meta_of(obj).get("built_from", {})
        for up in upstream_of(name):
            cur = version_of(cache.get(up))
            if cache.get(up) is not None and cur > int(built.get(up, 0)):
                out.append({"artifact": name, "upstream": up, "built_from_version": int(built.get(up, 0)), "current_version": cur})
    return out


def today():
    return datetime.date.today().isoformat()


# ---------------------------------------------------------------- helpers
def by_id(items, key="id"):
    return {i[key]: i for i in items or [] if key in i}


def active_phases(lifecycle):
    return [p for p in (lifecycle or {}).get("phases", []) if p.get("status") == "active"]


def system_name(brief):
    return ((brief or {}).get("system_of_interest") or {}).get("name", "System")


# ---------------------------------------------------------------- renderer wrapper
def run_renderer(name, default_out, ready_fn, render_fn, description, add_args=None):
    """Standard CLI for visual generators.

    ready_fn(ws, args) -> list of missing-data messages (empty = ready)
    render_fn(ws, args) -> html string
    add_args(parser) may add renderer-specific options.
    """
    ap = argparse.ArgumentParser(prog=name, description=description + " Writes a self-contained HTML file.")
    ap.add_argument("--workspace", default="./sysreq", help="project workspace folder (default ./sysreq)")
    ap.add_argument("--out", help="output HTML path (default <workspace>/views/" + default_out + ")")
    ap.add_argument("--check-ready", action="store_true", help="only report whether enough data exists; exit 3 if not")
    if add_args:
        add_args(ap)
    args = ap.parse_args()
    ws = Path(args.workspace)
    missing = ready_fn(ws, args)
    if args.check_ready:
        emit({"ready": not missing, "missing": missing})
        sys.exit(3 if missing else 0)
    if missing:
        emit({"ready": False, "missing": missing})
        sys.stderr.write("error: not enough data to generate this view (see 'missing').\n")
        sys.exit(3)
    out = Path(args.out) if args.out else ws / "views" / default_out.format(**vars(args))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_fn(ws, args), encoding="utf-8")
    emit({"ready": True, "out": str(out)})


def need(ws, name, *conditions):
    """Missing-data messages for an artifact. conditions are (label, predicate(obj))."""
    obj = load(ws, name)
    if obj is None:
        return [f"{name}.json does not exist"]
    return [f"{name}: {label}" for label, pred in conditions if not pred(obj)]


# ---------------------------------------------------------------- HTML / SVG
e = html.escape

CSS = """
:root{--bg:#fbfbfa;--fg:#1c1d1f;--mut:#62666d;--line:#c9ccd1;--card:#fff;--acc:#2457c5;--acc2:#0f8a6a;--warn:#b4541a;--bad:#b3261e;--soft:#eef1f6}
@media (prefers-color-scheme:dark){:root{--bg:#14151a;--fg:#e7e8ea;--mut:#9ea3ad;--line:#3a3d46;--card:#1d1f26;--acc:#7da2ff;--acc2:#4cc7a1;--warn:#f0a468;--bad:#ff8f87;--soft:#23262f}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;padding:24px 16px 48px}
main{max-width:1100px;margin:0 auto}h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 8px}p.sub{color:var(--mut);margin:0 0 18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}th{background:var(--soft)}
.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:0 8px;font-size:12px;color:var(--mut);margin:1px 2px;background:var(--soft)}
.ok{color:var(--acc2)}.warn{color:var(--warn)}.bad{color:var(--bad)}.mut{color:var(--mut)}
.bar{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}.bar button,.tabs button{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--fg);padding:4px 12px;border-radius:999px;cursor:pointer}
.bar button.on,.tabs button.on{background:var(--acc);color:#fff;border-color:var(--acc)}
svg{max-width:100%;height:auto}svg text{fill:var(--fg);font-family:system-ui,sans-serif}svg .box{fill:var(--card);stroke:var(--line);stroke-width:1.5}
svg .sys{fill:var(--soft);stroke:var(--acc);stroke-width:2}svg .line{stroke:var(--mut);stroke-width:1.4;fill:none}svg .mut{fill:var(--mut)}
.lbl{paint-order:stroke;stroke:var(--card);stroke-width:4px;stroke-linejoin:round}.hide{display:none}details{margin:4px 0}summary{cursor:pointer}
"""


def page(title, subtitle, body, script=""):
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{e(title)}</title><style>{CSS}</style></head><body><main>"
        f"<h1>{e(title)}</h1><p class=\"sub\">{e(subtitle)}</p>{body}</main>"
        f"<script>{script}</script></body></html>"
    )


def wrap(text, width):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines or [""]


def svg_text(x, y, text, width=24, size=13, anchor="middle", cls="", line_h=16):
    lines = wrap(text, width)
    tspans = "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else line_h}">{e(l)}</tspan>' for i, l in enumerate(lines)
    )
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" class="{cls}">{tspans}</text>', len(lines)


def meta_line(ws_obj):
    m = meta_of(ws_obj)
    return f"version {m.get('version', 0)} · status {m.get('status', 'draft')}"


ARROW_DEFS = (
    '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    '<path d="M0 0L10 5L0 10z" style="fill:var(--mut)"/></marker></defs>'
)


def tab_script():
    """Tiny tab switcher: buttons with data-tab show elements with matching data-panel."""
    return (
        "document.querySelectorAll('[data-tab]').forEach(function(b){b.addEventListener('click',function(){"
        "var g=b.getAttribute('data-group');"
        "document.querySelectorAll('[data-tab][data-group=\"'+g+'\"]').forEach(function(x){x.classList.toggle('on',x===b)});"
        "document.querySelectorAll('[data-panel][data-group=\"'+g+'\"]').forEach(function(p){"
        "p.classList.toggle('hide',p.getAttribute('data-panel')!==b.getAttribute('data-tab'))});});});"
    )
