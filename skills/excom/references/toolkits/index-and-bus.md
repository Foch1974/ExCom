# ExCom v2.0 — Inter-Director Event Bus & SOTA 2026 Tooling Architecture

In **Stage 3 (360° Execution & Control)**, ExCom transitions from an advisory board into a **cross-communicating Executive Operating System**. Every Director operates on a **Shared Digital Twin** (`project-state.json` + `events-bus.jsonl`) managed by [excom_engine.py](../../scripts/excom_engine.py).

---

## 1. How Cross-Perimeter Upstream Detection Works

Projects rarely fail inside a single silo—they fail when a silent shift in **Perimeter A** (e.g., `CTO` switching an API feed, or `CPO` changing a supplier) creates a downstream collision in **Perimeter B** (`CFO` break-even, `CLO` statutory scope, `CCO-Compliance` licensing) weeks later.

ExCom prevents this via **3 synchronized mechanisms**:

1. **DAG Schedule & Budget Contagion (`update-task`)**:
   Whenever any seat updates task duration, status, or cost via `excom_engine.py update-task`, the engine recomputes **CPM Forward/Backward Pass (`ES/EF/LS/LF`, Total Float, Critical Path)** and **Earned Value (`CPI, SPI, EAC, VAC`)**, automatically raising upstream alerts in the inboxes of downstream Directors whose start dates slip, whose float erodes, or whose cost buffers shrink.
2. **Typed Cross-Director Signal Broadcast (`emit-signal`)**:
   Whenever a Director produces a deep deliverable (vendor sourcing, legal redline, infra benchmark, tax model) and uncovers a parameter change or constraint, they **must** emit a signal onto `events-bus.jsonl` (`excom_engine.py emit-signal`), automatically waking coupled seats via the **10 Canonical Contagion Laws** below.
3. **Pre-Emptive Cross-Director Audit (`CoPil 360°`)**:
   Running `excom_engine.py audit` lists `directors_to_summon_preemptively`. The CEO/PMO immediately dispatches those impacted Directors (in parallel subagents) to adapt their clauses, budgets, or specs *before* their milestone begins, closing the loop via `resolve-alert`.

---

## 2. The 10 Canonical Cross-Perimeter Contagion Laws

| Upstream Trigger (Source Perimeter) | Impacted Downstream Seats Automatically Alerted | Pre-Emptive Check Triggered Upstream |
| :--- | :--- | :--- |
| **1. Supplier / Broker / Partner Change** (`CPO`, `COO`) | `CLO`, `CISO`, `CCO-Compliance`, `CFO`, `CSO-Sustainability` | Contract jurisdiction & liability (`CLO`), SOC2/API security (`CISO`), KYC/EMIR/PRIIPs/customs (`CCO-Compliance`), FX/payment terms/TCO (`CFO`). |
| **2. Tech Stack, API or Infra Shift** (`CTO`, `CIO`, `CAIO`) | `CFO`, `CISO`, `CCO-Compliance`, `COO`, `CDO-Data` | Cloud/token/pro-data FinOps impact (`CFO`), new attack surface (`CISO`), AI Act/GDPR/HFT thresholds (`CCO-Compliance`), ops runbook (`COO`). |
| **3. Cost Overrun or Pricing Shift > 10%** (`Any Seat`) | `CFO`, `CRO-Risk`, `PMO`, `CEO` | Break-even & runway recalculation (`CFO`), contingency burn & proximity to Hard Kill Criteria (`CRO-Risk`). |
| **4. Critical-Path Slip >= 2 Days** (`Any Seat`) | `PMO`, `COO`, `CHRO`, + *All Downstream DAG Owners* | Parallel pre-work unblocking (`PMO`), calendar/bandwidth reallocation (`COO`, `CHRO`). |
| **5. Legal Wrapper or Clause Constraint** (`CLO`, `CCO-Compliance`) | `CFO`, `CPO`, `CMO`, `CCO-Commercial`, `CHRO` | Tax/social impact (`CFO`, `CHRO`), product/instrument eligibility (`CPO`), permissible marketing claims (`CMO`). |
| **6. Scope Addition / Feature Creep** (`CPO`, `CMO`, `OPTIMIST`) | `PMO`, `CTO`, `COO`, `CFO`, `CHRO` | MVP boundary defense (`PMO`), engineering debt (`CTO`), burn/margin erosion (`CFO`), founder burnout check (`CHRO`). |
| **7. Faster-Than-Planned Demand / GTM Push** (`CMO`, `CRO-Revenue`) | `COO`, `CFO`, `CCO-Customer`, `CTO`, `CHRO` | Fulfillment & SLA bottleneck check (`COO`), working-capital cash valley (`CFO`), onboarding capacity (`CCO-Customer`). |
| **8. Data Schema, Telemetry or AI Model Drift** (`CDO-Data`, `CAIO`) | `CTO`, `CFO`, `CRO-Risk`, `CCO-Compliance` | Accounting/KPI reconciliation integrity (`CFO`), model risk & kill switch (`CRO-Risk`), audit trail (`CCO-Compliance`). |
| **9. Key-Person Bandwidth / Social Status Shift** (`CHRO`) | `COO`, `PMO`, `CFO`, `CLO` | Weekly hour cap enforcement (`PMO`, `COO`), corporate governance & remuneration/PUMa rules (`CLO`, `CFO`). |
| **10. Macro, Counterparty or Regulatory Shock** (`CRO-Risk`, `DEVIL`) | `CEO`, `CFO`, `CLO`, `CSO-Strategy`, `PMO` | Stress-test re-run, collateral sweep, and option to trigger pre-committed pivot or Kill Criterion (`CEO`). |

