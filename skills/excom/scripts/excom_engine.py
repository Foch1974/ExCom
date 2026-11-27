#!/usr/bin/env python3
"""ExCom v3.3 — 360° Enterprise Q-C-D-R Control Tower, Contagion Bus & Interchange Engine.

100% Python 3.8+ standard library (zero external pip dependencies).
Universal across ALL project types (Real Estate/Construction, IT/ERP, Industrial, M&A, Quant, Personal):
  1. Schedule (Délais): CPM + PERT P85, FS/SS/FF/SF dependencies with lag, Hard Target Deadline &
     Negative Float (backward planning), Near-Critical Path (<= 5d float), and transitive slip contagion.
  2. Cost (Coûts): 5-Column Enterprise Budget (Initial BAC -> Approved TMA/Changes -> Revised Budget ->
     Committed -> Actual AC -> Remaining ETC -> Forecast EAC -> Variance VAC), Contingency vs Management
     Reserve separation, multi-year TCO (incl. OPEX, indexation, incentives, exit/dilapidation), & S-Curve.
  3. Risks & Contracts (Risques & Contractuel): Quantified Risk Register (EMV Cost + Expected Delay vs
     remaining contingency) + Contractual Negotiation & Suspensive Conditions Tracker (incl. HSE clauses).
  4. Quality & HSE / Compliance Gate (Qualité & Conformité): Asset/Regulatory Testing, Punch-List Reserves,
     Remediation Cost/Delay Contagion, and Hard Go-Live Blocker until 100% certificates are issued.
  5. Governance & Interchange: Adaptive Methodology Selector, RACI Matrix, Decision Log, 1-click CoPil
     Brief, Multi-View HTML Cockpit, MS Project XML (MSPDI), Native 7-Tab Excel (.xlsx), UTF-8-BOM CSVs
     (incl. Jira/Asana/Monday), iCalendar (.ics), and Bidirectional CSV / MS Project XML Import.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import math
from pathlib import Path
import sys
import uuid
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from excom_interop import (
    _parse_dep_spec,
    export_copil_brief,
    export_enterprise_csvs,
    export_excel_xlsx,
    export_icalendar_ics,
    export_msproject_xml,
    import_msproject_xml,
    import_tasks_csv,
    select_methodology,
)
from excom_office_cad import (
    audit_dxf_file,
    export_copil_docx,
    export_copil_pptx,
    generate_space_plan_dxf,
)


SCHEMA_VERSION = "3.4.0"

DEFAULT_DOMAIN_COUPLINGS: Dict[str, List[str]] = {
    "COST": ["CFO", "CRO-Risk", "PMO"],
    "SCHEDULE": ["PMO", "COO", "CHRO"],
    "LEGAL": ["CLO", "CCO-Compliance", "CRO-Risk"],
    "COMPLIANCE": ["CCO-Compliance", "CLO", "CISO", "COO", "PMO"],
    "HSE": ["CCO-Compliance", "COO", "CLO", "CFO", "PMO"],
    "VENDOR": ["COO", "CPO", "CLO", "CISO", "CFO"],
    "TECH": ["CTO", "CIO", "CISO", "CAIO", "CFO"],
    "DATA_AI": ["CDO-Data", "CAIO", "CISO", "CCO-Compliance"],
    "MARKET": ["CMO", "CRO-Revenue", "CCO-Commercial", "CPO", "COO"],
    "HUMAN": ["CHRO", "COO", "CXO"],
    "RISK": ["CRO-Risk", "CFO", "CLO", "PMO"],
    "ESG": ["CSO-Sustainability", "CCO-Compliance", "COO", "CFO"],
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(str(s)[:10])


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
        for raw_dep in t.get("depends_on", []):
            dep_id, _, _ = _parse_dep_spec(raw_dep)
            if dep_id in by_id:
                in_deg[t["id"]] += 1
                succ[dep_id].append(t["id"])

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


def _forward_es_from_dep(dep_es: float, dep_ef: float, own_dur: float, dep_type: str, lag: float) -> float:
    if dep_type == "SS":
        return max(0.0, dep_es + lag)
    if dep_type == "FF":
        return max(0.0, dep_ef + lag - own_dur)
    if dep_type == "SF":
        return max(0.0, dep_es + lag - own_dur)
    # Default: FS
    return max(0.0, dep_ef + lag)


def _backward_lf_from_succ(succ_ls: float, succ_lf: float, own_dur: float, dep_type: str, lag: float) -> float:
    if dep_type == "SS":
        return succ_ls - lag + own_dur
    if dep_type == "FF":
        return succ_lf - lag
    if dep_type == "SF":
        return succ_lf - lag + own_dur
    # Default: FS
    return succ_ls - lag


def compute_schedule_and_evm(state: Dict[str, Any], as_of_str: Optional[str] = None) -> Dict[str, Any]:
    start_dt = parse_date(state.get("start_date", dt.date.today().isoformat()))
    as_of = parse_date(as_of_str) if as_of_str else parse_date(state.get("as_of_date", start_dt.isoformat()))
    target_end_str = str(state.get("target_end_date", "") or "").strip()
    target_end_dt = parse_date(target_end_str) if target_end_str else None
    target_horizon_days = float((target_end_dt - start_dt).days) if target_end_dt else None

    tasks = state.get("tasks", [])
    by_id = {t["id"]: t for t in tasks}
    order = topological_sort(tasks)

    # Pre-aggregate approved Change Orders (TMA) per task
    change_orders = state.get("change_orders", [])
    approved_co_cost_by_task: Dict[str, float] = {}
    approved_co_delay_by_task: Dict[str, float] = {}
    unassigned_approved_co_cost = 0.0
    approved_co_total = 0.0
    for co in change_orders:
        if str(co.get("status", "")).strip().upper() == "APPROVED":
            c_imp = float(co.get("cost_impact_eur", 0.0))
            d_imp = float(co.get("delay_impact_days", 0.0))
            approved_co_total += c_imp
            ltid = str(co.get("linked_task_id", "")).strip()
            if ltid and ltid in by_id:
                approved_co_cost_by_task[ltid] = approved_co_cost_by_task.get(ltid, 0.0) + c_imp
                approved_co_delay_by_task[ltid] = approved_co_delay_by_task.get(ltid, 0.0) + d_imp
            else:
                unassigned_approved_co_cost += c_imp

    # Parse dependency graph with FS/SS/FF/SF + lag
    deps_parsed: Dict[str, List[Tuple[str, str, float]]] = {}
    succ_edges: Dict[str, List[Tuple[str, str, float]]] = {tid: [] for tid in order}
    for tid in order:
        plist: List[Tuple[str, str, float]] = []
        for raw_dep in by_id[tid].get("depends_on", []):
            dep_id, dep_type, lag_d = _parse_dep_spec(raw_dep)
            if dep_id in by_id:
                plist.append((dep_id, dep_type, lag_d))
                succ_edges[dep_id].append((tid, dep_type, lag_d))
        deps_parsed[tid] = plist

    # 1. Baseline schedule pass
    base_es: Dict[str, float] = {}
    base_ef: Dict[str, float] = {}
    base_dur_map: Dict[str, float] = {}
    for tid in order:
        t = by_id[tid]
        b_dur, _ = pert_duration(t, use_forecast=False)
        base_dur_map[tid] = b_dur
        es = max(
            (_forward_es_from_dep(base_es[d], base_ef[d], b_dur, dt_t, lg) for d, dt_t, lg in deps_parsed[tid]),
            default=0.0,
        )
        base_es[tid] = round(es, 1)
        base_ef[tid] = round(es + b_dur, 1)

    baseline_project_days = round(max(base_ef.values(), default=0.0), 1)

    # 2. Live / Forecast CPM forward pass (includes explicit forecast_days + approved CO delay if not already baked in)
    es_map: Dict[str, float] = {}
    ef_map: Dict[str, float] = {}
    dur_map: Dict[str, float] = {}
    sigma_map: Dict[str, float] = {}
    for tid in order:
        t = by_id[tid]
        dur, sig = pert_duration(t, use_forecast=True)
        if t.get("forecast_days") is None and approved_co_delay_by_task.get(tid, 0.0) > 0:
            dur = round(dur + approved_co_delay_by_task[tid], 1)
        dur_map[tid] = dur
        sigma_map[tid] = sig
        es = max(
            (_forward_es_from_dep(es_map[d], ef_map[d], dur, dt_t, lg) for d, dt_t, lg in deps_parsed[tid]),
            default=0.0,
        )
        es_map[tid] = round(es, 1)
        ef_map[tid] = round(es + dur, 1)

    live_project_days = round(max(ef_map.values(), default=0.0), 1)

    # 3. Backward pass: standard CPM float vs Live Finish, AND Hard-Target Backward Slack (Negative Float!)
    lf_map: Dict[str, float] = {}
    ls_map: Dict[str, float] = {}
    float_map: Dict[str, float] = {}
    t_lf_map: Dict[str, float] = {}
    t_ls_map: Dict[str, float] = {}
    target_slack_map: Dict[str, float] = {}

    hard_end_ref = target_horizon_days if target_horizon_days is not None else live_project_days

    for tid in reversed(order):
        s_list = succ_edges[tid]
        lf = min((_backward_lf_from_succ(ls_map[s], lf_map[s], dur_map[tid], dt_t, lg) for s, dt_t, lg in s_list), default=live_project_days)
        ls = lf - dur_map[tid]
        lf_map[tid] = round(lf, 1)
        ls_map[tid] = round(ls, 1)
        float_map[tid] = round(max(0.0, lf - ef_map[tid]), 1)

        tlf = min((_backward_lf_from_succ(t_ls_map[s], t_lf_map[s], dur_map[tid], dt_t, lg) for s, dt_t, lg in s_list), default=hard_end_ref)
        tls = tlf - dur_map[tid]
        t_lf_map[tid] = round(tlf, 1)
        t_ls_map[tid] = round(tls, 1)
        target_slack_map[tid] = round(tlf - ef_map[tid], 1)

    critical_path: List[str] = []
    near_critical_tasks: List[str] = []
    crit_sigma_sq = 0.0

    # 4. Enrich tasks + 5-Column Budget & EVM Rollup + Monthly Cash-Flow S-Curve
    bac = 0.0
    revised_budget_total = unassigned_approved_co_cost
    pv = 0.0
    ev = 0.0
    ac = 0.0
    committed_total = 0.0
    etc_total = 0.0
    task_eac_sum = unassigned_approved_co_cost
    monthly_cashflow: Dict[str, float] = {}

    for tid in order:
        t = by_id[tid]
        is_crit = float_map[tid] <= 0.05 and dur_map[tid] > 0
        is_near_crit = (not is_crit) and (0.05 < float_map[tid] <= 5.0) and dur_map[tid] > 0
        if is_crit:
            critical_path.append(tid)
            crit_sigma_sq += sigma_map[tid] ** 2
        elif is_near_crit:
            near_critical_tasks.append(tid)

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
        co_cost = round(approved_co_cost_by_task.get(tid, 0.0), 2)
        revised_b = round(planned_cost + co_cost, 2)
        actual_cost = float(t.get("actual_cost", 0.0))
        committed_cost = max(actual_cost, float(t.get("committed_cost", actual_cost)))
        if t.get("etc_cost") is not None:
            task_etc = max(0.0, float(t["etc_cost"]))
        else:
            task_etc = round(max(0.0, max(revised_b, committed_cost) - actual_cost), 2)
        task_eac = round(actual_cost + task_etc, 2)
        task_vac = round(revised_b - task_eac, 2)

        if as_of >= p_end:
            pv_ratio = 1.0
        elif as_of <= p_start:
            pv_ratio = 0.0
        else:
            span = max(1, (p_end - p_start).days)
            pv_ratio = min(1.0, max(0.0, (as_of - p_start).days / span))

        bac += planned_cost
        revised_budget_total += revised_b
        pv += revised_b * pv_ratio
        ev += revised_b * (progress / 100.0)
        ac += actual_cost
        committed_total += committed_cost
        etc_total += task_etc
        task_eac_sum += task_eac

        # Monthly Cash-Flow S-Curve allocation across forecast duration
        if task_eac > 0:
            ym_key = f_end.strftime("%Y-%m")
            monthly_cashflow[ym_key] = round(monthly_cashflow.get(ym_key, 0.0) + task_eac, 2)

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
            "target_slack_days": target_slack_map[tid],
            "is_critical": is_crit,
            "is_near_critical": is_near_crit,
            "planned_start": p_start.isoformat(),
            "planned_end": p_end.isoformat(),
            "forecast_start": f_start.isoformat(),
            "forecast_end": f_end.isoformat(),
            "slip_days": slip_days,
            "own_slip_days": own_slip_days,
            "inherited_delay_days": inherited_delay_days,
            "is_overdue": is_overdue,
            "approved_changes_eur": co_cost,
            "revised_budget": revised_b,
            "committed_cost": round(committed_cost, 2),
            "etc_eur": round(task_etc, 2),
            "task_eac_eur": task_eac,
            "task_vac_eur": task_vac,
            "cost_variance": round((revised_b * (progress / 100.0)) - actual_cost, 2) if ac > 0 else 0.0,
            "budget_overrun_eur": round(max(0.0, task_eac - revised_b), 2),
        }

    # 5. Global 5-Column EVM, Contingency vs Management Reserve, & Multi-Year TCO
    recurring_annual = sum(float(r.get("annual_eur", 0.0)) for r in state.get("recurring_opex", []))
    contingency_pct = float(state.get("contingency_pct", 12.0))
    mgmt_reserve_pct = float(state.get("management_reserve_pct", 5.0))
    contingency_eur = round(bac * (contingency_pct / 100.0), 2)
    mgmt_reserve_eur = round(bac * (mgmt_reserve_pct / 100.0), 2)
    contingency_remaining = round(contingency_eur - approved_co_total, 2)

    cpi = round(ev / ac, 2) if ac > 0 else 1.0
    spi = round(ev / pv, 2) if pv > 0 else 1.0
    eac = round(max(task_eac_sum, (revised_budget_total / cpi) if (ac > 0 and ev > 0 and cpi < 1.0) else task_eac_sum), 2)
    vac = round(revised_budget_total - eac, 2)
    denom_tcpi = revised_budget_total - ac
    tcpi = round((revised_budget_total - ev) / denom_tcpi, 2) if denom_tcpi > 0 else 1.0

    # Multi-Year TCO (CAPEX EAC + Indexed OPEX + Exit/Dilapidations - Landlord/Grant Incentives)
    tco_years = int(state.get("tco_horizon_years", 6))
    idx_rate = float(state.get("indexation_annual_pct", 2.0)) / 100.0
    opex_tco = sum(recurring_annual * ((1.0 + idx_rate) ** yr) for yr in range(tco_years))
    exit_dilap = float(state.get("exit_dilapidation_eur", 0.0))
    incentives = float(state.get("incentives_ti_allowance_eur", 0.0))
    tco_total = round(eac + opex_tco + exit_dilap - incentives, 2)

    # 6. Q-C-D-R Enterprise Register Rollups (Risks EMV, HSE/Compliance Go-Live Gate, Contracts)
    open_risks = [r for r in state.get("risk_register", []) if str(r.get("status", "OPEN")).upper() == "OPEN"]
    risk_emv_eur = round(sum(float(r.get("probability_pct", 0.0)) / 100.0 * float(r.get("cost_impact_eur", 0.0)) for r in open_risks), 2)
    risk_exp_delay = round(sum(float(r.get("probability_pct", 0.0)) / 100.0 * float(r.get("delay_impact_days", 0.0)) for r in open_risks), 1)
    crit_risks = sum(1 for r in open_risks if float(r.get("probability_pct", 0.0)) >= 40.0 and (float(r.get("cost_impact_eur", 0.0)) >= 10000 or float(r.get("delay_impact_days", 0.0)) >= 10))

    comp_items = state.get("compliance_register", [])
    comp_total = len(comp_items)
    certs_issued = sum(1 for c in comp_items if bool(c.get("certificate_issued", False)))
    blocking_comp_open = sum(
        1 for c in comp_items
        if bool(c.get("blocking_go_live", True))
        and (not bool(c.get("certificate_issued", False)) or (bool(str(c.get("reserves", "")).strip()) and not bool(c.get("reserves_lifted", False))))
    )
    open_reserves = sum(1 for c in comp_items if bool(str(c.get("reserves", "")).strip()) and not bool(c.get("reserves_lifted", False)))
    comp_remed_cost = round(sum(float(c.get("remediation_cost_eur", 0.0)) for c in comp_items if not bool(c.get("reserves_lifted", False)) and not bool(c.get("certificate_issued", False))), 2)
    comp_remed_delay = round(sum(float(c.get("remediation_delay_days", 0.0)) for c in comp_items if not bool(c.get("reserves_lifted", False)) and not bool(c.get("certificate_issued", False))), 1)
    go_live_status = "BLOCKED_BY_COMPLIANCE" if blocking_comp_open > 0 else "READY"

    contracts = state.get("contracts_register", [])
    ct_signed = sum(1 for ct in contracts if str(ct.get("status", "")).upper() == "SIGNED")
    ct_open_red = sum(1 for ct in contracts if str(ct.get("status", "")).upper() in ("NEGOTIATING", "DISPUTED", "REDLINE", "BLOCKED"))
    open_suspensive = sum(1 for ct in contracts if bool(ct.get("is_suspensive_condition", False)) and str(ct.get("status", "")).upper() not in ("LIFTED", "SATISFIED", "SIGNED"))
    ct_exposure = round(sum(float(ct.get("financial_exposure_eur", 0.0)) for ct in contracts if str(ct.get("status", "")).upper() != "SIGNED"), 2)

    p85_buffer_days = round(1.04 * math.sqrt(crit_sigma_sq), 1)
    project_slip_days = round(live_project_days - baseline_project_days, 1)
    forecast_end_dt = start_dt + dt.timedelta(days=int(round(live_project_days)))
    target_margin_days = round(target_horizon_days - live_project_days, 1) if target_horizon_days is not None else None

    overall_pct = round((ev / revised_budget_total) * 100.0, 1) if revised_budget_total > 0 else round(
        sum(float(t.get("progress_pct", 0.0)) for t in tasks) / max(1, len(tasks)), 1
    )

    state["metrics"] = {
        "as_of_date": as_of.isoformat(),
        "baseline_duration_days": baseline_project_days,
        "forecast_duration_days": live_project_days,
        "p85_duration_days": round(live_project_days + p85_buffer_days, 1),
        "project_slip_days": project_slip_days,
        "baseline_end_date": (start_dt + dt.timedelta(days=int(round(baseline_project_days)))).isoformat(),
        "forecast_end_date": forecast_end_dt.isoformat(),
        "target_end_date": target_end_str or None,
        "target_margin_days": target_margin_days,
        "critical_path": critical_path,
        "near_critical_tasks": near_critical_tasks,
        "overall_progress_pct": overall_pct,
        "monthly_cashflow_s_curve": dict(sorted(monthly_cashflow.items())),
        "evm": {
            "bac_eur": round(bac, 2),
            "approved_changes_eur": round(approved_co_total, 2),
            "revised_budget_eur": round(revised_budget_total, 2),
            "contingency_eur": contingency_eur,
            "contingency_remaining_eur": contingency_remaining,
            "management_reserve_eur": mgmt_reserve_eur,
            "total_envelope_eur": round(bac + contingency_eur + mgmt_reserve_eur, 2),
            "committed_eur": round(committed_total, 2),
            "pv_eur": round(pv, 2),
            "ev_eur": round(ev, 2),
            "ac_eur": round(ac, 2),
            "etc_eur": round(etc_total, 2),
            "cpi": cpi,
            "spi": spi,
            "eac_eur": eac,
            "vac_eur": vac,
            "tcpi": tcpi,
            "recurring_annual_opex_eur": round(recurring_annual, 2),
            "tco_horizon_years": tco_years,
            "tco_total_eur": tco_total,
        },
        "qcdr": {
            "risk_emv_eur": risk_emv_eur,
            "risk_expected_delay_days": risk_exp_delay,
            "open_risks_count": len(open_risks),
            "critical_risks_count": crit_risks,
            "compliance_total": comp_total,
            "certificates_issued": certs_issued,
            "certificates_pct": round((certs_issued / comp_total) * 100.0, 1) if comp_total > 0 else 100.0,
            "blocking_compliance_open": blocking_comp_open,
            "open_reserves_count": open_reserves,
            "compliance_remediation_cost_eur": comp_remed_cost,
            "compliance_remediation_delay_days": comp_remed_delay,
            "go_live_gate_status": go_live_status,
            "contracts_signed_count": ct_signed,
            "contracts_open_redlines": ct_open_red,
            "open_suspensive_conditions": open_suspensive,
            "contracts_open_exposure_eur": ct_exposure,
        },
    }
    return state


def run_contagion_radar(state: Dict[str, Any], project_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Detects upstream schedule, hard-deadline, cost, EMV risk, HSE/compliance, and contractual drifts."""
    existing_alerts: List[Dict[str, Any]] = state.setdefault("alerts", [])
    existing_fps = {a.get("fingerprint") for a in existing_alerts if a.get("status") == "OPEN"}

    tasks = state.get("tasks", [])
    by_id = {t["id"]: t for t in tasks}
    m = state.get("metrics", {})
    evm = m.get("evm", {})
    qcdr = m.get("qcdr", {})
    as_of = parse_date(m.get("as_of_date", dt.date.today().isoformat()))
    ccy = state.get("currency", "EUR")
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
            append_event(project_dir, {
                "type": "CONTAGION_ALERT_RAISED",
                "alert_id": alert["id"],
                "severity": severity,
                "source_seat": source_seat,
                "target_seats": clean_targets,
                "title": title,
            })

    # Build transitive downstream map
    adj: Dict[str, List[str]] = {t["id"]: [] for t in tasks}
    for t in tasks:
        for raw_dep in t.get("depends_on", []):
            dep_id, _, _ = _parse_dep_spec(raw_dep)
            if dep_id in adj:
                adj[dep_id].append(t["id"])

    def transitive_downstream(start_tid: str) -> List[str]:
        seen: List[str] = []
        stack = list(adj.get(start_tid, []))
        while stack:
            cur = stack.pop(0)
            if cur not in seen:
                seen.append(cur)
                stack.extend(adj.get(cur, []))
        return seen

    # 1. Hard Target Deadline Breach (Negative Float!)
    t_margin = m.get("target_margin_days")
    if t_margin is not None and float(t_margin) < 0:
        register_alert(
            fingerprint=f"HARD_DEADLINE_BREACH:{int(round(t_margin))}",
            severity="CRITICAL",
            category="SCHEDULE",
            source_seat="PMO",
            target_seats=["CEO", "COO", "CLO", "CFO", "CHRO"],
            title=f"Hard Target Deadline BREACHED by {abs(t_margin):.1f} days ({m.get('forecast_end_date')} > {m.get('target_end_date')})",
            upstream_cause=f"Critical Path ({' -> '.join(m.get('critical_path', []))}) exceeds non-negotiable target deadline (Negative Float = {t_margin:.1f}d).",
            preventive_action="Trigger Fast-Tracking (SS overlap), Crashing, or formal lease/contract extension negotiation immediately.",
        )

    # 2. Task-level Schedule Slip, Overdue, Overrun & Blockers
    for t in tasks:
        comp = t.get("computed", {})
        tid = t["id"]
        owner = t.get("owner_seat", "PMO")
        own_slip = float(comp.get("own_slip_days", 0.0))
        overrun = float(comp.get("budget_overrun_eur", 0.0))
        revised_b = float(comp.get("revised_budget", t.get("planned_budget", 0.0)))

        if own_slip >= 1.5:
            desc_ids = transitive_downstream(tid)
            downstream_seats: List[str] = []
            for d_id in desc_ids:
                other = by_id[d_id]
                downstream_seats.append(other.get("owner_seat", "PMO"))
                downstream_seats.extend(other.get("coupled_seats", {}).keys())
            severity = "CRITICAL" if comp.get("is_critical") else "WARNING"
            cascade_desc = ", ".join(f"{d_id} ({by_id[d_id].get('owner_seat', 'PMO')})" for d_id in desc_ids) or "Project Completion"
            register_alert(
                fingerprint=f"ROOT_SLIP:{tid}:{int(round(own_slip))}",
                severity=severity,
                category="SCHEDULE",
                source_seat=owner,
                target_seats=downstream_seats + ["PMO", "COO"],
                task_id=tid,
                title=f"Upstream schedule slip on {tid} (+{own_slip}d) -> cascading into {cascade_desc}",
                upstream_cause=f"Source workstream '{t['name']}' ({owner}) extended by +{own_slip}d ({'Critical Path shift' if comp.get('is_critical') else 'Float erosion'}).",
                preventive_action="Pre-stage prerequisites for impacted downstream owners in parallel to absorb the slip.",
            )

        if comp.get("is_overdue"):
            register_alert(
                fingerprint=f"OVERDUE:{tid}",
                severity="CRITICAL" if comp.get("is_critical") else "WARNING",
                category="SCHEDULE",
                source_seat=owner,
                target_seats=["PMO", "COO"] + list(t.get("coupled_seats", {}).keys()),
                task_id=tid,
                title=f"Past-due milestone on {tid} ({t['name']})",
                upstream_cause=f"Forecast finish {comp.get('forecast_end')} passed at {t.get('progress_pct', 0)}% completion.",
                preventive_action=f"Convene flash Steering Check with PMO + {owner} to unblock or re-sequence.",
            )

        if overrun > 0 and (revised_b == 0 or (overrun / max(1.0, revised_b)) >= 0.08):
            pct = round((overrun / revised_b) * 100.0, 1) if revised_b > 0 else 100.0
            register_alert(
                fingerprint=f"COST:{tid}:{int(overrun)}",
                severity="CRITICAL" if pct >= 20.0 else "WARNING",
                category="COST",
                source_seat=owner,
                target_seats=["CFO", "CRO-Risk", "PMO"] + list(t.get("coupled_seats", {}).keys()),
                task_id=tid,
                title=f"Workstream budget overrun on {tid} (+{overrun:,.0f} {ccy} / +{pct}%)",
                upstream_cause=f"Forecast EAC ({comp.get('task_eac_eur'):,.0f} {ccy}) exceeds revised budget ({revised_b:,.0f} {ccy}) on '{t['name']}'.",
                preventive_action="Log formal Change Order (TMA) and validate contingency drawdown with CFO before committing spend.",
            )

        if t.get("status") == "BLOCKED":
            register_alert(
                fingerprint=f"BLOCKED:{tid}",
                severity="CRITICAL",
                category="RISK",
                source_seat=owner,
                target_seats=["PMO", "CEO", "COO"] + list(t.get("coupled_seats", {}).keys()),
                task_id=tid,
                title=f"Critical blocker declared on {tid} ({t['name']})",
                upstream_cause=t.get("notes", "Operational blocker flagged by task owner."),
                preventive_action="Escalate immediately to coupled Directors and Sponsor for arbitration.",
            )

    # 3. Contingency Exhaustion & Quantified Risk EMV Coverage Check
    if evm.get("contingency_remaining_eur", 0) < 0:
        register_alert(
            fingerprint="CONTINGENCY_EXHAUSTED",
            severity="CRITICAL",
            category="COST",
            source_seat="CFO",
            target_seats=["CEO", "PMO", "CRO-Risk"],
            title=f"Project Contingency EXHAUSTED ({evm.get('contingency_remaining_eur'):,.0f} {ccy})",
            upstream_cause=f"Approved Change Orders ({evm.get('approved_changes_eur'):,.0f} {ccy}) exceeded initial project contingency ({evm.get('contingency_eur'):,.0f} {ccy}).",
            preventive_action="Request formal ComEx Management Reserve release or execute value-engineering descoping.",
        )
    elif qcdr.get("risk_emv_eur", 0) > max(0.0, evm.get("contingency_remaining_eur", 0)) and qcdr.get("risk_emv_eur", 0) > 0:
        register_alert(
            fingerprint=f"EMV_EXCEEDS_CONTINGENCY:{int(qcdr['risk_emv_eur'])}",
            severity="WARNING",
            category="RISK",
            source_seat="CRO-Risk",
            target_seats=["CFO", "PMO", "CEO"],
            title=f"Quantified Risk EMV ({qcdr['risk_emv_eur']:,.0f} {ccy}) exceeds remaining contingency ({evm.get('contingency_remaining_eur'):,.0f} {ccy})",
            upstream_cause=f"{qcdr.get('open_risks_count')} open risks carry {qcdr['risk_emv_eur']:,.0f} {ccy} expected exposure and {qcdr.get('risk_expected_delay_days')}d expected delay.",
            preventive_action="Accelerate top risk mitigations or expand contingency buffer before signing irreversible commitments.",
        )

    # 4. HSE / Compliance / Testing / Reserves Go-Live Gate Contagion
    for item in state.get("compliance_register", []):
        cid = item.get("id", "HSE")
        has_open_res = bool(str(item.get("reserves", "")).strip()) and not bool(item.get("reserves_lifted", False))
        missing_cert = not bool(item.get("certificate_issued", False))
        is_blocker = bool(item.get("blocking_go_live", True))
        if has_open_res:
            rem_c = float(item.get("remediation_cost_eur", 0.0))
            rem_d = float(item.get("remediation_delay_days", 0.0))
            register_alert(
                fingerprint=f"HSE_RESERVE:{cid}:{int(rem_c)}:{int(rem_d)}",
                severity="CRITICAL" if is_blocker else "WARNING",
                category="HSE",
                source_seat=item.get("owner_seat", "CCO-Compliance"),
                target_seats=["COO", "CFO", "CLO", "PMO"],
                task_id=item.get("linked_task_id") or None,
                title=f"Unlifted HSE/Compliance Reserve on {cid} ({item.get('standard', '')}): +{rem_c:,.0f} {ccy} / +{rem_d}d",
                upstream_cause=f"Requirement '{item.get('requirement')}' has open reserve: {item.get('reserves')}. Go-Live blocked={is_blocker}.",
                preventive_action="Issue corrective work order (linked task + TMA), re-test with accredited inspector, and collect signed clearance certificate.",
            )
        elif is_blocker and missing_cert and str(item.get("status", "")).upper() in ("NON_COMPLIANT", "FAILED", "BLOCKED"):
            register_alert(
                fingerprint=f"HSE_NONCOMPLIANT:{cid}",
                severity="CRITICAL",
                category="COMPLIANCE",
                source_seat=item.get("owner_seat", "CCO-Compliance"),
                target_seats=["CEO", "CLO", "COO", "CFO", "PMO"],
                title=f"Go-Live BLOCKED: Non-compliant requirement {cid} ({item.get('requirement')})",
                upstream_cause=f"Mandatory standard '{item.get('standard')}' flagged {item.get('status')} with no compliance certificate.",
                preventive_action="Halt occupancy/Go-Live until remediation works pass accredited certification.",
            )

    # 5. Contractual Negotiation & Suspensive Conditions Contagion
    for ct in state.get("contracts_register", []):
        ctid = ct.get("id", "CTR")
        st = str(ct.get("status", "")).upper()
        if st in ("DISPUTED", "BLOCKED", "REJECTED"):
            register_alert(
                fingerprint=f"CONTRACT_DEADLOCK:{ctid}",
                severity="CRITICAL" if ct.get("is_suspensive_condition") or ct.get("hse_compliance_linked") else "WARNING",
                category="LEGAL",
                source_seat=ct.get("owner_seat", "CLO"),
                target_seats=["CEO", "CFO", "CCO-Compliance", "PMO"],
                title=f"Contractual deadlock on {ctid} ({ct.get('clause_topic')} · {ct.get('counterparty')})",
                upstream_cause=f"Status={st} (HSE-linked={ct.get('hse_compliance_linked', False)}, Exposure={float(ct.get('financial_exposure_eur', 0)):,.0f} {ccy}).",
                preventive_action="Escalate walk-away BATNA / redline fallback to Sponsor before signing.",
            )
        if ct.get("is_suspensive_condition") and st not in ("LIFTED", "SATISFIED", "SIGNED") and ct.get("deadline"):
            days_left = (parse_date(ct["deadline"]) - as_of).days
            if days_left <= 14:
                register_alert(
                    fingerprint=f"SUSPENSIVE_DUE:{ctid}",
                    severity="CRITICAL" if days_left <= 5 else "WARNING",
                    category="LEGAL",
                    source_seat="CLO",
                    target_seats=["CEO", "CFO", "CCO-Compliance", "PMO"],
                    title=f"Suspensive condition {ctid} due in {days_left}d ({ct['deadline']}): {ct.get('clause_topic')}",
                    upstream_cause=f"Unlifted suspensive condition with {ct.get('counterparty')} risks automatic contract lapse or forced waiver.",
                    preventive_action="Deliver clearance proof or sign formal written extension before deadline expires.",
                )

    # 6. Global EVM CPI / SPI drift
    if evm.get("ac_eur", 0) > 0 and evm.get("cpi", 1.0) < 0.90:
        register_alert(
            fingerprint=f"EVM_CPI:{evm['cpi']}",
            severity="CRITICAL" if evm["cpi"] < 0.80 else "WARNING",
            category="COST",
            source_seat="PMO",
            target_seats=["CFO", "CEO", "CRO-Risk"],
            title=f"Portfolio Cost Efficiency Alert (CPI = {evm['cpi']} < 0.90)",
            upstream_cause=f"Projected EAC ({evm['eac_eur']:,.0f} {ccy}) vs Revised Budget ({evm['revised_budget_eur']:,.0f} {ccy}).",
            preventive_action="Freeze discretionary spend and audit top variance workstreams.",
        )

    if evm.get("pv_eur", 0) > 0 and evm.get("spi", 1.0) < 0.85:
        register_alert(
            fingerprint=f"EVM_SPI:{evm['spi']}",
            severity="CRITICAL" if evm["spi"] < 0.75 else "WARNING",
            category="SCHEDULE",
            source_seat="PMO",
            target_seats=["COO", "CEO", "CHRO"],
            title=f"Schedule Velocity Lag Alert (SPI = {evm['spi']} < 0.85)",
            upstream_cause=f"Earned value ({evm['ev_eur']:,.0f} {ccy}) lags planned value ({evm['pv_eur']:,.0f} {ccy}).",
            preventive_action="Re-allocate bandwidth to Critical Path tasks and remove external bottlenecks.",
        )

    # 7. Overall RAG computation
    open_alerts = [a for a in existing_alerts if a.get("status") == "OPEN"]
    if any(a.get("severity") == "CRITICAL" for a in open_alerts) or (t_margin is not None and float(t_margin) < 0):
        state["overall_rag"] = "RED"
    elif open_alerts or qcdr.get("blocking_compliance_open", 0) > 0:
        state["overall_rag"] = "AMBER"
    else:
        state["overall_rag"] = "GREEN"

    return new_alerts


