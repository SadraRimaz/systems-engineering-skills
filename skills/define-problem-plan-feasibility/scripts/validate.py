#!/usr/bin/env python3
"""Validate workspace artifacts: JSON Schema + cross-artifact rules + stale flags.

Usage:
  python scripts/validate.py --workspace ./sysreq [--artifact stakeholders] [--require concept-brief,stakeholders]

Exit codes: 0 ok | 1 errors found or required input missing | 2 usage
Output (stdout): JSON {"ok", "results": [{artifact, ok, errors, warnings}], "stale", "missing_required"}
"""
import argparse
import sys
from pathlib import Path

import sysreq_lib as L

try:
    import jsonschema
except ImportError:  # pragma: no cover
    L.fail("the 'jsonschema' package is required: pip install -r scripts/requirements.txt", 2)

from lint_requirements import lint_requirement

NUM = (int, float)


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def dup_ids(items, label, r, key="id"):
    seen = set()
    for i in items:
        v = i.get(key)
        if v in seen:
            r.err(f"{label}: duplicate id {v}")
        seen.add(v)


def check_meta(obj, name, r):
    m = obj.get("meta")
    if not isinstance(m, dict):
        return r.err("meta is missing")
    if m.get("artifact") != name:
        r.err(f"meta.artifact must be '{name}'")
    if not isinstance(m.get("version"), int) or m["version"] < 0:
        r.err("meta.version must be an integer >= 0")
    if m.get("status") not in ("draft", "approved"):
        r.err("meta.status must be 'draft' or 'approved'")
    if not isinstance(m.get("built_from", {}), dict):
        r.err("meta.built_from must be an object")
    if not isinstance(m.get("changelog", []), list):
        r.err("meta.changelog must be a list")


def check_schema(obj, name, r):
    schema = L.read_json(L.SCHEMA_DIR / f"{name}.schema.json")
    for e in sorted(jsonschema.Draft202012Validator(schema).iter_errors(obj), key=lambda x: list(x.path)):
        where = "/".join(str(p) for p in e.path) or "(root)"
        r.err(f"schema: {where}: {e.message[:220]}")


def issues_check(obj, r):
    for i in obj.get("open_issues", []):
        if i.get("status") == "open":
            r.warn(f"open issue {i.get('id')} ({i.get('kind')}, owner {i.get('owner')}): {i.get('text')}")


# ------------------------------------------------------------ per artifact
def v_concept_brief(o, ws, r):
    if not o["boundary_hypothesis"]["outside"]:
        r.warn("boundary_hypothesis.outside is empty: name at least the obvious external parties")
    if not o["solution_bias_flags"]:
        r.warn("solution_bias_flags is empty: confirm the problem statement was challenged for solution bias")
    dup_ids(o["decisions_log"], "decisions_log", r)
    dup_ids(o["open_issues"], "open_issues", r)


def v_stakeholders(o, ws, r):
    classes = {c["id"] for c in L.data("stakeholder-classes")}
    dup_ids(o["stakeholders"], "stakeholders", r)
    used = set()
    for s in o["stakeholders"]:
        c = s["class"]
        used.add(c)
        if c not in classes and not c.startswith("other:"):
            r.err(f"{s['id']}: class '{c}' is not a known class (use one of {sorted(classes)} or 'other:<label>')")
    covered = {c["class"] for c in o.get("class_coverage", [])}
    for c in classes:
        if c not in used and c not in covered:
            r.err(f"class '{c}' has no stakeholder and no class_coverage entry explaining why none applies")
    for c in covered & used:
        r.warn(f"class '{c}' is listed in class_coverage as none but has stakeholders")
    if not any(s["pays"] for s in o["stakeholders"]):
        r.err("no stakeholder has pays=true: someone pays for the system in at least one phase")
    lc = L.load(ws, "lifecycle")
    if lc:
        referenced = {sid for p in L.active_phases(lc) for sid in p.get("stakeholder_ids", [])}
        for s in o["stakeholders"]:
            if s["id"] not in referenced:
                r.warn(f"{s['id']} ({s['name']}) is not active in any lifecycle phase yet")
    dup_ids(o["open_issues"], "open_issues", r)


