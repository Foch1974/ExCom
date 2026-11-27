# Adaptive Project Methodology Selector & Enterprise Interchange (`ExCom v3.3`)

Before initializing any project Control Tower, **always** run the deterministic methodology selector so `ExCom` configures the exact WBS phases, Stage-Gates, Q-C-D-R registers, and Clean-Room Board cadence matched to the project's physics:

```bash
python "<skill-dir>/scripts/excom_engine.py" select-methodology \
  --description "Corporate HQ relocation, commercial lease negotiation, full fit-out works and team move-in" \
  --uncertainty LOW --regulatory HIGH --capital HIGH --cadence MILESTONE
```

---

## 1. The 6 Gold-Standard Project Methodologies

| Methodology ID | Industry Standards | Best Suited For | Clean-Room Cadence | Core Governance Lock |
| :--- | :--- | :--- | :--- | :--- |
| **`PREDICTIVE_STAGE_GATE`** | PMI Predictive · Loi MOP · RIBA · PRINCE2 · FIDIC | Corporate Real Estate, Ground-Up Construction (MOA/BEFA/VEFA), Industrial Capex, Infrastructure, Hardware BOM, Legal/M&A | `EVERY_MAJOR_MILESTONE` (at every Stage-Gate SG0..SG6) | Frozen scope per stage (`Design Freeze`), Hard Target Deadline negative float, Blocking HSE/Compliance Go-Live Gate |
| **`HYBRID_STAGE_GATE_AGILE`** | PMI Hybrid · European PM² | Workplace Fit-Out + IT/Digital Rollout, ERP/CRM Migration, Corporate Restructuring, Connected Product Launch | `EVERY_MAJOR_MILESTONE` (at Stage-Gates + pre-cutover) | Stage-Gate contract/budget/regulatory wrapper + iterative Agile delivery waves |
| **`AGILE_SCRUM_SHAPE_UP`** | Scrum · Shape Up · Continuous CI/CD | SaaS Applications, Web/Mobile Apps, Evolving Customer Software | `EVERY_MAJOR_MILESTONE` (post-sprint/release candidate) | North-Star adoption ceiling vs target + automated test twins |
| **`LEAN_KANBAN_TOC`** | Kanban · Theory of Constraints (Drum-Buffer-Rope) | Ongoing Operations, Multi-Site Maintenance, Continuous Sourcing/Supply Chain, Support Queues | `PLATEAU_2` (or quarterly operational audit) | WIP caps, cycle-time bottleneck elimination & SLA tracking |
| **`SCIENTIFIC_QUANT_RD`** | CRISP-DM · Aeronautical `SHA-256` Gates · Independent Clean-Room | Quantitative Trading, AI/ML Models, Data/Genomics Pipelines, Algorithmic R&D | `EVERY_MAJOR_MILESTONE` (immediately after EVERY backtest/run) | Isolated 1-change runs, Mock-vs-Real Schema Parity, Post-Run 3-Auditor Clean-Room Report |
| **`PATRIMONIAL_ADVISORY_STAGE_GATE`** | ExCom Dual-Circle · Stage-Gate Execution | Corporate/Tax Structuring (SASU/Holding), Personal Real Estate Purchase, Wealth & Life Transitions | `EVERY_MAJOR_MILESTONE` (pre-signing & post-filing) | Dated statutory provenance, Python zero-mental-math models, uncapped-liability redlines |

---

## 2. Universal 360° Q-C-D-R Control Tower Registers (`excom_engine.py`)

Every project can activate any subset of the 6 integrated registers inside `project-state.json` (with automatic cross-perimeter contagion):
1. **Schedule (`tasks`)**: CPM + PERT `P85`, real dependency types (`FS`, `SS`, `FF`, `SF` + `lag_days`, e.g., `"M2:SS+10"`), **Hard Target Deadline (`target_end_date`) & Negative Float (`target_margin_days`)**, and **Near-Critical Path (`<= 5d` float)**.
2. **5-Column Cost & TCO (`tasks`, `change_orders`, `recurring_opex`)**: `Initial BAC` -> `Approved Change Orders (TMA)` -> `Revised Budget` -> `Committed` -> `Actual (AC)` -> `Remaining (ETC)` -> `Forecast Landing (EAC)` -> `Variance (VAC)`, separating **Project Contingency** from **ComEx Management Reserve**, plus **Multi-Year TCO** (indexed OPEX + exit/dilapidations − landlord/grant incentives) and **Monthly Cash-Flow S-Curve**.
3. **Quantified 360° Risk Register (`risk_register`)**: Probability × Cost Impact & Delay Impact (`EMV` in currency and days) automatically tested against remaining Project Contingency.
4. **HSE / Regulatory Compliance, Testing & Punch-List Reserves (`compliance_register`)**: Requirement -> Compliance Status -> Accredited Test Required/Done -> Reserves/Snags -> Remediation Task/Cost/Delay -> Reserves Lifted -> Certificate Issued -> **Hard Go-Live Blocker (`BLOCKED_BY_COMPLIANCE` vs `READY`)**.
5. **Contractual Negotiation & Suspensive Conditions (`contracts_register`)**: Lease/BEFA/VEFA/Construction/Vendor clauses, Target vs Counterparty position, HSE-compliance linkage, Suspensive Condition deadlines (`<= 14d` auto-alert), Financial Exposure, and Redline status.
6. **Governance (`raci_matrix`, `decision_log`, `alerts`)**: RACI accountability, Decision Log, Cross-Director Contagion Radar, and 1-click **Steering Committee (`CoPil`) Brief (`export-copil`)**.

