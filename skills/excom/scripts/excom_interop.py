#!/usr/bin/env python3
"""ExCom v3.3 — Adaptive Methodology Selector & Zero-Dependency Enterprise Interchange Engine.

100% Python 3.8+ standard library (zero external pip dependencies).
Provides market-standard bidirectional compatibility across corporate PMO/ERP/planning tools:
  1. Adaptive Methodology Selector (`select_methodology`): routes any project into 6 standard
     methodologies (Predictive/Stage-Gate, Hybrid, Agile Scrum, Lean/Kanban/TOC, Scientific R&D,
     Patrimonial Advisory) with tailored WBS phases, gates, Clean-Room Board panel, and domain pack.
  2. MS Project XML (`MSPDI`) Export & Import (`schedule_msproject.xml`): opens natively in
     Microsoft Project, Primavera P6, Smartsheet, ProjectLibre, GanttProject, Monday.com, Wrike.
  3. Native Multi-Sheet Excel Workbook (`control_tower_workbook.xlsx`, 7 enterprise tabs) written
     directly as valid OOXML SpreadsheetML via stdlib `zipfile` (native numeric cells + styled headers).
  4. UTF-8-BOM CSV Suite + Jira/Asana/Monday Import CSV + Bidirectional CSV Import (`;` and `,`).
  5. RFC 5545 iCalendar (`milestones_calendar.ics`) for 1-click Outlook / Google Calendar import.
  6. 1-Click Steering Committee (`CoPil`) Executive Brief (`PMO_CoPil_Executive_Brief.md`).
"""

from __future__ import annotations

import csv
import datetime as dt
import io
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET
import zipfile


METHODOLOGY_CATALOG: Dict[str, Dict[str, Any]] = {
    "PREDICTIVE_STAGE_GATE": {
        "name": "Predictive / Stage-Gate (PMI Predictive · Loi MOP · RIBA · PRINCE2)",
        "best_for": "Corporate Real Estate, Ground-Up Construction (MOA/BEFA/VEFA), Industrial Capex, Infrastructure, Hardware BOM, Legal/M&A",
        "clean_room_policy": "EVERY_MAJOR_MILESTONE",
        "clean_room_panel": [
            {"role": "technical_quality_hse_auditor", "focus": "Plans, building codes, ERP/IGH/ICPE/HSE testing, reserves & commissioning"},
            {"role": "finance_tco_contracts_auditor", "focus": "5-column budget, TCO, change orders, lease/construction redlines & insurances"},
            {"role": "devil_schedule_compliance_auditor", "focus": "Hard target deadline negative float, hidden regulatory lead times & suspensive clauses"},
        ],
        "mandatory_registers": [
            "tasks_cpm", "budget_5col", "change_orders", "risk_register",
            "compliance_register", "contracts_register", "raci_matrix", "decision_log",
        ],
        "default_stage_gates": [
            {"gate": "SG0", "phase": "Feasibility & Site/Asset Search", "freeze": "Mandate, TCO Envelope & Hard Deadline Locked"},
            {"gate": "SG1", "phase": "Due Diligence, HSE Audit & Contract Negotiation", "freeze": "Lease/BEFA/Purchase Signed with Suspensive Conditions"},
            {"gate": "SG2", "phase": "Program & Design Freeze (APS -> APD -> Permits)", "freeze": "Space Plan, Technical Specs & Permits (PC/AT ERP/ICPE) Purged"},
            {"gate": "SG3", "phase": "Procurement & Tender Award (PRO/DCE -> ACT)", "freeze": "Contractor Bids, DO/TRC/Decennale Insurances & Subcontractors Approved"},
            {"gate": "SG4", "phase": "Construction, Fit-Out & Technical Execution (EXE)", "freeze": "Works Complete, TMA Log Balanced, CSE Consulted"},
            {"gate": "SG5", "phase": "Commissioning, OPR, Reserves & Compliance Certificates", "freeze": "100% Blocking HSE/ERP/ICPE Certificates Issued & Critical Reserves Lifted"},
            {"gate": "SG6", "phase": "Handover, Move-In, Hypercare & Old-Site Dilapidations", "freeze": "DOE/DIUO Delivered, Teams Operational, GPA/1yr Warranty Active"},
        ],
        "interchange_formats": ["MS Project XML (.xml)", "Excel 7-Tab (.xlsx)", "UTF-8-BOM CSV", "iCalendar (.ics)", "Google Sheets/Docs"],
    },
    "HYBRID_STAGE_GATE_AGILE": {
        "name": "Hybrid Stage-Gate + Iterative Agile (PMI Hybrid · PM²)",
        "best_for": "Workplace Fit-Out + IT/Digital Rollout, ERP/CRM Migration, Corporate Restructuring, Connected Product Launch",
        "clean_room_policy": "EVERY_MAJOR_MILESTONE",
        "clean_room_panel": [
            {"role": "architecture_quality_auditor", "focus": "Integration readiness, UAT/commissioning, security & compliance gates"},
            {"role": "finance_vendor_auditor", "focus": "5-column capex/opex landing, vendor SLAs & change-order control"},
            {"role": "devil_cutover_risk_auditor", "focus": "Cutover readiness, business continuity, negative float & user adoption"},
        ],
        "mandatory_registers": [
            "tasks_cpm", "budget_5col", "change_orders", "risk_register",
            "compliance_register", "contracts_register", "raci_matrix", "decision_log",
        ],
        "default_stage_gates": [
            {"gate": "SG0", "phase": "Charter, Architecture & Target Blueprint", "freeze": "Scope Boundary, Budget & Hard Cutover Date"},
            {"gate": "SG1", "phase": "Contracting & Core Foundations", "freeze": "Vendors/Contracts Signed, Core Environments Live"},
            {"gate": "SG2", "phase": "Iterative Delivery Sprints (Waves 1..N)", "freeze": "Incremental UAT Sign-Off & Change Control"},
            {"gate": "SG3", "phase": "Pre-Cutover Dress Rehearsal & Compliance Sign-Off", "freeze": "100% Security/Regulatory Certificates & Rollback Tested"},
            {"gate": "SG4", "phase": "Go-Live, Change Management & Hypercare", "freeze": "Production Stabilized & Handover to Run Ops"},
        ],
        "interchange_formats": ["MS Project XML (.xml)", "Excel 7-Tab (.xlsx)", "Jira/Monday CSV", "iCalendar (.ics)", "Google Sheets/Docs"],
    },
    "AGILE_SCRUM_SHAPE_UP": {
        "name": "Agile Product Delivery (Scrum · Shape Up · Continuous CI/CD)",
        "best_for": "SaaS Applications, Web/Mobile Products, Customer-Facing Software with Evolving UX/Market Discovery",
        "clean_room_policy": "EVERY_MAJOR_MILESTONE",
        "clean_room_panel": [
            {"role": "code_security_auditor", "focus": "100% code review, AST drift, test parity & security boundaries"},
            {"role": "product_unit_econ_auditor", "focus": "North-Star adoption/retention ceiling vs target & FinOps cost"},
            {"role": "devil_ux_debt_auditor", "focus": "Complacent mocks, hidden tech debt & scope creep"},
        ],
        "mandatory_registers": ["tasks_cpm", "budget_5col", "risk_register", "compliance_register", "decision_log"],
        "default_stage_gates": [
            {"gate": "P0", "phase": "Problem Shaping & Gate 0 MVP Scope", "freeze": "North-Star Metric & Kill Criteria"},
            {"gate": "P1", "phase": "Core Slice & Walking Skeleton", "freeze": "End-to-End Automated Test Twin"},
            {"gate": "P2", "phase": "Beta Release & Security/Privacy Gate", "freeze": "Zero Critical Security/Compliance Findings"},
            {"gate": "P3", "phase": "General Availability & Telemetry Review", "freeze": "Post-Release Clean-Room Audit"},
        ],
        "interchange_formats": ["Jira/Asana/Monday CSV", "Excel 7-Tab (.xlsx)", "MS Project XML (.xml)", "iCalendar (.ics)"],
    },
    "LEAN_KANBAN_TOC": {
        "name": "Lean Kanban & Theory of Constraints (TOC Drum-Buffer-Rope)",
        "best_for": "Ongoing Operations, Multi-Site Maintenance, Continuous Sourcing/Supply-Chain, Support Queues",
        "clean_room_policy": "PLATEAU_2",
        "clean_room_panel": [
            {"role": "throughput_bottleneck_auditor", "focus": "Cycle time, WIP limits & primary TOC bottleneck"},
            {"role": "cost_sla_auditor", "focus": "Landed unit cost, OPEX drift & vendor SLA compliance"},
            {"role": "devil_spof_auditor", "focus": "Single points of failure & compliance expirations"},
        ],
        "mandatory_registers": ["tasks_cpm", "budget_5col", "risk_register", "compliance_register"],
        "default_stage_gates": [
            {"gate": "K0", "phase": "Baseline Bottleneck & SLA Mapping", "freeze": "WIP Caps & SLA Thresholds"},
            {"gate": "K1", "phase": "Continuous Flow & Quarterly Audits", "freeze": "Zero Bottleneck Regression"},
        ],
        "interchange_formats": ["Jira/Asana/Monday CSV", "Excel 7-Tab (.xlsx)", "UTF-8-BOM CSV"],
    },
    "SCIENTIFIC_QUANT_RD": {
        "name": "Scientific & Quantitative R&D (CRISP-DM · Aeronautical SHA-256 Gates · Post-Run Clean-Room Board)",
        "best_for": "Quantitative Trading Strategies, AI/ML Model Development, Data/Genomics Pipelines, Algorithmic R&D",
        "clean_room_policy": "EVERY_MAJOR_MILESTONE",
        "clean_room_panel": [
            {"role": "code_plumbing_forensics_auditor", "focus": "100% module read, AST discards/latches, execution frictions & schema parity"},
            {"role": "math_ceiling_stats_auditor", "focus": "Zero-friction IC/Sharpe/accuracy ceiling vs target, collinearity & Monte Carlo stress"},
            {"role": "devil_twins_dogma_auditor", "focus": "Complacent local test twins, Gate 0 binding truth & confounded dead-ends"},
        ],
        "mandatory_registers": ["tasks_cpm", "risk_register", "decision_log"],
        "default_stage_gates": [
            {"gate": "P0", "phase": "Gate 0 Evidence-Bound Autopsy & Hypothesis Lock", "freeze": "Strict Bindings & Single Isolated Change"},
            {"gate": "P1", "phase": "Local Deterministic Harness & Schema Parity", "freeze": "Zero Mock-vs-Real Schema Drift & 100% Indelible Tests"},
            {"gate": "P2", "phase": "Heavy Empirical / Cloud Backtest Run", "freeze": "Mandatory Post-Run Multi-Agent Clean-Room Board Report"},
            {"gate": "P3", "phase": "Out-Of-Sample Sanctuary & Paper/Live Promotion", "freeze": "DSR / Statistical Significance & Risk Kill-Switches"},
        ],
        "interchange_formats": ["Excel 7-Tab (.xlsx)", "UTF-8-BOM CSV", "Google Sheets/Docs"],
    },
    "PATRIMONIAL_ADVISORY_STAGE_GATE": {
        "name": "Executive Patrimonial & Corporate Structuring (Dual-Circle ExCom · Stage-Gate Execution)",
        "best_for": "Corporate/Tax Wrapper Structuring (SASU/Holding), Personal Real Estate Acquisition, Wealth & Life Decisions",
        "clean_room_policy": "EVERY_MAJOR_MILESTONE",
        "clean_room_panel": [
            {"role": "legal_tax_compliance_auditor", "focus": "Dated statutory codes, clauses, liabilities & filing deadlines"},
            {"role": "financial_tco_model_auditor", "focus": "Script-verified compounding, net cash-flow & hidden fee drag"},
            {"role": "devil_downside_liquidity_auditor", "focus": "Irreversible lock-ins, tax traps & liquidity stress"},
        ],
        "mandatory_registers": ["tasks_cpm", "budget_5col", "risk_register", "compliance_register", "contracts_register", "decision_log"],
        "default_stage_gates": [
            {"gate": "G0", "phase": "360° Dual-Circle Structuring & Gate 0 Arbitration", "freeze": "Selected Legal/Financial Architecture"},
            {"gate": "G1", "phase": "Deed Drafting, Counsel Review & Pre-Signing Audit", "freeze": "Zero Uncapped Liability Clauses"},
            {"gate": "G2", "phase": "Execution, Filings & Bank/Custody Onboarding", "freeze": "100% Statutory Registrations Complete"},
        ],
        "interchange_formats": ["Excel 7-Tab (.xlsx)", "iCalendar (.ics)", "Google Sheets/Docs"],
    },
}