def v_lifecycle(o, ws, r):
    baseline = {p["id"] for p in L.data("baseline-lifecycle")}
    kinds = {k["id"] for k in L.data("scenario-kinds")}
    st = L.load(ws, "stakeholders", required=False)
    stk = L.by_id(st["stakeholders"]) if st else {}
    if not st:
        r.err("stakeholders.json is required to validate lifecycle phases")
    dup_ids(o["phases"], "phases", r)
    ids = {p["id"] for p in o["phases"]}
    seen_baseline = set()
    for p in o["phases"]:
        ref = p["baseline_ref"]
        if ref != "custom" and ref not in baseline:
            r.err(f"{p['id']}: baseline_ref '{ref}' is unknown (use one of {sorted(baseline)} or 'custom')")
        seen_baseline.add(ref)
        if p["status"] == "not_applicable" and not p.get("reason"):
            r.err(f"{p['id']}: not_applicable needs a reason")
        if p["status"] == "merged":
            if p.get("merged_into") not in ids:
                r.err(f"{p['id']}: merged_into must name an existing phase id")
            if not p.get("reason"):
                r.err(f"{p['id']}: merged needs a reason")
        if p["status"] == "active":
            if not p.get("stakeholder_ids"):
                r.err(f"{p['id']}: an active phase needs at least one stakeholder_id")
            if not p.get("enabling_system"):
                r.warn(f"{p['id']}: enabling_system is empty")
        for sid in p.get("stakeholder_ids", []):
            if stk and sid not in stk:
                r.err(f"{p['id']}: unknown stakeholder id {sid}")
        for n in p.get("concurrency_notes", []):
            if n["with_phase"] not in ids:
                r.err(f"{p['id']}: concurrency note refers to unknown phase {n['with_phase']}")
        for k in p.get("scenario_seeds", []):
            if k not in kinds and not k.startswith("custom:"):
                r.err(f"{p['id']}: scenario seed '{k}' is not a known scenario kind")
    for b in baseline - seen_baseline:
        r.err(f"baseline phase '{b}' is not represented: add it as active, not_applicable (with reason) or merged")
    if not L.active_phases(o):
        r.err("at least one phase must be active")
    dup_ids(o["open_issues"], "open_issues", r)


def v_scenarios(o, ws, r):
    brief = L.load(ws, "concept-brief")
    lc = L.load(ws, "lifecycle")
    st = L.load(ws, "stakeholders")
    if not (brief and lc and st):
        return r.err("concept-brief, stakeholders and lifecycle are required to validate scenarios")
    sysname = L.system_name(brief).lower()
    kinds = {k["id"] for k in L.data("scenario-kinds")}
    phases = L.by_id(L.active_phases(lc))
    stk = L.by_id(st["stakeholders"])
    dup_ids(o["scenarios"], "scenarios", r)
    dup_ids(o.get("mission_requirements", []), "mission_requirements", r)
    covered = {}
    for s in o["scenarios"]:
        sid = s["id"]
        ph = phases.get(s["phase_id"])
        if not ph:
            r.err(f"{sid}: phase_id {s['phase_id']} is not an active lifecycle phase")
        if s["kind"] not in kinds and not s["kind"].startswith("custom:"):
            r.err(f"{sid}: kind '{s['kind']}' is not a known scenario kind (or use 'custom:<label>')")
        for k in s["stakeholder_ids"]:
            if k not in stk:
                r.err(f"{sid}: unknown stakeholder {k}")
            elif ph and k not in ph.get("stakeholder_ids", []):
                r.warn(f"{sid}: {k} is not listed as active in {ph['id']}")
        for x in s["exchanges"]:
            a, b = x["from"].lower(), x["to"].lower()
            if a == b:
                r.err(f"{sid}: exchange '{x['item']}' goes from and to the same actor")
            if sysname not in (a, b):
                r.err(f"{sid}: exchange '{x['item']}' does not involve the system '{L.system_name(brief)}' (inputs/outputs only, no internal processing)")
        covered.setdefault(s["phase_id"], {"kinds": set(), "stk": set()})
        covered[s["phase_id"]]["kinds"].add(s["kind"])
        covered[s["phase_id"]]["stk"].update(s["stakeholder_ids"])
        if not s.get("variations"):
            r.warn(f"{sid}: no variations listed")
    notes = {(n["phase_id"], n["kind"]) for n in o.get("coverage_notes", [])}
    for pid, ph in phases.items():
        c = covered.get(pid, {"kinds": set(), "stk": set()})
        for k in ph.get("stakeholder_ids", []):
            if k not in c["stk"]:
                r.err(f"{pid}: stakeholder {k} has no scenario in this phase")
        for k in kinds:
            if k not in c["kinds"] and (pid, k) not in notes:
                r.err(f"{pid}: no '{k}' scenario and no coverage_note marking it n/a")
    for m in o.get("mission_requirements", []):
        for k in m["stakeholder_ids"]:
            if k not in stk:
                r.err(f"{m['id']}: unknown stakeholder {k}")
    if not o.get("mission_requirements"):
        r.warn("no mission_requirements recorded")
    dup_ids(o["open_issues"], "open_issues", r)