def render_dashboard_html(project_dir: Path, state: Dict[str, Any]) -> Path:
    """Renders the upgraded 360° Q-C-D-R Multi-Section HTML Executive Cockpit."""
    m = state.get("metrics", {})
    evm = m.get("evm", {})
    qcdr = m.get("qcdr", {})
    ccy = state.get("currency", "EUR")
    rag = state.get("overall_rag", "GREEN")
    rag_color = {"GREEN": "#10b981", "AMBER": "#f59e0b", "RED": "#ef4444"}.get(rag, "#64748b")

    tasks = state.get("tasks", [])
    total_days = max(1.0, float(m.get("forecast_duration_days", 1.0)), float(m.get("baseline_duration_days", 1.0)))
    seats = sorted({t.get("owner_seat", "PMO") for t in tasks} | {a.get("source_seat", "PMO") for a in state.get("alerts", [])})
    seat_buttons = ['<button class="chip active" onclick="filterSeat(\'ALL\', this)">All Directors (360°)</button>'] + [
        f'<button class="chip" onclick="filterSeat(\'{html.escape(s)}\', this)">{html.escape(s)}</button>' for s in seats
    ]

    # Alerts HTML
    open_alerts = [a for a in state.get("alerts", []) if a.get("status") == "OPEN"]
    alert_cards = []
    for a in open_alerts:
        sev = a.get("severity", "INFO")
        border = {"CRITICAL": "#ef4444", "WARNING": "#f59e0b", "INFO": "#3b82f6"}.get(sev, "#64748b")
        targets = ", ".join(a.get("target_seats", []))
        seats_attr = " ".join([a.get("source_seat", "")] + a.get("target_seats", []))
        alert_cards.append(
            f'<div class="card alert-card seat-item" data-seats="{html.escape(seats_attr)}" style="border-left:4px solid {border};">'
            f'<div class="alert-top"><span class="badge" style="background:{border};">{html.escape(sev)}</span>'
            f'<span class="tag">{html.escape(a.get("category", ""))}</span>'
            f'<span class="flow">{html.escape(a.get("source_seat", ""))} &rarr; {html.escape(targets)}</span></div>'
            f'<div class="alert-title">{html.escape(a.get("title", ""))}</div>'
            f'<div class="alert-meta"><strong>Cause:</strong> {html.escape(a.get("upstream_cause", ""))}</div>'
            f'<div class="alert-meta"><strong>Action:</strong> {html.escape(a.get("preventive_action", ""))}</div></div>'
        )
    if not alert_cards:
        alert_cards.append('<div class="empty">No active contagion alerts — all Q-C-D-R perimeters aligned.</div>')

    # Gantt rows
    gantt_rows = []
    for t in tasks:
        c = t.get("computed", {})
        b_left = round((c.get("baseline_es", 0) / total_days) * 100.0, 2)
        b_width = max(1.5, round(((c.get("baseline_ef", 0) - c.get("baseline_es", 0)) / total_days) * 100.0, 2))
        f_left = round((c.get("es", 0) / total_days) * 100.0, 2)
        f_width = max(1.5, round((c.get("duration_days", 0) / total_days) * 100.0, 2))
        bar_col = "#ef4444" if c.get("is_critical") else ("#f59e0b" if c.get("is_near_critical") else ("#10b981" if t.get("status") == "DONE" else "#3b82f6"))
        seats_attr = " ".join([t.get("owner_seat", "")] + list(t.get("coupled_seats", {}).keys()))
        crit_tag = ' <span class="mini-badge crit">CRITICAL</span>' if c.get("is_critical") else (' <span class="mini-badge warn">NEAR-CRIT</span>' if c.get("is_near_critical") else "")
        gate_tag = f' <span class="mini-badge gate">{html.escape(str(t.get("hard_gate")))}</span>' if t.get("hard_gate") else ""
        gantt_rows.append(
            f'<div class="gantt-row seat-item" data-seats="{html.escape(seats_attr)}">'
            f'<div class="gantt-label"><strong>{html.escape(t["id"])}</strong> {html.escape(t["name"])}{crit_tag}{gate_tag}'
            f'<div class="sub">{html.escape(t.get("owner_seat", ""))} · {html.escape(t.get("status", ""))} ({t.get("progress_pct", 0)}%) · Float: {c.get("total_float_days", 0)}d · {c.get("forecast_start", "")} &rarr; {c.get("forecast_end", "")}</div></div>'
            f'<div class="gantt-track"><div class="bar-base" style="left:{b_left}%;width:{b_width}%;"></div>'
            f'<div class="bar-live" style="left:{f_left}%;width:{f_width}%;background:{bar_col};"><div class="bar-prog" style="width:{min(100, float(t.get("progress_pct", 0)))}%;"></div></div></div></div>'
        )

    # 5-Column Budget rows
    budget_rows = []
    for t in tasks:
        c = t.get("computed", {})
        vac_t = float(c.get("task_vac_eur", 0))
        v_col = "#ef4444" if vac_t < 0 else "#10b981"
        budget_rows.append(
            f'<tr class="seat-item" data-seats="{html.escape(t.get("owner_seat", ""))}">'
            f'<td><strong>{html.escape(t["id"])}</strong> {html.escape(t["name"])}</td>'
            f'<td>{html.escape(t.get("owner_seat", ""))}</td>'
            f'<td class="num">{float(t.get("planned_budget", 0)):,.0f}</td>'
            f'<td class="num">{float(c.get("approved_changes_eur", 0)):+,.0f}</td>'
            f'<td class="num"><strong>{float(c.get("revised_budget", 0)):,.0f}</strong></td>'
            f'<td class="num">{float(c.get("committed_cost", 0)):,.0f}</td>'
            f'<td class="num">{float(t.get("actual_cost", 0)):,.0f}</td>'
            f'<td class="num">{float(c.get("task_eac_eur", 0)):,.0f}</td>'
            f'<td class="num" style="color:{v_col};font-weight:700;">{vac_t:+,.0f}</td></tr>'
        )

    # Risks rows
    risk_rows = []
    for r in state.get("risk_register", []):
        p = float(r.get("probability_pct", 0))
        ci = float(r.get("cost_impact_eur", 0))
        di = float(r.get("delay_impact_days", 0))
        risk_rows.append(
            f'<tr><td><strong>{html.escape(str(r.get("id", "")))}</strong></td><td>{html.escape(str(r.get("category", "")))}</td>'
            f'<td>{html.escape(str(r.get("title", "")))}<div class="sub">{html.escape(str(r.get("mitigation", "")))}</div></td>'
            f'<td>{html.escape(str(r.get("owner_seat", "")))}</td><td class="num">{p:.0f}%</td>'
            f'<td class="num">{ci * p / 100.0:,.0f} {ccy}</td><td class="num">{di * p / 100.0:.1f}d</td><td>{html.escape(str(r.get("status", "OPEN")))}</td></tr>'
        )

    # HSE / Compliance / Reserves rows
    comp_rows = []
    for c in state.get("compliance_register", []):
        blk = '<span class="mini-badge crit">BLOCKER</span>' if c.get("blocking_go_live", True) else ""
        cert = "✅ ISSUED" if c.get("certificate_issued") else "❌ MISSING"
        comp_rows.append(
            f'<tr><td><strong>{html.escape(str(c.get("id", "")))}</strong> {blk}</td><td>{html.escape(str(c.get("standard", "")))}</td>'
            f'<td>{html.escape(str(c.get("requirement", "")))}<div class="sub">Reserves: {html.escape(str(c.get("reserves") or "None"))}</div></td>'
            f'<td>{html.escape(str(c.get("status", "")))}</td><td>{"Done" if c.get("test_completed") else "Pending"} ({html.escape(str(c.get("test_date", "TBD")))})</td>'
            f'<td class="num">+{float(c.get("remediation_cost_eur", 0)):,.0f} {ccy} / +{float(c.get("remediation_delay_days", 0))}d</td>'
            f'<td>{cert}</td></tr>'
        )

    # Contracts rows
    ct_rows = []
    for ct in state.get("contracts_register", []):
        susp = ' <span class="mini-badge warn">SUSPENSIVE</span>' if ct.get("is_suspensive_condition") else ""
        hse_b = ' <span class="mini-badge gate">HSE</span>' if ct.get("hse_compliance_linked") else ""
        ct_rows.append(
            f'<tr><td><strong>{html.escape(str(ct.get("id", "")))}</strong>{susp}{hse_b}</td><td>{html.escape(str(ct.get("counterparty", "")))}</td>'
            f'<td>{html.escape(str(ct.get("clause_topic", "")))}<div class="sub">Target: {html.escape(str(ct.get("target_position", "")))}</div></td>'
            f'<td>{html.escape(str(ct.get("deadline", "N/A")))}</td><td class="num">{float(ct.get("financial_exposure_eur", 0)):,.0f} {ccy}</td>'
            f'<td><strong>{html.escape(str(ct.get("status", "")))}</strong></td></tr>'
        )

    t_margin = m.get("target_margin_days")
    deadline_sub = f"Hard Target: {m.get('target_end_date')} (Slack: {t_margin:+.1f}d)" if m.get("target_end_date") else f"P85 Buffered: {m.get('p85_duration_days', 0)}d"

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>ExCom v3.3 Control Tower — {html.escape(state.get('project_name', 'Project'))}</title>
<style>
  :root {{ --bg:#0b1120; --panel:#111827; --card:#1e293b; --text:#f1f5f9; --muted:#94a3b8; --border:#334155; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:var(--bg); color:var(--text); line-height:1.45; }}
  .wrap {{ max-width:1420px; margin:0 auto; padding:24px; }}
  header {{ display:flex; justify-content:space-between; align-items:flex-start; gap:16px; border-bottom:1px solid var(--border); padding-bottom:16px; margin-bottom:20px; }}
  h1 {{ margin:0 0 6px; font-size:1.55rem; }}
  .meta {{ color:var(--muted); font-size:0.86rem; }}
  .rag-pill {{ padding:8px 16px; border-radius:999px; font-weight:700; font-size:0.9rem; background:{rag_color}; color:#fff; white-space:nowrap; }}
  .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; margin-bottom:20px; }}
  .kpi {{ background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:14px; }}
  .kpi .lbl {{ color:var(--muted); font-size:0.74rem; text-transform:uppercase; letter-spacing:0.05em; }}
  .kpi .val {{ font-size:1.38rem; font-weight:700; margin-top:4px; }}
  .kpi .sub {{ font-size:0.78rem; color:var(--muted); margin-top:4px; }}
  .filter-bar {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:18px; align-items:center; }}
  .chip {{ background:var(--panel); color:var(--text); border:1px solid var(--border); border-radius:999px; padding:5px 12px; cursor:pointer; font-size:0.8rem; }}
  .chip.active {{ background:#2563eb; border-color:#2563eb; }}
  section {{ background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:18px; margin-bottom:18px; overflow-x:auto; }}
  h2 {{ margin:0 0 12px; font-size:1.08rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; }}
  .card {{ background:var(--card); border-radius:8px; padding:12px 14px; margin-bottom:10px; }}
  .alert-top {{ display:flex; gap:8px; align-items:center; margin-bottom:6px; flex-wrap:wrap; }}
  .badge {{ padding:2px 8px; border-radius:4px; font-size:0.72rem; font-weight:700; color:#fff; }}
  .tag {{ background:#334155; padding:2px 8px; border-radius:4px; font-size:0.72rem; }}
  .flow {{ color:#93c5fd; font-size:0.8rem; font-weight:600; }}
  .alert-title {{ font-weight:600; margin-bottom:4px; }}
  .alert-meta {{ font-size:0.82rem; color:var(--muted); }}
  .gantt-row {{ display:grid; grid-template-columns:340px 1fr; gap:14px; align-items:center; padding:8px 0; border-bottom:1px solid #1e293b; }}
  .gantt-label {{ font-size:0.86rem; }}
  .gantt-label .sub {{ font-size:0.74rem; color:var(--muted); margin-top:2px; }}
  .gantt-track {{ position:relative; height:24px; background:#0f172a; border-radius:6px; overflow:hidden; }}
  .bar-base {{ position:absolute; top:3px; height:6px; background:#475569; border-radius:3px; }}
  .bar-live {{ position:absolute; top:11px; height:10px; border-radius:4px; overflow:hidden; }}
  .bar-prog {{ height:100%; background:rgba(255,255,255,0.38); }}
  .mini-badge {{ font-size:0.65rem; padding:1px 6px; border-radius:4px; font-weight:700; vertical-align:middle; }}
  .mini-badge.crit {{ background:#991b1b; color:#fecaca; }}
  .mini-badge.warn {{ background:#92400e; color:#fef3c7; }}
  .mini-badge.gate {{ background:#1d4ed8; color:#dbeafe; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.82rem; }}
  th, td {{ padding:8px 10px; border-bottom:1px solid #1e293b; text-align:left; vertical-align:top; }}
  th {{ color:var(--muted); font-weight:600; font-size:0.74rem; text-transform:uppercase; }}
  .num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  .sub {{ font-size:0.74rem; color:var(--muted); margin-top:2px; }}
  .empty {{ color:var(--muted); font-style:italic; padding:8px 0; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>ExCom v3.3 — 360° Q-C-D-R Control Tower : {html.escape(state.get('project_name', 'Project'))}</h1>
      <div class="meta">Methodology: <strong>{html.escape(str(state.get('methodology_id', 'PREDICTIVE_STAGE_GATE')))}</strong> · Start: {html.escape(state.get('start_date', ''))} · As-Of: {html.escape(m.get('as_of_date', ''))} · Exports: MS Project XML · Excel 7-Tab (.xlsx) · iCal (.ics) · CSV</div>
    </div>
    <div class="rag-pill">RAG: {html.escape(rag)}</div>
  </header>

  <div class="kpis">
    <div class="kpi">
      <div class="lbl">Schedule &amp; Hard Deadline</div>
      <div class="val">{html.escape(m.get('forecast_end_date', ''))}</div>
      <div class="sub">{html.escape(deadline_sub)} · Progress: {m.get('overall_progress_pct', 0)}%</div>
    </div>
    <div class="kpi">
      <div class="lbl">5-Column Budget ({ccy})</div>
      <div class="val">{evm.get('eac_eur', 0):,.0f} EAC</div>
      <div class="sub">Revised: {evm.get('revised_budget_eur', 0):,.0f} · VAC: {evm.get('vac_eur', 0):+,.0f} · Contingency left: {evm.get('contingency_remaining_eur', 0):,.0f}</div>
    </div>
    <div class="kpi">
      <div class="lbl">Multi-Year TCO ({evm.get('tco_horizon_years', 6)}y)</div>
      <div class="val">{evm.get('tco_total_eur', 0):,.0f} {ccy}</div>
      <div class="sub">Annual OPEX: {evm.get('recurring_annual_opex_eur', 0):,.0f} · CPI {evm.get('cpi', 1.0)} / SPI {evm.get('spi', 1.0)}</div>
    </div>
    <div class="kpi">
      <div class="lbl">HSE / Compliance Go-Live Gate</div>
      <div class="val">{html.escape(qcdr.get('go_live_gate_status', 'READY'))}</div>
      <div class="sub">Certs: {qcdr.get('certificates_pct', 100)}% · Blockers: {qcdr.get('blocking_compliance_open', 0)} · Open Reserves: {qcdr.get('open_reserves_count', 0)}</div>
    </div>
    <div class="kpi">
      <div class="lbl">Risks (EMV) &amp; Contracts</div>
      <div class="val">{qcdr.get('risk_emv_eur', 0):,.0f} {ccy}</div>
      <div class="sub">Exp. Delay: {qcdr.get('risk_expected_delay_days', 0)}d · Suspensive Open: {qcdr.get('open_suspensive_conditions', 0)} · Alerts: {len(open_alerts)}</div>
    </div>
  </div>

  <div class="filter-bar">
    <span style="font-size:0.82rem;color:var(--muted);font-weight:600;">Filter by Director:</span>
    {''.join(seat_buttons)}
  </div>

  <section>
    <h2><span>1. Upstream Cross-Perimeter Contagion Radar</span><span style="font-size:0.8rem;color:var(--muted);">{len(open_alerts)} open alerts</span></h2>
    {''.join(alert_cards)}
  </section>

  <section>
    <h2><span>2. CPM Critical-Path Gantt (FS/SS/FF + Hard Target)</span><span style="font-size:0.8rem;color:var(--muted);">Critical Path: {html.escape(' -> '.join(m.get('critical_path', [])))}</span></h2>
    {''.join(gantt_rows)}
  </section>

  <section>
    <h2><span>3. 5-Column Budget &amp; Change-Order Control ({ccy})</span><span style="font-size:0.8rem;color:var(--muted);">Envelope incl. Contingency + Mgmt Reserve: {evm.get('total_envelope_eur', 0):,.0f} {ccy}</span></h2>
    <table>
      <thead><tr><th>Workstream</th><th>Owner</th><th class="num">Initial BAC</th><th class="num">Approved TMA</th><th class="num">Revised</th><th class="num">Committed</th><th class="num">Actual AC</th><th class="num">Landing EAC</th><th class="num">Variance</th></tr></thead>
      <tbody>{''.join(budget_rows)}</tbody>
    </table>
  </section>

  <section>
    <h2><span>4. HSE, Regulatory Compliance, Testing &amp; Punch-List Reserves (Go-Live Gate)</span><span style="font-size:0.8rem;color:var(--muted);">Remediation impact: +{qcdr.get('compliance_remediation_cost_eur', 0):,.0f} {ccy} / +{qcdr.get('compliance_remediation_delay_days', 0)}d</span></h2>
    {('<table><thead><tr><th>ID</th><th>Standard</th><th>Requirement &amp; Reserves</th><th>Status</th><th>Test</th><th class="num">Remediation Impact</th><th>Certificate</th></tr></thead><tbody>' + ''.join(comp_rows) + '</tbody></table>') if comp_rows else '<div class="empty">No compliance/HSE items registered yet.</div>'}
  </section>

  <section>
    <h2><span>5. Contractual Negotiation &amp; Suspensive Conditions</span><span style="font-size:0.8rem;color:var(--muted);">Open exposure: {qcdr.get('contracts_open_exposure_eur', 0):,.0f} {ccy}</span></h2>
    {('<table><thead><tr><th>ID</th><th>Counterparty</th><th>Clause &amp; Target Position</th><th>Deadline</th><th class="num">Exposure</th><th>Status</th></tr></thead><tbody>' + ''.join(ct_rows) + '</tbody></table>') if ct_rows else '<div class="empty">No contracts/negotiation clauses registered yet.</div>'}
  </section>

  <section>
    <h2><span>6. Quantified 360° Risk Register (EMV)</span><span style="font-size:0.8rem;color:var(--muted);">Total EMV: {qcdr.get('risk_emv_eur', 0):,.0f} {ccy} · {qcdr.get('risk_expected_delay_days', 0)}d</span></h2>
    {('<table><thead><tr><th>ID</th><th>Category</th><th>Risk &amp; Mitigation</th><th>Owner</th><th class="num">Prob</th><th class="num">EMV Cost</th><th class="num">Exp. Delay</th><th>Status</th></tr></thead><tbody>' + ''.join(risk_rows) + '</tbody></table>') if risk_rows else '<div class="empty">No risks registered yet.</div>'}
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


def save_and_refresh(project_dir: Path, state: Dict[str, Any], as_of: Optional[str] = None) -> Tuple[Path, List[Dict[str, Any]], Dict[str, str]]:
    state["schema_version"] = SCHEMA_VERSION
    state["updated_at"] = now_iso()
    compute_schedule_and_evm(state, as_of_str=as_of)
    new_alerts = run_contagion_radar(state, project_dir=project_dir)
    write_json(project_dir / "project-state.json", state)
    export_enterprise_csvs(project_dir, state)
    msp_xml = export_msproject_xml(project_dir, state)
    xlsx_wb = export_excel_xlsx(project_dir, state)
    ics_cal = export_icalendar_ics(project_dir, state)
    pptx_deck = export_copil_pptx(project_dir, state)
    docx_rep = export_copil_docx(project_dir, state)
    dash = render_dashboard_html(project_dir, state)
    artifacts = {
        "dashboard_html": str(dash),
        "msproject_xml": str(msp_xml),
        "excel_xlsx": str(xlsx_wb),
        "calendar_ics": str(ics_cal),
        "copil_pptx": str(pptx_deck),
        "copil_docx": str(docx_rep),
        "exports_dir": str(project_dir / "exports"),
    }
    return dash, new_alerts, artifacts


# ---------------------------------------------------------------------------
# CLI Subcommands
# ---------------------------------------------------------------------------

def cmd_select_methodology(args: argparse.Namespace) -> None:
    res = select_methodology(
        description=args.description,
        project_type=args.project_type,
        uncertainty=args.uncertainty,
        regulatory_irreversibility=args.regulatory,
        capital_intensity=args.capital,
        delivery_cadence=args.cadence,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))


def cmd_init(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    spec = read_json(Path(args.spec).resolve())
    if not spec.get("methodology_id"):
        meth = select_methodology(
            description=str(spec.get("locked_decision", "")) + " " + str(spec.get("project_name", "")),
            project_type=str(spec.get("project_type", "")),
        )
        spec["methodology_id"] = meth["methodology_id"]
    (project_dir / "deliverables").mkdir(parents=True, exist_ok=True)
    dash, new_alerts, artifacts = save_and_refresh(project_dir, spec)
    append_event(project_dir, {
        "type": "PROJECT_INITIALIZED",
        "actor": "PMO",
        "project_name": spec.get("project_name", ""),
        "methodology_id": spec.get("methodology_id"),
        "tasks_count": len(spec.get("tasks", [])),
    })
    print(json.dumps({
        "status": "OK",
        "project_dir": str(project_dir),
        "methodology_id": spec.get("methodology_id"),
        "overall_rag": spec.get("overall_rag"),
        "critical_path": spec["metrics"]["critical_path"],
        "target_margin_days": spec["metrics"].get("target_margin_days"),
        "go_live_gate_status": spec["metrics"]["qcdr"]["go_live_gate_status"],
        "open_alerts_count": len([a for a in spec.get("alerts", []) if a.get("status") == "OPEN"]),
        "new_alerts_raised": len(new_alerts),
        "artifacts": artifacts,
    }, ensure_ascii=False, indent=2))


def cmd_update_task(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    target = next((t for t in state.get("tasks", []) if t["id"] == args.id), None)
    if target is None:
        sys.exit(f"Error: task '{args.id}' not found.")

    changes: Dict[str, Any] = {}
    for attr, key in (
        ("status", "status"), ("progress", "progress_pct"), ("forecast_days", "forecast_days"),
        ("committed_cost", "committed_cost"), ("actual_cost", "actual_cost"), ("etc_cost", "etc_cost"), ("note", "notes"),
    ):
        val = getattr(args, attr, None)
        if val is not None:
            target[key] = val
            changes[key] = val

    append_event(project_dir, {"type": "TASK_UPDATED", "actor": args.actor, "task_id": args.id, "changes": changes})
    _, new_alerts, artifacts = save_and_refresh(project_dir, state, as_of=args.as_of)
    print(json.dumps({
        "status": "OK", "updated_task": args.id, "overall_rag": state.get("overall_rag"),
        "new_contagion_alerts": new_alerts, "artifacts": artifacts,
    }, ensure_ascii=False, indent=2))


def cmd_add_change_order(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    co = {
        "id": args.id or f"TMA-{len(state.get('change_orders', [])) + 1:03d}",
        "date": now_iso()[:10],
        "title": args.title,
        "linked_task_id": args.task_id or "",
        "owner_seat": args.owner_seat,
        "approved_by": args.approved_by,
        "cost_impact_eur": float(args.cost_impact),
        "delay_impact_days": float(args.delay_impact),
        "status": args.status,
    }
    state.setdefault("change_orders", []).append(co)
    append_event(project_dir, {"type": "CHANGE_ORDER_LOGGED", **co})
    _, new_alerts, artifacts = save_and_refresh(project_dir, state)
    print(json.dumps({"status": "OK", "change_order": co, "overall_rag": state.get("overall_rag"), "new_alerts": new_alerts, "artifacts": artifacts}, ensure_ascii=False, indent=2))


def cmd_upsert_risk(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    risks = state.setdefault("risk_register", [])
    existing = next((r for r in risks if r.get("id") == args.id), None)
    rec = {
        "id": args.id,
        "category": args.category,
        "title": args.title,
        "owner_seat": args.owner_seat,
        "probability_pct": float(args.probability),
        "cost_impact_eur": float(args.cost_impact),
        "delay_impact_days": float(args.delay_impact),
        "mitigation": args.mitigation,
        "status": args.status,
    }
    if existing:
        existing.update(rec)
    else:
        risks.append(rec)
    append_event(project_dir, {"type": "RISK_UPSERTED", **rec})
    _, new_alerts, artifacts = save_and_refresh(project_dir, state)
    print(json.dumps({"status": "OK", "risk": rec, "overall_rag": state.get("overall_rag"), "new_alerts": new_alerts, "artifacts": artifacts}, ensure_ascii=False, indent=2))


def cmd_upsert_compliance(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    comp = state.setdefault("compliance_register", [])
    existing = next((c for c in comp if c.get("id") == args.id), None)
    rec = {
        "id": args.id,
        "domain": args.domain,
        "requirement": args.requirement,
        "standard": args.standard,
        "status": args.status,
        "test_required": not bool(args.no_test_required),
        "test_completed": bool(args.test_completed),
        "test_date": args.test_date or "",
        "reserves": args.reserves or "",
        "linked_task_id": args.task_id or "",
        "remediation_cost_eur": float(args.remediation_cost),
        "remediation_delay_days": float(args.remediation_delay),
        "reserves_lifted": bool(args.reserves_lifted),
        "certificate_issued": bool(args.certificate_issued),
        "blocking_go_live": not bool(args.non_blocking),
        "owner_seat": args.owner_seat,
    }
    if existing:
        existing.update(rec)
    else:
        comp.append(rec)
    append_event(project_dir, {"type": "COMPLIANCE_HSE_UPSERTED", **rec})
    _, new_alerts, artifacts = save_and_refresh(project_dir, state)
    print(json.dumps({"status": "OK", "compliance_item": rec, "go_live_gate_status": state["metrics"]["qcdr"]["go_live_gate_status"], "overall_rag": state.get("overall_rag"), "new_alerts": new_alerts, "artifacts": artifacts}, ensure_ascii=False, indent=2))


def cmd_upsert_contract(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    cts = state.setdefault("contracts_register", [])
    existing = next((c for c in cts if c.get("id") == args.id), None)
    rec = {
        "id": args.id,
        "contract_type": args.contract_type,
        "counterparty": args.counterparty,
        "clause_topic": args.clause_topic,
        "target_position": args.target_position,
        "counterparty_position": args.counterparty_position,
        "hse_compliance_linked": bool(args.hse_linked),
        "is_suspensive_condition": bool(args.suspensive),
        "deadline": args.deadline or "",
        "financial_exposure_eur": float(args.exposure),
        "status": args.status,
        "owner_seat": args.owner_seat,
    }
    if existing:
        existing.update(rec)
    else:
        cts.append(rec)
    append_event(project_dir, {"type": "CONTRACT_UPSERTED", **rec})
    _, new_alerts, artifacts = save_and_refresh(project_dir, state)
    print(json.dumps({"status": "OK", "contract": rec, "overall_rag": state.get("overall_rag"), "new_alerts": new_alerts, "artifacts": artifacts}, ensure_ascii=False, indent=2))


def cmd_import_external(args: argparse.Namespace) -> None:
    """Bidirectional import from MS Project XML or Excel/Smartsheet/Jira CSV into live Control Tower."""
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    src_path = Path(args.file).resolve()
    if args.cmd == "import-msproject":
        incoming = import_msproject_xml(src_path)
    else:
        incoming = import_tasks_csv(src_path)

    by_id = {t["id"]: t for t in state.get("tasks", [])}
    updated, added = 0, 0
    for item in incoming:
        tid = item["id"]
        if tid in by_id:
            for k, v in item.items():
                if k != "id" and v not in ("", None):
                    by_id[tid][k] = v
            updated += 1
        else:
            state.setdefault("tasks", []).append({
                "id": tid,
                "phase": item.get("phase", "Imported"),
                "name": item.get("name", tid),
                "owner_seat": item.get("owner_seat", "PMO"),
                "depends_on": item.get("depends_on", []),
                "duration_days": item.get("forecast_days", 5.0),
                "forecast_days": item.get("forecast_days", 5.0),
                "planned_budget": item.get("planned_budget", 0.0),
                "actual_cost": item.get("actual_cost", 0.0),
                "progress_pct": item.get("progress_pct", 0.0),
                "status": item.get("status", "TODO"),
                "notes": item.get("notes", ""),
            })
            added += 1

    append_event(project_dir, {"type": "EXTERNAL_IMPORT", "source": str(src_path), "updated": updated, "added": added})
    _, new_alerts, artifacts = save_and_refresh(project_dir, state)
    print(json.dumps({"status": "OK", "imported_from": str(src_path), "tasks_updated": updated, "tasks_added": added, "overall_rag": state.get("overall_rag"), "new_alerts": len(new_alerts), "artifacts": artifacts}, ensure_ascii=False, indent=2))


def cmd_export_copil(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    _, _, artifacts = save_and_refresh(project_dir, state, as_of=args.as_of)
    brief = export_copil_brief(project_dir, state)
    print(json.dumps({
        "status": "OK",
        "copil_brief_md": str(brief),
        "copil_deck_pptx": artifacts["copil_pptx"],
        "copil_report_docx": artifacts["copil_docx"],
        "artifacts": artifacts,
    }, ensure_ascii=False, indent=2))


def cmd_generate_space_plan(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    project_dir.mkdir(parents=True, exist_ok=True)
    if args.spec:
        spec = read_json(Path(args.spec).resolve())
    elif (project_dir / "project-state.json").is_file():
        st = read_json(project_dir / "project-state.json")
        spec = st.get("space_plan", {"title": f"{st.get('project_name', 'Floorplate')} — Space Plan"})
    else:
        spec = {"title": "Corporate Floorplate — Macro & Micro-Zoning"}
    res = generate_space_plan_dxf(project_dir, spec)
    print(json.dumps({"status": "OK", **res}, ensure_ascii=False, indent=2))


def cmd_audit_dxf(args: argparse.Namespace) -> None:
    dxf_path = Path(args.file).resolve()
    if not dxf_path.is_file():
        sys.exit(f"Error: DXF file not found: {dxf_path}")
    res = audit_dxf_file(dxf_path)
    print(json.dumps({"status": "OK", **res}, ensure_ascii=False, indent=2))


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
    append_event(project_dir, {"type": "CROSS_DIRECTOR_SIGNAL", "signal_id": alert["id"], "from_seat": args.from_seat, "target_seats": targets, "title": args.title})
    _, _, artifacts = save_and_refresh(project_dir, state)
    print(json.dumps({"status": "OK", "signal_id": alert["id"], "woken_target_seats": targets, "overall_rag": state.get("overall_rag"), "artifacts": artifacts}, ensure_ascii=False, indent=2))


def cmd_register_deliverable(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    entry = {"id": f"DLV-{uuid.uuid4().hex[:6].upper()}", "created_at": now_iso(), "seat": args.seat, "task_id": args.task_id, "title": args.title, "path": args.path, "summary": args.summary}
    state.setdefault("deliverables", []).append(entry)
    append_event(project_dir, {"type": "DELIVERABLE_PUBLISHED", **entry})
    _, _, artifacts = save_and_refresh(project_dir, state)
    print(json.dumps({"status": "OK", "deliverable": entry, "artifacts": artifacts}, ensure_ascii=False, indent=2))


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
    append_event(project_dir, {"type": "ALERT_RESOLVED", "alert_id": args.alert_id, "by_seat": args.by_seat, "resolution": args.resolution})
    _, _, artifacts = save_and_refresh(project_dir, state)
    print(json.dumps({"status": "OK", "overall_rag": state.get("overall_rag"), "artifacts": artifacts}, ensure_ascii=False, indent=2))


def cmd_audit(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    state = read_json(project_dir / "project-state.json")
    if args.as_of:
        state["as_of_date"] = args.as_of
    _, new_alerts, artifacts = save_and_refresh(project_dir, state, as_of=args.as_of)
    open_alerts = [a for a in state.get("alerts", []) if a.get("status") == "OPEN"]
    seats_to_summon = sorted({s for a in open_alerts for s in a.get("target_seats", [])})
    print(json.dumps({
        "overall_rag": state.get("overall_rag"),
        "methodology_id": state.get("methodology_id"),
        "metrics": state.get("metrics"),
        "open_alerts_count": len(open_alerts),
        "newly_detected_alerts": len(new_alerts),
        "directors_to_summon_preemptively": seats_to_summon,
        "open_alerts": open_alerts,
        "artifacts": artifacts,
    }, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ExCom v3.3 — 360° Enterprise Q-C-D-R Control Tower & Interchange CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_sel = sub.add_parser("select-methodology", help="Deterministically select optimal project methodology & WBS structure")
    p_sel.add_argument("--description", default="")
    p_sel.add_argument("--project-type", default="")
    p_sel.add_argument("--uncertainty", choices=["LOW", "MEDIUM", "HIGH"], default="MEDIUM")
    p_sel.add_argument("--regulatory", choices=["LOW", "MEDIUM", "HIGH"], default="MEDIUM")
    p_sel.add_argument("--capital", choices=["LOW", "MEDIUM", "HIGH"], default="MEDIUM")
    p_sel.add_argument("--cadence", choices=["MILESTONE", "ITERATIVE", "CONTINUOUS"], default="MILESTONE")
    p_sel.set_defaults(func=cmd_select_methodology)

    p_init = sub.add_parser("init", help="Initialize 360° Q-C-D-R Control Tower & export MS Project XML / Excel / ICS / CSV")
    p_init.add_argument("--project-dir", required=True)
    p_init.add_argument("--spec", required=True)
    p_init.set_defaults(func=cmd_init)

    p_upd = sub.add_parser("update-task", help="Update task schedule/budget/progress and propagate contagion")
    p_upd.add_argument("--project-dir", required=True)
    p_upd.add_argument("--id", required=True)
    p_upd.add_argument("--actor", required=True)
    p_upd.add_argument("--status", choices=["TODO", "IN_PROGRESS", "BLOCKED", "DONE"])
    p_upd.add_argument("--progress", type=float)
    p_upd.add_argument("--forecast-days", type=float)
    p_upd.add_argument("--committed-cost", type=float)
    p_upd.add_argument("--actual-cost", type=float)
    p_upd.add_argument("--etc-cost", type=float)
    p_upd.add_argument("--note")
    p_upd.add_argument("--as-of")
    p_upd.set_defaults(func=cmd_update_task)

    p_co = sub.add_parser("add-change-order", help="Log a formal Change Order / TMA affecting 5-column budget & schedule")
    p_co.add_argument("--project-dir", required=True)
    p_co.add_argument("--id", default="")
    p_co.add_argument("--title", required=True)
    p_co.add_argument("--task-id", default="")
    p_co.add_argument("--owner-seat", default="PMO")
    p_co.add_argument("--approved-by", default="Sponsor")
    p_co.add_argument("--cost-impact", type=float, required=True)
    p_co.add_argument("--delay-impact", type=float, default=0.0)
    p_co.add_argument("--status", choices=["PENDING", "APPROVED", "REJECTED"], default="PENDING")
    p_co.set_defaults(func=cmd_add_change_order)

    p_rk = sub.add_parser("upsert-risk", help="Add or update a quantified EMV risk in the 360° Risk Register")
    p_rk.add_argument("--project-dir", required=True)
    p_rk.add_argument("--id", required=True)
    p_rk.add_argument("--category", required=True)
    p_rk.add_argument("--title", required=True)
    p_rk.add_argument("--owner-seat", default="CRO-Risk")
    p_rk.add_argument("--probability", type=float, required=True)
    p_rk.add_argument("--cost-impact", type=float, required=True)
    p_rk.add_argument("--delay-impact", type=float, default=0.0)
    p_rk.add_argument("--mitigation", default="")
    p_rk.add_argument("--status", choices=["OPEN", "MITIGATED", "CLOSED"], default="OPEN")
    p_rk.set_defaults(func=cmd_upsert_risk)

    p_cp = sub.add_parser("upsert-compliance", help="Add or update an HSE / Regulatory Compliance / Testing / Reserve item")
    p_cp.add_argument("--project-dir", required=True)
    p_cp.add_argument("--id", required=True)
    p_cp.add_argument("--domain", default="HSE")
    p_cp.add_argument("--requirement", required=True)
    p_cp.add_argument("--standard", default="")
    p_cp.add_argument("--status", choices=["PENDING", "IN_PROGRESS", "COMPLIANT", "NON_COMPLIANT", "WITH_RESERVES", "BLOCKED"], default="PENDING")
    p_cp.add_argument("--no-test-required", action="store_true")
    p_cp.add_argument("--test-completed", action="store_true")
    p_cp.add_argument("--test-date", default="")
    p_cp.add_argument("--reserves", default="")
    p_cp.add_argument("--task-id", default="")
    p_cp.add_argument("--remediation-cost", type=float, default=0.0)
    p_cp.add_argument("--remediation-delay", type=float, default=0.0)
    p_cp.add_argument("--reserves-lifted", action="store_true")
    p_cp.add_argument("--certificate-issued", action="store_true")
    p_cp.add_argument("--non-blocking", action="store_true")
    p_cp.add_argument("--owner-seat", default="CCO-Compliance")
    p_cp.set_defaults(func=cmd_upsert_compliance)

    p_ct = sub.add_parser("upsert-contract", help="Add or update a contractual negotiation clause / suspensive condition")
    p_ct.add_argument("--project-dir", required=True)
    p_ct.add_argument("--id", required=True)
    p_ct.add_argument("--contract-type", required=True)
    p_ct.add_argument("--counterparty", required=True)
    p_ct.add_argument("--clause-topic", required=True)
    p_ct.add_argument("--target-position", default="")
    p_ct.add_argument("--counterparty-position", default="")
    p_ct.add_argument("--hse-linked", action="store_true")
    p_ct.add_argument("--suspensive", action="store_true")
    p_ct.add_argument("--deadline", default="")
    p_ct.add_argument("--exposure", type=float, default=0.0)
    p_ct.add_argument("--status", choices=["DRAFT", "NEGOTIATING", "DISPUTED", "SIGNED", "LIFTED", "REJECTED"], default="NEGOTIATING")
    p_ct.add_argument("--owner-seat", default="CLO")
    p_ct.set_defaults(func=cmd_upsert_contract)

    p_imp_xml = sub.add_parser("import-msproject", help="Import/sync tasks from MS Project / Primavera / Smartsheet MSPDI .xml")
    p_imp_xml.add_argument("--project-dir", required=True)
    p_imp_xml.add_argument("--file", required=True)
    p_imp_xml.set_defaults(func=cmd_import_external)

    p_imp_csv = sub.add_parser("import-csv", help="Import/sync tasks from Excel/Smartsheet/Jira CSV (comma or semicolon)")
    p_imp_csv.add_argument("--project-dir", required=True)
    p_imp_csv.add_argument("--file", required=True)
    p_imp_csv.set_defaults(func=cmd_import_external)

    p_copil = sub.add_parser("export-copil", help="Generate 1-click CoPil Executive Pack (PowerPoint .pptx + Word .docx + Markdown)")
    p_copil.add_argument("--project-dir", required=True)
    p_copil.add_argument("--as-of", default=None)
    p_copil.set_defaults(func=cmd_export_copil)

    p_sp = sub.add_parser("generate-space-plan", help="Generate parametric AutoCAD .dxf (Macro + Micro-Zoning), scaled .svg & Workplace Audit JSON")
    p_sp.add_argument("--project-dir", required=True)
    p_sp.add_argument("--spec", default="", help="Optional JSON floorplan specification (dimensions, zones, desk specs)")
    p_sp.set_defaults(func=cmd_generate_space_plan)

    p_adxf = sub.add_parser("audit-dxf", help="Audit layers, bounding box, and closed-polygon m2 areas in any ASCII AutoCAD .dxf file")
    p_adxf.add_argument("--file", required=True)
    p_adxf.set_defaults(func=cmd_audit_dxf)

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

    p_aud = sub.add_parser("audit", help="Run a 360° Q-C-D-R, EVM, HSE, Contracts & Contagion audit")
    p_aud.add_argument("--project-dir", required=True)
    p_aud.add_argument("--as-of")
    p_aud.set_defaults(func=cmd_audit)

    return p


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    ns = parser.parse_args()
    ns.func(ns)