def select_methodology(
    description: str = "",
    project_type: str = "",
    uncertainty: str = "MEDIUM",
    regulatory_irreversibility: str = "MEDIUM",
    capital_intensity: str = "MEDIUM",
    delivery_cadence: str = "MILESTONE",
) -> Dict[str, Any]:
    """Deterministically selects the optimal project methodology & modular domain pack."""
    blob = f"{project_type} {description}".lower()
    unc = uncertainty.strip().upper()
    reg = regulatory_irreversibility.strip().upper()
    cap = capital_intensity.strip().upper()
    cad = delivery_cadence.strip().upper()

    domain_pack = ""
    if any(k in blob for k in (
        "real estate", "immobilier", "construction", "bâtiment", "batiment", "bail", "befa", "vefa",
        "travaux", "aménagement", "amenagement", "icpe", "erp", "igh", "entrepôt", "entrepot",
        "warehouse", "office", "bureaux", "workplace", "moa", "foncier", "terrain",
    )):
        domain_pack = "references/domain-packs/corporate-real-estate.md"

    # Explicit deterministic classification rules
    if any(k in blob for k in ("quant", "backtest", "trading", "alpha", "sharpe", "machine learning", "ml model", "genomics", "research", "r&d", "data science")):
        chosen = "SCIENTIFIC_QUANT_RD"
        rationale = "High empirical hypothesis uncertainty with heavy run/experiment cycles requires Aeronautical Gates + immediate post-run Multi-Agent Clean-Room Board."
    elif domain_pack and any(k in blob for k in ("it ", "erp migration", "digital", "software", "si ", "transformation")):
        chosen = "HYBRID_STAGE_GATE_AGILE"
        rationale = "Physical real-estate/regulatory milestones require Predictive Stage-Gates while concurrent IT/workplace digital streams benefit from iterative Agile waves."
    elif domain_pack or any(k in blob for k in ("factory", "usine", "infrastructure", "hardware", "bom", "m&a", "acquisition", "industrial")):
        chosen = "PREDICTIVE_STAGE_GATE"
        rationale = "High physical/contractual/regulatory irreversibility (permits, HSE/ICPE/ERP, leases, capex) mandates strict Predictive Stage-Gates with design freezes and Go-Live compliance locks."
    elif any(k in blob for k in ("sasu", "holding", "fiscal", "tax", "patrimoine", "wealth", "personal", "perso", "statuts")):
        chosen = "PATRIMONIAL_ADVISORY_STAGE_GATE"
        rationale = "High statutory and irreversible financial structuring stakes require Dual-Circle ExCom vetting followed by gated legal/tax execution."
    elif cad == "CONTINUOUS" or any(k in blob for k in ("kanban", "maintenance", "operations", "support", "supply chain", "sourcing ongoing", "run ops")):
        chosen = "LEAN_KANBAN_TOC"
        rationale = "Continuous operational flow without a fixed terminal date is best governed via Kanban WIP limits and Theory of Constraints bottleneck tracking."
    elif reg == "HIGH" or cap == "HIGH":
        if unc == "HIGH":
            chosen = "HYBRID_STAGE_GATE_AGILE"
            rationale = "Combining high regulatory/capital stakes with high scope uncertainty requires Stage-Gate governance wrapping iterative delivery streams."
        else:
            chosen = "PREDICTIVE_STAGE_GATE"
            rationale = "High regulatory irreversibility or capital intensity with definable scope requires Predictive Stage-Gate control."
    elif unc == "HIGH" and reg == "LOW":
        chosen = "AGILE_SCRUM_SHAPE_UP"
        rationale = "High requirement/market uncertainty with low physical/regulatory irreversibility favors short iterative product discovery cycles."
    else:
        chosen = "HYBRID_STAGE_GATE_AGILE"
        rationale = "Balanced uncertainty and business constraints are best served by Hybrid Stage-Gate milestones with iterative workstream execution."

    meta = METHODOLOGY_CATALOG[chosen]
    return {
        "methodology_id": chosen,
        "methodology_name": meta["name"],
        "best_for": meta["best_for"],
        "rationale": rationale,
        "clean_room_policy": meta["clean_room_policy"],
        "clean_room_panel": meta["clean_room_panel"],
        "mandatory_registers": meta["mandatory_registers"],
        "default_stage_gates": meta["default_stage_gates"],
        "recommended_domain_pack": domain_pack or "Standard ExCom 25-Role Core",
        "interchange_formats": meta["interchange_formats"],
    }


def _iso_dt(date_str: str, end_of_day: bool = False) -> str:
    d = str(date_str or dt.date.today().isoformat())[:10]
    return f"{d}T17:00:00" if end_of_day else f"{d}T09:00:00"


