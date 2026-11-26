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
- **1-Click Steering Committee (`CoPil`) Brief**: `excom_engine.py export-copil --project-dir <dir>`

---

## Step 3 — Live Interactive & Corporate Surface Delivery

Never leave deliverables behind dead `file:///.../*.html` chat links:
1. **Local Multi-View Cockpit**: Launch `dashboard.html` directly in the OS default browser (`Start-Process "<path>/dashboard.html"` on Windows, `open` on macOS, `xdg-open` on Linux).
2. **Market-Standard Corporate Exports (`exports/`)**: Hand off `control_tower_workbook.xlsx` (`7` Excel sheets), `schedule_msproject.xml` (MS Project / Primavera / Smartsheet / Monday), `milestones_calendar.ics` (Outlook / Google Calendar), and `jira_asana_monday_import.csv` directly to finance, legal, contractors, and internal teams.
3. **Google Workspace Sync (`gsheets` / `gdocs` / `gslides`, when connected)**: Mirror `exports/` tables into Google Sheets and sync `deliverables/PMO_CoPil_Executive_Brief.md` into Google Docs/Slides with direct clickable `https://docs.google.com/...` links.
