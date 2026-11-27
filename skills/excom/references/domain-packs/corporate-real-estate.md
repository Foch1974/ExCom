# Modular Domain Pack — Corporate Real Estate, Construction & Workplace Fit-Out (`MOA / Project Director 360°`)

> **Activation**: Load this modular domain pack whenever a user manages corporate real-estate search, lease/BEFA/VEFA negotiation, ground-up construction (`MOA`), industrial/logistics warehouse deployment, retail fit-out, or team relocation. All underlying tracking runs on the universal `excom_engine.py` Q-C-D-R Control Tower (`methodology = PREDICTIVE_STAGE_GATE` or `HYBRID_STAGE_GATE_AGILE` when paired with heavy IT rollout).

---

## 1. Asset-Class Regulatory Adaptation Matrix (All 4 Corporate Asset Types)

| Asset Class | Primary Building & Safety Regimes | Key Hidden Technical / Regulatory Traps |
| :--- | :--- | :--- |
| **Corporate Offices (Tertiary)** | Labor Code (*Code du travail*), `ERP` Cat. 5 (or Cat. 1–4 if auditorium/canteen), `IGH` (`> 28m` / `> 50m`), Energy Tertiary Decree (*Décret Tertiaire* `-40%` by 2030), `BACS` BMS Decree, `PMR` Accessibility, `LOM` EV Chargers | Dual-carrier fiber lead time (`3–6 mo`), mandatory `CSE/CSSCT` consultation before move, `Open Space` acoustics, badge/CCTV `CNIL` compliance, old-site dilapidation costs |
| **Logistics & Warehouses (`ICPE`)** | **`ICPE` Rubriques `1510` / `1530` / `2925`** (Declaration / Registration `5–7 mo` / Environmental Authorization `9–15 mo`), Sprinkler `APSAD R1 / NFPA`, Firewater retention basins, `ATEX` battery charging | Inheriting previous tenant's **soil pollution / unclosed ICPE cessation**, rack load slab certification, dock leveler `VGP`, fire department (`SDIS`) clearance |
| **Industrial & Manufacturing Sites** | Full `ICPE` / `SEVESO`, `ATEX`, Environmental Impact Study, `RE2020`, High-Voltage `HTA` Transformer (`Enedis` `6–12 mo`), Process utilities (compressed air, wastewater pretreatment) | Soil Phase 1 & Phase 2 contamination audit, `Enedis/GRDF` reinforcement lead time, noise boundary limits, machine foundation structural engineering |
| **Retail & Public-Facing (`ERP`)** | Strict **`ERP` Categories 1–4** (`AT ERP` permit = `4 mo` incompressible), **`CDAC`** commercial planning authorization (`> 1,000 m²`), mandatory **Safety Commission (`Commission de Sécurité`) site visit & positive PV before opening** | **Zero legal opening without signed PV Commission de Sécurité**, smoke extraction (`désenfumage`), emergency exit width, `PMR` step-free access & acoustic/signage rules |

---

## 2. Full 360° Q-C-D-R Checklist (Zero Blind Spots for Project Directors)

### Pillar 1 — QUALITY (Program, Technical Lots, Commissioning, Workplace & Change)
- **Frozen Program & Design Freezes (`APS -> APD -> PRO -> EXE`)**: Obtain formal written *Sign-Off* from internal business sponsors at each stage; route any post-freeze change through the **Change Order (`TMA`) Log** with cost + schedule impact before execution.
- **Hidden Critical Technical Lots**: Dual-operator Fiber (`CFA`), server room cooling/UPS, Wi-Fi/5G indoor survey, AV meeting rooms, access control/CCTV (`CNIL` + `CSE`), `HVAC/CVC` air renewal, lighting lux levels, acoustic attenuation (dB partitions & reverberation time), `PMR` accessibility, `IRVE` EV charging & bike storage, **5–10 yr space modularity/reversibility**.
- **Energy & ESG Compliance**: `Décret Tertiaire` (`OPERAT` baseline), `Décret BACS` (Building Management System), `RE2020`, target certifications (`HQE`, `BREEAM`, `LEED`, `OsmoZ`).
- **Industrial Handover Chain**: Load-testing **Commissioning** (HVAC, smoke extraction, `SSI` fire alarm, backup power, network throughput) -> **`OPR`** (*Opérations Préalables à la Réception*) -> **Punch-List / Reserves Tracker** backed by statutory **`5%` Retention Money** (*retenue de garantie*) -> Complete **`DOE`** (*Dossier des Ouvrages Exécutés*) & **`DIUO`** required before final payment -> Post-handover warranties (**`GPA` 1-yr, `Biennale` 2-yr, `Décennale` 10-yr**).
- **Social Dialogue, Move & Old-Site Exit**: Mandatory **`CSE / CSSCT` information-consultation** (prevents criminal obstruction / injunction halting the move!), **Move Management & Business Continuity Plan** (`Day-1` & `Hypercare J+1..J+30`), and **Old-Site Dilapidations (*Remise en état / État des lieux de sortie*)** started `6–12 mo` before lease expiry.