def _parse_dep_spec(dep: Any) -> Tuple[str, str, float]:
    """Parses either simple `'M1'` or structured `'M1:SS+5'` / `{'id':'M1','type':'SS','lag_days':5}`."""
    if isinstance(dep, dict):
        return str(dep.get("id", "")).strip(), str(dep.get("type", "FS")).strip().upper(), float(dep.get("lag_days", 0.0))
    s = str(dep).strip()
    m = re.match(r"^([^:]+):(FS|SS|FF|SF)([+-]\d+(?:\.\d+)?)?$", s, re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).upper(), float(m.group(3) or 0.0)
    return s, "FS", 0.0


# ---------------------------------------------------------------------------
# 1. MS Project XML (MSPDI) Export & Bidirectional Import
# ---------------------------------------------------------------------------

def export_msproject_xml(project_dir: Path, state: Dict[str, Any]) -> Path:
    """Exports a standard MS Project MSPDI .xml file compatible with MS Project, Primavera, Smartsheet, ProjectLibre."""
    exp_dir = project_dir / "exports"
    exp_dir.mkdir(parents=True, exist_ok=True)
    out_path = exp_dir / "schedule_msproject.xml"

    ns = "http://schemas.microsoft.com/project"
    ET.register_namespace("", ns)
    root = ET.Element(f"{{{ns}}}Project")

    def sub(parent: ET.Element, tag: str, text: Any = None) -> ET.Element:
        el = ET.SubElement(parent, f"{{{ns}}}{tag}")
        if text is not None:
            el.text = str(text)
        return el

    m = state.get("metrics", {})
    sub(root, "SaveVersion", "14")
    sub(root, "Name", state.get("project_name", "ExCom Project"))
    sub(root, "Title", state.get("project_name", "ExCom Project"))
    sub(root, "CreationDate", _iso_dt(state.get("start_date", dt.date.today().isoformat())))
    sub(root, "LastSaved", _iso_dt(m.get("as_of_date", dt.date.today().isoformat()), end_of_day=True))
    sub(root, "StartDate", _iso_dt(state.get("start_date", dt.date.today().isoformat())))
    sub(root, "FinishDate", _iso_dt(m.get("forecast_end_date", state.get("start_date", dt.date.today().isoformat())), end_of_day=True))
    sub(root, "CurrencyCode", state.get("currency", "EUR"))
    sub(root, "MinutesPerDay", "480")
    sub(root, "MinutesPerWeek", "2400")
    sub(root, "DaysPerMonth", "20")

    tasks = state.get("tasks", [])
    uid_by_tid = {t["id"]: idx + 1 for idx, t in enumerate(tasks)}
    tasks_el = sub(root, "Tasks")

    # Summary Task UID=0
    t0 = sub(tasks_el, "Task")
    sub(t0, "UID", "0")
    sub(t0, "ID", "0")
    sub(t0, "Name", state.get("project_name", "ExCom Project"))
    sub(t0, "Type", "1")
    sub(t0, "IsNull", "0")
    sub(t0, "OutlineLevel", "0")
    sub(t0, "Summary", "1")
    sub(t0, "Start", _iso_dt(state.get("start_date", dt.date.today().isoformat())))
    sub(t0, "Finish", _iso_dt(m.get("forecast_end_date", state.get("start_date", dt.date.today().isoformat())), end_of_day=True))

    msp_link_type = {"FF": "0", "FS": "1", "SF": "2", "SS": "3"}
    owners: List[str] = []

    for idx, t in enumerate(tasks):
        uid = idx + 1
        c = t.get("computed", {})
        dur_d = float(c.get("duration_days", t.get("duration_days", 1.0)))
        dur_h = int(round(max(0.0, dur_d) * 8.0))
        is_milestone = "1" if (dur_d <= 0.0 or t.get("is_milestone")) else "0"
        owner = str(t.get("owner_seat", "PMO"))
        if owner not in owners:
            owners.append(owner)

        tel = sub(tasks_el, "Task")
        sub(tel, "UID", str(uid))
        sub(tel, "ID", str(uid))
        sub(tel, "Name", f"[{t['id']}] {t['name']}")
        sub(tel, "WBS", str(t.get("wbs", f"{idx + 1}")))
        sub(tel, "OutlineLevel", "1")
        sub(tel, "Start", _iso_dt(c.get("forecast_start", state.get("start_date", ""))))
        sub(tel, "Finish", _iso_dt(c.get("forecast_end", state.get("start_date", "")), end_of_day=True))
        sub(tel, "Duration", f"PT{dur_h}H0M0S")
        sub(tel, "DurationFormat", "7")
        sub(tel, "Milestone", is_milestone)
        sub(tel, "Summary", "0")
        sub(tel, "Critical", "1" if c.get("is_critical") else "0")
        sub(tel, "PercentComplete", str(int(round(float(t.get("progress_pct", 0.0))))))
        sub(tel, "Cost", f"{float(c.get('revised_budget', t.get('planned_budget', 0.0))):.2f}")
        sub(tel, "ActualCost", f"{float(t.get('actual_cost', 0.0)):.2f}")
        note_parts = [f"ExComID={t['id']}", f"Phase={t.get('phase', '')}", f"Owner={owner}"]
        if t.get("hard_gate"):
            note_parts.append(f"HardGate={t['hard_gate']}")
        if t.get("notes"):
            note_parts.append(str(t["notes"]))
        sub(tel, "Notes", " | ".join(note_parts))

        for dep in t.get("depends_on", []):
            dep_id, dep_type, lag_d = _parse_dep_spec(dep)
            if dep_id in uid_by_tid:
                pl = sub(tel, "PredecessorLink")
                sub(pl, "PredecessorUID", str(uid_by_tid[dep_id]))
                sub(pl, "Type", msp_link_type.get(dep_type, "1"))
                # MSPDI LinkLag is in tenths of a minute (1 workday = 480 min = 4800)
                sub(pl, "LinkLag", str(int(round(lag_d * 4800))))
                sub(pl, "LagFormat", "7")

    # Resources & Assignments
    res_el = sub(root, "Resources")
    res_uid_by_owner: Dict[str, int] = {}
    for r_idx, own in enumerate(owners, start=1):
        res_uid_by_owner[own] = r_idx
        rel = sub(res_el, "Resource")
        sub(rel, "UID", str(r_idx))
        sub(rel, "ID", str(r_idx))
        sub(rel, "Name", own)
        sub(rel, "Type", "1")

    asg_el = sub(root, "Assignments")
    for idx, t in enumerate(tasks, start=1):
        own = str(t.get("owner_seat", "PMO"))
        ael = sub(asg_el, "Assignment")
        sub(ael, "UID", str(idx))
        sub(ael, "TaskUID", str(idx))
        sub(ael, "ResourceUID", str(res_uid_by_owner.get(own, 1)))
        sub(ael, "Units", "1")

    tree = ET.ElementTree(root)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    return out_path