def v_boundary(o, ws, r):
    brief, lc, sc = L.load(ws, "concept-brief"), L.load(ws, "lifecycle"), L.load(ws, "scenarios")
    if not (brief and lc and sc):
        return r.err("concept-brief, lifecycle and scenarios are required to validate the boundary")
    sysname = L.system_name(brief)
    phases = L.by_id(L.active_phases(lc))
    for key in ("external_systems", "interfaces", "controls", "boundary_decisions"):
        dup_ids(o.get(key, []), key, r)
    ext = L.by_id(o["external_systems"])
    names = {}
    for x in o["external_systems"]:
        if x["name"].lower() in names:
            r.err(f"{x['id']}: duplicate external system name '{x['name']}'")
        names[x["name"].lower()] = x
        if x["name"].lower() == sysname.lower():
            r.err(f"{x['id']}: the system itself cannot be an external system")
        for p in x["phase_ids"]:
            if p not in phases:
                r.err(f"{x['id']}: phase {p} is not an active lifecycle phase")
    ifaces = o["interfaces"]
    for i in ifaces:
        x = ext.get(i["external_id"])
        if not x:
            r.err(f"{i['id']}: unknown external_id {i['external_id']}")
        elif i["phase_id"] not in x["phase_ids"]:
            r.err(f"{i['id']}: phase {i['phase_id']} is not in {x['id']}.phase_ids")
    matched = set()
    for s in sc["scenarios"]:
        for x in s["exchanges"]:
            out = x["from"].lower() == sysname.lower()
            partner = (x["to"] if out else x["from"]).lower()
            want = ("output",) if out else ("input", "control")
            ex = names.get(partner)
            if not ex:
                r.err(f"{s['id']}: actor '{x['to'] if out else x['from']}' has no entry in external_systems")
                continue
            hit = [i for i in ifaces if i["phase_id"] == s["phase_id"] and i["external_id"] == ex["id"]
                   and i["direction"] in want and i["item"].lower() == x["item"].lower()]
            if not hit:
                r.err(f"{s['id']}: exchange '{x['item']}' ({'out to' if out else 'in from'} {ex['name']}) has no matching interface in {s['phase_id']}")
            matched.update(i["id"] for i in hit)
    for i in ifaces:
        if i["id"] not in matched:
            r.warn(f"{i['id']} is not used by any scenario exchange")
    for pid in phases:
        for x in o["external_systems"]:
            if pid not in x["phase_ids"]:
                continue
            outs = [i for i in ifaces if i["phase_id"] == pid and i["external_id"] == x["id"] and i["direction"] == "output"]
            if x["kind"] == "context" and outs:
                r.err(f"{x['id']} is context but receives outputs in {pid}: context cannot be impacted by the system")
            if x["kind"] != "context" and not outs:
                r.err(f"{x['id']} receives no system output in {pid}: it is either context or an interface is missing")
    for c in o.get("controls", []):
        for p in c["applies_to_phases"]:
            if p not in phases:
                r.err(f"{c['id']}: phase {p} is not an active lifecycle phase")
        if c.get("source_external_id") and c["source_external_id"] not in ext:
            r.err(f"{c['id']}: unknown source_external_id")
    if not o.get("boundary_decisions"):
        r.warn("no boundary_decisions recorded: note who decided what is in or out and the cost/schedule implication")
    dup_ids(o["open_issues"], "open_issues", r)