### Pillar 2 — COST (5-Column Budget, TCO, Cash-Flow & Accounting)
- **5-Column Financial Control**: `Initial Budget (BAC)` -> `Approved Change Orders (TMA)` -> `Revised Budget` -> `Committed (POs/Contracts)` -> `Actual Invoiced (AC)` -> `Remaining (ETC)` -> `Forecast Landing (EAC)` -> `Variance (VAC)`.
- **Reserve Separation**: **Project Contingency (`10–15%`)** managed by the Project Director vs **Management Reserve (`5%`)** locked at ComEx level; zero unapproved extra works.
- **Full `3/6/9`-Year TCO**: Headline rent + service charges + property/office taxes + multi-technical maintenance + utilities − rent-free periods & landlord TI allowances + **all soft fees** (`AMO`, `MOE`/Architect, `OPC`, Accredited Control Bureau `BC`, `CSPS`, Notary, Broker) + **double-rent overlap during works** + old-site exit/dilapidation costs.
- **Cash-Flow, Indexation & Accounting**: Monthly **Cash-Flow S-Curve** (VEFA stage calls / monthly contractor progress billing), **`ILAT / ILC / BT01` indexation exposure**, VAT recovery, component depreciation, and **`IFRS 16` balance-sheet impact** on long leases.

### Pillar 3 — SCHEDULE (Backward Planning, Hidden Lead Times & Dependencies)
- **Hard Target Deadline & Negative Float**: Lock `target_end_date` (e.g., **existing lease break notice via bailiff `6 mo` prior!**). Whenever `forecast_end_date > target_end_date`, `excom_engine.py` computes exact **Negative Float** and triggers `CRITICAL` recovery alerts (`Fast-Tracking` via `SS` overlaps or `Crashing`).
- **Incompressible Regulatory & External Lead Times**:
  - Building Permit (`PC`) / `AT ERP` (`4 mo`) + **Third-Party Appeal Purge (`2 mo`) + Administrative Withdrawal (`3 mo`)**;
  - `ICPE` Registration (`5–7 mo`) / Environmental Authorization (`9–15 mo`);
  - Utility Grid & Dual Fiber (`Enedis` / `GRDF` / Fiber = `3–9 mo`);
  - `CSE / CSSCT` Consultation (`1–2 mo`);
  - **Long-Lead Items** (chillers/HVAC, `TGBT` switchgear, elevators, glazed partitions = `12–24 weeks`);
  - Workday vs calendar-day BTP holiday buffers (August / late December) & weather days.
- **Dependency Logic & Near-Critical Path**: Model real `FS`, `SS + lag`, and `FF` overlaps; monitor **Near-Critical tasks (`<= 5d` float)** and **Contractual Suspensive Condition deadlines**.

### Pillar 4 — RISKS, CONTRACTUAL NEGOTIATION & HSE / COMPLIANCE GATE
- **Quantified Risk Register (`EMV`)**: Every risk carries `probability_pct`, `cost_impact_eur`, `delay_impact_days`, owner, and mitigation; total `EMV` is continuously benchmarked against remaining Project Contingency.
- **Lease / `BEFA` Negotiation Playbook (`contracts_register`)**:
  - **Statutory Cost Allocation (`Loi Pinel` / Art. `606` Civil Code)**: Heavy structure, roof/facade, and statutory/regulatory upgrades (asbestos, `Décret Tertiaire`, accessibility) remain strictly **Landlord responsibility**;
  - **Delivery Penalties & Walk-Away Right**: Daily liquidated damages on landlord/BEFA delay + penalty-free termination beyond `X` months;
  - **End-of-Lease Reinstatement (*Remise en état*)**: Negotiate *"normal wear and tear, excluding demolition of landlord-approved fit-outs"* (regularly saves `100–500k EUR` at exit!);
  - **Green Lease (*Bail Vert*)** & `Décret Tertiaire` capex sharing;
  - **Mandatory Pre-Signing / Suspensive HSE Conditions**: Complete **`DTA`** (Asbestos Technical File), Lead/DPE/ERP hazard diagnostics, **Phase 1 / Phase 2 Soil Pollution Audit**, **Previous Operator `ICPE` Cessation Certificate** (prevents inheriting environmental liability!), and valid periodic inspections (**`Q18`** electrical, **`Q19`** thermography, **`Q4`** extinguishers, elevators, smoke extraction).