---

## 3. Market-Standard Corporate Software Interchange (Zero External Dependencies)

Every `excom_engine.py init`, `update-task`, `audit`, or register update automatically refreshes a complete zero-friction corporate export bundle under `<project-dir>/exports/`:

| File Generated | Format Standard | Corporate Tools Directly Compatible (No API / No IT Friction) |
| :--- | :--- | :--- |
| **`exports/schedule_msproject.xml`** | Microsoft Project Data Interchange (`MSPDI`) | **Microsoft Project**, **Primavera P6**, **Smartsheet**, **ProjectLibre**, **GanttProject**, **Monday.com**, **Wrike** |
| **`exports/control_tower_workbook.xlsx`** | Native **9-Sheet Live-Formula** Excel Workbook (`.xlsx`) | **Microsoft Excel**, **Google Sheets**, **LibreOffice Calc**, **Power BI**, **CFO / Finance Controllers** (`0_Inputs_Hypotheses` + live P&L/TCO/IFRS 16 + live 5-Col Budget & EMV formulas!) |
| **`deliverables/PMO_CoPil_Executive_Deck.pptx`** | Native 7-Slide 16:9 PowerPoint Deck (`.pptx`) | **Microsoft PowerPoint**, **Google Slides**, **Keynote** (ready to project in ComEx / CoPil!) |
| **`deliverables/PMO_CoPil_Executive_Report.docx`** | Native Word Executive Report (`.docx`) | **Microsoft Word**, **Google Docs**, **LibreOffice Writer** |
| **`exports/space_plan_macro_micro.dxf`** + **`.svg`** | AutoCAD R12 ASCII `.dxf` + Scaled `.svg` + Audit JSON | **AutoCAD**, **AutoCAD LT**, **Autodesk DWG TrueView**, **LibreCAD**, **QCAD**, **Revit import** (10 architectural layers: Macro Zones + Micro-Zoning Desks/Offices/Meetings/PMR 1.50m circles) |
| **`exports/milestones_calendar.ics`** | RFC 5545 iCalendar (`.ics`) | **Microsoft Outlook**, **Microsoft Teams**, **Google Calendar**, **Apple Calendar** (1-click deadline import) |
| **`exports/jira_asana_monday_import.csv`** | UTF-8-BOM Issue/Task CSV | **Jira**, **Asana**, **Monday.com**, **Linear**, **Notion**, **Trello** |
| **`exports/*.csv`** (`6` domain CSVs) | UTF-8-BOM CSV (Excel FR/US accent-safe) | **Power BI**, **Tableau**, **SAP/ERP Flat Import**, **Excel**, **Google Sheets (`gsheets`)** |
| **`deliverables/PMO_CoPil_Executive_Brief.md`** | Executive Markdown Brief | **Google Docs (`gdocs`)**, **Google Slides (`gslides`)**, **Word / PowerPoint**, **Confluence** |
| **`dashboard.html`** | Standalone Interactive HTML Cockpit | Any desktop browser (`Start-Process` / `open` / `xdg-open`) |

### Bidirectional Import (Ingesting External Updates from Architects, OPCs, Controllers)
```bash
# Re-import an updated MS Project / Smartsheet / Primavera XML schedule
python "<skill-dir>/scripts/excom_engine.py" import-msproject \
  --project-dir "<project-dir>" --file "<path>/updated_schedule.xml"

# Re-import an updated Excel FR (;) or US (,) CSV tracker
python "<skill-dir>/scripts/excom_engine.py" import-csv \
  --project-dir "<project-dir>" --file "<path>/updated_tasks.csv"
```