def v_objectives(o, ws, r):
    st, lc, sc = L.load(ws, "stakeholders"), L.load(ws, "lifecycle"), L.load(ws, "scenarios")
    if not (st and lc and sc):
        return r.err("stakeholders, lifecycle and scenarios are required to validate objectives")
    stk, scn = L.by_id(st["stakeholders"]), L.by_id(sc["scenarios"])
    phases = L.by_id(L.active_phases(lc))
    dup_ids(o["hierarchies"], "hierarchies", r)
    dup_ids(o["nodes"], "nodes", r)
    hier = L.by_id(o["hierarchies"])
    nodes = L.by_id(o["nodes"])
    for h in o["hierarchies"]:
        if h.get("scope_phase_id") and h["scope_phase_id"] not in phases:
            r.err(f"{h['id']}: scope_phase_id is not an active phase")
        for k in h.get("stakeholder_ids", []):
            if k not in stk:
                r.err(f"{h['id']}: unknown stakeholder {k}")
    children = {}
    for n in o["nodes"]:
        if n["hierarchy_id"] not in hier:
            r.err(f"{n['id']}: unknown hierarchy {n['hierarchy_id']}")
        p = n["parent_id"]
        if p is not None:
            if p not in nodes:
                r.err(f"{n['id']}: unknown parent {p}")
            elif nodes[p]["hierarchy_id"] != n["hierarchy_id"]:
                r.err(f"{n['id']}: parent is in a different hierarchy")
        children.setdefault(p, []).append(n)
        if not n["design_independent"]:
            r.err(f"{n['id']} '{n['name']}': a means objective (a way to achieve value, not value itself) does not belong in the hierarchy")
        for k in n.get("stakeholder_ids", []):
            if k not in stk:
                r.err(f"{n['id']}: unknown stakeholder {k}")
        for k in n.get("scenario_ids", []):
            if k not in scn:
                r.err(f"{n['id']}: unknown scenario {k}")
    for hid in hier:
        roots = [n for n in o["nodes"] if n["hierarchy_id"] == hid and n["parent_id"] is None]
        if len(roots) != 1:
            r.err(f"{hid}: needs exactly one root node (found {len(roots)})")
            continue
        if roots[0]["level"] != "fundamental":
            r.err(f"{roots[0]['id']}: the root must have level 'fundamental'")
        depth = {"max": 0}

        def walk(n, d, seen):
            if n["id"] in seen:
                return r.err(f"{hid}: cycle at {n['id']}")
            depth["max"] = max(depth["max"], d)
            kids = children.get(n["id"], [])
            if kids:
                if n["level"] == "measure":
                    r.err(f"{n['id']}: a measure cannot have children")
                if n.get("threshold") is not None:
                    r.warn(f"{n['id']}: only leaves carry thresholds and goals")
                total = 0.0
                for k in kids:
                    if k.get("weight") is None:
                        r.err(f"{k['id']}: missing weight")
                    else:
                        total += k["weight"]
                if abs(total - 1) > 0.001:
                    r.err(f"{n['id']}: child weights sum to {total:.3f}, must be 1")
            else:
                if n["level"] != "measure":
                    r.err(f"{n['id']}: a leaf must be a measure (decompose further or make it measurable)")
                for f in ("measure_kind", "unit", "direction", "threshold", "goal", "value_curve"):
                    if n.get(f) in (None, ""):
                        r.err(f"{n['id']}: leaf measure is missing '{f}'")
                if isinstance(n.get("threshold"), NUM) and isinstance(n.get("goal"), NUM) and n.get("direction"):
                    ok = n["goal"] > n["threshold"] if n["direction"] == "increase" else n["goal"] < n["threshold"]
                    if not ok:
                        r.err(f"{n['id']}: goal must be beyond threshold in the '{n['direction']}' direction")
                vc = n.get("value_curve") or {}
                if vc.get("shape") == "piecewise" and len(vc.get("points", [])) < 2:
                    r.err(f"{n['id']}: piecewise value_curve needs at least 2 points")
            for k in kids:
                walk(k, d + 1, seen | {n["id"]})

        walk(roots[0], 1, set())
        if depth["max"] < 2:
            r.err(f"{hid}: needs at least 2 levels")
        if depth["max"] > 5:
            r.warn(f"{hid}: {depth['max']} levels deep; decomposing past 5 usually means design is creeping in")
    dup_ids(o["open_issues"], "open_issues", r)