- **Construction / `VEFA` / Contractor Contracts (`contracts_register`)**:
  - **Mandatory Pre-Start Insurances (ZERO site start without proof)**: **`Dommages-Ouvrage (DO)`** (mandatory Spinetta Law!), **`TRC`** (All-Risk Construction), **`CNR`**, and named, current **`RCD` (10-yr Decennial)** certificates for every contractor;
  - **Subcontractor Approval (`1975 Subcontracting Law`)**: Mandatory written MOA approval + payment guarantee (prevents direct financial claims against the Owner!);
  - **Site Health & Safety (`CSPS`)**: Accredited `CSPS` coordinator, `PGC`, `PPSPS`, Prevention Plan (*Plan de Prévention* on occupied sites), Hot-Work Permits (*Permis de Feu*) — direct **criminal liability** of the Project Director / Site Head;
  - **Financial Securities**: `5%` Retention Money or Bank Guarantee, `GFA` (*Garantie Financière d'Achèvement* in VEFA), capped non-liberatory delay penalties, `BIM/CAD` IP ownership.
- **Zero-Amnesia HSE / Compliance / Testing / Reserves Go-Live Gate (`compliance_register`)**:
  - Every mandatory inspection (`ICPE`, `ERP Safety Commission PV`, `Consuel`, `RICT`/`RFCT` Control Bureau report, `Q18/Q19/Q4`, `DTA`, `SSI`, `VGP` elevators/docks) is tracked end-to-end: `Status -> Accredited Test -> Open Reserves -> Linked Remediation Task (+EUR, +Days) -> Reserves Lifted -> Signed Certificate`.
  - **Hard Go-Live Lock**: `go_live_gate_status` remains **`BLOCKED_BY_COMPLIANCE`** until **`100%`** of blocking certificates are issued and critical reserves are formally lifted.
- **Stakeholder `RACI`, Decision Log & Steering Committee (`CoPil`)**: Lock `RACI` across Sponsor/ComEx, Internal Clients, CFO, CLO, IT/CIO, HR/`CSE`, Landlord, `AMO`/`MOE`/Architect, `OPC`, Control Bureau (`Apave`/`Socotec`/`Bureau Veritas`), `CSPS`, Municipality/`SDIS`, and General Contractor.

---

## 3. Ready-to-Use `spec.json` Blueprint (Corporate Real Estate / Construction Project)

Use this template as the starting spec for `excom_engine.py init --project-dir <dir> --spec <spec.json>`:

```json
{
  "project_name": "Corporate Site Relocation & Fit-Out (MOA)",
  "project_type": "corporate real estate construction fit-out",
  "methodology_id": "PREDICTIVE_STAGE_GATE",
  "currency": "EUR",
  "locked_decision": "Deliver compliant 3,000 m2 corporate facility on hard lease-expiry deadline",
  "start_date": "2026-01-05",
  "as_of_date": "2026-01-05",
  "target_end_date": "2026-12-15",
  "contingency_pct": 12.0,
  "management_reserve_pct": 5.0,
  "tco_horizon_years": 6,
  "indexation_annual_pct": 2.5,
  "exit_dilapidation_eur": 120000,
  "incentives_ti_allowance_eur": 250000,
  "recurring_opex": [
    {"name": "Annual Headline Rent + Service Charges", "seat": "CFO", "annual_eur": 780000},
    {"name": "Multi-Technical Maintenance & Utilities", "seat": "COO", "annual_eur": 110000}
  ],
  "tasks": [
    {"id": "SG0_SEARCH", "wbs": "1.1", "phase": "SG0 Feasibility", "name": "Site Search, Shortlist & TCO Mandate", "owner_seat": "COO", "depends_on": [], "optimistic_days": 20, "likely_days": 30, "pessimistic_days": 45, "planned_budget": 25000, "status": "IN_PROGRESS", "progress_pct": 50, "hard_gate": "SG0_MANDATE"},
    {"id": "SG1_LEASE_DD", "wbs": "2.1", "phase": "SG1 Negotiation & HSE DD", "name": "HSE/Soil/ICPE Audit & Lease/BEFA Negotiation", "owner_seat": "CLO", "depends_on": ["SG0_SEARCH"], "optimistic_days": 30, "likely_days": 45, "pessimistic_days": 65, "planned_budget": 45000, "status": "TODO", "progress_pct": 0, "hard_gate": "SG1_SIGNED", "coupled_seats": {"CCO-Compliance": "HSE/DTA/ICPE clearance", "CFO": "Pinel 606 & IFRS 16"}},
    {"id": "SG2_DESIGN_PERMIT", "wbs": "3.1", "phase": "SG2 Program & Permits", "name": "APS/APD Freeze, AT ERP / PC Filing & Purge", "owner_seat": "CPO", "depends_on": ["SG1_LEASE_DD:SS+15"], "optimistic_days": 90, "likely_days": 120, "pessimistic_days": 150, "planned_budget": 140000, "status": "TODO", "progress_pct": 0, "hard_gate": "SG2_PERMIT_PURGED"},
    {"id": "SG2_CSE", "wbs": "3.2", "phase": "SG2 Social Dialogue", "name": "Mandatory CSE / CSSCT Information-Consultation", "owner_seat": "CHRO", "depends_on": ["SG1_LEASE_DD"], "optimistic_days": 30, "likely_days": 45, "pessimistic_days": 60, "planned_budget": 10000, "status": "TODO", "progress_pct": 0, "hard_gate": "CSE_OPINION"},
    {"id": "SG3_TENDER_INS", "wbs": "4.1", "phase": "SG3 Procurement", "name": "DCE/ACT Contractor Award, DO/TRC/RCD & CSPS", "owner_seat": "COO", "depends_on": ["SG2_DESIGN_PERMIT:SS+60"], "optimistic_days": 30, "likely_days": 40, "pessimistic_days": 55, "planned_budget": 65000, "status": "TODO", "progress_pct": 0, "hard_gate": "SG3_INSURANCES_OK"},
    {"id": "SG4_WORKS_IT", "wbs": "5.1", "phase": "SG4 Execution", "name": "Fit-Out Works, HVAC/CVC, Dual-Fiber CFA & Security", "owner_seat": "COO", "depends_on": ["SG2_DESIGN_PERMIT", "SG3_TENDER_INS"], "optimistic_days": 75, "likely_days": 95, "pessimistic_days": 125, "planned_budget": 1200000, "status": "TODO", "progress_pct": 0, "coupled_seats": {"CIO": "Dual-fiber & AV", "CCO-Compliance": "CSPS & Control Bureau"}},
    {"id": "SG5_OPR_CERTS", "wbs": "6.1", "phase": "SG5 Commissioning & HSE", "name": "Load Commissioning, OPR, Reserves Lift & 100% Certificates", "owner_seat": "CCO-Compliance", "depends_on": ["SG4_WORKS_IT"], "optimistic_days": 15, "likely_days": 20, "pessimistic_days": 35, "planned_budget": 35000, "status": "TODO", "progress_pct": 0, "hard_gate": "SG5_GO_LIVE_CERTS"},
    {"id": "SG6_MOVE_EXIT", "wbs": "7.1", "phase": "SG6 Move & Old Site", "name": "Team Relocation, Hypercare, DOE/DIUO & Old-Site Handback", "owner_seat": "COO", "depends_on": ["SG5_OPR_CERTS", "SG2_CSE"], "optimistic_days": 10, "likely_days": 15, "pessimistic_days": 25, "planned_budget": 80000, "status": "TODO", "progress_pct": 0, "hard_gate": "SG6_OCCUPANCY"}
  ],
  "risk_register": [
    {"id": "RSK-01", "category": "HSE", "title": "Undiscovered asbestos or soil anomaly during works", "owner_seat": "CCO-Compliance", "probability_pct": 25, "cost_impact_eur": 120000, "delay_impact_days": 30, "mitigation": "Mandatory pre-signing DTA + Phase 1/2 soil audit as suspensive condition", "status": "OPEN"},
    {"id": "RSK-02", "category": "SCHEDULE", "title": "Dual-operator fiber trenching civil-works delay", "owner_seat": "CIO", "probability_pct": 40, "cost_impact_eur": 15000, "delay_impact_days": 25, "mitigation": "Order both fiber operators at SG1 + 5G enterprise failover router", "status": "OPEN"}
  ],
  "compliance_register": [
    {"id": "HSE-01", "domain": "HSE", "requirement": "Asbestos DTA & Soil Phase 1/2 Clearance", "standard": "Code sante publique / ICPE", "status": "PENDING", "test_required": true, "test_completed": false, "reserves": "", "remediation_cost_eur": 0, "remediation_delay_days": 0, "reserves_lifted": false, "certificate_issued": false, "blocking_go_live": true, "owner_seat": "CCO-Compliance"},
    {"id": "HSE-02", "domain": "FIRE_SAFETY", "requirement": "ERP Safety Commission Site Visit & Positive PV + SSI/Q18/Q4", "standard": "ERP / APSAD Q18-Q4 / Consuel", "status": "PENDING", "test_required": true, "test_completed": false, "reserves": "", "remediation_cost_eur": 0, "remediation_delay_days": 0, "reserves_lifted": false, "certificate_issued": false, "blocking_go_live": true, "owner_seat": "CCO-Compliance"}
  ],
  "contracts_register": [
    {"id": "CTR-01", "contract_type": "Commercial Lease / BEFA", "counterparty": "Landlord", "clause_topic": "Pinel Art. 606 + End-of-Lease Normal Wear + HSE Suspensive Conditions", "target_position": "100% structural/statutory capex on Landlord; no demolition of approved fit-out; full DTA/ICPE clearance prior to effective date", "counterparty_position": "Standard landlord draft", "hse_compliance_linked": true, "is_suspensive_condition": true, "deadline": "2026-03-31", "financial_exposure_eur": 350000, "status": "NEGOTIATING", "owner_seat": "CLO"}
  ],
  "raci_matrix": [
    {"id": "RACI-1", "deliverable": "Lease / Construction Contract & Suspensive Clauses", "R": "CLO", "A": "Project Director", "C": "CFO, CCO-Compliance", "I": "ComEx"},
    {"id": "RACI-2", "deliverable": "Design Freeze, Works Execution & OPR Punch-List", "R": "COO / MOE", "A": "Project Director", "C": "Internal Clients, CIO, CSPS", "I": "CFO"},
    {"id": "RACI-3", "deliverable": "100% HSE / ERP / ICPE Certificates & Go-Live Clearance", "R": "CCO-Compliance", "A": "Project Director", "C": "Control Bureau, SDIS", "I": "ComEx, CSE"}
  ],
  "guardrails": [
    {"seat": "CLO", "rule": "Zero site start without signed Dommages-Ouvrage (DO), TRC, Decennale RCD, and approved 1975 subcontractors", "status": "ACTIVE"},
    {"seat": "CCO-Compliance", "rule": "Zero team occupancy until 100% blocking HSE/ERP/ICPE certificates are issued and critical reserves lifted", "status": "ACTIVE"}
  ],
  "kill_criteria": [
    {"phase": "SG1", "owner_seat": "CLO", "trigger": "Unresolved soil/ICPE contamination liability or Landlord refusal of Art. 606/reinstatement cap", "action": "Walk away to backup site B before lease signature", "status": "ARMED"}
  ]
}
```

---

## 4. Parametric AutoCAD Macro & Micro-Zoning Space Planning (`.dxf` + `.svg` + Audit)

Use `excom_engine.py generate-space-plan` for **MOA feasibility test-fits, landlord challenges, and internal client space workshops**:
- **Macro-Zoning**: partitions floorplates into department zones (`OPEN_SPACE`, `PRIVATE_OFFICES`, `MEETING_HUB`, `RECEPTION`, `BREAKOUT`, `SERVER_CFA`) around an ERP-compliant egress corridor (`>= 1.40m` / `2 UP`).
- **Micro-Zoning**: lays out exact metric benching desk islands (`1.60m × 0.80m`) + chairs + `1.60m` clearances, enclosed executive offices with `90°` door swings, conference rooms + tables + chairs, `1.30m` acoustic phone booths, server racks, and `Ø 1.50m` PMR wheelchair turning circles across **10 standard AutoCAD layers**.
- **Honest MOA Boundary**: Ideal for feasibility test-fits, capacity checks (`AFNOR NF X 35-102 >= 10 m²/workstation`), and pre-architect briefs; execution construction drawings (`EXE` / `BIM Revit` / MEP clash detection / permit stamps) remain the legal scope of the licensed Architect & MOE.
- **External Architect Audit**: Run `excom_engine.py audit-dxf --file <architect.dxf>` to verify bounding boxes, layer entity counts, and closed-polygon `m²` areas directly from external ASCII `.dxf` exports.