def import_msproject_xml(xml_path: Path) -> List[Dict[str, Any]]:
    """Imports tasks from an MS Project / Primavera / Smartsheet / ProjectLibre MSPDI .xml file."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ns_m = re.match(r"^\{([^}]+)\}", root.tag)
    ns_pref = f"{{{ns_m.group(1)}}}" if ns_m else ""

    def txt(el: ET.Element, tag: str, default: str = "") -> str:
        child = el.find(f"{ns_pref}{tag}")
        return child.text.strip() if (child is not None and child.text) else default

    raw_tasks: List[Dict[str, Any]] = []
    uid_to_excom_id: Dict[str, str] = {}
    rev_link = {"0": "FF", "1": "FS", "2": "SF", "3": "SS"}

    tasks_container = root.find(f"{ns_pref}Tasks")
    if tasks_container is None:
        return []

    for tel in tasks_container.findall(f"{ns_pref}Task"):
        uid = txt(tel, "UID")
        if uid == "0" or txt(tel, "Summary") == "1":
            continue
        name = txt(tel, "Name")
        if not name:
            continue
        notes = txt(tel, "Notes")
        ex_m = re.search(r"ExComID=([A-Za-z0-9_-]+)", notes) or re.match(r"^\[([A-Za-z0-9_-]+)\]\s*", name)
        tid = ex_m.group(1) if ex_m else f"T{uid}"
        clean_name = re.sub(r"^\[[A-Za-z0-9_-]+\]\s*", "", name).strip()
        uid_to_excom_id[uid] = tid

        dur_raw = txt(tel, "Duration", "PT8H0M0S")
        hm = re.search(r"PT(\d+)H", dur_raw)
        dur_days = round(int(hm.group(1)) / 8.0, 1) if hm else 1.0

        raw_preds = []
        for pl in tel.findall(f"{ns_pref}PredecessorLink"):
            p_uid = txt(pl, "PredecessorUID")
            p_type = rev_link.get(txt(pl, "Type", "1"), "FS")
            lag_raw = float(txt(pl, "LinkLag", "0") or 0)
            lag_days = round(lag_raw / 4800.0, 1)
            raw_preds.append((p_uid, p_type, lag_days))

        raw_tasks.append({
            "id": tid,
            "name": clean_name,
            "forecast_days": dur_days,
            "progress_pct": float(txt(tel, "PercentComplete", "0") or 0),
            "planned_budget": float(txt(tel, "Cost", "0") or 0),
            "actual_cost": float(txt(tel, "ActualCost", "0") or 0),
            "raw_preds": raw_preds,
            "notes": notes,
        })

    # Resolve predecessor UIDs to ExCom task IDs
    for rt in raw_tasks:
        deps: List[str] = []
        for p_uid, p_type, lag_d in rt.pop("raw_preds"):
            pid = uid_to_excom_id.get(p_uid)
            if not pid:
                continue
            if p_type == "FS" and abs(lag_d) < 1e-6:
                deps.append(pid)
            else:
                sign = "+" if lag_d >= 0 else ""
                lag_s = f"{sign}{lag_d:g}" if abs(lag_d) >= 1e-6 else ""
                deps.append(f"{pid}:{p_type}{lag_s}")
        rt["depends_on"] = deps
    return raw_tasks


# ---------------------------------------------------------------------------
# 2. Pure-Stdlib Multi-Sheet Excel (.xlsx OOXML) Writer
# ---------------------------------------------------------------------------

def _col_letter(idx_1based: int) -> str:
    res = ""
    n = idx_1based
    while n > 0:
        n, rem = divmod(n - 1, 26)
        res = chr(65 + rem) + res
    return res


def _xml_esc(s: Any) -> str:
    txt = str(s if s is not None else "")
    # Strip illegal XML control characters
    txt = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", txt)
    return (
        txt.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def write_xlsx_workbook(out_path: Path, sheets: List[Tuple[str, List[List[Any]]]]) -> Path:
    """Writes a genuine multi-sheet OOXML .xlsx file using Python stdlib zipfile only."""
    shared_strings: List[str] = []
    ss_index: Dict[str, int] = {}

    def get_ss_idx(val: str) -> int:
        if val not in ss_index:
            ss_index[val] = len(shared_strings)
            shared_strings.append(val)
        return ss_index[val]

    sheet_xmls: List[str] = []
    for _, rows in sheets:
        col_widths: Dict[int, int] = {}
        row_xmls: List[str] = []
        for r_idx, row in enumerate(rows, start=1):
            cells_xml: List[str] = []
            style_id = "1" if r_idx == 1 else "0"
            for c_idx, val in enumerate(row, start=1):
                ref = f"{_col_letter(c_idx)}{r_idx}"
                s_len = len(str(val if val is not None else ""))
                col_widths[c_idx] = min(48, max(col_widths.get(c_idx, 10), s_len + 3))
                if isinstance(val, bool):
                    s_i = get_ss_idx("YES" if val else "NO")
                    cells_xml.append(f'<c r="{ref}" t="s" s="{style_id}"><v>{s_i}</v></c>')
                elif isinstance(val, str) and val.startswith("=") and r_idx > 1:
                    # Live dynamic Excel OOXML formula cell (escape &, <, > only; keep literal quotes for Excel sheet refs)
                    f_esc = val[1:].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    cells_xml.append(f'<c r="{ref}" s="0"><f>{f_esc}</f></c>')
                elif isinstance(val, (int, float)) and r_idx > 1:
                    cells_xml.append(f'<c r="{ref}" s="0"><v>{val}</v></c>')
                else:
                    s_i = get_ss_idx(str(val if val is not None else ""))
                    cells_xml.append(f'<c r="{ref}" t="s" s="{style_id}"><v>{s_i}</v></c>')
            row_xmls.append(f'<row r="{r_idx}">{"".join(cells_xml)}</row>')

        cols_xml = "".join(
            f'<col min="{ci}" max="{ci}" width="{w}" customWidth="1"/>'
            for ci, w in sorted(col_widths.items())
        )
        ws_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<cols>{cols_xml}</cols>'
            f'<sheetData>{"".join(row_xmls)}</sheetData>'
            '</worksheet>'
        )
        sheet_xmls.append(ws_xml)

    ss_items = "".join(f"<si><t>{_xml_esc(s)}</t></si>" for s in shared_strings)
    ss_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(shared_strings)}" uniqueCount="{len(shared_strings)}">'
        f"{ss_items}</sst>"
    )

    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2">'
        '<font><sz val="10"/><name val="Calibri"/></font>'
        '<font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>'
        '</fonts>'
        '<fills count="3">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF1E293B"/><bgColor indexed="64"/></patternFill></fill>'
        '</fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>'
        '</cellXfs>'
        '</styleSheet>'
    )

    wb_sheets_xml = []
    wb_rels_xml = []
    ct_overrides = [
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
        '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>',
    ]
    for i, (name, _) in enumerate(sheets, start=1):
        safe_name = re.sub(r"[\[\]:*?/\\]", "_", name)[:31]
        wb_sheets_xml.append(f'<sheet name="{_xml_esc(safe_name)}" sheetId="{i}" r:id="rId{i}"/>')
        wb_rels_xml.append(
            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
        )
        ct_overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )

    rel_styles_id = len(sheets) + 1
    rel_ss_id = len(sheets) + 2
    wb_rels_xml.append(
        f'<Relationship Id="rId{rel_styles_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    )
    wb_rels_xml.append(
        f'<Relationship Id="rId{rel_ss_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f'{"".join(ct_overrides)}</Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets>{"".join(wb_sheets_xml)}</sheets></workbook>'
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'{"".join(wb_rels_xml)}</Relationships>'
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/styles.xml", styles_xml)
        zf.writestr("xl/sharedStrings.xml", ss_xml)
        for i, ws_xml in enumerate(sheet_xmls, start=1):
            zf.writestr(f"xl/worksheets/sheet{i}.xml", ws_xml)
    return out_path


def export_excel_xlsx(project_dir: Path, state: Dict[str, Any]) -> Path:
    """Exports the 9-sheet Executive Control Tower .xlsx workbook WITH LIVE DYNAMIC EXCEL FORMULAS
    (Parametric Inputs + Multi-Year P&L / TCO / Cash-Flow + 5-Col Budget + EMV Risks + HSE + Contracts)."""
    m = state.get("metrics", {})
    evm = m.get("evm", {})
    qcdr = m.get("qcdr", {})
    ccy = state.get("currency", "EUR")
    tasks = state.get("tasks", [])
    n_tasks = len(tasks)
    bud_last_row = n_tasks + 1
    bud_tot_row = n_tasks + 2

    # Sheet 1: 0_Inputs_Hypotheses (Editable Blue-Input Parametric Driver Sheet for Corporate Confidential Plug-In)
    area_m2 = float(state.get("floor_area_m2", 2500.0))
    annual_opex_tot = float(evm.get("recurring_annual_opex_eur", 0.0))
    rent_per_m2 = round((annual_opex_tot * 0.85) / max(1.0, area_m2), 2) if annual_opex_tot > 0 else 320.0
    charges_per_m2 = round((annual_opex_tot * 0.15) / max(1.0, area_m2), 2) if annual_opex_tot > 0 else 65.0
    capex_per_m2 = round(float(evm.get("bac_eur", 0.0)) / max(1.0, area_m2), 2) if float(evm.get("bac_eur", 0.0)) > 0 else 650.0
    tco_yrs = int(state.get("tco_horizon_years", 6))
    s_inputs: List[List[Any]] = [
        ["Input_Parameter", "Value", "Unit", "Usage_Note_Edit_Internally_In_Excel"],
        ["Floor_Area_Or_Scale_Units", area_m2, "m2", "Overwrite with confidential real surface area locally"],
        ["Annual_Headline_Rent_Per_Unit", rent_per_m2, f"{ccy}/m2/yr", "Drives dynamic Multi-Year P&L Rent line"],
        ["Annual_Charges_Maint_Per_Unit", charges_per_m2, f"{ccy}/m2/yr", "Service charges, taxes, utilities & maintenance"],
        ["FitOut_Capex_Per_Unit", capex_per_m2, f"{ccy}/m2", "Reference unit CAPEX benchmark"],
        ["Contingency_Pct", float(state.get("contingency_pct", 12.0)) / 100.0, "ratio", "Project Director contingency reserve rate"],
        ["Management_Reserve_Pct", float(state.get("management_reserve_pct", 5.0)) / 100.0, "ratio", "ComEx management reserve rate"],
        ["Annual_Indexation_ILAT_BT01", float(state.get("indexation_annual_pct", 2.0)) / 100.0, "ratio", "Annual compounding indexation on OPEX/Rent"],
        ["Rent_Free_Months_Year1", float(state.get("rent_free_months", 6.0)), "months", "Landlord commercial rent-free abatement in Year 1"],
        ["Landlord_TI_Allowance_Incentive", float(state.get("incentives_ti_allowance_eur", 0.0)), ccy, "Cash contribution from landlord / grant"],
        ["Old_Site_Exit_Dilapidations", float(state.get("exit_dilapidation_eur", 0.0)), ccy, "Reinstatement & moving exit cost"],
        ["Capex_Depreciation_Years", float(state.get("depreciation_years", 9.0)), "years", "Straight-line P&L amortization period"],
        ["IFRS16_Discount_Rate", float(state.get("ifrs16_discount_rate_pct", 4.5)) / 100.0, "ratio", "Incremental borrowing rate for lease PV"],
        ["TCO_Horizon_Years", tco_yrs, "years", "Multi-year P&L & TCO evaluation horizon"],
    ]

    # Sheet 2: 1_PnL_TCO_CashFlow (100% Live Excel Formulas Linked to 0_Inputs_Hypotheses & 3_Budget_5Col_EVM!)
    yrs = list(range(1, max(6, min(12, tco_yrs)) + 1))
    s_pnl: List[List[Any]] = [["PnL_And_CashFlow_Line", *[f"Year_{y}" for y in yrs], "Total_Horizon"]]
    end_col = _col_letter(len(yrs) + 1)

    rent_row: List[Any] = [f"Headline Rent ({ccy})"]
    rf_row: List[Any] = [f"Less: Rent-Free Abatement ({ccy})"]
    chg_row: List[Any] = [f"Service Charges, Taxes & Maint ({ccy})"]
    dep_row: List[Any] = [f"CAPEX Amortization / Depreciation ({ccy})"]
    pnl_tot_row: List[Any] = [f"TOTAL ANNUAL P&L IMPACT ({ccy})"]
    capex_cf_row: List[Any] = [f"CAPEX Cash Outflow Net of TI ({ccy})"]
    exit_cf_row: List[Any] = [f"Exit / Dilapidation Cash Outflow ({ccy})"]
    net_cf_row: List[Any] = [f"NET ANNUAL CASH OUTFLOW ({ccy})"]
    pv_lease_row: List[Any] = [f"Discounted Lease PV (IFRS 16 Proxy, {ccy})"]

    for idx_y, y in enumerate(yrs):
        col = _col_letter(idx_y + 2)
        pow_exp = y - 1
        rent_row.append(f"='0_Inputs_Hypotheses'!$B$2*'0_Inputs_Hypotheses'!$B$3*((1+'0_Inputs_Hypotheses'!$B$8)^{pow_exp})")
        rf_row.append(f"=-'0_Inputs_Hypotheses'!$B$2*'0_Inputs_Hypotheses'!$B$3*('0_Inputs_Hypotheses'!$B$9/12)" if y == 1 else 0.0)
        chg_row.append(f"='0_Inputs_Hypotheses'!$B$2*'0_Inputs_Hypotheses'!$B$4*((1+'0_Inputs_Hypotheses'!$B$8)^{pow_exp})")
        dep_row.append(f"='3_Budget_5Col_EVM'!$J${bud_tot_row}/'0_Inputs_Hypotheses'!$B$12")
        pnl_tot_row.append(f"={col}2+{col}3+{col}4+{col}5")
        capex_cf_row.append(f"='3_Budget_5Col_EVM'!$J${bud_tot_row}-'0_Inputs_Hypotheses'!$B$10" if y == 1 else 0.0)
        exit_cf_row.append("='0_Inputs_Hypotheses'!$B$11" if y == 1 else 0.0)
        net_cf_row.append(f"={col}2+{col}3+{col}4+{col}7+{col}8")
        pv_lease_row.append(f"=({col}2+{col}3)/((1+'0_Inputs_Hypotheses'!$B$13)^{y})")

    for r_idx_f, r_arr in enumerate([rent_row, rf_row, chg_row, dep_row, pnl_tot_row, capex_cf_row, exit_cf_row, net_cf_row, pv_lease_row], start=2):
        r_arr.append(f"=SUM(B{r_idx_f}:{end_col}{r_idx_f})")
        s_pnl.append(r_arr)

    # Append Monthly CAPEX Cash-Flow S-Curve below P&L
    s_pnl.append(["", "", "", "", "", "", "", ""])
    s_pnl.append(["Monthly_CAPEX_CashFlow_S_Curve", "Planned_Month_Outflow", "Cumulative_Outflow", "", "", "", "", ""])
    s_curve = m.get("monthly_cashflow_s_curve", {})
    base_sc_row = len(s_pnl) + 1
    for i_m, (ym, amt) in enumerate(s_curve.items()):
        r_now = base_sc_row + i_m
        cum_f = f"=B{r_now}" if i_m == 0 else f"=C{r_now - 1}+B{r_now}"
        s_pnl.append([ym, amt, cum_f])

    # Sheet 3: 0_Executive_Summary (Live links to Budget/PnL/Risks!)
    s0: List[List[Any]] = [
        ["KPI / Control Dimension", "Current Value", "Target / Baseline", "Status / Notes"],
        ["Project Name", state.get("project_name", ""), state.get("methodology_id", "PREDICTIVE_STAGE_GATE"), state.get("overall_rag", "GREEN")],
        ["As-Of Date", m.get("as_of_date", ""), f"Start: {state.get('start_date', '')}", f"Overall Progress: {m.get('overall_progress_pct', 0)}%"],
        ["Forecast Completion Date", m.get("forecast_end_date", ""), f"Hard Target: {m.get('target_end_date') or 'N/A'}", f"Target Slack: {m.get('target_margin_days', 'N/A')} d (P85: {m.get('p85_duration_days', 0)} d)"],
        ["Critical Path", " -> ".join(m.get("critical_path", [])), f"Near-Critical (<=5d): {', '.join(m.get('near_critical_tasks', [])) or 'None'}", f"Project Slip: {m.get('project_slip_days', 0)} d"],
        [f"Initial Baseline Budget (BAC, {ccy})", f"='3_Budget_5Col_EVM'!D{bud_tot_row}", f"='3_Budget_5Col_EVM'!E{bud_tot_row}", "Live formula from 3_Budget_5Col_EVM (Col D=BAC, E=Approved TMA)"],
        [f"Revised Budget / EAC Landing ({ccy})", f"='3_Budget_5Col_EVM'!F{bud_tot_row}", f"='3_Budget_5Col_EVM'!J{bud_tot_row}", f"CPI: {evm.get('cpi', 1.0)} | SPI: {evm.get('spi', 1.0)}"],
        [f"Budget Variance (VAC, {ccy})", f"='3_Budget_5Col_EVM'!K{bud_tot_row}", f"Contingency: {evm.get('contingency_remaining_eur', 0):,.0f}", f"Mgmt Reserve: {evm.get('management_reserve_eur', 0):,.0f}"],
        [f"Multi-Year Total Cash TCO / IFRS16 PV ({ccy})", f"='1_PnL_TCO_CashFlow'!{_col_letter(len(yrs) + 2)}9", f"='1_PnL_TCO_CashFlow'!{_col_letter(len(yrs) + 2)}10", "Col B = Total Cash TCO, Col C = IFRS 16 Lease PV (live formulas from 0_Inputs_Hypotheses)"],
        [f"Total Risk Exposure EMV ({ccy})", qcdr.get("risk_emv_eur", 0), f"Expected Risk Delay: {qcdr.get('risk_expected_delay_days', 0)} d", f"High/Critical Risks: {qcdr.get('critical_risks_count', 0)}"],
        ["HSE / Compliance Go-Live Gate", qcdr.get("go_live_gate_status", "READY"), f"Certificates Issued: {qcdr.get('certificates_pct', 100)}%", f"Blockers: {qcdr.get('blocking_compliance_open', 0)} | Open Reserves: {qcdr.get('open_reserves_count', 0)}"],
        ["Contracts & Suspensive Clauses", f"Signed: {qcdr.get('contracts_signed_count', 0)}", f"Open Redlines: {qcdr.get('contracts_open_redlines', 0)}", f"Open Suspensive Conditions: {qcdr.get('open_suspensive_conditions', 0)}"],
    ]

    # Sheet 4: 2_Schedule_CPM
    s1: List[List[Any]] = [[
        "Task_ID", "WBS", "Phase", "Name", "Owner", "Status", "Progress_Pct", "Depends_On",
        "Baseline_Days", "Forecast_Days", "Planned_Start", "Planned_End", "Forecast_Start",
        "Forecast_End", "Total_Float_Days", "Target_Slack_Days", "Critical", "Near_Critical", "Hard_Gate",
    ]]
    for idx, t in enumerate(tasks, start=1):
        c = t.get("computed", {})
        deps = "; ".join(dep if isinstance(dep, str) else f"{dep.get('id')}:{dep.get('type','FS')}" for dep in t.get("depends_on", []))
        s1.append([
            t["id"], t.get("wbs", str(idx)), t.get("phase", ""), t["name"], t.get("owner_seat", ""),
            t.get("status", ""), float(t.get("progress_pct", 0)), deps,
            c.get("baseline_ef", 0) - c.get("baseline_es", 0), c.get("duration_days", 0),
            c.get("planned_start", ""), c.get("planned_end", ""), c.get("forecast_start", ""),
            c.get("forecast_end", ""), c.get("total_float_days", 0), c.get("target_slack_days", 0),
            bool(c.get("is_critical")), bool(c.get("is_near_critical")), t.get("hard_gate", ""),
        ])

    # Sheet 5: 3_Budget_5Col_EVM (LIVE EXCEL FORMULAS ON EVERY ROW + SUM ROLLUP!)
    s2: List[List[Any]] = [[
        "Task_ID", "Workstream", "Owner", f"Initial_BAC_{ccy}", f"Approved_Changes_{ccy}",
        f"Revised_Budget_{ccy}", f"Committed_{ccy}", f"Actual_AC_{ccy}",
        f"Remaining_ETC_{ccy}", f"Forecast_EAC_{ccy}", f"Variance_VAC_{ccy}",
    ]]
    for idx, t in enumerate(tasks, start=2):
        c = t.get("computed", {})
        s2.append([
            t["id"], t["name"], t.get("owner_seat", ""),
            float(t.get("planned_budget", 0)),
            float(c.get("approved_changes_eur", 0)),
            f"=D{idx}+E{idx}",            # Revised = Initial BAC + Approved Changes
            float(c.get("committed_cost", 0)),
            float(t.get("actual_cost", 0)),
            float(c.get("etc_eur", 0)),
            f"=H{idx}+I{idx}",            # EAC = Actual AC + Remaining ETC
            f"=F{idx}-J{idx}",            # VAC = Revised - EAC
        ])
    if n_tasks > 0:
        s2.append([
            "TOTAL", "PROJECT CAPEX ROLLUP", "CFO",
            f"=SUM(D2:D{bud_last_row})", f"=SUM(E2:E{bud_last_row})", f"=SUM(F2:F{bud_last_row})",
            f"=SUM(G2:G{bud_last_row})", f"=SUM(H2:H{bud_last_row})", f"=SUM(I2:I{bud_last_row})",
            f"=SUM(J2:J{bud_last_row})", f"=SUM(K2:K{bud_last_row})",
        ])
    else:
        s2.append(["TOTAL", "PROJECT CAPEX ROLLUP", "CFO", 0, 0, 0, 0, 0, 0, 0, 0])

    # Sheet 6: 4_Risk_Register (LIVE EMV FORMULAS!)
    risks = state.get("risk_register", [])
    s3: List[List[Any]] = [[
        "Risk_ID", "Category", "Title", "Owner", "Status", "Probability_Pct",
        f"Cost_Impact_{ccy}", "Delay_Impact_Days", f"EMV_{ccy}", "Expected_Delay_Days", "Mitigation_Plan",
    ]]
    for idx, r in enumerate(risks, start=2):
        s3.append([
            r.get("id", ""), r.get("category", ""), r.get("title", ""), r.get("owner_seat", "CRO-Risk"),
            r.get("status", "OPEN"), float(r.get("probability_pct", 0.0)),
            float(r.get("cost_impact_eur", 0.0)), float(r.get("delay_impact_days", 0.0)),
            f"=(F{idx}/100)*G{idx}", f"=(F{idx}/100)*H{idx}", r.get("mitigation", ""),
        ])
    if risks:
        r_last = len(risks) + 1
        s3.append(["TOTAL", "EXPOSURE", "TOTAL QUANTIFIED RISK EMV", "CRO-Risk", "OPEN", "", f"=SUM(G2:G{r_last})", f"=SUM(H2:H{r_last})", f"=SUM(I2:I{r_last})", f"=SUM(J2:J{r_last})", ""])

    # Sheet 7: 5_Compliance_HSE_Snags
    s4: List[List[Any]] = [[
        "Item_ID", "Domain", "Asset_Or_Requirement", "Regulation_Standard", "Compliance_Status",
        "Test_Required", "Test_Completed", "Test_Date", "Reserves_Or_Snags", "Remediation_Task_ID",
        f"Remediation_Cost_{ccy}", "Remediation_Delay_Days", "Reserves_Lifted",
        "Certificate_Issued", "Blocking_GoLive", "Owner",
    ]]
    for item in state.get("compliance_register", []):
        s4.append([
            item.get("id", ""), item.get("domain", "HSE"), item.get("requirement", ""),
            item.get("standard", ""), item.get("status", "PENDING"),
            bool(item.get("test_required", True)), bool(item.get("test_completed", False)),
            item.get("test_date", ""), item.get("reserves", ""), item.get("linked_task_id", ""),
            float(item.get("remediation_cost_eur", 0.0)), float(item.get("remediation_delay_days", 0.0)),
            bool(item.get("reserves_lifted", False)), bool(item.get("certificate_issued", False)),
            bool(item.get("blocking_go_live", True)), item.get("owner_seat", "CCO-Compliance"),
        ])

    # Sheet 8: 6_Contracts_Negotiation
    s5: List[List[Any]] = [[
        "Contract_ID", "Contract_Type", "Counterparty", "Clause_Topic", "Target_Position",
        "Counterparty_Position", "HSE_Compliance_Clause", "Suspensive_Condition",
        "Deadline", f"Exposure_{ccy}", "Status", "Owner",
    ]]
    for ct in state.get("contracts_register", []):
        s5.append([
            ct.get("id", ""), ct.get("contract_type", ""), ct.get("counterparty", ""),
            ct.get("clause_topic", ""), ct.get("target_position", ""),
            ct.get("counterparty_position", ""), bool(ct.get("hse_compliance_linked", False)),
            bool(ct.get("is_suspensive_condition", False)), ct.get("deadline", ""),
            float(ct.get("financial_exposure_eur", 0.0)), ct.get("status", "NEGOTIATING"),
            ct.get("owner_seat", "CLO"),
        ])

    # Sheet 9: 7_Changes_Decisions_RACI
    s6: List[List[Any]] = [["Record_Type", "ID", "Date", "Title_Or_Workstream", "Owner_R", "Accountable_A", "Consulted_C", "Informed_I", f"Cost_Impact_{ccy}", "Delay_Days", "Status"]]
    for co in state.get("change_orders", []):
        s6.append([
            "CHANGE_ORDER_TMA", co.get("id", ""), co.get("date", ""), co.get("title", ""),
            co.get("owner_seat", "PMO"), co.get("approved_by", "Sponsor"), co.get("linked_task_id", ""), "",
            float(co.get("cost_impact_eur", 0.0)), float(co.get("delay_impact_days", 0.0)), co.get("status", "PENDING"),
        ])
    for dec in state.get("decision_log", []):
        s6.append([
            "DECISION", dec.get("id", ""), dec.get("date", ""), dec.get("title", ""),
            dec.get("decided_by", "Sponsor"), "", dec.get("rationale", ""), "", 0.0, 0.0, dec.get("status", "LOCKED"),
        ])
    for rc in state.get("raci_matrix", []):
        s6.append([
            "RACI", rc.get("id", ""), "", rc.get("deliverable", ""),
            rc.get("R", ""), rc.get("A", ""), rc.get("C", ""), rc.get("I", ""), 0.0, 0.0, "ACTIVE",
        ])

    out_path = project_dir / "exports" / "control_tower_workbook.xlsx"
    return write_xlsx_workbook(out_path, [
        ("0_Inputs_Hypotheses", s_inputs),
        ("1_PnL_TCO_CashFlow", s_pnl),
        ("0_Executive_Summary", s0),
        ("2_Schedule_CPM", s1),
        ("3_Budget_5Col_EVM", s2),
        ("4_Risk_Register", s3),
        ("5_Compliance_HSE_Snags", s4),
        ("6_Contracts_Negotiation", s5),
        ("7_Changes_Decisions_RACI", s6),
    ])


# ---------------------------------------------------------------------------
# 3. RFC 5545 iCalendar (.ics) Export for Outlook / Google Calendar
# ---------------------------------------------------------------------------

def export_icalendar_ics(project_dir: Path, state: Dict[str, Any]) -> Path:
    exp_dir = project_dir / "exports"
    exp_dir.mkdir(parents=True, exist_ok=True)
    out_path = exp_dir / "milestones_calendar.ics"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//ExCom v3.3//Enterprise Control Tower//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{state.get('project_name', 'ExCom Project')} Milestones",
    ]

    def add_event(uid: str, date_iso: str, summary: str, desc: str) -> None:
        if not date_iso or len(date_iso) < 10:
            return
        d_clean = date_iso[:10].replace("-", "")
        dt_end = (dt.date.fromisoformat(date_iso[:10]) + dt.timedelta(days=1)).strftime("%Y%m%d")
        safe_sum = summary.replace("\n", " ").replace(",", "\\,").replace(";", "\\;")
        safe_desc = desc.replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}@excom.local",
            f"DTSTART;VALUE=DATE:{d_clean}",
            f"DTEND;VALUE=DATE:{dt_end}",
            f"SUMMARY:{safe_sum}",
            f"DESCRIPTION:{safe_desc}",
            "END:VEVENT",
        ])

    m = state.get("metrics", {})
    if m.get("target_end_date"):
        add_event("hard-target-deadline", m["target_end_date"], f"[HARD DEADLINE] {state.get('project_name', 'Project')}", "Non-negotiable target completion date.")

    for t in state.get("tasks", []):
        c = t.get("computed", {})
        if t.get("hard_gate") or c.get("is_critical") or t.get("is_milestone"):
            add_event(
                f"task-{t['id']}",
                c.get("forecast_end", ""),
                f"[{t['id']}] {t['name']} ({t.get('owner_seat', 'PMO')})",
                f"Phase: {t.get('phase', '')} | Gate: {t.get('hard_gate', 'None')} | Float: {c.get('total_float_days', 0)}d",
            )

    for ct in state.get("contracts_register", []):
        if ct.get("deadline") and ct.get("status") != "SIGNED":
            add_event(
                f"contract-{ct.get('id', 'c')}",
                ct["deadline"],
                f"[CONTRACT DEADLINE] {ct.get('clause_topic', '')} ({ct.get('counterparty', '')})",
                f"Suspensive: {ct.get('is_suspensive_condition', False)} | Status: {ct.get('status', '')}",
            )

    for cmp_it in state.get("compliance_register", []):
        if cmp_it.get("test_date") and not cmp_it.get("certificate_issued"):
            add_event(
                f"hse-{cmp_it.get('id', 'h')}",
                cmp_it["test_date"],
                f"[HSE/COMPLIANCE TEST] {cmp_it.get('requirement', '')}",
                f"Standard: {cmp_it.get('standard', '')} | Go-Live Blocker: {cmp_it.get('blocking_go_live', True)}",
            )

    lines.append("END:VCALENDAR")
    out_path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# 4. UTF-8-BOM Enterprise CSV Suite + Jira/Asana/Monday CSV + CSV Importer
# ---------------------------------------------------------------------------

def export_enterprise_csvs(project_dir: Path, state: Dict[str, Any]) -> List[Path]:
    exp_dir = project_dir / "exports"
    exp_dir.mkdir(parents=True, exist_ok=True)
    ccy = state.get("currency", "EUR")
    written: List[Path] = []

    def dump_csv(filename: str, headers: List[str], rows: List[List[Any]]) -> None:
        fp = exp_dir / filename
        with fp.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(rows)
        written.append(fp)

    # 1. Gantt CPM CSV
    dump_csv(
        "gantt_schedule.csv",
        ["Task_ID", "Phase", "Name", "Owner_Seat", "Depends_On", "Status", "Progress_Pct",
         "Planned_Start", "Planned_End", "Forecast_Start", "Forecast_End", "Duration_Days",
         "Total_Float_Days", "Target_Slack_Days", "Is_Critical", "Is_Near_Critical", "Hard_Gate"],
        [
            [
                t["id"], t.get("phase", ""), t["name"], t.get("owner_seat", ""),
                ";".join(d if isinstance(d, str) else str(d.get("id", "")) for d in t.get("depends_on", [])),
                t.get("status", ""), t.get("progress_pct", 0),
                t["computed"]["planned_start"], t["computed"]["planned_end"],
                t["computed"]["forecast_start"], t["computed"]["forecast_end"],
                t["computed"]["duration_days"], t["computed"]["total_float_days"],
                t["computed"].get("target_slack_days", 0),
                t["computed"]["is_critical"], t["computed"].get("is_near_critical", False),
                t.get("hard_gate", ""),
            ]
            for t in state.get("tasks", [])
        ],
    )

    # 2. Budget 5-Column EVM CSV
    dump_csv(
        "budget_evm.csv",
        ["Task_ID", "Name", "Owner_Seat", f"Initial_BAC_{ccy}", f"Approved_Changes_{ccy}",
         f"Revised_Budget_{ccy}", f"Committed_{ccy}", f"Actual_AC_{ccy}", f"Remaining_ETC_{ccy}",
         f"Forecast_EAC_{ccy}", f"Variance_VAC_{ccy}", "Progress_Pct"],
        [
            [
                t["id"], t["name"], t.get("owner_seat", ""),
                t.get("planned_budget", 0), t["computed"].get("approved_changes_eur", 0),
                t["computed"].get("revised_budget", 0), t["computed"]["committed_cost"],
                t.get("actual_cost", 0), t["computed"].get("etc_eur", 0),
                t["computed"].get("task_eac_eur", 0), t["computed"].get("task_vac_eur", 0),
                t.get("progress_pct", 0),
            ]
            for t in state.get("tasks", [])
        ],
    )

    # 3. Risk Register CSV
    dump_csv(
        "risk_register.csv",
        ["Risk_ID", "Category", "Title", "Owner", "Status", "Probability_Pct",
         f"Cost_Impact_{ccy}", "Delay_Impact_Days", f"EMV_{ccy}", "Expected_Delay_Days", "Mitigation"],
        [
            [
                r.get("id", ""), r.get("category", ""), r.get("title", ""), r.get("owner_seat", "CRO-Risk"),
                r.get("status", "OPEN"), float(r.get("probability_pct", 0)),
                float(r.get("cost_impact_eur", 0)), float(r.get("delay_impact_days", 0)),
                round(float(r.get("probability_pct", 0)) / 100.0 * float(r.get("cost_impact_eur", 0)), 2),
                round(float(r.get("probability_pct", 0)) / 100.0 * float(r.get("delay_impact_days", 0)), 1),
                r.get("mitigation", ""),
            ]
            for r in state.get("risk_register", [])
        ],
    )

    # 4. Compliance / HSE / Testing / Reserves CSV
    dump_csv(
        "compliance_hse_snags.csv",
        ["Item_ID", "Domain", "Requirement", "Standard", "Status", "Test_Required", "Test_Completed",
         "Test_Date", "Reserves", "Linked_Task_ID", f"Remediation_Cost_{ccy}", "Remediation_Delay_Days",
         "Reserves_Lifted", "Certificate_Issued", "Blocking_GoLive", "Owner"],
        [
            [
                c.get("id", ""), c.get("domain", "HSE"), c.get("requirement", ""), c.get("standard", ""),
                c.get("status", "PENDING"), c.get("test_required", True), c.get("test_completed", False),
                c.get("test_date", ""), c.get("reserves", ""), c.get("linked_task_id", ""),
                c.get("remediation_cost_eur", 0), c.get("remediation_delay_days", 0),
                c.get("reserves_lifted", False), c.get("certificate_issued", False),
                c.get("blocking_go_live", True), c.get("owner_seat", "CCO-Compliance"),
            ]
            for c in state.get("compliance_register", [])
        ],
    )

    # 5. Contracts & Negotiation CSV
    dump_csv(
        "contracts_negotiation.csv",
        ["Contract_ID", "Contract_Type", "Counterparty", "Clause_Topic", "Target_Position",
         "Counterparty_Position", "HSE_Compliance_Linked", "Suspensive_Condition",
         "Deadline", f"Exposure_{ccy}", "Status", "Owner"],
        [
            [
                ct.get("id", ""), ct.get("contract_type", ""), ct.get("counterparty", ""),
                ct.get("clause_topic", ""), ct.get("target_position", ""), ct.get("counterparty_position", ""),
                ct.get("hse_compliance_linked", False), ct.get("is_suspensive_condition", False),
                ct.get("deadline", ""), ct.get("financial_exposure_eur", 0),
                ct.get("status", "NEGOTIATING"), ct.get("owner_seat", "CLO"),
            ]
            for ct in state.get("contracts_register", [])
        ],
    )

    # 6. Contagion Alerts CSV
    dump_csv(
        "contagion_alerts.csv",
        ["Alert_ID", "Status", "Severity", "Category", "Source_Seat", "Target_Seats",
         "Title", "Upstream_Cause", "Preventive_Action"],
        [
            [
                a.get("id", ""), a.get("status", ""), a.get("severity", ""), a.get("category", ""),
                a.get("source_seat", ""), ";".join(a.get("target_seats", [])),
                a.get("title", ""), a.get("upstream_cause", ""), a.get("preventive_action", ""),
            ]
            for a in state.get("alerts", [])
        ],
    )

    # 7. Jira / Asana / Monday.com Ready Import CSV
    dump_csv(
        "jira_asana_monday_import.csv",
        ["Summary", "Issue Type", "Assignee", "Status", "Priority", "Start Date", "Due Date", "Labels", "Description"],
        [
            [
                f"[{t['id']}] {t['name']}",
                "Milestone" if (t.get("hard_gate") or t.get("is_milestone")) else "Task",
                t.get("owner_seat", "PMO"),
                t.get("status", "TODO"),
                "Highest" if t["computed"]["is_critical"] else ("High" if t["computed"].get("is_near_critical") else "Medium"),
                t["computed"]["forecast_start"],
                t["computed"]["forecast_end"],
                f"{state.get('methodology_id', 'EXCOM')},{t.get('phase', 'Phase').replace(' ', '_')}",
                f"Budget: {t['computed'].get('revised_budget', 0)} {ccy} | Progress: {t.get('progress_pct', 0)}% | Gate: {t.get('hard_gate', 'None')}",
            ]
            for t in state.get("tasks", [])
        ],
    )
    return written


def import_tasks_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """Imports task updates from standard comma- or semicolon-delimited CSV (Excel FR/US, Smartsheet, Jira)."""
    raw = csv_path.read_text(encoding="utf-8-sig", errors="replace")
    sample = raw[:2048]
    delim = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(raw), delimiter=delim)
    imported: List[Dict[str, Any]] = []

    for row in reader:
        norm = {str(k).strip().lower(): (str(v).strip() if v is not None else "") for k, v in row.items() if k}
        tid = norm.get("task_id") or norm.get("id") or ""
        if not tid:
            continue
        item: Dict[str, Any] = {"id": tid}
        if norm.get("name") or norm.get("summary"):
            item["name"] = norm.get("name") or norm.get("summary")
        if norm.get("phase"):
            item["phase"] = norm["phase"]
        if norm.get("owner_seat") or norm.get("owner") or norm.get("assignee"):
            item["owner_seat"] = norm.get("owner_seat") or norm.get("owner") or norm.get("assignee")
        if norm.get("status"):
            item["status"] = norm["status"].upper()
        for src_k, dst_k in (
            ("progress_pct", "progress_pct"), ("progress", "progress_pct"),
            ("duration_days", "forecast_days"), ("forecast_days", "forecast_days"),
            ("planned_budget", "planned_budget"), ("committed_cost", "committed_cost"),
            ("actual_cost", "actual_cost"), ("actual_ac", "actual_cost"),
        ):
            if norm.get(src_k):
                try:
                    item[dst_k] = float(norm[src_k].replace(",", ".").replace(" ", ""))
                except ValueError:
                    pass
        if norm.get("notes"):
            item["notes"] = norm["notes"]
        imported.append(item)
    return imported


# ---------------------------------------------------------------------------
# 5. Steering Committee (CoPil) 1-Click Executive Brief Generator
# ---------------------------------------------------------------------------

def export_copil_brief(project_dir: Path, state: Dict[str, Any]) -> Path:
    m = state.get("metrics", {})
    evm = m.get("evm", {})
    qcdr = m.get("qcdr", {})
    ccy = state.get("currency", "EUR")
    open_alerts = [a for a in state.get("alerts", []) if a.get("status") == "OPEN"]
    open_risks = [r for r in state.get("risk_register", []) if str(r.get("status", "OPEN")).upper() == "OPEN"]
    open_comp = [c for c in state.get("compliance_register", []) if not c.get("certificate_issued")]
    open_contracts = [c for c in state.get("contracts_register", []) if str(c.get("status", "")).upper() != "SIGNED"]
    pending_cos = [co for co in state.get("change_orders", []) if str(co.get("status", "")).upper() == "PENDING"]

    lines = [
        f"# Steering Committee (CoPil) Executive Brief — {state.get('project_name', 'Project')}",
        "",
        f"- **As-Of Date** : `{m.get('as_of_date', '')}` · **Overall RAG** : `{state.get('overall_rag', 'GREEN')}` · **Methodology** : `{state.get('methodology_id', 'PREDICTIVE_STAGE_GATE')}`",
        f"- **Progress** : `{m.get('overall_progress_pct', 0)}%` · **Forecast End** : `{m.get('forecast_end_date', '')}` (Hard Target: `{m.get('target_end_date') or 'N/A'}` · Target Slack: `{m.get('target_margin_days', 'N/A')}d` · P85: `{m.get('p85_duration_days', 0)}d`)",
        f"- **Critical Path** : `{' -> '.join(m.get('critical_path', []))}`",
        "",
        "## 1. Q-C-D-R Executive Weather",
        "| Pillar | RAG / Status | Key Metric | Exposure / Blocker |",
        "| :--- | :---: | :--- | :--- |",
        f"| **Quality & HSE/Compliance** | `{qcdr.get('go_live_gate_status', 'READY')}` | `{qcdr.get('certificates_pct', 100)}%` certificates issued | `{qcdr.get('blocking_compliance_open', 0)}` Go-Live blockers · `{qcdr.get('open_reserves_count', 0)}` open reserves |",
        f"| **Cost (5-Column EVM)** | `{'RED' if evm.get('vac_eur', 0) < -evm.get('contingency_eur', 0) else ('AMBER' if evm.get('vac_eur', 0) < 0 else 'GREEN')}` | Revised `{evm.get('revised_budget_eur', 0):,.0f} {ccy}` · EAC `{evm.get('eac_eur', 0):,.0f} {ccy}` | Contingency left: `{evm.get('contingency_remaining_eur', 0):,.0f} {ccy}` · CPI `{evm.get('cpi', 1.0)}` |",
        f"| **Schedule (CPM / Hard Target)** | `{'RED' if (m.get('target_margin_days') is not None and m.get('target_margin_days') < 0) else ('AMBER' if m.get('project_slip_days', 0) > 0 else 'GREEN')}` | Forecast `{m.get('forecast_duration_days', 0)}d` vs Baseline `{m.get('baseline_duration_days', 0)}d` | Slip: `+{m.get('project_slip_days', 0)}d` · Near-critical: `{len(m.get('near_critical_tasks', []))}` tasks |",
        f"| **Risks & Contracts** | `{'RED' if qcdr.get('critical_risks_count', 0) > 0 else ('AMBER' if len(open_risks) > 0 else 'GREEN')}` | Total Risk EMV: `{qcdr.get('risk_emv_eur', 0):,.0f} {ccy}` / `{qcdr.get('risk_expected_delay_days', 0)}d` | `{qcdr.get('open_suspensive_conditions', 0)}` open suspensive conditions · `{len(open_contracts)}` contracts in negotiation |",
        "",
        f"## 2. Decisions & Change Orders Requiring Executive Arbitration (`{len(pending_cos)}` pending TMA)",
    ]
    if pending_cos:
        for co in pending_cos:
            lines.append(f"- **`{co.get('id')}`** — {co.get('title')} (`+{co.get('cost_impact_eur', 0):,.0f} {ccy}`, `+{co.get('delay_impact_days', 0)}d`, owner: `{co.get('owner_seat', 'PMO')}`)")
    else:
        lines.append("- No pending Change Orders awaiting signature.")

    lines.extend(["", f"## 3. Open Blocking HSE / Compliance & Reserves (`{len(open_comp)}`)"])
    if open_comp:
        for c in open_comp[:12]:
            blk = " **[GO-LIVE BLOCKER]**" if c.get("blocking_go_live", True) else ""
            lines.append(f"- **`{c.get('id')}`** ({c.get('domain', 'HSE')} · `{c.get('standard', '')}`){blk}: {c.get('requirement')} — Status `{c.get('status')}` · Reserves: `{c.get('reserves') or 'None'}` · Est. `+{c.get('remediation_cost_eur', 0):,.0f} {ccy}` / `+{c.get('remediation_delay_days', 0)}d`")
    else:
        lines.append("- 100% of tracked compliance certificates issued and reserves lifted.")

    lines.extend(["", f"## 4. Active Cross-Perimeter Contagion Alerts (`{len(open_alerts)}`)"])
    if open_alerts:
        for a in open_alerts[:12]:
            lines.append(f"- `[{a.get('severity')}]` `{a.get('source_seat')} -> {', '.join(a.get('target_seats', []))}`: **{a.get('title')}** — *{a.get('preventive_action')}*")
    else:
        lines.append("- Zero open contagion alerts.")

    if state.get("raci_matrix"):
        lines.extend(["", "## 5. Stakeholder RACI Matrix", "| Deliverable | R (Responsible) | A (Accountable) | C (Consulted) | I (Informed) |", "| :--- | :---: | :---: | :---: | :---: |"])
        for rc in state["raci_matrix"]:
            lines.append(f"| {rc.get('deliverable', '')} | `{rc.get('R', '')}` | `{rc.get('A', '')}` | `{rc.get('C', '')}` | `{rc.get('I', '')}` |")

    out_dir = project_dir / "deliverables"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "PMO_CoPil_Executive_Brief.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path