def v_requirements(o, ws, r):
    st, lc, sc = L.load(ws, "stakeholders"), L.load(ws, "lifecycle"), L.load(ws, "scenarios")
    bd, ob = L.load(ws, "boundary"), L.load(ws, "objectives")
    if not all((st, lc, sc, bd, ob)):
        return r.err("stakeholders, lifecycle, scenarios, boundary and objectives are required to validate requirements")
    cats = {c["id"]: c for c in L.data("requirement-categories")["categories"]}
    groups = [g["id"] for g in L.data("requirement-categories")["groups"]]
    phases = L.by_id(L.active_phases(lc))
    stk, scn = L.by_id(st["stakeholders"]), L.by_id(sc["scenarios"])
    msn = L.by_id(sc.get("mission_requirements", []))
    ifs, objs = L.by_id(bd["interfaces"]), L.by_id(ob["nodes"])
    dup_ids(o["requirements"], "requirements", r)
    seen_text = {}
    refs_if, refs_obj, by_phase_group = set(), {}, {}
    cross = []
    for q in o["requirements"]:
        qid, c = q["id"], q["category"]
        if c not in cats:
            r.err(f"{qid}: unknown category '{c}'")
            continue
        g = cats[c]["group"]
        if q["phase_id"] == "ALL":
            if c != "cost_performance_tradeoff":
                r.err(f"{qid}: phase_id 'ALL' is only for the overall cross-phase cost_performance_tradeoff requirement")
            else:
                cross.append(qid)
        elif q["phase_id"] not in phases:
            r.err(f"{qid}: phase_id {q['phase_id']} is not an active lifecycle phase")
        else:
            by_phase_group.setdefault((q["phase_id"], g), []).append(qid)
        s = q["sources"]
        for k, table, label in (("stakeholder_ids", stk, "stakeholder"), ("scenario_ids", scn, "scenario"),
                                ("interface_ids", ifs, "interface"), ("objective_ids", objs, "objective"), ("mission_ids", msn, "mission requirement")):
            for x in s.get(k, []):
                if x not in table:
                    r.err(f"{qid}: unknown {label} {x}")
        refs_if.update(s.get("interface_ids", []) if g == "io" and c in ("input", "output", "external_interface") else [])
        for x in s.get("objective_ids", []):
            refs_obj.setdefault(x, []).append(q)
        if not (s.get("stakeholder_ids") or s.get("scenario_ids") or s.get("mission_ids")):
            r.err(f"{qid}: not traced to any stakeholder, scenario or mission requirement")
        if q["kind"] == "performance":
            if q.get("threshold") in (None, ""):
                r.err(f"{qid}: a performance requirement needs a threshold (minimum acceptable level)")
            elif isinstance(q["threshold"], NUM) and not q.get("unit"):
                r.err(f"{qid}: numeric threshold needs a unit")
            if q.get("goal") in (None, ""):
                r.warn(f"{qid}: no goal set (the level beyond which stakeholders see no added value)")
            if g in ("io", "system_wide") and not q.get("qualification_method"):
                r.err(f"{qid}: performance requirement needs a qualification_method")
        elif g in ("io", "system_wide") and not q.get("qualification_method"):
            r.warn(f"{qid}: no qualification_method")
        leaf_ids = [x for x in s.get("objective_ids", []) if objs.get(x, {}).get("level") == "measure"]
        if len(leaf_ids) == 1 and isinstance(q.get("threshold"), NUM):
            ob_n = objs[leaf_ids[0]]
            for f in ("threshold", "goal", "unit"):
                if q.get(f) not in (None, "") and ob_n.get(f) is not None and q[f] != ob_n[f]:
                    r.err(f"{qid}: {f} {q[f]!r} differs from {leaf_ids[0]} ({ob_n[f]!r}); the objective is the source of truth, align one of them")
        if isinstance(q.get("threshold"), NUM) and f"{q['threshold']:g}" not in q["statement"].replace(",", ""):
            r.warn(f"{qid}: the threshold {q['threshold']:g} does not appear in the statement text")
        if q.get("tbd"):
            r.warn(f"{qid}: flagged TBD")
        key = " ".join(q["statement"].lower().split())
        if key in seen_text:
            r.err(f"{qid}: duplicates the statement of {seen_text[key]}")
        seen_text[key] = qid
        for f in lint_requirement(q["statement"], q):
            (r.err if f["severity"] == "error" else r.warn)(f"{qid}: {f['rule']}: {f['message']}")
    if len(cross) != 1:
        r.err(f"exactly one overall cross-phase cost_performance_tradeoff requirement (phase_id 'ALL') is required, found {len(cross)}")
    notes = {(n["phase_id"], n["group"]) for n in o.get("partition_notes", [])}
    for pid in phases:
        for g in groups:
            if not by_phase_group.get((pid, g)) and (pid, g) not in notes:
                r.err(f"{pid}: no '{g}' requirements and no partition_note marking the group n/a")
    for iid in ifs:
        if iid not in refs_if:
            r.err(f"interface {iid} has no input/output/external_interface requirement")
    for n in ob["nodes"]:
        if n["level"] == "measure":
            reqs = refs_obj.get(n["id"], [])
            if not any(q.get("threshold") is not None and q.get("goal") is not None for q in reqs):
                r.err(f"objective measure {n['id']} '{n['name']}' has no requirement with threshold and goal")
    if not any(q["category"] == "acceptance" for q in o["requirements"]):
        r.err("no acceptance requirement: stakeholders must be able to approve how the system will be accepted")
    dup_ids(o["open_issues"], "open_issues", r)


