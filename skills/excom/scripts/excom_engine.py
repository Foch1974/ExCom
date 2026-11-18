#!/usr/bin/env python3
"""ExCom v2.0 — Project Control Tower & Cross-Perimeter Contagion Engine.

Zero-dependency Python 3.8+ standard-library CLI engine for:
  1. Initializing persistent project workspaces (`project-state.json` + `events-bus.jsonl`)
  2. Computing CPM (Critical Path Method) + PERT 3-point schedules & float/slack erosion
  3. Computing Earned Value Management (EVM: BAC, PV, EV, AC, CPI, SPI, EAC, VAC)
  4. Propagating Cross-Perimeter Contagion & Upstream Early-Warning Alerts across all 25 ExCom seats
  5. Rendering a self-contained interactive HTML Executive Cockpit (`dashboard.html`) + CSV exports
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import math
from pathlib import Path
import sys
import uuid
from typing import Any, Dict, List, Optional, Tuple


SCHEMA_VERSION = "2.0.0"

DEFAULT_DOMAIN_COUPLINGS: Dict[str, List[str]] = {
    "COST": ["CFO", "CRO-Risk", "PMO"],
    "SCHEDULE": ["PMO", "COO", "CHRO"],
    "LEGAL": ["CLO", "CCO-Compliance", "CRO-Risk"],
    "COMPLIANCE": ["CCO-Compliance", "CLO", "CISO"],
    "VENDOR": ["COO", "CPO", "CLO", "CISO", "CFO"],
    "TECH": ["CTO", "CIO", "CISO", "CAIO", "CFO"],
    "DATA_AI": ["CDO-Data", "CAIO", "CISO", "CCO-Compliance"],
    "MARKET": ["CMO", "CRO-Revenue", "CCO-Commercial", "CPO", "COO"],
    "HUMAN": ["CHRO", "COO", "CXO"],
    "RISK": ["CRO-Risk", "CFO", "CLO", "PMO"],
    "ESG": ["CSO-Sustainability", "CCO-Compliance", "COO"],
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s[:10])


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_event(project_dir: Path, event: Dict[str, Any]) -> None:
    bus_path = project_dir / "events-bus.jsonl"
    bus_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}", "timestamp": now_iso(), **event}
    with bus_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def pert_duration(task: Dict[str, Any], use_forecast: bool = True) -> Tuple[float, float]:
    o = task.get("optimistic_days")
    m = task.get("likely_days")
    p = task.get("pessimistic_days")
    base = float(task.get("duration_days", m if m is not None else 5.0))
    if o is not None and m is not None and p is not None:
        expected = round((float(o) + 4.0 * float(m) + float(p)) / 6.0, 1)
        sigma = round(max(0.0, (float(p) - float(o)) / 6.0), 2)
    else:
        expected = round(base, 1)
        sigma = round(expected * 0.15, 2)

    if use_forecast and task.get("forecast_days") is not None:
        return round(float(task["forecast_days"]), 1), sigma
    return expected, sigma


def topological_sort(tasks: List[Dict[str, Any]]) -> List[str]:
    by_id = {t["id"]: t for t in tasks}
    in_deg = {t["id"]: 0 for t in tasks}
    succ: Dict[str, List[str]] = {t["id"]: [] for t in tasks}

    for t in tasks:
        for dep in t.get("depends_on", []):
            if dep in by_id:
                in_deg[t["id"]] += 1
                succ[dep].append(t["id"])

    queue = [tid for tid, d in in_deg.items() if d == 0]
    order: List[str] = []
    while queue:
        curr = queue.pop(0)
        order.append(curr)
        for nxt in succ[curr]:
            in_deg[nxt] -= 1
            if in_deg[nxt] == 0:
                queue.append(nxt)

    if len(order) != len(tasks):
        missing = [t["id"] for t in tasks if t["id"] not in order]
        raise ValueError(f"Dependency cycle detected among tasks: {missing}")
    return order


def compute_schedule_and_evm(state: Dict[str, Any], as_of_str: Optional[str] = None) -> Dict[str, Any]:
    start_dt = parse_date(state.get("start_date", dt.date.today().isoformat()))
    as_of = parse_date(as_of_str) if as_of_str else parse_date(state.get("as_of_date", start_dt.isoformat()))
    tasks = state.get("tasks", [])
    by_id = {t["id"]: t for t in tasks}
    order = topological_sort(tasks)

    # 1. Baseline schedule pass (without forecast overrides)
    base_es: Dict[str, float] = {}
    base_ef: Dict[str, float] = {}
    base_dur_map: Dict[str, float] = {}
    for tid in order:
        t = by_id[tid]
        b_dur, _ = pert_duration(t, use_forecast=False)
        base_dur_map[tid] = b_dur
        deps = [d for d in t.get("depends_on", []) if d in by_id]
        es = max((base_ef[d] for d in deps), default=0.0)
        base_es[tid] = round(es, 1)
        base_ef[tid] = round(es + b_dur, 1)

    baseline_project_days = round(max(base_ef.values(), default=0.0), 1)

    # 2. Live / Forecast CPM forward pass
    es_map: Dict[str, float] = {}
    ef_map: Dict[str, float] = {}
    dur_map: Dict[str, float] = {}
    sigma_map: Dict[str, float] = {}
    succ_map: Dict[str, List[str]] = {tid: [] for tid in order}

    for tid in order:
        t = by_id[tid]
        dur, sig = pert_duration(t, use_forecast=True)
        dur_map[tid] = dur
        sigma_map[tid] = sig
        deps = [d for d in t.get("depends_on", []) if d in by_id]
        for d in deps:
            succ_map[d].append(tid)
        es = max((ef_map[d] for d in deps), default=0.0)
        es_map[tid] = round(es, 1)
        ef_map[tid] = round(es + dur, 1)

    live_project_days = round(max(ef_map.values(), default=0.0), 1)

    # 3. Backward pass for LF, LS, Total Float & Critical Path
    lf_map: Dict[str, float] = {}
    ls_map: Dict[str, float] = {}
    float_map: Dict[str, float] = {}

    for tid in reversed(order):
        succs = succ_map[tid]
        lf = min((ls_map[s] for s in succs), default=live_project_days)
        ls = lf - dur_map[tid]
        lf_map[tid] = round(lf, 1)
        ls_map[tid] = round(ls, 1)
        float_map[tid] = round(max(0.0, lf - ef_map[tid]), 1)

    critical_path: List[str] = []
    crit_sigma_sq = 0.0

    # Enrich tasks & compute EVM
    bac = 0.0
    pv = 0.0
    ev = 0.0
    ac = 0.0
    committed_total = 0.0

    for tid in order:
        t = by_id[tid]
        is_crit = float_map[tid] <= 0.05 and dur_map[tid] > 0
        if is_crit:
            critical_path.append(tid)
            crit_sigma_sq += sigma_map[tid] ** 2

        p_start = start_dt + dt.timedelta(days=int(round(base_es[tid])))
        p_end = start_dt + dt.timedelta(days=int(round(base_ef[tid])))
        f_start = start_dt + dt.timedelta(days=int(round(es_map[tid])))
        f_end = start_dt + dt.timedelta(days=int(round(ef_map[tid])))
        slip_days = round(ef_map[tid] - base_ef[tid], 1)
        own_slip_days = round(dur_map[tid] - base_dur_map[tid], 1)
        inherited_delay_days = round(es_map[tid] - base_es[tid], 1)

        progress = float(t.get("progress_pct", 0.0))
        if t.get("status") == "DONE":
            progress = 100.0
            t["progress_pct"] = 100.0

        planned_cost = float(t.get("planned_budget", 0.0))
        actual_cost = float(t.get("actual_cost", 0.0))
        committed_cost = max(actual_cost, float(t.get("committed_cost", actual_cost)))

        # Planned value pro-rata as of `as_of`
        if as_of >= p_end:
            pv_ratio = 1.0
        elif as_of <= p_start:
            pv_ratio = 0.0
        else:
            span = max(1, (p_end - p_start).days)
            pv_ratio = min(1.0, max(0.0, (as_of - p_start).days / span))

        bac += planned_cost
        pv += planned_cost * pv_ratio
        ev += planned_cost * (progress / 100.0)
        ac += actual_cost
        committed_total += committed_cost

        is_overdue = (as_of > f_end) and (progress < 100.0)

        t["computed"] = {
            "baseline_es": base_es[tid],
            "baseline_ef": base_ef[tid],
            "es": es_map[tid],
            "ef": ef_map[tid],
            "ls": ls_map[tid],
            "lf": lf_map[tid],
            "duration_days": dur_map[tid],
            "sigma_days": sigma_map[tid],
            "total_float_days": float_map[tid],
            "is_critical": is_crit,
            "planned_start": p_start.isoformat(),
            "planned_end": p_end.isoformat(),
            "forecast_start": f_start.isoformat(),
            "forecast_end": f_end.isoformat(),
            "slip_days": slip_days,
            "own_slip_days": own_slip_days,
            "inherited_delay_days": inherited_delay_days,
            "is_overdue": is_overdue,
            "committed_cost": round(committed_cost, 2),
            "cost_variance": round((planned_cost * (progress / 100.0)) - actual_cost, 2) if ac > 0 else 0.0,
            "budget_overrun_eur": round(max(0.0, committed_cost - planned_cost), 2),
        }

    # Include recurring/overhead budget lines in global budget rollup
    recurring_annual = sum(float(r.get("annual_eur", 0.0)) for r in state.get("recurring_opex", []))
    contingency_pct = float(state.get("contingency_pct", 15.0))
    contingency_eur = round(bac * (contingency_pct / 100.0), 2)

    cpi = round(ev / ac, 2) if ac > 0 else 1.0
    spi = round(ev / pv, 2) if pv > 0 else 1.0
    if ac > 0 and ev > 0:
        eac = round(bac / cpi, 2)
    else:
        eac = round(max(bac, committed_total), 2)
    vac = round(bac - eac, 2)
    denom_tcpi = bac - ac
    tcpi = round((bac - ev) / denom_tcpi, 2) if denom_tcpi > 0 else 1.0

    p85_buffer_days = round(1.04 * math.sqrt(crit_sigma_sq), 1)
    project_slip_days = round(live_project_days - baseline_project_days, 1)

    overall_pct = round((ev / bac) * 100.0, 1) if bac > 0 else round(
        sum(float(t.get("progress_pct", 0.0)) for t in tasks) / max(1, len(tasks)), 1
    )

    state["metrics"] = {
        "as_of_date": as_of.isoformat(),
        "baseline_duration_days": baseline_project_days,
        "forecast_duration_days": live_project_days,
        "p85_duration_days": round(live_project_days + p85_buffer_days, 1),
        "project_slip_days": project_slip_days,
        "baseline_end_date": (start_dt + dt.timedelta(days=int(round(baseline_project_days)))).isoformat(),
        "forecast_end_date": (start_dt + dt.timedelta(days=int(round(live_project_days)))).isoformat(),
        "critical_path": critical_path,
        "overall_progress_pct": overall_pct,
        "evm": {
            "bac_eur": round(bac, 2),
            "contingency_eur": contingency_eur,
            "total_envelope_eur": round(bac + contingency_eur, 2),
            "committed_eur": round(committed_total, 2),
            "pv_eur": round(pv, 2),
            "ev_eur": round(ev, 2),
            "ac_eur": round(ac, 2),
            "cpi": cpi,
            "spi": spi,
            "eac_eur": eac,
            "vac_eur": vac,
            "tcpi": tcpi,
            "recurring_annual_opex_eur": round(recurring_annual, 2),
        },
    }
    return state


def run_contagion_radar(state: Dict[str, Any], project_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Detects upstream schedule/cost/scope drifts and populates cross-director alerts."""
    existing_alerts: List[Dict[str, Any]] = state.setdefault("alerts", [])
    existing_fps = {a.get("fingerprint") for a in existing_alerts if a.get("status") == "OPEN"}

    tasks = state.get("tasks", [])
    by_id = {t["id"]: t for t in tasks}
    new_alerts: List[Dict[str, Any]] = []

    def register_alert(
        fingerprint: str,
        severity: str,
        category: str,
        source_seat: str,
        target_seats: List[str],
        title: str,
        upstream_cause: str,
        preventive_action: str,
        task_id: Optional[str] = None,
    ) -> None:
        if fingerprint in existing_fps:
            return
        clean_targets = sorted({s for s in target_seats if s and s != source_seat}) or ["PMO"]
        alert = {
            "id": f"ALT-{uuid.uuid4().hex[:6].upper()}",
            "fingerprint": fingerprint,
            "created_at": now_iso(),
            "status": "OPEN",
            "severity": severity,
            "category": category,
            "task_id": task_id,
            "source_seat": source_seat,
            "target_seats": clean_targets,
            "title": title,
            "upstream_cause": upstream_cause,
            "preventive_action": preventive_action,
        }
        existing_alerts.append(alert)
        existing_fps.add(fingerprint)
        new_alerts.append(alert)
        if project_dir is not None:
            append_event(
                project_dir,
                {
                    "type": "CONTAGION_ALERT_RAISED",
                    "alert_id": alert["id"],
                    "severity": severity,
                    "source_seat": source_seat,
                    "target_seats": clean_targets,
                    "title": title,
                },
            )

    # Build transitive downstream map for root-cause contagion attribution
    adj: Dict[str, List[str]] = {t["id"]: [] for t in tasks}
    for t in tasks:
        for dep in t.get("depends_on", []):
            if dep in adj:
                adj[dep].append(t["id"])

    def transitive_downstream(start_tid: str) -> List[str]:
        seen: List[str] = []
        stack = list(adj.get(start_tid, []))
        while stack:
            cur = stack.pop(0)
            if cur not in seen:
                seen.append(cur)
                stack.extend(adj.get(cur, []))
        return seen

    # 1. Task-level Root-Cause Schedule Slip, Overdue & Downstream Cross-Perimeter Contagion
    for t in tasks:
        comp = t.get("computed", {})
        tid = t["id"]
        owner = t.get("owner_seat", "PMO")
        own_slip = float(comp.get("own_slip_days", 0.0))
        overrun = float(comp.get("budget_overrun_eur", 0.0))
        planned_b = float(t.get("planned_budget", 0.0))

        # Propagate ROOT-CAUSE duration slip transitively to all downstream Directors
        if own_slip >= 1.5:
            desc_ids = transitive_downstream(tid)
            downstream_seats: List[str] = []
            for d_id in desc_ids:
                other = by_id[d_id]
                downstream_seats.append(other.get("owner_seat", "PMO"))
                for c_seat in other.get("coupled_seats", {}).keys():
                    downstream_seats.append(c_seat)
            severity = "CRITICAL" if comp.get("is_critical") else "WARNING"
            cascade_desc = ", ".join(f"{d_id} ({by_id[d_id].get('owner_seat', 'PMO')})" for d_id in desc_ids) or "Clôture projet"
            register_alert(
                fingerprint=f"ROOT_SLIP:{tid}:{int(round(own_slip))}",
                severity=severity,
                category="SCHEDULE",
                source_seat=owner,
                target_seats=downstream_seats + ["PMO", "COO"],
                task_id=tid,
                title=f"Contagion planning amont depuis {tid} (+{own_slip}j) → cascade sur {cascade_desc}",
                upstream_cause=f"Le chantier source '{t['name']}' ({owner}) s'allonge de +{own_slip}j ({'Chemin Critique : décalage direct de la date de fin' if comp.get('is_critical') else 'Érosion de marge libre'}).",
                preventive_action="Anticiper dès maintenant les prérequis des Directeurs aval impactés (pré-remplissage KYC/statuts/scripts) pour absorber le glissement sans retarder le Go-Live.",
            )

        if comp.get("is_overdue"):
            register_alert(
                fingerprint=f"OVERDUE:{tid}",
                severity="CRITICAL" if comp.get("is_critical") else "WARNING",
                category="SCHEDULE",
                source_seat=owner,
                target_seats=["PMO", "COO"] + list(t.get("coupled_seats", {}).keys()),
                task_id=tid,
                title=f"Échéance dépassée sur {tid} ({t['name']})",
                upstream_cause=f"Date cible {comp.get('forecast_end')} dépassée à {t.get('progress_pct', 0)}% d'avancement.",
                preventive_action=f"Convoquer un CoPil flash PMO + {owner} pour débloquer ou re-séquencer.",
            )

        # Cost / Commitment overrun contagion -> CFO + CRO-Risk + coupled seats
        if overrun > 0 and (planned_b == 0 or (overrun / max(1.0, planned_b)) >= 0.10):
            pct = round((overrun / planned_b) * 100.0, 1) if planned_b > 0 else 100.0
            sev = "CRITICAL" if pct >= 25.0 else "WARNING"
            register_alert(
                fingerprint=f"COST:{tid}:{int(overrun)}",
                severity=sev,
                category="COST",
                source_seat=owner,
                target_seats=["CFO", "CRO-Risk", "PMO"] + list(t.get("coupled_seats", {}).keys()),
                task_id=tid,
                title=f"Dépassement budgétaire amont sur {tid} (+{overrun:,.0f} € / +{pct}%)",
                upstream_cause=f"Coût engagé/réel ({comp.get('committed_cost'):,.0f} €) supérieur à l'enveloppe votée ({planned_b:,.0f} €) sur '{t['name']}'.",
                preventive_action="Audit CFO immédiat sur l'enveloppe de contingence et vérification des Kill Criteria avec CRO-Risk.",
            )

        # Blocked status contagion
        if t.get("status") == "BLOCKED":
            register_alert(
                fingerprint=f"BLOCKED:{tid}",
                severity="CRITICAL",
                category="RISK",
                source_seat=owner,
                target_seats=["PMO", "CEO", "COO"] + list(t.get("coupled_seats", {}).keys()),
                task_id=tid,
                title=f"Blocage critique déclaré sur {tid} ({t['name']})",
                upstream_cause=t.get("notes", "Blocage opérationnel signalé par le porteur."),
                preventive_action="Escalade immédiate aux Directeurs couplés et arbitrage CEO si verrou externe.",
            )

    # 2. Global EVM CPI / SPI drift check
    evm = state.get("metrics", {}).get("evm", {})
    if evm.get("ac_eur", 0) > 0 and evm.get("cpi", 1.0) < 0.90:
        register_alert(
            fingerprint=f"EVM_CPI:{evm['cpi']}",
            severity="CRITICAL" if evm["cpi"] < 0.80 else "WARNING",
            category="COST",
            source_seat="PMO",
            target_seats=["CFO", "CRO-Risk", "CEO"],
            title=f"Alerte EVM : Efficience budgétaire dégradée (CPI = {evm['cpi']})",
            upstream_cause=f"Projection finale EAC à {evm['eac_eur']:,.0f} € contre un budget BAC de {evm['bac_eur']:,.0f} €.",
            preventive_action="Gel des engagements non critiques par le CFO et revue de périmètre CPO/COO.",
        )

    # Update overall RAG health
    open_alerts = [a for a in existing_alerts if a.get("status") == "OPEN"]
    if any(a.get("severity") == "CRITICAL" for a in open_alerts):
        state["overall_rag"] = "RED"
    elif any(a.get("severity") == "WARNING" for a in open_alerts):
        state["overall_rag"] = "AMBER"
    else:
        state["overall_rag"] = "GREEN"

    return new_alerts


