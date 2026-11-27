#!/usr/bin/env python3
"""ExCom v3.4 — Native Zero-Dependency Office (.pptx, .docx) & AutoCAD (.dxf + .svg) Engine.

100% Python 3.8+ standard library (zero external pip dependencies).
Generates corporate-ready native files that work cleanly inside locked-down IT environments:
  1. Native PowerPoint Deck (`export_copil_pptx` -> `.pptx` PresentationML 16:9, 7 executive slides)
  2. Native Word Report (`export_copil_docx` -> `.docx` WordprocessingML, full Q-C-D-R tables)
  3. Parametric AutoCAD Macro + Micro-Zoning Floorplan (`generate_space_plan_dxf`):
       - Generates AutoCAD R12 ASCII `.dxf` (100% compatible with AutoCAD, AutoCAD LT, Autodesk
         DWG TrueView, LibreCAD, QCAD, BricsCAD, Revit import) with 10 standard architectural layers:
         `A-WALL`, `A-CORE`, `A-DOOR`, `A-ZONE-MACRO`, `A-FURN-DESK`, `A-FURN-MEET`,
         `A-CIRC-EGRESS`, `A-PMR-150`, `A-ANNO-TEXT`, `A-DIMS`.
       - Generates scaled vector preview `.svg` (ready for browsers, PDF print, PowerPoint).
       - Generates quantitative Workplace & Regulatory Audit JSON (m2/desk, flex ratio, AFNOR
         NF X 35-102 >= 10 m2/person check, ERP 2-UP 1.40m corridor check, meeting/booth ratios).
  4. ASCII `.dxf` Surface & Layer Auditor (`audit_dxf_file`): parses layers, bounding box, and
     closed-polygon Shoelace areas (m2) from external architect `.dxf` exports.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import zipfile


def _xml_esc(val: Any) -> str:
    txt = str(val if val is not None else "")
    txt = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", txt)
    return (
        txt.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


# ===========================================================================
# 1. NATIVE POWERPOINT (.pptx) 16:9 STEERING COMMITTEE DECK GENERATOR
# ===========================================================================

def _pptx_textbox(
    sp_id: int,
    name: str,
    x_in: float,
    y_in: float,
    w_in: float,
    h_in: float,
    lines: List[Tuple[str, int, bool, str]],
    fill_hex: Optional[str] = None,
    border_hex: Optional[str] = None,
) -> str:
    """Builds a DrawingML shape (`p:sp`) with optional background fill and styled paragraphs.
    `lines` is a list of `(text, font_pt, bold, rgb_hex)`.
    """
    emu = 914400
    x, y, cx, cy = int(x_in * emu), int(y_in * emu), int(w_in * emu), int(h_in * emu)
    fill_xml = f'<a:solidFill><a:srgbClr val="{fill_hex}"/></a:solidFill>' if fill_hex else "<a:noFill/>"
    ln_xml = f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{border_hex}"/></a:solidFill></a:ln>' if border_hex else '<a:ln><a:noFill/></a:ln>'

    paras = []
    for text, pt, bold, color in lines:
        b_attr = ' b="1"' if bold else ""
        sz = int(pt * 100)
        paras.append(
            "<a:p>"
            f'<a:r><a:rPr lang="en-US" sz="{sz}"{b_attr} dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            '<a:latin typeface="Calibri"/>'
            f"</a:rPr><a:t>{_xml_esc(text)}</a:t></a:r>"
            "</a:p>"
        )
    if not paras:
        paras.append("<a:p><a:endParaRPr lang=\"en-US\"/></a:p>")

    return (
        "<p:sp>"
        "<p:nvSpPr>"
        f'<p:cNvPr id="{sp_id}" name="{_xml_esc(name)}"/>'
        "<p:cNvSpPr txBox=\"1\"/>"
        "<p:nvPr/>"
        "</p:nvSpPr>"
        "<p:spPr>"
        f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>'
        f"{fill_xml}{ln_xml}"
        "</p:spPr>"
        "<p:txBody>"
        '<a:bodyPr wrap="square" lIns="91440" tIns="68580" rIns="91440" bIns="68580"/>'
        "<a:lstStyle/>"
        f'{"".join(paras)}'
        "</p:txBody>"
        "</p:sp>"
    )


def _pptx_table(
    gf_id: int,
    name: str,
    x_in: float,
    y_in: float,
    w_in: float,
    h_in: float,
    headers: List[str],
    rows: List[List[Any]],
    col_weights: Optional[List[float]] = None,
) -> str:
    """Builds a real editable PowerPoint DrawingML table (`p:graphicFrame`)."""
    emu = 914400
    x, y, cx, cy = int(x_in * emu), int(y_in * emu), int(w_in * emu), int(h_in * emu)
    ncols = max(1, len(headers))
    weights = col_weights if (col_weights and len(col_weights) == ncols) else [1.0] * ncols
    w_sum = sum(weights)
    col_widths = [int(cx * (w / w_sum)) for w in weights]
    grid_cols = "".join(f'<a:gridCol w="{cw}"/>' for cw in col_widths)

    all_rows = [headers] + rows[:12]
    row_h = max(240000, int(cy / max(1, len(all_rows))))
    tr_xmls: List[str] = []

    for r_idx, row in enumerate(all_rows):
        is_hdr = r_idx == 0
        bg = "1E293B" if is_hdr else ("F8FAFC" if r_idx % 2 == 1 else "FFFFFF")
        fg = "FFFFFF" if is_hdr else "0F172A"
        sz = 1050 if is_hdr else 950
        b_attr = ' b="1"' if is_hdr else ""
        tcs: List[str] = []
        for c_idx in range(ncols):
            val = str(row[c_idx])[:95] if c_idx < len(row) else ""
            tcs.append(
                "<a:tc>"
                "<a:txBody><a:bodyPr wrap=\"square\" lIns=\"55000\" rIns=\"55000\" tIns=\"35000\" bIns=\"35000\"/>"
                "<a:lstStyle/><a:p>"
                f'<a:r><a:rPr lang="en-US" sz="{sz}"{b_attr}><a:solidFill><a:srgbClr val="{fg}"/></a:solidFill>'
                '<a:latin typeface="Calibri"/></a:rPr>'
                f"<a:t>{_xml_esc(val)}</a:t></a:r>"
                "</a:p></a:txBody>"
                '<a:tcPr marL="55000" marR="55000" marT="35000" marB="35000">'
                '<a:lnL w="6350"><a:solidFill><a:srgbClr val="CBD5E1"/></a:solidFill></a:lnL>'
                '<a:lnR w="6350"><a:solidFill><a:srgbClr val="CBD5E1"/></a:solidFill></a:lnR>'
                '<a:lnT w="6350"><a:solidFill><a:srgbClr val="CBD5E1"/></a:solidFill></a:lnT>'
                '<a:lnB w="6350"><a:solidFill><a:srgbClr val="CBD5E1"/></a:solidFill></a:lnB>'
                f'<a:solidFill><a:srgbClr val="{bg}"/></a:solidFill>'
                "</a:tcPr>"
                "</a:tc>"
            )
        tr_xmls.append(f'<a:tr h="{row_h}">{"".join(tcs)}</a:tr>')

    return (
        "<p:graphicFrame>"
        "<p:nvGraphicFramePr>"
        f'<p:cNvPr id="{gf_id}" name="{_xml_esc(name)}"/>'
        "<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp=\"1\"/></p:cNvGraphicFramePr>"
        "<p:nvPr/>"
        "</p:nvGraphicFramePr>"
        f'<p:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></p:xfrm>'
        "<a:graphic>"
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
        "<a:tbl>"
        '<a:tblPr firstRow="1" bandRow="1"/>'
        f"<a:tblGrid>{grid_cols}</a:tblGrid>"
        f'{"".join(tr_xmls)}'
        "</a:tbl>"
        "</a:graphicData>"
        "</a:graphic>"
        "</p:graphicFrame>"
    )


def _wrap_slide(shapes_xml: str, bg_hex: str = "FFFFFF") -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        "<p:cSld>"
        f'<p:bg><p:bgPr><a:solidFill><a:srgbClr val="{bg_hex}"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>'
        "<p:spTree>"
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
        f"{shapes_xml}"
        "</p:spTree>"
        "</p:cSld>"
        "<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>"
        "</p:sld>"
    )


def _slide_header(title: str, subtitle: str, rag: str) -> str:
    rag_hex = {"GREEN": "10B981", "AMBER": "F59E0B", "RED": "EF4444"}.get(rag, "64748B")
    return (
        _pptx_textbox(2, "HeaderBar", 0.0, 0.0, 13.33, 1.05, [(title, 22, True, "FFFFFF"), (subtitle, 11, False, "CBD5E1")], fill_hex="0F172A")
        + _pptx_textbox(3, "RagBadge", 11.4, 0.22, 1.65, 0.55, [(f"RAG: {rag}", 13, True, "FFFFFF")], fill_hex=rag_hex)
    )


def export_copil_pptx(project_dir: Path, state: Dict[str, Any]) -> Path:
    """Exports a native 7-slide 16:9 Microsoft PowerPoint CoPil deck (pure Python stdlib OOXML)."""
    m = state.get("metrics", {})
    evm = m.get("evm", {})
    qcdr = m.get("qcdr", {})
    ccy = state.get("currency", "EUR")
    rag = state.get("overall_rag", "GREEN")
    proj = state.get("project_name", "ExCom Project")
    meth = state.get("methodology_id", "PREDICTIVE_STAGE_GATE")
    as_of = m.get("as_of_date", "")

    slides: List[str] = []

    # Slide 1 — Executive Cover & KPI Cards
    s1_shapes = (
        _pptx_textbox(2, "Banner", 0.0, 0.0, 13.33, 2.3, [
            ("STEERING COMMITTEE (CoPil) — EXECUTIVE REPORT", 13, True, "93C5FD"),
            (proj, 30, True, "FFFFFF"),
            (f"Methodology: {meth}  |  As-Of: {as_of}  |  Progress: {m.get('overall_progress_pct', 0)}%", 13, False, "CBD5E1"),
        ], fill_hex="0F172A")
        + _pptx_textbox(3, "RagCard", 10.6, 0.55, 2.3, 0.85, [(f"OVERALL RAG: {rag}", 16, True, "FFFFFF")],
                        fill_hex={"GREEN": "10B981", "AMBER": "F59E0B", "RED": "EF4444"}.get(rag, "64748B"))
        + _pptx_textbox(4, "KPI1", 0.5, 2.8, 3.8, 1.8, [
            ("SCHEDULE & HARD DEADLINE", 11, True, "475569"),
            (f"Forecast: {m.get('forecast_end_date', '')}", 18, True, "0F172A"),
            (f"Hard Target: {m.get('target_end_date') or 'N/A'}", 12, False, "334155"),
            (f"Target Slack: {m.get('target_margin_days', 'N/A')}d  |  P85: {m.get('p85_duration_days', 0)}d", 11, False, "64748B"),
        ], fill_hex="F8FAFC", border_hex="CBD5E1")
        + _pptx_textbox(5, "KPI2", 4.75, 2.8, 3.8, 1.8, [
            (f"5-COLUMN BUDGET & TCO ({ccy})", 11, True, "475569"),
            (f"EAC: {evm.get('eac_eur', 0):,.0f} {ccy}", 18, True, "0F172A"),
            (f"Revised: {evm.get('revised_budget_eur', 0):,.0f} | VAC: {evm.get('vac_eur', 0):+,.0f}", 11, False, "334155"),
            (f"Contingency left: {evm.get('contingency_remaining_eur', 0):,.0f} | {evm.get('tco_horizon_years', 6)}y TCO: {evm.get('tco_total_eur', 0):,.0f}", 10, False, "64748B"),
        ], fill_hex="F8FAFC", border_hex="CBD5E1")
        + _pptx_textbox(6, "KPI3", 9.0, 2.8, 3.8, 1.8, [
            ("HSE / COMPLIANCE GO-LIVE GATE", 11, True, "475569"),
            (str(qcdr.get("go_live_gate_status", "READY")), 16, True, "DC2626" if qcdr.get("blocking_compliance_open", 0) > 0 else "059669"),
            (f"Certificates: {qcdr.get('certificates_pct', 100)}% | Blockers: {qcdr.get('blocking_compliance_open', 0)}", 12, False, "334155"),
            (f"Open Reserves: {qcdr.get('open_reserves_count', 0)} | Risk EMV: {qcdr.get('risk_emv_eur', 0):,.0f} {ccy}", 10, False, "64748B"),
        ], fill_hex="F8FAFC", border_hex="CBD5E1")
        + _pptx_textbox(7, "Footer", 0.5, 5.1, 12.3, 1.8, [
            ("EXECUTIVE SUMMARY & CRITICAL PATH", 11, True, "1E293B"),
            (f"Locked Decision: {state.get('locked_decision', '')}", 11, False, "334155"),
            (f"Critical Path: {' -> '.join(m.get('critical_path', []))}", 11, True, "B91C1C"),
            (f"Open Contagion Alerts: {len([a for a in state.get('alerts', []) if a.get('status') == 'OPEN'])}  |  Pending Change Orders: {len([c for c in state.get('change_orders', []) if str(c.get('status','')).upper() == 'PENDING'])}", 11, False, "475569"),
        ], fill_hex="F1F5F9", border_hex="94A3B8")
    )
    slides.append(_wrap_slide(s1_shapes))

    # Slide 2 — 360° Q-C-D-R Scorecard
    qcdr_rows = [
        ["Quality & HSE / Compliance", str(qcdr.get("go_live_gate_status", "READY")), f"{qcdr.get('certificates_pct', 100)}% certs issued", f"{qcdr.get('blocking_compliance_open', 0)} blockers · {qcdr.get('open_reserves_count', 0)} open reserves"],
        ["Cost (5-Column EVM & TCO)", "RED" if evm.get("vac_eur", 0) < -evm.get("contingency_eur", 0) else ("AMBER" if evm.get("vac_eur", 0) < 0 else "GREEN"), f"EAC {evm.get('eac_eur', 0):,.0f} {ccy} (CPI {evm.get('cpi', 1.0)})", f"Contingency left {evm.get('contingency_remaining_eur', 0):,.0f} {ccy} · TCO {evm.get('tco_total_eur', 0):,.0f} {ccy}"],
        ["Schedule (CPM & Hard Target)", "RED" if (m.get("target_margin_days") is not None and m.get("target_margin_days") < 0) else ("AMBER" if m.get("project_slip_days", 0) > 0 else "GREEN"), f"End {m.get('forecast_end_date', '')} (SPI {evm.get('spi', 1.0)})", f"Target slack {m.get('target_margin_days', 'N/A')}d · Slip +{m.get('project_slip_days', 0)}d"],
        ["Risks (EMV) & Contracts", "RED" if qcdr.get("critical_risks_count", 0) > 0 else "AMBER", f"EMV {qcdr.get('risk_emv_eur', 0):,.0f} {ccy} / {qcdr.get('risk_expected_delay_days', 0)}d", f"{qcdr.get('open_suspensive_conditions', 0)} suspensive clauses · {qcdr.get('contracts_open_redlines', 0)} open redlines"],
    ]
    slides.append(_wrap_slide(
        _slide_header("1. 360° Q-C-D-R Executive Weather", proj, rag)
        + _pptx_table(10, "QCDRTable", 0.5, 1.35, 12.33, 5.4, ["Pillar", "Status", "Key Performance Metric", "Exposure / Actionable Focus"], qcdr_rows, [2.2, 1.8, 3.8, 4.5])
    ))

    # Slide 3 — Critical Path Schedule & Hard Target
    sched_rows = []
    for t in state.get("tasks", [])[:11]:
        c = t.get("computed", {})
        sched_rows.append([
            t["id"], t["name"][:42], t.get("owner_seat", ""), t.get("status", ""),
            f"{t.get('progress_pct', 0):.0f}%", c.get("forecast_end", ""),
            f"{c.get('total_float_days', 0)}d", "CRITICAL" if c.get("is_critical") else ("NEAR" if c.get("is_near_critical") else "OK"),
        ])
    slides.append(_wrap_slide(
        _slide_header("2. Schedule, Critical Path & Hard Target Deadline", f"Hard Target: {m.get('target_end_date') or 'N/A'} | Forecast: {m.get('forecast_end_date', '')} | Slack: {m.get('target_margin_days', 'N/A')}d", rag)
        + _pptx_table(11, "SchedTable", 0.45, 1.3, 12.43, 5.7, ["ID", "Workstream", "Owner", "Status", "%", "Forecast End", "Float", "Path"], sched_rows, [1.4, 3.6, 1.3, 1.2, 0.7, 1.4, 0.9, 1.1])
    ))

    # Slide 4 — 5-Column Budget & TCO Landing
    bud_rows = []
    for t in state.get("tasks", [])[:10]:
        c = t.get("computed", {})
        bud_rows.append([
            f"{t['id']} {t['name'][:28]}", f"{float(t.get('planned_budget', 0)):,.0f}", f"{float(c.get('approved_changes_eur', 0)):+,.0f}",
            f"{float(c.get('revised_budget', 0)):,.0f}", f"{float(c.get('committed_cost', 0)):,.0f}",
            f"{float(t.get('actual_cost', 0)):,.0f}", f"{float(c.get('task_eac_eur', 0)):,.0f}", f"{float(c.get('task_vac_eur', 0)):+,.0f}",
        ])
    bud_rows.append([
        "TOTAL CAPEX ROLLUP", f"{evm.get('bac_eur', 0):,.0f}", f"{evm.get('approved_changes_eur', 0):+,.0f}",
        f"{evm.get('revised_budget_eur', 0):,.0f}", f"{evm.get('committed_eur', 0):,.0f}",
        f"{evm.get('ac_eur', 0):,.0f}", f"{evm.get('eac_eur', 0):,.0f}", f"{evm.get('vac_eur', 0):+,.0f}",
    ])
    slides.append(_wrap_slide(
        _slide_header(f"3. 5-Column Budget, Change Orders & Multi-Year TCO ({ccy})", f"Contingency Left: {evm.get('contingency_remaining_eur', 0):,.0f} {ccy} | Mgmt Reserve: {evm.get('management_reserve_eur', 0):,.0f} {ccy} | {evm.get('tco_horizon_years', 6)}y TCO: {evm.get('tco_total_eur', 0):,.0f} {ccy}", rag)
        + _pptx_table(12, "BudTable", 0.4, 1.3, 12.53, 5.7, ["Workstream", "Init BAC", "TMA", "Revised", "Committed", "Actual AC", "EAC", "VAC"], bud_rows, [3.5, 1.25, 1.1, 1.25, 1.3, 1.25, 1.3, 1.2])
    ))

    # Slide 5 — HSE, Compliance, Testing & Punch-List Reserves (Go-Live Gate)
    comp_rows = []
    for c in state.get("compliance_register", [])[:11]:
        comp_rows.append([
            c.get("id", ""), c.get("standard", "")[:22], c.get("requirement", "")[:34],
            c.get("status", ""), "YES" if c.get("test_completed") else "NO",
            (c.get("reserves") or "None")[:28], f"+{float(c.get('remediation_cost_eur', 0)):,.0f} / +{float(c.get('remediation_delay_days', 0))}d",
            "ISSUED" if c.get("certificate_issued") else ("BLOCKER" if c.get("blocking_go_live", True) else "OPEN"),
        ])
    if not comp_rows:
        comp_rows.append(["N/A", "-", "No compliance/HSE items registered", "READY", "-", "None", "0", "READY"])
    slides.append(_wrap_slide(
        _slide_header("4. HSE, Regulatory Compliance, Testing & Reserves (Go-Live Gate)", f"Go-Live Status: {qcdr.get('go_live_gate_status')} | Certificates: {qcdr.get('certificates_pct', 100)}% | Remediation Impact: +{qcdr.get('compliance_remediation_cost_eur', 0):,.0f} {ccy}", rag)
        + _pptx_table(13, "CompTable", 0.4, 1.3, 12.53, 5.7, ["ID", "Standard", "Requirement", "Status", "Tested", "Open Reserves", "Impact", "Cert"], comp_rows, [0.9, 1.6, 2.7, 1.3, 0.8, 2.3, 1.6, 1.1])
    ))

    # Slide 6 — Contractual Negotiation & Quantified Risk EMV
    rc_rows = []
    for ct in state.get("contracts_register", [])[:5]:
        rc_rows.append(["CONTRACT", ct.get("id", ""), f"{ct.get('counterparty', '')}: {ct.get('clause_topic', '')[:38]}", ct.get("deadline", "N/A"), f"{float(ct.get('financial_exposure_eur', 0)):,.0f} {ccy}", ct.get("status", "")])
    for r in state.get("risk_register", [])[:6]:
        p = float(r.get("probability_pct", 0))
        rc_rows.append(["RISK EMV", r.get("id", ""), f"{r.get('title', '')[:42]} ({p:.0f}%)", f"+{float(r.get('delay_impact_days', 0))*p/100:.1f}d", f"{float(r.get('cost_impact_eur', 0))*p/100:,.0f} {ccy}", r.get("status", "OPEN")])
    if not rc_rows:
        rc_rows.append(["INFO", "-", "No open contracts or risks registered", "-", "0", "CLEAR"])
    slides.append(_wrap_slide(
        _slide_header("5. Contractual Redlines, Suspensive Conditions & Quantified Risk EMV", f"Total Risk EMV: {qcdr.get('risk_emv_eur', 0):,.0f} {ccy} | Open Contract Exposure: {qcdr.get('contracts_open_exposure_eur', 0):,.0f} {ccy}", rag)
        + _pptx_table(14, "RiskCtTable", 0.45, 1.3, 12.43, 5.7, ["Type", "ID", "Clause / Risk Item", "Deadline / Delay", "Exposure / EMV", "Status"], rc_rows, [1.2, 1.0, 5.0, 1.7, 1.9, 1.5])
    ))

    # Slide 7 — Decisions, Contagion Alerts & RACI Governance
    gov_rows = []
    for a in [x for x in state.get("alerts", []) if x.get("status") == "OPEN"][:5]:
        gov_rows.append(["ALERT", a.get("severity", ""), a.get("title", "")[:46], f"{a.get('source_seat')} -> {','.join(a.get('target_seats', [])[:2])}", a.get("preventive_action", "")[:38]])
    for co in [x for x in state.get("change_orders", []) if str(x.get("status", "")).upper() == "PENDING"][:3]:
        gov_rows.append(["TMA ARBITR.", "PENDING", co.get("title", "")[:46], co.get("owner_seat", ""), f"+{float(co.get('cost_impact_eur', 0)):,.0f} {ccy} / +{co.get('delay_impact_days', 0)}d"])
    for rc in state.get("raci_matrix", [])[:4]:
        gov_rows.append(["RACI", rc.get("R", ""), rc.get("deliverable", "")[:46], f"A: {rc.get('A', '')}", f"C: {rc.get('C', '')} | I: {rc.get('I', '')}"])
    if not gov_rows:
        gov_rows.append(["CLEAR", "GREEN", "Zero open escalations or pending arbitrations", "PMO", "Proceed per baseline schedule"])
    slides.append(_wrap_slide(
        _slide_header("6. Executive Escalations, Pending TMA Arbitrations & RACI", "Decisions required from Steering Committee (CoPil)", rag)
        + _pptx_table(15, "GovTable", 0.45, 1.3, 12.43, 5.7, ["Category", "Priority / R", "Item / Deliverable", "Flow / Accountable", "Action / Impact"], gov_rows, [1.3, 1.3, 4.3, 2.3, 3.2])
    ))

    # Build minimal valid PresentationML ZIP package (widescreen 13.333 x 7.5 in = 12192000 x 6858000 EMU)
    n_slides = len(slides)
    ct_slides = "".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, n_slides + 1)
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
        f"{ct_slides}</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
        "</Relationships>"
    )
    sld_id_lst = "".join(f'<p:sldId id="{255 + i}" r:id="rId{i + 1}"/>' for i in range(1, n_slides + 1))
    pres_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
        f"<p:sldIdLst>{sld_id_lst}</p:sldIdLst>"
        '<p:sldSz cx="12192000" cy="6858000"/>'
        '<p:notesSz cx="6858000" cy="9144000"/>'
        "</p:presentation>"
    )
    pres_rels_items = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    ] + [
        f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, n_slides + 1)
    ]
    pres_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'{"".join(pres_rels_items)}</Relationships>'
    )
    slide_master = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>'
        '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
        '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
        "</p:sldMaster>"
    )
    slide_master_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>'
        "</Relationships>"
    )
    slide_layout = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank">'
        '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>'
        "</p:sldLayout>"
    )
    slide_layout_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
        "</Relationships>"
    )
    slide_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
        "</Relationships>"
    )
    theme_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="ExCom Corporate">'
        '<a:themeElements><a:clrScheme name="ExCom">'
        '<a:dk1><a:srgbClr val="0F172A"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
        '<a:dk2><a:srgbClr val="1E293B"/></a:dk2><a:lt2><a:srgbClr val="F8FAFC"/></a:lt2>'
        '<a:accent1><a:srgbClr val="2563EB"/></a:accent1><a:accent2><a:srgbClr val="10B981"/></a:accent2>'
        '<a:accent3><a:srgbClr val="F59E0B"/></a:accent3><a:accent4><a:srgbClr val="EF4444"/></a:accent4>'
        '<a:accent5><a:srgbClr val="6366F1"/></a:accent5><a:accent6><a:srgbClr val="0EA5E9"/></a:accent6>'
        '<a:hlink><a:srgbClr val="2563EB"/></a:hlink><a:folHlink><a:srgbClr val="6366F1"/></a:folHlink>'
        '</a:clrScheme>'
        '<a:fontScheme name="ExCom"><a:majorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
        '<a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>'
        '<a:fmtScheme name="ExCom"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>'
        '<a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>'
        '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
        '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>'
        "</a:themeElements></a:theme>"
    )

    out_dir = project_dir / "deliverables"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "PMO_CoPil_Executive_Deck.pptx"
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("ppt/presentation.xml", pres_xml)
        zf.writestr("ppt/_rels/presentation.xml.rels", pres_rels)
        zf.writestr("ppt/slideMasters/slideMaster1.xml", slide_master)
        zf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", slide_master_rels)
        zf.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout)
        zf.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", slide_layout_rels)
        zf.writestr("ppt/theme/theme1.xml", theme_xml)
        for idx, s_xml in enumerate(slides, start=1):
            zf.writestr(f"ppt/slides/slide{idx}.xml", s_xml)
            zf.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", slide_rels)
    return out_path


# ===========================================================================
# 2. NATIVE MICROSOFT WORD (.docx) EXECUTIVE REPORT GENERATOR
# ===========================================================================

def _docx_p(text: str, bold: bool = False, size_half_pt: int = 20, color: str = "0F172A", space_after: int = 100) -> str:
    b = "<w:b/>" if bold else ""
    return (
        f'<w:p><w:pPr><w:spacing w:after="{space_after}"/></w:pPr>'
        f'<w:r><w:rPr>{b}<w:color w:val="{color}"/><w:sz w:val="{size_half_pt}"/><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/></w:rPr>'
        f'<w:t xml:space="preserve">{_xml_esc(text)}</w:t></w:r></w:p>'
    )


def _docx_table(headers: List[str], rows: List[List[Any]]) -> str:
    all_rows = [headers] + rows
    tr_xmls = []
    for r_idx, row in enumerate(all_rows):
        is_hdr = r_idx == 0
        shd = "1E293B" if is_hdr else ("F8FAFC" if r_idx % 2 == 1 else "FFFFFF")
        fg = "FFFFFF" if is_hdr else "0F172A"
        tcs = []
        for c_idx in range(len(headers)):
            val = str(row[c_idx]) if c_idx < len(row) else ""
            tcs.append(
                f'<w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="{shd}"/></w:tcPr>'
                + _docx_p(val, bold=is_hdr, size_half_pt=18, color=fg, space_after=40)
                + "</w:tc>"
            )
        tr_xmls.append(f'<w:tr>{"".join(tcs)}</w:tr>')
    borders = (
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:color="CBD5E1"/><w:bottom w:val="single" w:sz="4" w:color="CBD5E1"/>'
        '<w:left w:val="single" w:sz="4" w:color="CBD5E1"/><w:right w:val="single" w:sz="4" w:color="CBD5E1"/>'
        '<w:insideH w:val="single" w:sz="4" w:color="E2E8F0"/><w:insideV w:val="single" w:sz="4" w:color="E2E8F0"/>'
        "</w:tblBorders>"
    )
    return f'<w:tbl><w:tblPr><w:tblW w:w="9500" w:type="dxa"/>{borders}</w:tblPr>{"".join(tr_xmls)}</w:tbl>'


def export_copil_docx(project_dir: Path, state: Dict[str, Any]) -> Path:
    """Exports a native Microsoft Word (.docx) Steering Committee Executive Report (pure stdlib OOXML)."""
    m = state.get("metrics", {})
    evm = m.get("evm", {})
    qcdr = m.get("qcdr", {})
    ccy = state.get("currency", "EUR")

    body: List[str] = [
        _docx_p(f"EXECUTIVE STEERING REPORT (CoPil) — {state.get('project_name', 'Project')}", bold=True, size_half_pt=32, color="0F172A", space_after=140),
        _docx_p(
            f"As-Of: {m.get('as_of_date', '')}  |  Overall RAG: {state.get('overall_rag', 'GREEN')}  |  Methodology: {state.get('methodology_id', '')}  |  Progress: {m.get('overall_progress_pct', 0)}%",
            bold=True, size_half_pt=20, color="1D4ED8", space_after=180,
        ),
        _docx_p("1. 360° Q-C-D-R Executive Summary", bold=True, size_half_pt=26, color="1E293B", space_after=100),
        _docx_table(
            ["Dimension", "Metric / Status", "Target / Envelope", "Risk / Exposure"],
            [
                ["Schedule", f"Forecast End: {m.get('forecast_end_date', '')}", f"Hard Target: {m.get('target_end_date') or 'N/A'}", f"Slack: {m.get('target_margin_days', 'N/A')}d | Slip: +{m.get('project_slip_days', 0)}d"],
                [f"Cost ({ccy})", f"EAC: {evm.get('eac_eur', 0):,.0f}", f"Revised: {evm.get('revised_budget_eur', 0):,.0f} (BAC {evm.get('bac_eur', 0):,.0f})", f"VAC: {evm.get('vac_eur', 0):+,.0f} | Contingency left: {evm.get('contingency_remaining_eur', 0):,.0f}"],
                [f"Multi-Year TCO ({evm.get('tco_horizon_years', 6)}y)", f"{evm.get('tco_total_eur', 0):,.0f} {ccy}", f"Annual OPEX: {evm.get('recurring_annual_opex_eur', 0):,.0f}", f"CPI: {evm.get('cpi', 1.0)} | SPI: {evm.get('spi', 1.0)}"],
                ["HSE / Compliance Gate", str(qcdr.get("go_live_gate_status", "READY")), f"Certificates: {qcdr.get('certificates_pct', 100)}%", f"Blockers: {qcdr.get('blocking_compliance_open', 0)} | Open Reserves: {qcdr.get('open_reserves_count', 0)}"],
                ["Risks & Contracts", f"Risk EMV: {qcdr.get('risk_emv_eur', 0):,.0f} {ccy}", f"Exp. Delay: {qcdr.get('risk_expected_delay_days', 0)}d", f"Suspensive Open: {qcdr.get('open_suspensive_conditions', 0)} | Contract Exposure: {qcdr.get('contracts_open_exposure_eur', 0):,.0f}"],
            ],
        ),
        _docx_p("", space_after=80),
        _docx_p("2. Schedule & 5-Column Budget Control", bold=True, size_half_pt=26, color="1E293B", space_after=100),
        _docx_table(
            ["Task ID", "Workstream", "Owner", "End Date", "Revised", "EAC", "VAC"],
            [
                [t["id"], t["name"], t.get("owner_seat", ""), t["computed"]["forecast_end"], f"{t['computed']['revised_budget']:,.0f}", f"{t['computed']['task_eac_eur']:,.0f}", f"{t['computed']['task_vac_eur']:+,.0f}"]
                for t in state.get("tasks", [])
            ],
        ),
        _docx_p("", space_after=80),
        _docx_p("3. HSE / Compliance Certificates & Punch-List Reserves", bold=True, size_half_pt=26, color="1E293B", space_after=100),
        _docx_table(
            ["ID", "Standard", "Requirement", "Status", "Reserves", "Certificate"],
            [
                [c.get("id", ""), c.get("standard", ""), c.get("requirement", ""), c.get("status", ""), c.get("reserves") or "None", "ISSUED" if c.get("certificate_issued") else "MISSING"]
                for c in state.get("compliance_register", [])
            ] or [["-", "-", "No compliance items registered", "READY", "None", "READY"]],
        ),
        _docx_p("", space_after=80),
        _docx_p("4. Open Contagion Alerts & Decisions", bold=True, size_half_pt=26, color="1E293B", space_after=100),
        _docx_table(
            ["Severity", "Category", "Flow", "Title", "Preventive Action"],
            [
                [a.get("severity", ""), a.get("category", ""), f"{a.get('source_seat')} -> {','.join(a.get('target_seats', []))}", a.get("title", ""), a.get("preventive_action", "")]
                for a in state.get("alerts", []) if a.get("status") == "OPEN"
            ] or [["CLEAR", "-", "PMO", "Zero open alerts", "Maintain execution cadence"]],
        ),
    ]

    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:body>{"".join(body)}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1000" w:right="1000" w:bottom="1000" w:left="1000"/></w:sectPr></w:body>'
        "</w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    out_dir = project_dir / "deliverables"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "PMO_CoPil_Executive_Report.docx"
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("word/document.xml", doc_xml)
    return out_path


# ===========================================================================
# 3. AUTOCAD .DXF (MACRO + MICRO-ZONING) + SCALED .SVG + SPACE AUDIT ENGINE
# ===========================================================================

DXF_LAYERS: Dict[str, Tuple[int, str]] = {
    "A-WALL": (7, "#0f172a"),         # White/Black exterior & interior walls
    "A-CORE": (8, "#475569"),         # Gray elevator/stairs/restroom core
    "A-DOOR": (30, "#ea580c"),        # Orange door openings & swing arcs
    "A-ZONE-MACRO": (5, "#2563eb"),   # Blue macro department zone boundaries
    "A-FURN-DESK": (3, "#059669"),    # Green workstations & chairs (micro-zoning)
    "A-FURN-MEET": (6, "#7c3aed"),    # Magenta meeting tables & booths
    "A-CIRC-EGRESS": (2, "#d97706"),  # Yellow/Amber ERP egress corridor
    "A-PMR-150": (4, "#0891b2"),      # Cyan 1.50m PMR wheelchair turning circles
    "A-ANNO-TEXT": (7, "#0f172a"),    # Annotations & m2 labels
    "A-DIMS": (1, "#dc2626"),         # Red dimension callouts
}


class _DxfSvgBuilder:
    """Simultaneously emits standard AutoCAD R12 ASCII DXF entities and scaled 2D SVG primitives."""

    def __init__(self, width_m: float, depth_m: float) -> None:
        self.width_m = width_m
        self.depth_m = depth_m
        self.dxf_entities: List[str] = []
        self.svg_elements: List[str] = []
        self.scale = 24.0  # px per meter in SVG
        self.pad = 48.0

    def _sx(self, x: float) -> float:
        return round(self.pad + x * self.scale, 2)

    def _sy(self, y: float) -> float:
        # Flip Y so CAD bottom-left origin maps cleanly to architectural top-down SVG
        return round(self.pad + (self.depth_m - y) * self.scale, 2)

    def add_line(self, layer: str, x1: float, y1: float, x2: float, y2: float, stroke_w: float = 1.4, dashed: bool = False) -> None:
        self.dxf_entities.append(
            f"0\nLINE\n8\n{layer}\n10\n{x1:.3f}\n20\n{y1:.3f}\n30\n0.0\n11\n{x2:.3f}\n21\n{y2:.3f}\n31\n0.0"
        )
        col = DXF_LAYERS.get(layer, (7, "#334155"))[1]
        dash = ' stroke-dasharray="5,4"' if dashed else ""
        self.svg_elements.append(
            f'<line x1="{self._sx(x1)}" y1="{self._sy(y1)}" x2="{self._sx(x2)}" y2="{self._sy(y2)}" '
            f'stroke="{col}" stroke-width="{stroke_w}"{dash}/>'
        )

    def add_rect(
        self,
        layer: str,
        x: float,
        y: float,
        w: float,
        h: float,
        fill_svg: str = "none",
        fill_opacity: float = 0.14,
        stroke_w: float = 1.4,
        dashed: bool = False,
    ) -> None:
        # Emit closed R12 POLYLINE (supported by 100% of CAD tools + Shoelace area auditable!)
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        verts = "\n".join(f"0\nVERTEX\n8\n{layer}\n10\n{px:.3f}\n20\n{py:.3f}\n30\n0.0" for px, py in pts)
        self.dxf_entities.append(f"0\nPOLYLINE\n8\n{layer}\n66\n1\n70\n1\n{verts}\n0\nSEQEND")

        col = DXF_LAYERS.get(layer, (7, "#334155"))[1]
        dash = ' stroke-dasharray="6,4"' if dashed else ""
        self.svg_elements.append(
            f'<rect x="{self._sx(x)}" y="{self._sy(y + h)}" width="{round(w * self.scale, 2)}" height="{round(h * self.scale, 2)}" '
            f'fill="{fill_svg}" fill-opacity="{fill_opacity}" stroke="{col}" stroke-width="{stroke_w}"{dash}/>'
        )

    def add_circle(self, layer: str, cx: float, cy: float, r: float, dashed: bool = True) -> None:
        self.dxf_entities.append(f"0\nCIRCLE\n8\n{layer}\n10\n{cx:.3f}\n20\n{cy:.3f}\n30\n0.0\n40\n{r:.3f}")
        col = DXF_LAYERS.get(layer, (4, "#0891b2"))[1]
        dash = ' stroke-dasharray="4,3"' if dashed else ""
        self.svg_elements.append(
            f'<circle cx="{self._sx(cx)}" cy="{self._sy(cy)}" r="{round(r * self.scale, 2)}" '
            f'fill="none" stroke="{col}" stroke-width="1.2"{dash}/>'
        )

    def add_door_swing(self, x: float, y: float, r: float = 0.90) -> None:
        self.dxf_entities.append(
            f"0\nARC\n8\nA-DOOR\n10\n{x:.3f}\n20\n{y:.3f}\n30\n0.0\n40\n{r:.3f}\n50\n0.0\n51\n90.0"
        )
        self.add_line("A-DOOR", x, y, x, y + r, stroke_w=1.2)
        sr = round(r * self.scale, 2)
        self.svg_elements.append(
            f'<path d="M {self._sx(x + r)} {self._sy(y)} A {sr} {sr} 0 0 0 {self._sx(x)} {self._sy(y + r)}" '
            'fill="none" stroke="#ea580c" stroke-width="1.1" stroke-dasharray="3,2"/>'
        )

    def add_text(self, layer: str, x: float, y: float, text: str, height_m: float = 0.35, bold: bool = False) -> None:
        clean = text.replace("\n", " ")
        self.dxf_entities.append(
            f"0\nTEXT\n8\n{layer}\n10\n{x:.3f}\n20\n{y:.3f}\n30\n0.0\n40\n{height_m:.2f}\n1\n{clean}"
        )
        col = DXF_LAYERS.get(layer, (7, "#0f172a"))[1]
        px = max(9, int(round(height_m * self.scale * 0.9)))
        fw = ' font-weight="700"' if bold else ""
        self.svg_elements.append(
            f'<text x="{self._sx(x)}" y="{self._sy(y)}" font-family="Segoe UI,Calibri,sans-serif" font-size="{px}" fill="{col}"{fw}>{_xml_esc(clean)}</text>'
        )

    def build_dxf(self) -> str:
        layer_defs = []
        for lname, (aci, _) in DXF_LAYERS.items():
            layer_defs.append(f"0\nLAYER\n2\n{lname}\n70\n0\n62\n{aci}\n6\nCONTINUOUS")
        header = (
            "0\nSECTION\n2\nHEADER\n"
            "9\n$ACADVER\n1\nAC1009\n"
            "9\n$INSUNITS\n70\n6\n"  # 6 = Meters
            "0\nENDSEC\n"
            "0\nSECTION\n2\nTABLES\n"
            f"0\nTABLE\n2\nLAYER\n70\n{len(DXF_LAYERS)}\n"
            + "\n".join(layer_defs)
            + "\n0\nENDTAB\n0\nENDSEC\n"
        )
        entities = "0\nSECTION\n2\nENTITIES\n" + "\n".join(self.dxf_entities) + "\n0\nENDSEC\n0\nEOF\n"
        return header + entities

    def build_svg(self, title: str, audit: Dict[str, Any]) -> str:
        svg_w = int(round(self.width_m * self.scale + self.pad * 2))
        svg_h = int(round(self.depth_m * self.scale + self.pad * 2 + 74))
        legend_y = int(round(self.depth_m * self.scale + self.pad * 1.45))
        summary = (
            f"{title} | Gross: {audit['gross_area_m2']:.0f} m2 | Desks: {audit['total_workstations']} "
            f"(Flex {audit['flex_ratio']} -> {audit['max_headcount_at_flex']} staff) | "
            f"{audit['m2_per_workstation']:.1f} m2/desk ({audit['m2_per_employee_flex']:.1f} m2/staff) | "
            f"Meeting Seats: {audit['meeting_seats_total']} | AFNOR>=10m2: {'OK' if audit['afnor_nfx35102_compliant'] else 'ALERT'} | "
            f"ERP Corridor>=1.40m: {'OK' if audit['erp_egress_up_compliant'] else 'ALERT'}"
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" style="background:#ffffff;">'
            f'<rect x="0" y="0" width="{svg_w}" height="{svg_h}" fill="#ffffff"/>'
            f'<text x="{int(self.pad)}" y="24" font-family="Segoe UI,Calibri,sans-serif" font-size="14" font-weight="700" fill="#0f172a">{_xml_esc(summary)}</text>'
            + "".join(self.svg_elements)
            + f'<text x="{int(self.pad)}" y="{legend_y + 28}" font-family="Segoe UI,Calibri,sans-serif" font-size="11" fill="#475569">'
            'Legend: [Black] Structural/Interior Walls | [Blue Dashed] Macro Zones | [Green] Micro-Zoning Workstations &amp; Chairs | [Purple] Meeting Tables/Booths | [Amber] ERP Egress Corridor | [Cyan] PMR 1.50m Circles | [Orange] Door Swings'
            "</text></svg>"
        )


def generate_space_plan_dxf(project_dir: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    """Generates AutoCAD .dxf (Macro + Micro-Zoning), scaled .svg preview, and Workplace Audit JSON."""
    title = str(spec.get("title", "Corporate Floorplate — Macro & Micro-Zoning"))
    length_m = float(spec.get("length_m", 40.0))
    depth_m = float(spec.get("depth_m", 20.0))
    corridor_w = float(spec.get("corridor_width_m", 1.80))
    flex_ratio = float(spec.get("flex_ratio", 0.80))
    target_hc = int(spec.get("target_headcount", 60))

    b = _DxfSvgBuilder(length_m, depth_m)

    # Outer building perimeter walls + overall dimensions
    b.add_rect("A-WALL", 0.0, 0.0, length_m, depth_m, fill_svg="#f8fafc", fill_opacity=0.6, stroke_w=2.6)
    b.add_text("A-DIMS", length_m * 0.44, -0.75, f"TOTAL LENGTH: {length_m:.2f} m", height_m=0.45, bold=True)
    b.add_text("A-DIMS", 0.3, depth_m + 0.45, f"DEPTH: {depth_m:.2f} m  |  GROSS AREA: {length_m * depth_m:.1f} m2", height_m=0.45, bold=True)

    # Central horizontal ERP circulation spine
    corr_y = round((depth_m - corridor_w) / 2.0, 2)
    b.add_rect("A-CIRC-EGRESS", 0.0, corr_y, length_m, corridor_w, fill_svg="#fef3c7", fill_opacity=0.55, stroke_w=1.2, dashed=True)
    b.add_text("A-CIRC-EGRESS", 0.6, corr_y + corridor_w * 0.35, f"MAIN ERP EGRESS CORRIDOR ({corridor_w:.2f}m)", height_m=0.35, bold=True)

    # PMR 1.50m turning circles along main egress & entries
    for cx_pmr in (1.5, length_m * 0.5, length_m - 1.5):
        b.add_circle("A-PMR-150", cx_pmr, corr_y + corridor_w / 2.0, 0.75, dashed=True)

    # Default zones if none supplied
    zones_in = spec.get("zones") or [
        {"name": "Open Space — Ops & Sales", "zone_type": "OPEN_SPACE", "side": "NORTH", "share_pct": 55},
        {"name": "Open Space — Tech & Finance", "zone_type": "OPEN_SPACE", "side": "NORTH", "share_pct": 45},
        {"name": "Reception & Welcome", "zone_type": "RECEPTION", "side": "SOUTH", "share_pct": 15},
        {"name": "Meeting Hub & Phone Booths", "zone_type": "MEETING_HUB", "side": "SOUTH", "share_pct": 35},
        {"name": "Enclosed Offices (Exec / HR)", "zone_type": "PRIVATE_OFFICES", "side": "SOUTH", "share_pct": 25},
        {"name": "Breakout / QVT Lounge", "zone_type": "BREAKOUT", "side": "SOUTH", "share_pct": 15},
        {"name": "IT Server / CFA & Core", "zone_type": "SERVER_CFA", "side": "SOUTH", "share_pct": 10},
    ]

    north_zones = [z for z in zones_in if str(z.get("side", "NORTH")).upper() == "NORTH"]
    south_zones = [z for z in zones_in if str(z.get("side", "SOUTH")).upper() != "NORTH"]
    if not north_zones:
        north_zones = zones_in[: max(1, len(zones_in) // 2)]
        south_zones = zones_in[max(1, len(zones_in) // 2):]

    north_y0 = corr_y + corridor_w
    north_h = round(depth_m - north_y0, 2)
    south_y0 = 0.0
    south_h = round(corr_y, 2)

    total_desks = 0
    total_meeting_seats = 0
    total_booths = 0
    total_private_offices = 0
    zone_audit: List[Dict[str, Any]] = []

    def layout_strip(zlist: List[Dict[str, Any]], y0: float, strip_h: float, is_north: bool) -> None:
        nonlocal total_desks, total_meeting_seats, total_booths, total_private_offices
        if not zlist or strip_h <= 1.0:
            return
        share_sum = sum(max(1.0, float(z.get("share_pct", 10.0))) for z in zlist)
        cur_x = 0.0
        for idx, z in enumerate(zlist):
            w = round(length_m * (max(1.0, float(z.get("share_pct", 10.0))) / share_sum), 2)
            if idx == len(zlist) - 1:
                w = round(length_m - cur_x, 2)
            ztype = str(z.get("zone_type", "OPEN_SPACE")).upper()
            zname = str(z.get("name", f"Zone {idx + 1}"))
            area_m2 = round(w * strip_h, 1)

            # Macro-zoning boundary
            fill_map = {
                "OPEN_SPACE": "#dcfce7", "PRIVATE_OFFICES": "#e0e7ff", "MEETING_HUB": "#f3e8ff",
                "RECEPTION": "#ffedd5", "BREAKOUT": "#fef9c3", "SERVER_CFA": "#e2e8f0", "ARCHIVE_TECH": "#e2e8f0",
            }
            b.add_rect("A-ZONE-MACRO", cur_x, y0, w, strip_h, fill_svg=fill_map.get(ztype, "#f1f5f9"), fill_opacity=0.45, stroke_w=1.5, dashed=True)
            # Internal partition wall between zones
            if cur_x > 0.1:
                b.add_line("A-WALL", cur_x, y0, cur_x, y0 + strip_h, stroke_w=1.8)

            desks_here = 0
            seats_here = 0
            booths_here = 0

            # MICRO-ZONING FURNITURE & ROOM GENERATION
            if ztype == "OPEN_SPACE":
                dw = float(z.get("desk_w_m", 1.60))
                dd = float(z.get("desk_d_m", 0.80))
                aisle_x = 1.40
                aisle_y = 1.60  # double-sided benching clearance
                margin = 1.0
                # Place double-sided benching islands (2 rows back-to-back = 2*dd)
                pitch_x = dw + 0.10
                pitch_y = (2.0 * dd) + aisle_y
                cols = max(0, int((w - 2 * margin - aisle_x) // pitch_x))
                banks = max(0, int((strip_h - 2 * margin) // pitch_y))
                for bi in range(banks):
                    by = y0 + margin + bi * pitch_y
                    for ci in range(cols):
                        bx = cur_x + margin + ci * pitch_x
                        if bx + dw > cur_x + w - margin or by + 2 * dd > y0 + strip_h - margin:
                            continue
                        # Bottom desk + chair
                        b.add_rect("A-FURN-DESK", bx, by, dw, dd, fill_svg="#10b981", fill_opacity=0.28, stroke_w=1.0)
                        b.add_circle("A-FURN-DESK", bx + dw * 0.5, by - 0.35, 0.24, dashed=False)
                        # Top back-to-back desk + chair
                        b.add_rect("A-FURN-DESK", bx, by + dd, dw, dd, fill_svg="#10b981", fill_opacity=0.28, stroke_w=1.0)
                        b.add_circle("A-FURN-DESK", bx + dw * 0.5, by + 2 * dd + 0.35, 0.24, dashed=False)
                        desks_here += 2
                total_desks += desks_here

            elif ztype == "PRIVATE_OFFICES":
                office_w = max(3.2, float(z.get("office_w_m", 3.6)))
                n_off = max(1, int(w // office_w))
                actual_w = round(w / n_off, 2)
                for oi in range(n_off):
                    ox = cur_x + oi * actual_w
                    b.add_rect("A-WALL", ox, y0, actual_w, strip_h, fill_svg="none", stroke_w=1.6)
                    door_y = y0 if is_north else (y0 + strip_h - 0.90)
                    b.add_door_swing(ox + 0.35, door_y, 0.85)
                    # Executive desk + 2 visitor chairs
                    dx = ox + (actual_w - 1.8) * 0.5
                    dy = y0 + strip_h * 0.45
                    if actual_w >= 2.2 and strip_h >= 2.5:
                        b.add_rect("A-FURN-DESK", dx, dy, 1.8, 0.9, fill_svg="#3b82f6", fill_opacity=0.3, stroke_w=1.1)
                        b.add_circle("A-FURN-DESK", dx + 0.9, dy - 0.4, 0.25, dashed=False)
                        b.add_circle("A-FURN-DESK", dx + 0.45, dy + 1.3, 0.22, dashed=False)
                        b.add_circle("A-FURN-DESK", dx + 1.35, dy + 1.3, 0.22, dashed=False)
                    desks_here += 1
                    total_private_offices += 1
                total_desks += desks_here

            elif ztype == "MEETING_HUB":
                # Reserve 25% of width for 1.3m acoustic phone booths, 75% for conference rooms
                booth_band = min(w * 0.25, 3.9)
                n_booths = max(0, int(booth_band // 1.3))
                rooms_w = w - (n_booths * 1.3)
                n_rooms = max(1, int(rooms_w // 4.5))
                rm_w = round(rooms_w / n_rooms, 2)
                for ri in range(n_rooms):
                    rx = cur_x + ri * rm_w
                    b.add_rect("A-WALL", rx, y0, rm_w, strip_h, fill_svg="none", stroke_w=1.6)
                    door_y = y0 if is_north else (y0 + strip_h - 0.90)
                    b.add_door_swing(rx + 0.4, door_y, 0.85)
                    tw = max(1.6, rm_w - 2.0)
                    th = max(1.2, min(2.2, strip_h - 2.6))
                    tx = rx + (rm_w - tw) * 0.5
                    ty = y0 + (strip_h - th) * 0.5
                    b.add_rect("A-FURN-MEET", tx, ty, tw, th, fill_svg="#7c3aed", fill_opacity=0.28, stroke_w=1.2)
                    n_side = max(2, int(tw // 0.75))
                    for si in range(n_side):
                        cx = tx + (si + 0.5) * (tw / n_side)
                        b.add_circle("A-FURN-MEET", cx, ty - 0.32, 0.22, dashed=False)
                        b.add_circle("A-FURN-MEET", cx, ty + th + 0.32, 0.22, dashed=False)
                    seats_here += 2 * n_side
                for bi in range(n_booths):
                    bx = cur_x + rooms_w + bi * 1.3
                    b.add_rect("A-FURN-MEET", bx + 0.08, y0 + 0.4, 1.14, min(1.4, strip_h - 0.8), fill_svg="#a855f7", fill_opacity=0.35, stroke_w=1.1)
                    booths_here += 1
                total_meeting_seats += seats_here
                total_booths += booths_here

            elif ztype == "SERVER_CFA":
                b.add_rect("A-CORE", cur_x, y0, w, strip_h, fill_svg="#94a3b8", fill_opacity=0.35, stroke_w=1.8)
                # Server racks 0.80m x 1.00m
                n_racks = max(1, int((w - 1.2) // 0.95))
                for rk in range(min(n_racks, 8)):
                    b.add_rect("A-CORE", cur_x + 0.6 + rk * 0.95, y0 + 1.2, 0.80, 1.00, fill_svg="#334155", fill_opacity=0.5, stroke_w=1.1)

            elif ztype == "RECEPTION":
                b.add_rect("A-FURN-MEET", cur_x + 1.0, y0 + strip_h * 0.45, max(1.8, min(3.2, w - 2.0)), 0.9, fill_svg="#f97316", fill_opacity=0.35, stroke_w=1.2)
                b.add_circle("A-PMR-150", cur_x + w * 0.5, y0 + strip_h * 0.22, 0.75, dashed=True)

            elif ztype == "BREAKOUT":
                # Cafe / QVT tables
                nt = max(1, int((w - 1.0) // 2.4))
                for ti in range(min(nt, 5)):
                    b.add_circle("A-FURN-MEET", cur_x + 1.2 + ti * 2.3, y0 + strip_h * 0.5, 0.55, dashed=False)

            lbl_y = y0 + strip_h - 0.65 if is_north else y0 + 0.35
            meta_lbl = f"{zname} ({area_m2:.0f}m2" + (f" · {desks_here} desks" if desks_here else "") + (f" · {seats_here} seats/{booths_here} booths" if seats_here else "") + ")"
            b.add_text("A-ANNO-TEXT", cur_x + 0.35, lbl_y, meta_lbl, height_m=0.32, bold=True)

            zone_audit.append({
                "name": zname, "zone_type": ztype, "side": "NORTH" if is_north else "SOUTH",
                "x_m": round(cur_x, 2), "y_m": round(y0, 2), "width_m": w, "depth_m": strip_h,
                "area_m2": area_m2, "workstations": desks_here, "meeting_seats": seats_here, "phone_booths": booths_here,
            })
            cur_x = round(cur_x + w, 2)

    layout_strip(north_zones, north_y0, north_h, is_north=True)
    layout_strip(south_zones, south_y0, south_h, is_north=False)

    gross_area = round(length_m * depth_m, 1)
    circ_area = round(length_m * corridor_w, 1)
    net_area = round(gross_area - circ_area, 1)
    max_hc_flex = int(round(total_desks / max(0.2, flex_ratio))) if total_desks > 0 else 0
    m2_per_desk = round(gross_area / max(1, total_desks), 2) if total_desks > 0 else 0.0
    m2_per_emp = round(gross_area / max(1, target_hc), 2)

    audit = {
        "title": title,
        "gross_area_m2": gross_area,
        "circulation_area_m2": circ_area,
        "net_zone_area_m2": net_area,
        "corridor_width_m": corridor_w,
        "target_headcount": target_hc,
        "flex_ratio": flex_ratio,
        "total_workstations": total_desks,
        "private_offices_count": total_private_offices,
        "max_headcount_at_flex": max_hc_flex,
        "headcount_fit_ok": max_hc_flex >= target_hc,
        "m2_per_workstation": m2_per_desk,
        "m2_per_employee_flex": m2_per_emp,
        "afnor_nfx35102_compliant": m2_per_desk >= 10.0,
        "erp_egress_up_compliant": corridor_w >= 1.40,
        "meeting_seats_total": total_meeting_seats,
        "meeting_seats_per_10_desks": round((total_meeting_seats / max(1, total_desks)) * 10.0, 1),
        "phone_booths_count": total_booths,
        "zones": zone_audit,
    }

    exp_dir = project_dir / "exports"
    exp_dir.mkdir(parents=True, exist_ok=True)
    dxf_path = exp_dir / "space_plan_macro_micro.dxf"
    svg_path = exp_dir / "space_plan_preview.svg"
    audit_path = exp_dir / "space_plan_audit.json"

    dxf_path.write_text(b.build_dxf(), encoding="utf-8")
    svg_path.write_text(b.build_svg(title, audit), encoding="utf-8")
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "dxf_path": str(dxf_path),
        "svg_path": str(svg_path),
        "audit_json_path": str(audit_path),
        "audit": audit,
    }


def _shoelace_area(pts: List[Tuple[float, float]]) -> float:
    if len(pts) < 3:
        return 0.0
    acc = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        acc += x1 * y2 - x2 * y1
    return abs(acc) * 0.5


def audit_dxf_file(dxf_path: Path) -> Dict[str, Any]:
    """Parses any ASCII .dxf file (R12/R2000+) to extract layers, bounding box, entity counts, and closed-polygon m2 areas."""
    raw_lines = [ln.strip() for ln in dxf_path.read_text(encoding="utf-8", errors="replace").splitlines()]
    pairs: List[Tuple[str, str]] = []
    i = 0
    while i + 1 < len(raw_lines):
        pairs.append((raw_lines[i], raw_lines[i + 1]))
        i += 2

    in_entities = False
    layer_counts: Dict[str, int] = {}
    layer_areas: Dict[str, float] = {}
    xs: List[float] = []
    ys: List[float] = []
    texts: List[str] = []

    idx = 0
    while idx < len(pairs):
        code, val = pairs[idx]
        if code == "2" and val == "ENTITIES":
            in_entities = True
            idx += 1
            continue
        if in_entities and code == "0" and val == "ENDSEC":
            break
        if not in_entities:
            idx += 1
            continue

        if code == "0" and val in ("LINE", "CIRCLE", "ARC", "TEXT", "MTEXT", "LWPOLYLINE", "POLYLINE"):
            etype = val
            layer = "0"
            pts: List[Tuple[float, float]] = []
            cur_x: Optional[float] = None
            closed = False
            idx += 1
            if etype == "POLYLINE":
                # Collect VERTEX until SEQEND
                while idx < len(pairs):
                    c2, v2 = pairs[idx]
                    if c2 == "0" and v2 == "SEQEND":
                        idx += 1
                        break
                    if c2 == "8":
                        layer = v2
                    elif c2 == "70":
                        closed = bool(int(v2) & 1)
                    elif c2 == "10":
                        cur_x = float(v2)
                    elif c2 == "20" and cur_x is not None:
                        py = float(v2)
                        pts.append((cur_x, py))
                        xs.append(cur_x)
                        ys.append(py)
                        cur_x = None
                    idx += 1
            else:
                while idx < len(pairs) and pairs[idx][0] != "0":
                    c2, v2 = pairs[idx]
                    if c2 == "8":
                        layer = v2
                    elif c2 == "70" and etype == "LWPOLYLINE":
                        closed = bool(int(v2) & 1)
                    elif c2 in ("10", "11"):
                        cur_x = float(v2)
                    elif c2 in ("20", "21") and cur_x is not None:
                        py = float(v2)
                        pts.append((cur_x, py))
                        if etype not in ("TEXT", "MTEXT"):
                            xs.append(cur_x)
                            ys.append(py)
                        cur_x = None
                    elif c2 == "1" and etype in ("TEXT", "MTEXT"):
                        texts.append(v2)
                    idx += 1

            layer_counts[layer] = layer_counts.get(layer, 0) + 1
            if closed and len(pts) >= 3:
                layer_areas[layer] = round(layer_areas.get(layer, 0.0) + _shoelace_area(pts), 2)
            continue
        idx += 1

    bbox_w = round(max(xs) - min(xs), 2) if xs else 0.0
    bbox_h = round(max(ys) - min(ys), 2) if ys else 0.0
    return {
        "file": str(dxf_path),
        "bounding_box_m": {"width": bbox_w, "depth": bbox_h, "bbox_area_m2": round(bbox_w * bbox_h, 2)},
        "entities_by_layer": dict(sorted(layer_counts.items())),
        "closed_polygon_area_m2_by_layer": dict(sorted(layer_areas.items())),
        "text_annotations_count": len(texts),
        "text_annotations_sample": texts[:15],
    }