def v_feasibility(o, ws, r):
    rq, sc, st = L.load(ws, "requirements"), L.load(ws, "scenarios"), L.load(ws, "stakeholders")
    if not (rq and sc and st):
        return r.err("requirements, scenarios and stakeholders are required to validate the feasibility plan")
    reqs, scn, stk = L.by_id(rq["requirements"]), L.by_id(sc["scenarios"]), L.by_id(st["stakeholders"])
    allids = []
    for key in ("feasibility_questions", "analyses", "prototype_tasks", "usability_tests", "elicitation_sessions"):
        dup_ids(o.get(key, []), key, r)
        allids += [i["id"] for i in o.get(key, [])]
    qs = L.by_id(o["feasibility_questions"])
    addressed = set()
    for q in o["feasibility_questions"]:
        for x in q["requirement_ids"]:
            if x not in reqs:
                r.err(f"{q['id']}: unknown requirement {x}")
    for a in o.get("analyses", []):
        addressed.update(a["question_ids"])
    protos = L.by_id(o.get("prototype_tasks", []))
    for p in o.get("prototype_tasks", []):
        addressed.update(p["question_ids"])
        orders = sorted(s["order"] for s in p["steps"])
        if orders != list(range(1, len(orders) + 1)):
            r.err(f"{p['id']}: step order must be 1..n without gaps")
        for d in p.get("depends_on", []):
            if d not in protos:
                r.err(f"{p['id']}: unknown dependency {d}")
    # cycle check
    state = {}

    def visit(pid, trail):
        if state.get(pid) == 2:
            return
        if state.get(pid) == 1:
            return r.err(f"prototype dependency cycle: {' -> '.join(trail + [pid])}")
        state[pid] = 1
        for d in protos.get(pid, {}).get("depends_on", []):
            if d in protos:
                visit(d, trail + [pid])
        state[pid] = 2

    for pid in protos:
        visit(pid, [])
    for es in o.get("elicitation_sessions", []):
        addressed.update(es.get("question_ids", []))
        for k in es["participants"]:
            if k not in stk:
                r.err(f"{es['id']}: unknown stakeholder {k}")
    for u in o.get("usability_tests", []):
        if u["prototype_id"] not in protos:
            r.err(f"{u['id']}: unknown prototype {u['prototype_id']}")
        for k in u["task_scenario_ids"]:
            if k not in scn:
                r.err(f"{u['id']}: unknown scenario {k}")
    for q in qs:
        if q not in addressed:
            r.err(f"{q}: no analysis, prototype task or elicitation session addresses this question")
    crit = {c["question_id"] for c in o.get("decision_criteria", [])}
    for q in qs:
        if q not in crit:
            r.err(f"{q}: missing decision_criteria (when is it feasible, infeasible, or a reason to change a requirement?)")
    for c in o.get("decision_criteria", []):
        if c["question_id"] not in qs:
            r.err(f"decision_criteria: unknown question {c['question_id']}")
    flagged = {x for q in o["feasibility_questions"] for x in q["requirement_ids"]}
    for rid, q in reqs.items():
        if q.get("tbd") and rid not in flagged:
            r.warn(f"{rid} is TBD but no feasibility question covers it")
    for res in o.get("results", []):
        if res["ref_id"] not in allids:
            r.err(f"results: unknown ref_id {res['ref_id']}")
    dup_ids(o["open_issues"], "open_issues", r)


