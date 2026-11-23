# Porte 0 & Aeronautical « Zéro-Oubli » Protocol (`v3.0`)

This reference documents the exact JSON schemas and CLI invocations for the 3 engineering & governance scripts that enforce **zero-complacency upfront triage (`Porte 0`)** and **100% validated lot-by-lot execution (`Lot 0` → `Portes P1..PK`)**.

---

## 1. Custom Domain Registration (Projects Outside Built-In Profiles)

When scanning a project whose domain is outside `QUANT_TRADING`, `DATA_OR_ML_PIPELINE`, or `WEB_OR_SAAS_APP` (e.g., `REAL_ESTATE_ACQUISITION`, `CORPORATE_TAX_SASU`, `INDUSTRIAL_HARDWARE`, `SMART_CONTRACTS`), lock its custom conservation equation and foundational invariants into the external ledger:

```bash
python "<skill-dir>/scripts/root_cause_guard.py" register-domain \
  --project-dir "<project-dir>" \
  --domain "INDUSTRIAL_HARDWARE_BOM" \
  --equation "Unit_Margin == Selling_Price - Landed_BOM - Tooling_Amortization - Customs_Logistics - Warranty_Defect_Rate" \
  --invariants "Dual-source qualification on every critical component|Golden sample physical QA pass before mass PO|Zero uncapped supplier liability"
```

Subsequent `root_cause_guard.py scan --project-dir "<project-dir>"` calls automatically enforce this custom profile and track file/document `SHA-256` drift.

---

## 2. Porte 0 — Universal Entry Decision Matrix (`porte0_carte_decideur.py`)

Run **before** asking for a `"Go"` on any strategic option list or fix batch:

```bash
python "<skill-dir>/scripts/porte0_carte_decideur.py" \
  --input "<scratch>/porte0_input.json" \
  --json-out "<scratch>/porte0_graded.json"
```

### Schema for `porte0_input.json`

```json
{
  "project": "ProjectName",
  "mode": "CODE",
  "domain": "QUANT_TRADING",
  "project_invariants": [
    "Zero magic literals (TOTAL MAGIC == 0)",
    "Parity between research simulator and live/cloud execution"
  ],
  "context": {
    "unresolved_foundational_brakes": true,
    "summary_note": "86.5% of net shortfall traced to excess spread turnover and rejected odd-lot orders.",
    "probe_script_path": "/abs/path/to/scratch/probe_attribution.py",
    "probe_output_path": "/abs/path/to/scratch/probe_out.json",
    "total_observed_gap": 100.0,
    "core_viability_at_zero_friction": 15.4,
    "measured_components": [
      {"component": "Spread/commission turnover", "measured_impact": 62.0},
      {"component": "Odd-lot order rejections", "measured_impact": 24.5}
    ],
    "verified_facts_or_sources": [
      "Required in METIER mode instead of probe_script_path (e.g. CGI Art. 38-6-1, IBKR Pro fee schedule)"
    ]
  },
  "proposals": [
    {
      "id": "FIX_01",
      "lot": "Lot 1",
      "gate": "P1",
      "owner_seat": "CTO",
      "title": "Enforce minimum economic ticket & hysteresis band",
      "kind": "EXECUTION_FRICTION",
      "fact_verified": true,
      "touches_healthy_brick": false,
      "new_free_parameters_or_layers": 0,
      "post_hoc_or_wishful_tuning": false,
      "estimated_stake_pct": 18.5,
      "blocks_critical_gate": true,
      "stake_label": "+62% gap recovery",
      "plain_sentence": "Eliminates micro-rebalancing trades whose broker fee exceeds expected alpha."
    }
  ]
}
```

> **Foundational `kind` values** (allowed while `unresolved_foundational_brakes == true`):
> - `CODE`: `PLUMBING_RUNTIME`, `ACCOUNTING_DOUBLE_CHARGE`, `EXECUTION_FRICTION`, `UNIVERSE_WIRING`, `DEAD_CODE_PURGE`, `ABLATION_SIMPLIFICATION`, `TEST_TWIN_PARITY`, `SECURITY_HARDENING`, `DATA_SCHEMA_FIX`.
> - `METIER`: `LEGAL_STATUTORY_FOUNDATION`, `TAX_CASH_FOUNDATION`, `CORE_VENDOR_QUALIFICATION`, `OPERATIONAL_BOTTLENECK`, `RISK_CONTINGENCY_SHIELD`, `COMPLIANCE_MANDATORY`, `MVP_CORE_SCOPE`.
> - Any secondary/premature `kind` (`SIGNAL_FORMULA`, `EXOTIC_WRAPPER`, `PREMATURE_SCALING`, `COSMETIC_OPTIMIZATION`) is automatically marked **`❌ SURENCHÈRE / BLOQUÉ`** until foundational brakes are cleared.

---

## 3. Aeronautical « Zéro-Oubli » Execution (`zero_oubli_runner.py`)

Once the User approves specific items from `Porte 0`:

### A. Initialize `Lot 0` & Certify `Porte P0`
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" init-lot0 \
  --project-dir "<project-dir>" \
  --ledger-dir "<external-or-project-ledger-dir>" \
  --spec "<scratch>/lot0_spec.json"
```

#### Schema for `lot0_spec.json`
```json
{
  "project_name": "MyProject",
  "mode": "CODE",
  "domain": "QUANT_TRADING",
  "project_invariants": ["Zero magic numbers", "100% cumulative test pass"],
  "test_command": "python -m unittest discover -s tests -p \"test_*.py\"",
  "sacred_files": ["reference_data.py"],
  "tracked_files": ["engine.py", "execution.py", "tests/test_suite.py"],
  "items": [
    {
      "id": "FIX_01",
      "title": "Enforce broker minimum ticket filter",
      "lot": "Lot 1",
      "gate": "P1",
      "owner_seat": "CTO",
      "mode": "CODE",
      "target_files": ["execution.py"],
      "test_file": "tests/test_suite.py",
      "test_id": "test_fix01_min_ticket_filter",
      "production_symbol": "apply_min_ticket_filter"
    },
    {
      "id": "DOC_01",
      "title": "Draft SASU Articles of Association with 100% own-funds lock",
      "lot": "Lot 2",
      "gate": "P2",
      "owner_seat": "CLO",
      "mode": "METIER",
      "deliverable_path": "deliverables/CLO_statuts_sasu.md",
      "min_bytes": 800,
      "required_markers": ["compte propre", "capitaux propres", "président", "sans rémunération"]
    }
  ]
}
```
*(Note: A single hybrid project can mix `mode: "CODE"` items and `mode: "METIER"` items across its Lots!)*

### B. Verify & Sign Gate `Pk` (`SHA-256` Blocking Gate)
After completing all items in `Lot k` (`Gate Pk`):
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" verify-gate \
  --ledger-dir "<ledger-dir>" \
  --project-dir "<project-dir>" \
  --gate P1
```
- Blocks with exit code `2` if `P_{k-1}` is uncertified, if any sacred file changed, if any `CODE` test lacks real `assert`s or fails to call `production_symbol` (*Zéro Faux Jumeau*), if any prior test was deleted (*Suite Indélébile*), if `test_command` fails, or if any `METIER` deliverable is missing mandatory clauses.
- On `100% PASS`, signs `gate_P1_certified.json` bound to `tree_sha256`.

### C. Live Integrity Check (`status`)
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" status \
  --ledger-dir "<ledger-dir>" \
  --project-dir "<project-dir>"
```
Automatically flags `STALE_SHA256_REVERIFY_REQUIRED` if any tracked file was edited after certification.