---

## 3. CLI Quick Reference (`scripts/excom_engine.py`)

Run with `python3` (or `python` on Windows):

```bash
# 1. Initialize project Digital Twin + Gantt/EVM HTML Cockpit + CSVs
python skills/excom/scripts/excom_engine.py init --project-dir <dir> --spec <spec.json>

# 2. Update a task (auto-recomputes CPM critical path, EVM & raises contagion alerts)
python skills/excom/scripts/excom_engine.py update-task --project-dir <dir> --id M1 --actor CLO --status IN_PROGRESS --progress 60 --committed-cost 1350

# 3. Broadcast an upstream cross-director discovery signal
python skills/excom/scripts/excom_engine.py emit-signal --project-dir <dir> --from-seat CPO --severity WARNING --category VENDOR --task-id M0 --title "..." --detail "..." --action-required "..." --impacts "CFO,CLO,CCO-Compliance"

# 4. Register a specialized deliverable file produced by a Director
python skills/excom/scripts/excom_engine.py register-deliverable --project-dir <dir> --seat CLO --task-id M1 --title "Draft SASU Statutes" --path "deliverables/CLO_statuts_sasu.md" --summary "..."

# 5. Run a 360° drift & contagion audit (identifies which Directors to summon preemptively)
python skills/excom/scripts/excom_engine.py audit --project-dir <dir>

# 6. Resolve an alert once the impacted Director has updated their workstream
python skills/excom/scripts/excom_engine.py resolve-alert --project-dir <dir> --alert-id ALT-XXXXXX --by-seat CFO --resolution "..."
```

---

## 4. Stage-3 Toolkits for Tier-1 Governance & Wildcards

- **`CEO` (Executive Arbitrator)**: CoPil 360° Chairing, Cross-Director Conflict Resolution, Go/Pivot/Kill Gatekeeper.
- **`DEVIL` (Continuous Red-Team)**: Live Assumption Decay Tracker, Sunk-Cost Drift Detector (challenges teams rationalizing missed Kill Criteria), Pre-Launch Chaos Drill.
- **`OUTSIDER` (Lateral Unblocker)**: *Via Negativa* Bottleneck Bypass (when a task is `BLOCKED`, proposes how to eliminate the step entirely rather than throwing time/money at it).
- **`OPTIMIST` (Asymmetric Capture)**: Byproduct Asset Harvester (turns internal tools, compliance setups, or audited data built during execution into reusable 10x moats).

## 5. Directory of All 20 C-Suite + PMO SOTA 2026 Toolkits

Load only the module(s) needed for the active workstream:
- **[pmo-and-ops-finance.md](./pmo-and-ops-finance.md)** — `PMO`, `COO`, `CFO`
- **[tech-data-ai-cyber.md](./tech-data-ai-cyber.md)** — `CTO`, `CIO`, `CISO`, `CDO-Data`, `CAIO`, `CDO-Digital`
- **[market-revenue-product-strategy.md](./market-revenue-product-strategy.md)** — `CMO`, `CRO-Revenue`, `CCO-Commercial`, `CCO-Customer`, `CXO`, `CPO`, `CSO-Strategy`
- **[people-legal-compliance-risk-esg.md](./people-legal-compliance-risk-esg.md)** — `CHRO`, `CLO`, `CCO-Compliance`, `CRO-Risk`, `CSO-Sustainability`