def collect_ids(ws):
    ids = {}

    def add(name, items):
        for i in items or []:
            if "id" in i:
                ids[i["id"]] = name

    for name in L.artifact_names():
        o = L.load(ws, name)
        if not o:
            continue
        if name == "stakeholders": add(name, o.get("stakeholders"))
        if name == "lifecycle": add(name, o.get("phases"))
        if name == "scenarios": add(name, o.get("scenarios")); add(name, o.get("mission_requirements"))
        if name == "boundary":
            for k in ("external_systems", "interfaces", "controls", "boundary_decisions"):
                add(name, o.get(k))
        if name == "objectives": add(name, o.get("hierarchies")); add(name, o.get("nodes"))
        if name == "requirements": add(name, o.get("requirements"))
        if name == "feasibility-plan":
            for k in ("feasibility_questions", "analyses", "prototype_tasks", "usability_tests", "elicitation_sessions"):
                add(name, o.get(k))
    return ids


def v_feedback(o, ws, r):
    ids = collect_ids(ws)
    stk = ids.keys()
    dup_ids(o["items"], "items", r)
    for i in o["items"]:
        for t in i["targets"]:
            if t not in ids:
                r.err(f"{i['id']}: target {t} does not exist in any artifact")
        if i.get("from_stakeholder_id") and i["from_stakeholder_id"] not in stk:
            r.err(f"{i['id']}: unknown stakeholder {i['from_stakeholder_id']}")
        if i["disposition"] == "accepted" and not i.get("applied_in"):
            r.err(f"{i['id']}: accepted items must record applied_in (artifact and version)")
        if i["disposition"] in ("rejected", "deferred") and not i.get("rationale"):
            r.err(f"{i['id']}: {i['disposition']} items need a rationale")
        if i["disposition"] == "needs_clarification":
            r.warn(f"{i['id']}: still needs clarification")
    for a in o["approvals"]:
        for k in a["stakeholder_ids"]:
            if k not in stk:
                r.err(f"approval: unknown stakeholder {k}")
    if not o["approvals"]:
        r.warn("no approval decision recorded yet")
    stale = L.stale_report(ws)
    for s in stale:
        r.err(f"stale: {s['artifact']} was built from {s['upstream']} v{s['built_from_version']} but it is now v{s['current_version']}")
    dup_ids(o["open_issues"], "open_issues", r)


VALIDATORS = {
    "concept-brief": v_concept_brief, "stakeholders": v_stakeholders, "lifecycle": v_lifecycle,
    "scenarios": v_scenarios, "boundary": v_boundary, "objectives": v_objectives,
    "requirements": v_requirements, "feasibility-plan": v_feasibility, "feedback": v_feedback,
}


def validate_artifact(ws, name):
    r = Report()
    obj = L.load(ws, name)
    if obj is None:
        r.err(f"{name}.json does not exist")
        return r
    check_meta(obj, name, r)
    n_before = len(r.errors)
    check_schema(obj, name, r)
    if len(r.errors) == n_before:  # semantic checks assume schema-valid shape
        VALIDATORS[name](obj, ws, r)
        issues_check(obj, r)
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", default="./sysreq", help="project workspace folder (default ./sysreq)")
    ap.add_argument("--artifact", help="validate one artifact (e.g. stakeholders); default: all that exist")
    ap.add_argument("--require", default="", help="comma-separated upstream artifacts that must exist, be stamped and approved")
    args = ap.parse_args()
    ws = Path(args.workspace)
    missing = []
    for name in [x.strip() for x in args.require.split(",") if x.strip()]:
        if name not in L.artifact_names():
            L.fail(f"unknown artifact '{name}'. Known: {', '.join(L.artifact_names())}", 2)
        obj = L.load(ws, name)
        sk = L.skill_for(name)["skill"]
        if obj is None:
            missing.append({"artifact": name, "problem": "missing", "run_first": sk})
        elif L.version_of(obj) < 1:
            missing.append({"artifact": name, "problem": "not finished (never stamped)", "run_first": sk})
        elif L.meta_of(obj).get("status") != "approved":
            missing.append({"artifact": name, "problem": "not approved", "run_first": sk})
    names = [args.artifact] if args.artifact else [n for n in L.artifact_names() if L.load(ws, n) is not None]
    for n in names:
        if n not in VALIDATORS:
            L.fail(f"unknown artifact '{n}'. Known: {', '.join(VALIDATORS)}", 2)
    results = []
    for n in names:
        rep = validate_artifact(ws, n)
        results.append({"artifact": n, "ok": not rep.errors, "errors": rep.errors, "warnings": rep.warnings})
    stale = L.stale_report(ws)
    ok = all(x["ok"] for x in results) and not missing
    L.emit({"ok": ok, "results": results, "stale": stale, "missing_required": missing})
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