def export_csvs(project_dir: Path, state: Dict[str, Any]) -> None:
    exp_dir = project_dir / "exports"
    exp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Schedule & CPM Gantt CSV
    with (exp_dir / "gantt_schedule.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "Task_ID", "Phase", "Name", "Owner_Seat", "Status", "Progress_Pct",
            "Depends_On", "Planned_Start", "Planned_End", "Forecast_Start",
            "Forecast_End", "Duration_Days", "Float_Days", "Is_Critical", "Slip_Days", "Hard_Gate"
        ])
        for t in state.get("tasks", []):
            c = t.get("computed", {})
            w.writerow([
                t["id"], t.get("phase", ""), t["name"], t.get("owner_seat", ""),
                t.get("status", "TODO"), t.get("progress_pct", 0),
                "|".join(t.get("depends_on", [])),
                c.get("planned_start", ""), c.get("planned_end", ""),
                c.get("forecast_start", ""), c.get("forecast_end", ""),
                c.get("duration_days", 0), c.get("total_float_days", 0),
                c.get("is_critical", False), c.get("slip_days", 0),
                t.get("hard_gate", ""),
            ])

    # 2. Budget & EVM CSV
    with (exp_dir / "budget_evm.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Task_ID", "Name", "Owner_Seat", "Planned_EUR", "Committed_EUR", "Actual_EUR", "Overrun_EUR"])
        for t in state.get("tasks", []):
            c = t.get("computed", {})
            w.writerow([
                t["id"], t["name"], t.get("owner_seat", ""),
                t.get("planned_budget", 0), c.get("committed_cost", 0),
                t.get("actual_cost", 0), c.get("budget_overrun_eur", 0),
            ])

    # 3. Alerts & Contagion CSV
    with (exp_dir / "contagion_alerts.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Alert_ID", "Status", "Severity", "Category", "Source_Seat", "Target_Seats", "Task_ID", "Title", "Preventive_Action"])
        for a in state.get("alerts", []):
            w.writerow([
                a["id"], a.get("status", "OPEN"), a.get("severity", ""),
                a.get("category", ""), a.get("source_seat", ""),
                "|".join(a.get("target_seats", [])), a.get("task_id", ""),
                a.get("title", ""), a.get("preventive_action", ""),
            ])


