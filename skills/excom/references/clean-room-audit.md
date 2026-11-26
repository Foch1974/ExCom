# Systematic Multi-Agent Clean-Room Review Board Playbook (`ExCom v3.3`)

## The Core Law: Separation of Powers (*The Builder Never Grades Their Own Homework*)

Iterative builder/PMO sessions inevitably develop **sunk-cost tunnel vision**: the agent that just implemented a lot or ran a project phase is anchored to defending its own prior choices, summaries, and local deltas.

`ExCom v3.3` solves this across **ALL** project types (Quant/ML/Software AND Corporate Real Estate/Construction/M&A/Business) via **Systematic Post-Milestone Clean-Room Governance**:
- **Default Policy (`EVERY_MAJOR_MILESTONE`, threshold = `1`)**: Immediately upon completion of **every major empirical run** (e.g., QuantConnect Cloud backtest, ML training run, release candidate) **OR every project Stage-Gate milestone** (e.g., Pre-Signing Lease/Purchase DD, Design/Permit Freeze, Tender Award, Pre-Handover OPR/Commissioning), `zero_oubli_runner.py record-kpi` automatically requires an **Isolated 3-Agent Clean-Room Review Board**.
- **Direct Executive Reporting**: The **Post-Run / Post-Stage-Gate Executive Report presented to the Decision-Maker MUST come directly from the Clean-Room Board** — NOT from the builder/PMO who executed the phase.
- **No Friction on Micro-Tasks**: Day-to-day micro-edits, task updates, and document drafts proceed at full speed without spawning a Clean-Room. Lightweight continuous-ops workflows (`LEAN_KANBAN_TOC`) may opt into `--clean-room-policy PLATEAU_2`.
- **Hard Physical Lock**: Until the Clean-Room Board certifies `zero_oubli_runner.py record-clean-room` (`100%` coverage + disk probe), both `porte0_carte_decideur.py evaluate` and the `PreToolUse` firewall physically block the next Lot.

---

## Multi-Agent Clean-Room Board Composition (3 Isolated Zero-History Subagents in Parallel)

Spawn **3 isolated subagents concurrently** (`invoke_subagent` / `run_workflow` / `Task`) with **ZERO prior conversation history**. Never leak the main thread's excuses or pet theories into their prompts.

### A. For `MODE = "CODE"` (Quant Trading, AI/ML, Software, Data Pipelines)
1. **Seat 1 — Forensic Code & Plumbing Auditor (`code_plumbing_forensics_auditor`)**:
   - Reads **`100%` of tracked production source files** line-by-line (never summaries alone).
   - Runs `root_cause_guard.py scan` and `root_cause_guard.py schema-parity` to expose silent parameter discards (`_ = param`), one-shot frozen-state latches, hardcoded exclusions, stacked clamps, and test-mock vs real-data schema drift.
   - Verifies every mechanical friction, execution channel, and accounting reconciliation (`100%` mass balance).
2. **Seat 2 — Structural Ceiling & Statistical Auditor (`math_ceiling_stats_auditor`)**:
   - Writes and executes a deterministic Python probe script on disk measuring the **end-to-end funnel** (`Raw Universe -> Effective Dimensionality / Collinearity -> Zero-Friction Theoretical Ceiling vs North-Star Target -> Attenuation Stack -> Net Output`) plus downside / Monte-Carlo stress tests.
   - Classifies the Foundation State (`DEAD_FOUNDATION`, `SUB_SCALE_FOUNDATION`, or `VIABLE_FOUNDATION`) with zero sugarcoating.
3. **Seat 3 — Adversarial Devil & Test-Twin Auditor (`devil_twins_dogma_auditor`)**:
   - Audits local test suites/harnesses for **complacent synthetic mocks** or Goodhart thresholds that diverge from real production data and secretly break production.
   - Cross-checks `CONTEXT_ANCHOR.md` invariants, prior Gate 0 claims (`file:line` reality!), and `dead_ends_registry.json` to flag stale equations or confounded multi-change dead-ends needing reopening.

### B. For `MODE = "METIER"` (Corporate Real Estate, Construction, Industrial, Legal/M&A, Business)
1. **Seat 1 — Independent Technical, Quality & HSE Auditor (`technical_quality_hse_auditor`)**:
   - Audits `100%` of active technical plans, program freezes, regulatory specs (`ERP`/`IGH`/`ICPE`/`Décret Tertiaire`/`BACS`/`CSPS`/`CSE`), test reports, open punch-list reserves, and compliance certificates.
2. **Seat 2 — Independent Finance, TCO & Contractual Auditor (`finance_tco_contracts_auditor`)**:
   - Audits the 5-column budget (`BAC -> TMA -> Revised -> Committed -> AC -> ETC -> EAC`), contingency vs management reserve, multi-year TCO (`IFRS 16`, indexation, dilapidations), insurances (`DO`/`TRC`/`RCD`), and lease/construction redlines + suspensive clauses using deterministic Python verification scripts.
3. **Seat 3 — Adversarial Schedule, Risk & Compliance Devil (`devil_schedule_compliance_auditor`)**:
   - Stress-tests the **Hard Target Deadline** (`Negative Float`), hidden external regulatory lead times (`PC`/`AT ERP` purge, `ICPE`, dual-fiber, `Long-Lead Items`), quantified Risk `EMV` coverage against remaining contingency, and Go-Live blocking compliance gaps.

---

## Standard Zero-History Subagent Prompt Contract

```text
ROLE: Isolated Clean-Room Board Member — [SEAT_NAME] (Zero Prior Chat History, Zero Complacency).
MODE: STRICTLY READ-ONLY — Do NOT modify any project file.

INPUTS PROVIDED ONLY:
- Project directory path & raw artifacts/deliverables (NO chat summaries or builder opinions).
- North-Star Target (`metric_name`, `target`, `champion` vs `latest`, `hard_target_deadline` if applicable).

MANDATE:
1. Read 100% of your perimeter's primary source files/contracts/data line-by-line.
2. Run deterministic verification scripts on disk (zero mental math, zero verbal guessing).
3. Separate Level-A (hidden execution/contractual/HSE defects) from Level-B (structural ceiling gaps
   preventing the project from hitting its North-Star Target or Hard Deadline).
4. List exact file:line or clause citations, quantified financial/schedule impacts, and any
   non-negotiable VETO before the next phase/run may begin.
```

---

## Certifying the Multi-Agent Clean-Room Board & Delivering the Report

Synthesize the 3 isolated memos into the **Independent Clean-Room Executive Report** (written directly for the User in the user's language, explicitly preserving any dissenting vetoes), then register the certification on disk:

```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" record-clean-room \
  --ledger-dir "<ledger-dir>" \
  --project-dir "<project-dir>" \
  --auditor-id "clean-room-board-run-04" \
  --panel-auditors "code_plumbing:sub-1,math_ceiling:sub-2,devil_twins:sub-3" \
  --files-read "<scratch>/clean_room_files_read.json" \
  --probe-script "<scratch>/clean_room_probe.py" \
  --probe-output "<scratch>/clean_room_probe_results.json" \
  --report-path "<deliverables>/CleanRoom_Board_Report_Run04.md" \
  --dissenting-vetoes "VETO on 3x leverage while core ceiling 0.62 < 2.0 target" \
  --theoretical-ceiling 0.62 \
  --findings-summary "3-agent Clean-Room Board completed 100% audit after Run 04" \
  --isolated-zero-history
```

`zero_oubli_runner.py` mechanically blocks certification (`exit 2`) if `--isolated-zero-history` is omitted, any listed file does not exist, production file coverage is `< 100%`, or the disk probe output is missing/empty.
