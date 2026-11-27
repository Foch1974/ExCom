# Tier 3 Enterprise PMO Playbook — 360° Q-C-D-R Control Tower & Interchange (`ExCom v3.3`)

The **Project Management Officer (`PMO`)** operates continuously from **Lot 0** through **Handover / Go-Live** to govern **Quality, Cost, Schedule, Risks, HSE/Compliance, and Contracts** without blind spots.

## Core Philosophy of the ExCom v3.3 Enterprise PMO

1. **Right Methodology From Day 1**: Run `excom_engine.py select-methodology` first to lock the exact WBS phases, Stage-Gates, Clean-Room cadence, and modular domain pack (e.g., [domain-packs/corporate-real-estate.md](./domain-packs/corporate-real-estate.md)).
2. **Executable 360° Control Tower (Never Static Prose Alone)**: Maintain a live Digital Twin via [scripts/excom_engine.py](../scripts/excom_engine.py) (`project-state.json`, `events-bus.jsonl`, `dashboard.html`, MS Project `.xml`, 7-Tab Excel `.xlsx`, Outlook `.ics`, UTF-8-BOM CSVs, and 1-click `CoPil` Brief).
3. **Separation of Powers at Every Stage-Gate**: At every major empirical run or Stage-Gate, an isolated 3-Agent Clean-Room Board ([clean-room-audit.md](./clean-room-audit.md)) audits 100% of raw deliverables and writes the executive report directly for the Project Director.

---

## Step 1 — Select Methodology & Initialize the 360° Control Tower

```bash
# 1. Select optimal methodology & domain pack
python "<skill-root>/scripts/excom_engine.py" select-methodology \
  --description "<project description>" --regulatory HIGH --capital HIGH

# 2. Initialize 360° Q-C-D-R Control Tower + auto-generate all corporate exports
python "<skill-root>/scripts/excom_engine.py" init \
  --project-dir "<project-dir>" --spec "<spec.json>"
```

Core `spec.json` sections supported natively:
- **Schedule & Hard Target**: `start_date`, `target_end_date` (computes Negative Float!), `tasks` with `depends_on` supporting `FS`, `SS+lag`, `FF`, `SF` (`"M1:SS+15"`), PERT 3-point durations, `hard_gate`, `coupled_seats`.
- **5-Column Cost & TCO**: `contingency_pct` (`10–15%`), `management_reserve_pct` (`5%`), `tco_horizon_years`, `indexation_annual_pct`, `exit_dilapidation_eur`, `incentives_ti_allowance_eur`, `recurring_opex`, and `change_orders` (`TMA`).
- **360° Enterprise Registers**: `risk_register` (`EMV` Cost + Delay), `compliance_register` (HSE/ERP/ICPE tests, punch-list reserves, remediation cost/delay, **blocking Go-Live certificates**), `contracts_register` (redlines, HSE clauses, **suspensive conditions** & deadlines), `raci_matrix`, `decision_log`, `guardrails`, `kill_criteria`.

---

## Step 2 — Day-to-Day Steering, Registers & Bidirectional Market Interchange

- **Log a Change Order (`TMA`)**: `excom_engine.py add-change-order --project-dir <dir> --title "..." --task-id <tid> --cost-impact 25000 --delay-impact 5 --status APPROVED`
- **Update Quantified Risk (`EMV`)**: `excom_engine.py upsert-risk --project-dir <dir> --id RSK-01 --category HSE --title "..." --probability 30 --cost-impact 100000 --delay-impact 20`
- **Track HSE / Compliance / Reserves (`Go-Live Gate`)**: `excom_engine.py upsert-compliance --project-dir <dir> --id HSE-02 --requirement "ERP Safety Commission PV" --standard "ERP" --status WITH_RESERVES --test-completed --reserves "Smoke damper B2" --remediation-cost 18000 --remediation-delay 10`
- **Track Contract Redlines & Suspensive Clauses**: `excom_engine.py upsert-contract --project-dir <dir> --id CTR-01 --contract-type "Commercial Lease" --counterparty "Landlord" --clause-topic "Art. 606 & DTA" --hse-linked --suspensive --deadline 2026-03-31 --exposure 350000 --status NEGOTIATING`
- **Import External Updates**: `excom_engine.py import-msproject --project-dir <dir> --file updated.xml` or `import-csv --project-dir <dir> --file tracker.csv`
- **1-Click Steering Committee (`CoPil`) Pack (`.pptx` + `.docx` + `.md`)**: `excom_engine.py export-copil --project-dir <dir>`
- **AutoCAD Macro & Micro-Zoning Space Plan (`.dxf` + `.svg` + Audit JSON)**: `excom_engine.py generate-space-plan --project-dir <dir> --spec <space_spec.json>`
- **Audit External Architect `.dxf` Floorplans**: `excom_engine.py audit-dxf --file <architect_floorplan.dxf>`

---

## Step 3 — Live Interactive, Locked-Down IT & Corporate Surface Delivery

Never leave deliverables behind dead `file:///.../*.html` chat links:
1. **Locked-Down Corporate IT Protocol (*Zero Data Exfiltration*)**:
   - **Preferred (Inside the Fence)**: Run ExCom's zero-dependency Python stdlib scripts offline on the corporate workstation once approved by IT/CISO (zero external `pip` packages, zero telemetry).
   - **Anonymized Parametric Twin**: When authoring templates externally, NEVER enter real company names, addresses, landlords, employee names, or confidential quotes; use coded aliases (`Site_A`, `Landlord_X`) and the editable **`0_Inputs_Hypotheses`** Excel tab so real figures are entered strictly inside the corporate network and all live formulas recalculate automatically.
2. **Local Multi-View Cockpit**: Launch `dashboard.html` directly in the OS default browser (`Start-Process "<path>/dashboard.html"` on Windows, `open` on macOS, `xdg-open` on Linux).
3. **Market-Standard Corporate Exports (`exports/` & `deliverables/`)**: Hand off **`control_tower_workbook.xlsx`** (`9` live-formula Excel sheets incl. P&L/TCO/IFRS 16), **`PMO_CoPil_Executive_Deck.pptx`** (`7`-slide PowerPoint), **`PMO_CoPil_Executive_Report.docx`** (Word), **`schedule_msproject.xml`** (MS Project / Primavera / Smartsheet), **`milestones_calendar.ics`** (Outlook), **`space_plan_macro_micro.dxf`** + **`.svg`** (AutoCAD / DWG TrueView), and **`jira_asana_monday_import.csv`**.
4. **Google Workspace Sync (`gsheets` / `gdocs` / `gslides`, when connected)**: Mirror `exports/` tables into Google Sheets and sync CoPil briefs into Google Docs/Slides with direct clickable `https://docs.google.com/...` links.