def render_dashboard_html(project_dir: Path, state: Dict[str, Any]) -> Path:
    m = state.get("metrics", {})
    evm = m.get("evm", {})
    tasks = state.get("tasks", [])
    alerts = state.get("alerts", [])
    open_alerts = [a for a in alerts if a.get("status") == "OPEN"]
    guardrails = state.get("guardrails", [])
    kill_criteria = state.get("kill_criteria", [])
    deliverables = state.get("deliverables", [])

    total_days = max(1.0, float(m.get("forecast_duration_days", 1.0)), float(m.get("baseline_duration_days", 1.0)))
    rag = state.get("overall_rag", "GREEN")
    rag_color = {"GREEN": "#10b981", "AMBER": "#f59e0b", "RED": "#ef4444"}.get(rag, "#38bdf8")

    # Collect unique seats for interactive filter
    seats = sorted({
        t.get("owner_seat", "PMO") for t in tasks
    } | {
        s for a in open_alerts for s in a.get("target_seats", [])
    } | {
        a.get("source_seat", "PMO") for a in open_alerts
    })

    seat_buttons = ['<button class="chip active" onclick="filterSeat(\'ALL\', this)">Tous (360°)</button>']
    for s in seats:
        esc = html.escape(s)
        seat_buttons.append(f'<button class="chip" onclick="filterSeat(\'{esc}\', this)">{esc}</button>')

    # Build Gantt rows
    gantt_rows = []
    for t in tasks:
        c = t.get("computed", {})
        left_pct = round((float(c.get("es", 0.0)) / total_days) * 100.0, 2)
        width_pct = max(2.5, round((float(c.get("duration_days", 1.0)) / total_days) * 100.0, 2))
        base_left = round((float(c.get("baseline_es", 0.0)) / total_days) * 100.0, 2)
        base_width = max(2.0, round((float(c.get("baseline_ef", 1.0)) - float(c.get("baseline_es", 0.0))) / total_days * 100.0, 2))
        prog = float(t.get("progress_pct", 0.0))
        is_crit = c.get("is_critical", False)
        bar_cls = "gantt-bar crit" if is_crit else "gantt-bar norm"
        if t.get("status") == "DONE":
            bar_cls = "gantt-bar done"
        coupled = list(t.get("coupled_seats", {}).keys())
        seat_tags = " ".join([t.get("owner_seat", "PMO")] + coupled)
        slip_badge = f'<span class="badge red">+{c.get("slip_days")}j</span>' if float(c.get("slip_days", 0)) > 0 else ""
        crit_badge = '<span class="badge crit-b">CRITIQUE</span>' if is_crit else f'<span class="badge muted">Marge {c.get("total_float_days")}j</span>'

        gantt_rows.append(f"""
        <div class="gantt-row seat-item" data-seats="{html.escape(seat_tags)}">
          <div class="gantt-meta">
            <div class="gantt-title"><strong>{html.escape(t['id'])}</strong> — {html.escape(t['name'])}</div>
            <div class="gantt-sub">
              <span class="seat-pill">{html.escape(t.get('owner_seat', 'PMO'))}</span>
              {crit_badge} {slip_badge}
              <span class="dates">{html.escape(c.get('forecast_start', ''))} → {html.escape(c.get('forecast_end', ''))}</span>
            </div>
          </div>
          <div class="gantt-track">
            <div class="gantt-baseline" style="left:{base_left}%;width:{base_width}%" title="Baseline initiale"></div>
            <div class="{bar_cls}" style="left:{left_pct}%;width:{width_pct}%">
              <div class="gantt-fill" style="width:{prog}%"></div>
              <span class="gantt-label">{int(prog)}%</span>
            </div>
          </div>
        </div>""")

    # Build Contagion Alerts cards
    alert_cards = []
    for a in reversed(open_alerts):
        sev = a.get("severity", "INFO")
        sev_cls = {"CRITICAL": "al-crit", "WARNING": "al-warn", "INFO": "al-info"}.get(sev, "al-info")
        targets = a.get("target_seats", [])
        seat_tags = " ".join([a.get("source_seat", "")] + targets)
        target_pills = " ".join(f'<span class="seat-pill target">→ {html.escape(ts)}</span>' for ts in targets)
        alert_cards.append(f"""
        <div class="alert-card {sev_cls} seat-item" data-seats="{html.escape(seat_tags)}">
          <div class="alert-head">
            <span class="badge {'red' if sev == 'CRITICAL' else 'amber'}">{html.escape(sev)} · {html.escape(a.get('category', ''))}</span>
            <span class="seat-pill">Source : {html.escape(a.get('source_seat', ''))}</span>
            {target_pills}
            <span class="muted-id">{html.escape(a['id'])}</span>
          </div>
          <h4>{html.escape(a.get('title', ''))}</h4>
          <p><strong>Origine amont :</strong> {html.escape(a.get('upstream_cause', ''))}</p>
          <p class="action-line"><strong>Parade inter-périmètres requise :</strong> {html.escape(a.get('preventive_action', ''))}</p>
        </div>""")
    if not alert_cards:
        alert_cards.append('<div class="empty-ok">Aucune alerte de contagion inter-périmètres ouverte — tous les couplages Directeurs sont au vert.</div>')

    # Budget table rows
    budget_rows = []
    for t in tasks:
        c = t.get("computed", {})
        planned = float(t.get("planned_budget", 0.0))
        committed = float(c.get("committed_cost", 0.0))
        actual = float(t.get("actual_cost", 0.0))
        over = float(c.get("budget_overrun_eur", 0.0))
        over_html = f'<span class="badge red">+{over:,.0f} €</span>' if over > 0 else '<span class="badge green">OK</span>'
        budget_rows.append(f"""
        <tr class="seat-item" data-seats="{html.escape(t.get('owner_seat', 'PMO'))} CFO">
          <td><strong>{html.escape(t['id'])}</strong> — {html.escape(t['name'])}</td>
          <td><span class="seat-pill">{html.escape(t.get('owner_seat', 'PMO'))}</span></td>
          <td class="num">{planned:,.0f} €</td>
          <td class="num">{committed:,.0f} €</td>
          <td class="num">{actual:,.0f} €</td>
          <td>{over_html}</td>
        </tr>""")

    # Guardrails & Kill Criteria
    gr_items = []
    for g in guardrails:
        st = g.get("status", "LOCKED")
        cls = "green" if st in ("VERIFIED", "ACTIVE", "LOCKED") else "amber"
        gr_items.append(f"""
        <li class="seat-item" data-seats="{html.escape(g.get('seat', 'PMO'))}">
          <span class="seat-pill">{html.escape(g.get('seat', ''))}</span>
          <span class="badge {cls}">{html.escape(st)}</span>
          {html.escape(g.get('rule', ''))}
        </li>""")

    kc_items = []
    for k in kill_criteria:
        st = k.get("status", "ARMED")
        cls = "red" if st == "TRIGGERED" else "crit-b"
        kc_items.append(f"""
        <li class="seat-item" data-seats="{html.escape(k.get('owner_seat', 'CRO-Risk'))} CEO PMO">
          <span class="badge {cls}">{html.escape(st)}</span>
          <strong>{html.escape(k.get('phase', ''))} :</strong> {html.escape(k.get('trigger', ''))}
          <em>→ {html.escape(k.get('action', ''))}</em>
        </li>""")

    deliv_items = []
    for d in deliverables:
        deliv_items.append(f"""
        <li class="seat-item" data-seats="{html.escape(d.get('seat', 'PMO'))}">
          <span class="seat-pill">{html.escape(d.get('seat', ''))}</span>
          <strong>{html.escape(d.get('title', ''))}</strong> — <code>{html.escape(d.get('path', ''))}</code>
          <span class="dates">({html.escape(d.get('summary', ''))})</span>
        </li>""")

    doc = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>ExCom Control Tower — {html.escape(state.get('project_name', 'Projet'))}</title>
