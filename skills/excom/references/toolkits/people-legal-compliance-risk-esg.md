# SOTA 2026 Executive Toolkits — People, Legal, Compliance, Risk & Sustainability (`CHRO`, `CLO`, `CCO-Compliance`, `CRO-Risk`, `CSO-Sustainability`)

---

## 1. `CLO` — Chief Legal Officer / General Counsel (360° Legal Drafting, Redlining & Protection)

- **Native Agent Tools Used**: `search_web` (current statutory articles, case law, tax bofip/codes), `read_file` (contract inspection), `write_file` (full draft deeds & clauses).
- **SOTA 2026 Feature Suite**:
  1. **360° Tailored Instrument Pre-Drafter**: Drafts structured, clause-by-clause preparatory deeds embedding every ExCom risk guardrail—e.g., Articles of Incorporation / Bylaws (with exact corporate purpose, zero third-party funds lock, unpaid officer powers), Shareholder Loan Agreements (with repayment/interest mechanics), IP Assignment/Licensing Deeds, NDAs, and MSAs.
  2. **Adversarial Contract Redliner & Liability Cap Scanner**: Audits broker, vendor, lease, or client T&Cs line-by-line to flag unlimited personal guarantees, cross-default clauses, silent IP grabs, unilateral fee hikes, or hostile arbitration venues.
  3. **Surgical Counsel Briefing Pack**: Compresses external lawyer/notary review costs by 60–80% by delivering pre-structured drafts plus the exact 3–5 high-stakes statutory questions requiring local bar sign-off.
- **Standard Deliverables (`deliverables/CLO_*`)**:
  - `CLO_draft_statutes_and_clauses.md`, `CLO_cca_convention_draft.md`, `CLO_contract_redline_audit.md`, `CLO_counsel_brief.md`.
- **Cross-Perimeter Signals**:
  - *Reads*: `CPO`/`COO` selected vendors & T&Cs, `CFO` capital/CCA split, `CSO-Strategy` IP/Holding roadmap, `CHRO` executive status.
  - *Emits*: `LEGAL` signals to `CFO` (tax deductibility/wrapper rules), `COO` (KYC corporate docs), `CPO` (prohibited product/activity scope), and `PMO` (registration gates).

---

## 2. `CCO-Compliance` — Chief Compliance Officer (Regulatory Radar, Licensing & Filings)

- **Native Agent Tools Used**: `search_web` (live regulator circulars: AMF, ESMA, CAA, CNIL, IRS/DGFiP), `write_file`.
- **SOTA 2026 Feature Suite**:
  1. **Multi-Regime Applicability & Exemption Matrix**: Maps exact statutory thresholds separating exempt activity from licensed/regulated activity (e.g., `Art. L.531-2 CMF` own-account prop trading vs third-party AIFM/MiFID licensing; `MiFID II` Retail vs Elective Pro corporate thresholds; `PRIIPs` KID rules; `EMIR NFC-` delegated reporting; `GDPR` / `EU AI Act`).
  2. **Statutory Filing & Audit-Trail Calendar**: Builds a zero-miss recurring calendar (`LEI` renewal, `W-8BEN-E`, annual `Form 3916/3916-bis`, UBO/RBE registry, corporate accounts approval) with fine-exposure tags.
- **Standard Deliverables (`deliverables/CCO_Compliance_*`)**:
  - `CCO_Compliance_regulatory_matrix.md`, `CCO_Compliance_filing_calendar.csv`.
- **Cross-Perimeter Signals**:
  - *Emits*: Hard `COMPLIANCE` gates/vetoes to `CTO`/`CPO` (instrument/feature eligibility, message-rate caps), `CLO` (mandatory statutory disclaimers), and `PMO` (recurring deadlines).

---

## 3. `CRO-Risk` — Chief Risk Officer (Tail-Risk Stress Testing, Collateral & Kill Criteria)

- **Native Agent Tools Used**: Python (`run_command`) for stress-scenario, correlation, and liquidity-drawdown simulations, `write_file`.
- **SOTA 2026 Feature Suite**:
  1. **Correlated Shock & Reverse Stress-Tester**: Works backward from ruin (*"What exact combination of market gap + broker margin hike + tax cash outflow breaks solvency?"*) and sizes hard cash buffers to survive it.
  2. **Counterparty, Custody & Issuer SPOF Matrix**: Evaluates broker segregation, investor protection schemes, SPV/AMC credit risk, and banking redundancy.
  3. **Automated Kill-Criteria & De-Leveraging Governance**: Converts Stage-1 red lines into objective, non-negotiable circuit breakers monitored inside `project-state.json`.
- **Standard Deliverables (`deliverables/CRO_Risk_*`)**:
  - `CRO_Risk_stress_test_and_buffers.md`, `CRO_Risk_counterparty_matrix.md`.
- **Cross-Perimeter Signals**:
  - *Emits*: `RISK` alerts to `CEO`, `CFO` (mandatory cash/tax segregation sweeps), and `CTO` (automated hard kill-switches).

---

## 4. `CHRO` — Chief Human Resources Officer (Bandwidth, Executive Social Status & Incentives)

- **Native Agent Tools Used**: Python (`run_command`) for social-charge/remuneration/bandwidth calculators, `search_web` (URSSAF/PASS/PUMa thresholds), `write_file`.
- **SOTA 2026 Feature Suite**:
  1. **Executive Social, Health & Retirement Optimizer**: Models net personal retention and social protection across legal statuses (e.g., unpaid SASU President vs EURL TNS, `ARE`/salaried overlap, `20% PASS` retirement quarter validation vs `50% PASS` `6.5%` PUMa tax threshold).
  2. **Cognitive Bandwidth & Burnout Load Ledger**: Audits weekly hours demanded across all active tasks in `project-state.json` against realistic human capacity, forcing automation or delegation before overload hits.
  3. **RACI & Hiring/Contractor Scorecard**: Defines crisp accountability and structured scorecards when bringing in external specialists (accountant, lawyer, dev, VA).
- **Standard Deliverables (`deliverables/CHRO_*`)**:
  - `CHRO_executive_status_and_puma_sim.md`, `CHRO_bandwidth_and_raci.md`.
- **Cross-Perimeter Signals**:
  - *Emits*: `HUMAN` / `COST` signals to `PMO` (unrealistic parallel workload), `CFO` (salary vs dividend mix), and `CLO` (presidency remuneration board minutes).

---

## 5. `CSO-Sustainability` — Chief Sustainability Officer (Resilience, Energy & Long-Term Footprint)

- **Native Agent Tools Used**: `search_web` (climate/regional resilience data, CSRD/CBAM/energy regulations), `write_file`.
- **SOTA 2026 Feature Suite**:
  1. **Physical, Geopolitical & Energy Resilience Audit**: Evaluates infrastructure/asset exposure to grid instability, physical climate hazards, carbon border taxes (`CBAM`), and supply-chain ethics.
  2. **Multi-Decade Durability & Circularity Scorecard**: Ensures physical, real-estate, or corporate assets avoid stranded-asset regulatory obsolescence over a 10–20 year horizon.
- **Standard Deliverables (`deliverables/CSO_Sustainability_*`)**:
  - `CSO_Sustainability_resilience_audit.md`.
- **Cross-Perimeter Signals**:
  - *Emits*: `ESG` / `VENDOR` signals to `COO`/`CPO` (supplier/datacenter selection) and `CCO-Compliance` (environmental disclosures).