<style>
  :root {{
    --bg: #0b1120; --panel: #111827; --panel2: #1e293b; --border: #334155;
    --text: #f8fafc; --muted: #94a3b8; --accent: #38bdf8;
    --green: #10b981; --amber: #f59e0b; --red: #ef4444; --crit: #f43f5e;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background: var(--bg); color: var(--text); line-height: 1.5; padding: 24px; }}
  .container {{ max-width: 1320px; margin: 0 auto; }}
  header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; border-bottom: 1px solid var(--border); padding-bottom: 18px; margin-bottom: 22px; flex-wrap: wrap; }}
  h1 {{ margin: 0 0 6px 0; font-size: 1.55rem; }}
  .rag-pill {{ padding: 8px 16px; border-radius: 999px; font-weight: 700; background: {rag_color}22; color: {rag_color}; border: 1px solid {rag_color}; }}
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(195px, 1fr)); gap: 14px; margin-bottom: 22px; }}
  .kpi {{ background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; }}
  .kpi .lbl {{ font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }}
  .kpi .val {{ font-size: 1.45rem; font-weight: 700; margin-top: 4px; }}
  .kpi .sub {{ font-size: 0.8rem; color: var(--muted); margin-top: 3px; }}
  .filter-bar {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 22px; background: var(--panel); padding: 12px 16px; border-radius: 12px; border: 1px solid var(--border); }}
  .chip {{ background: var(--panel2); color: var(--text); border: 1px solid var(--border); border-radius: 999px; padding: 5px 12px; cursor: pointer; font-size: 0.82rem; }}
  .chip.active {{ background: var(--accent); color: #0f172a; border-color: var(--accent); font-weight: 700; }}
  section {{ background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 18px 20px; margin-bottom: 20px; }}
  section h2 {{ margin: 0 0 14px 0; font-size: 1.1rem; color: var(--accent); display: flex; justify-content: space-between; align-items: center; }}
  .gantt-row {{ display: grid; grid-template-columns: 380px 1fr; gap: 16px; align-items: center; padding: 10px 0; border-bottom: 1px solid #1e293b; }}
  @media (max-width: 860px) {{ .gantt-row {{ grid-template-columns: 1fr; }} }}
  .gantt-title {{ font-size: 0.92rem; }}
  .gantt-sub {{ display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-top: 4px; font-size: 0.78rem; color: var(--muted); }}
  .gantt-track {{ position: relative; height: 30px; background: #0f172a; border-radius: 8px; border: 1px solid #1e293b; overflow: hidden; }}
  .gantt-baseline {{ position: absolute; top: 4px; height: 5px; background: #64748b88; border-radius: 3px; }}
  .gantt-bar {{ position: absolute; top: 11px; height: 15px; border-radius: 5px; overflow: hidden; display: flex; align-items: center; }}
  .gantt-bar.crit {{ background: #f43f5e33; border: 1px solid var(--crit); }}
  .gantt-bar.norm {{ background: #38bdf833; border: 1px solid var(--accent); }}
  .gantt-bar.done {{ background: #10b98133; border: 1px solid var(--green); }}
  .gantt-fill {{ height: 100%; background: currentColor; opacity: 0.45; }}
  .gantt-bar.crit .gantt-fill {{ background: var(--crit); }}
  .gantt-bar.norm .gantt-fill {{ background: var(--accent); }}
  .gantt-bar.done .gantt-fill {{ background: var(--green); }}
  .gantt-label {{ position: relative; z-index: 2; padding-left: 6px; font-size: 0.7rem; font-weight: 700; }}
  .seat-pill {{ background: #1e293b; border: 1px solid #475569; color: #e2e8f0; padding: 2px 8px; border-radius: 6px; font-size: 0.74rem; font-weight: 600; }}
  .seat-pill.target {{ background: #38bdf822; border-color: var(--accent); color: var(--accent); }}
  .badge {{ padding: 2px 7px; border-radius: 5px; font-size: 0.72rem; font-weight: 700; }}
  .badge.red {{ background: #ef444428; color: #fca5a5; border: 1px solid var(--red); }}
  .badge.amber {{ background: #f59e0b28; color: #fcd34d; border: 1px solid var(--amber); }}
  .badge.green {{ background: #10b98128; color: #6ee7b7; border: 1px solid var(--green); }}
  .badge.crit-b {{ background: #f43f5e28; color: #fda4af; border: 1px solid var(--crit); }}
  .badge.muted {{ background: #1e293b; color: var(--muted); }}
  .alert-card {{ border-radius: 10px; padding: 13px 15px; margin-bottom: 12px; background: #0f172a; border-left: 4px solid var(--accent); }}
  .alert-card.al-crit {{ border-left-color: var(--red); background: #ef444410; }}
  .alert-card.al-warn {{ border-left-color: var(--amber); background: #f59e0b10; }}
  .alert-head {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 6px; }}
  .alert-card h4 {{ margin: 4px 0 6px 0; font-size: 0.96rem; }}
  .alert-card p {{ margin: 4px 0; font-size: 0.86rem; color: #cbd5e1; }}
  .action-line {{ color: #f8fafc !important; }}
  .muted-id {{ margin-left: auto; font-size: 0.75rem; color: var(--muted); font-family: monospace; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid #1e293b; }}
  th {{ color: var(--muted); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; }}
  td.num {{ font-variant-numeric: tabular-nums; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
  @media (max-width: 900px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
  ul.clean {{ list-style: none; padding: 0; margin: 0; }}
  ul.clean li {{ padding: 8px 0; border-bottom: 1px solid #1e293b; font-size: 0.87rem; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
  .empty-ok {{ padding: 14px; border-radius: 8px; background: #10b98115; border: 1px solid var(--green); color: #6ee7b7; font-size: 0.9rem; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>ExCom 360° Control Tower — {html.escape(state.get('project_name', ''))}</h1>
      <div style="color:var(--muted);font-size:0.88rem;">
        Décision verrouillée : {html.escape(state.get('locked_decision', ''))} · Point arrêté au <strong>{html.escape(m.get('as_of_date', ''))}</strong>
      </div>
    </div>
    <div class="rag-pill">STATUT GLOBAL : {html.escape(rag)} · {len(open_alerts)} Alerte(s) Active(s)</div>
  </header>

  <div class="kpis">
    <div class="kpi">
      <div class="lbl">Avancement Pondéré (EV)</div>
      <div class="val">{m.get('overall_progress_pct', 0)}%</div>
      <div class="sub">SPI Planning : <strong>{evm.get('spi', 1.0)}</strong></div>
    </div>
    <div class="kpi">
      <div class="lbl">Horizon & Chemin Critique</div>
      <div class="val">{m.get('forecast_duration_days', 0)} j</div>
      <div class="sub">Fin prévue : {html.escape(m.get('forecast_end_date', ''))} (P85: {m.get('p85_duration_days', 0)}j)</div>
    </div>
    <div class="kpi">
      <div class="lbl">Budget CAPEX Amorçage (BAC)</div>
      <div class="val">{evm.get('bac_eur', 0):,.0f} €</div>
      <div class="sub">+ Contingence : {evm.get('contingency_eur', 0):,.0f} € · Engagé : {evm.get('committed_eur', 0):,.0f} €</div>
    </div>
    <div class="kpi">
      <div class="lbl">Efficience Coûts (CPI / EAC)</div>
      <div class="val">CPI {evm.get('cpi', 1.0)}</div>
      <div class="sub">Atterrissage EAC : {evm.get('eac_eur', 0):,.0f} € · OPEX/an : {evm.get('recurring_annual_opex_eur', 0):,.0f} €</div>
    </div>
    <div class="kpi">
      <div class="lbl">Contagion Inter-Périmètres</div>
      <div class="val">{len(open_alerts)}</div>
      <div class="sub">Chemin critique : {html.escape(' → '.join(m.get('critical_path', [])))}</div>
    </div>
  </div>

  <div class="filter-bar">
    <span style="font-size:0.84rem;color:var(--muted);font-weight:600;">Filtrer par Directeur / Périmètre :</span>
    {''.join(seat_buttons)}
  </div>

  <section>
    <h2><span>Radar d'Alertes &amp; Contagion Amont Inter-Directeurs</span><span style="font-size:0.8rem;color:var(--muted);">Propagation temps réel</span></h2>
    {''.join(alert_cards)}
  </section>

  <section>
    <h2><span>Rétroplanning Gantt CPM &amp; Marges (Baseline grise vs Prévision)</span><span style="font-size:0.8rem;color:var(--muted);">Durée totale : {m.get('forecast_duration_days', 0)} jours</span></h2>
    {''.join(gantt_rows)}
  </section>

  <section>
    <h2><span>Pilotage Budgétaire CFO &amp; Engagement par Chantier</span><span style="font-size:0.8rem;color:var(--muted);">Enveloppe totale av. contingence : {evm.get('total_envelope_eur', 0):,.0f} €</span></h2>
    <table>
      <thead><tr><th>Chantier</th><th>Porteur</th><th>Budget Voté</th><th>Engagé / Devis</th><th>Décaissé (AC)</th><th>Écart</th></tr></thead>
      <tbody>{''.join(budget_rows)}</tbody>
    </table>
  </section>

  <div class="grid-2">
    <section>
      <h2><span>Garde-Fous Non-Négociables ExCom</span></h2>
      <ul class="clean">{''.join(gr_items)}</ul>
    </section>
    <section>
      <h2><span>Kill Criteria Pré-Engagés (Arrêt Auto)</span></h2>
      <ul class="clean">{''.join(kc_items)}</ul>
    </section>
  </div>

  <section>
    <h2><span>Livrables Métiers Produits par les Directeurs</span></h2>
    <ul class="clean">{''.join(deliv_items) if deliv_items else '<li>Aucun livrable enregistré pour le moment.</li>'}</ul>
  </section>
</div>
<script>
function filterSeat(seat, btn) {{
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.seat-item').forEach(el => {{
    if (seat === 'ALL') {{ el.style.display = ''; return; }}
    const tokens = (el.getAttribute('data-seats') || '').split(/\\s+/);
    el.style.display = tokens.includes(seat) ? '' : 'none';
  }});
}}
</script>
</body>
</html>
"""
    out_path = project_dir / "dashboard.html"
    out_path.write_text(doc, encoding="utf-8")
    return out_path


def save_and_refresh(project_dir: Path, state: Dict[str, Any], as_of: Optional[str] = None) -> Tuple[Path, List[Dict[str, Any]]]:
    state["schema_version"] = SCHEMA_VERSION
    state["updated_at"] = now_iso()
    compute_schedule_and_evm(state, as_of_str=as_of)
    new_alerts = run_contagion_radar(state, project_dir=project_dir)
    write_json(project_dir / "project-state.json", state)
    export_csvs(project_dir, state)
    dash = render_dashboard_html(project_dir, state)
    return dash, new_alerts


def cmd_init(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    spec = read_json(Path(args.spec).resolve())
    (project_dir / "deliverables").mkdir(parents=True, exist_ok=True)
    dash, new_alerts = save_and_refresh(project_dir, spec)
    append_event(project_dir, {
        "type": "PROJECT_INITIALIZED",
        "actor": "PMO",
        "project_name": spec.get("project_name", ""),
        "tasks_count": len(spec.get("tasks", [])),
    })
    print(json.dumps({
        "status": "OK",
        "project_dir": str(project_dir),
        "state_file": str(project_dir / "project-state.json"),
        "dashboard_html": str(dash),
        "overall_rag": spec.get("overall_rag"),
        "critical_path": spec["metrics"]["critical_path"],
        "open_alerts_count": len([a for a in spec.get("alerts", []) if a.get("status") == "OPEN"]),
        "new_alerts_raised": len(new_alerts),
    }, ensure_ascii=False, indent=2))


def cmd_update_task(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    target = next((t for t in state.get("tasks", []) if t["id"] == args.id), None)
    if target is None:
        sys.exit(f"Error: task '{args.id}' not found.")

    changes: Dict[str, Any] = {}
    if args.status is not None:
        target["status"] = args.status
        changes["status"] = args.status
    if args.progress is not None:
        target["progress_pct"] = args.progress
        changes["progress_pct"] = args.progress
    if args.forecast_days is not None:
        target["forecast_days"] = args.forecast_days
        changes["forecast_days"] = args.forecast_days
    if args.committed_cost is not None:
        target["committed_cost"] = args.committed_cost
        changes["committed_cost"] = args.committed_cost
    if args.actual_cost is not None:
        target["actual_cost"] = args.actual_cost
        changes["actual_cost"] = args.actual_cost
    if args.note:
        target["notes"] = args.note
        changes["note"] = args.note

    append_event(project_dir, {
        "type": "TASK_UPDATED",
        "actor": args.actor,
        "task_id": args.id,
        "changes": changes,
    })
    dash, new_alerts = save_and_refresh(project_dir, state, as_of=args.as_of)
    print(json.dumps({
        "status": "OK",
        "updated_task": args.id,
        "overall_rag": state.get("overall_rag"),
        "new_contagion_alerts": new_alerts,
        "dashboard_html": str(dash),
    }, ensure_ascii=False, indent=2))


def cmd_emit_signal(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    raw_impacts = [s.strip() for s in (args.impacts or "").split(",") if s.strip()]
    auto_impacts = DEFAULT_DOMAIN_COUPLINGS.get(args.category, ["PMO"])
    targets = sorted({s for s in (raw_impacts + auto_impacts) if s and s != args.from_seat})

    alert = {
        "id": f"SIG-{uuid.uuid4().hex[:6].upper()}",
        "fingerprint": f"SIG:{args.from_seat}:{args.title[:40]}",
        "created_at": now_iso(),
        "status": "OPEN",
        "severity": args.severity,
        "category": args.category,
        "task_id": args.task_id,
        "source_seat": args.from_seat,
        "target_seats": targets,
        "title": args.title,
        "upstream_cause": args.detail,
        "preventive_action": args.action_required,
    }
    state.setdefault("alerts", []).append(alert)
    append_event(project_dir, {
        "type": "CROSS_DIRECTOR_SIGNAL",
        "signal_id": alert["id"],
        "from_seat": args.from_seat,
        "target_seats": targets,
        "severity": args.severity,
        "category": args.category,
        "title": args.title,
    })
    dash, _ = save_and_refresh(project_dir, state)
    print(json.dumps({
        "status": "OK",
        "signal_id": alert["id"],
        "woken_target_seats": targets,
        "overall_rag": state.get("overall_rag"),
        "dashboard_html": str(dash),
    }, ensure_ascii=False, indent=2))


def cmd_register_deliverable(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    entry = {
        "id": f"DLV-{uuid.uuid4().hex[:6].upper()}",
        "created_at": now_iso(),
        "seat": args.seat,
        "task_id": args.task_id,
        "title": args.title,
        "path": args.path,
        "summary": args.summary,
    }
    state.setdefault("deliverables", []).append(entry)
    append_event(project_dir, {"type": "DELIVERABLE_PUBLISHED", **entry})
    dash, _ = save_and_refresh(project_dir, state)
    print(json.dumps({"status": "OK", "deliverable": entry, "dashboard_html": str(dash)}, ensure_ascii=False, indent=2))


def cmd_resolve_alert(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    alert = next((a for a in state.get("alerts", []) if a["id"] == args.alert_id), None)
    if alert is None:
        sys.exit(f"Error: alert '{args.alert_id}' not found.")
    alert["status"] = "RESOLVED"
    alert["resolved_by"] = args.by_seat
    alert["resolution"] = args.resolution
    alert["resolved_at"] = now_iso()
    append_event(project_dir, {
        "type": "ALERT_RESOLVED",
        "alert_id": args.alert_id,
        "by_seat": args.by_seat,
        "resolution": args.resolution,
    })
    dash, _ = save_and_refresh(project_dir, state)
    print(json.dumps({"status": "OK", "overall_rag": state.get("overall_rag"), "dashboard_html": str(dash)}, ensure_ascii=False, indent=2))


def cmd_audit(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    if args.as_of:
        state["as_of_date"] = args.as_of
    dash, new_alerts = save_and_refresh(project_dir, state, as_of=args.as_of)
    open_alerts = [a for a in state.get("alerts", []) if a.get("status") == "OPEN"]
    seats_to_summon = sorted({s for a in open_alerts for s in a.get("target_seats", [])})
    print(json.dumps({
        "overall_rag": state.get("overall_rag"),
        "metrics": state.get("metrics"),
        "open_alerts_count": len(open_alerts),
        "newly_detected_alerts": len(new_alerts),
        "directors_to_summon_preemptively": seats_to_summon,
        "open_alerts": open_alerts,
        "dashboard_html": str(dash),
    }, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ExCom v2.0 Control Tower & Cross-Perimeter Contagion CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize a project Control Tower from a JSON spec")
    p_init.add_argument("--project-dir", required=True)
    p_init.add_argument("--spec", required=True)
    p_init.set_defaults(func=cmd_init)

    p_upd = sub.add_parser("update-task", help="Update task progress/schedule/cost and run contagion propagation")
    p_upd.add_argument("--project-dir", required=True)
    p_upd.add_argument("--id", required=True)
    p_upd.add_argument("--actor", required=True)
    p_upd.add_argument("--status", choices=["TODO", "IN_PROGRESS", "BLOCKED", "DONE"])
    p_upd.add_argument("--progress", type=float)
    p_upd.add_argument("--forecast-days", type=float)
    p_upd.add_argument("--committed-cost", type=float)
    p_upd.add_argument("--actual-cost", type=float)
    p_upd.add_argument("--note")
    p_upd.add_argument("--as-of")
    p_upd.set_defaults(func=cmd_update_task)

    p_sig = sub.add_parser("emit-signal", help="Emit an upstream cross-director drift/discovery signal")
    p_sig.add_argument("--project-dir", required=True)
    p_sig.add_argument("--from-seat", required=True)
    p_sig.add_argument("--severity", required=True, choices=["INFO", "WARNING", "CRITICAL"])
    p_sig.add_argument("--category", required=True, choices=list(DEFAULT_DOMAIN_COUPLINGS.keys()))
    p_sig.add_argument("--title", required=True)
    p_sig.add_argument("--detail", required=True)
    p_sig.add_argument("--action-required", required=True)
    p_sig.add_argument("--impacts", default="")
    p_sig.add_argument("--task-id")
    p_sig.set_defaults(func=cmd_emit_signal)

    p_dlv = sub.add_parser("register-deliverable", help="Register a specialized Director deliverable file")
    p_dlv.add_argument("--project-dir", required=True)
    p_dlv.add_argument("--seat", required=True)
    p_dlv.add_argument("--task-id", required=True)
    p_dlv.add_argument("--title", required=True)
    p_dlv.add_argument("--path", required=True)
    p_dlv.add_argument("--summary", required=True)
    p_dlv.set_defaults(func=cmd_register_deliverable)

    p_res = sub.add_parser("resolve-alert", help="Record a Director's counter-measure and close an alert")
    p_res.add_argument("--project-dir", required=True)
    p_res.add_argument("--alert-id", required=True)
    p_res.add_argument("--by-seat", required=True)
    p_res.add_argument("--resolution", required=True)
    p_res.set_defaults(func=cmd_resolve_alert)

    p_aud = sub.add_parser("audit", help="Run a 360-degree drift, EVM & contagion audit")
    p_aud.add_argument("--project-dir", required=True)
    p_aud.add_argument("--as-of")
    p_aud.set_defaults(func=cmd_audit)

    return p


if __name__ == "__main__":
    parser = build_parser()
    ns = parser.parse_args()
    ns.func(ns)
