# Gate 0, Dead-Ends, Physical Hooks & Aeronautical « Zero-Amnesia » Protocol (`v3.1`)

All CLI commands below use zero external dependencies (`Python 3.8+` stdlib) and render standard **US English (`en-US`)** visual chrome while keeping user-facing rationale strings in the user's language.

---

## 1. Custom Domain Registration (`root_cause_guard.py register-domain`)

For any project outside built-in software archetypes (e.g., `CORPORATE_TAX_STRUCTURING`, `REAL_ESTATE_DEAL`, `INDUSTRIAL_BOM`, `SMART_CONTRACTS`):

```bash
python "<skill-dir>/scripts/root_cause_guard.py" register-domain \
  --project-dir "<project-dir>" \
  --ledger-dir "<ledger-dir>" \
  --domain "INDUSTRIAL_HARDWARE_BOM" \
  --equation "Unit_Margin == Selling_Price - Landed_BOM - Tooling_Amortization - Customs_Logistics - Defect_Reserve" \
  --invariants "Dual-source critical components|Golden sample QA pass before mass PO|Zero uncapped supplier liability"
```

---

## 2. Gate 0 — Upfront Decision Matrix, Provenance Lock & Dead-End Anti-Loop (`porte0_carte_decideur.py`)

### A. Evaluate Options / Fixes at Gate 0
```bash
python "<skill-dir>/scripts/porte0_carte_decideur.py" evaluate \
  --input "<scratch>/gate0_input.json" \
  --ledger-dir "<ledger-dir>" \
  --auto-record-rejected \
  --json-out "<scratch>/gate0_graded.json"
```

#### Schema for `gate0_input.json` (`METIER` & `CODE` Modes)
```json
{
  "project": "ProjectName",
  "mode": "METIER",
  "domain": "CORPORATE_TAX_STRUCTURING",
  "project_invariants": [
    "100% own corporate capital (0 EUR third-party funds)",
    "100% flat EUR close 48h before fiscal year-end"
  ],
  "context": {
    "unresolved_foundational_brakes": true,
    "summary_note": "Core legal wrapper and automated accounting pipeline must be locked first.",
    "requires_financial_calc": true,
    "calc_script_path": "/abs/path/to/scratch/calc_net_compounding.py",
    "calc_output_path": "/abs/path/to/scratch/calc_out.json",
    "verified_sources": [
      {
        "ref": "CGI Art. 38-6-1",
        "url_or_file": "statute:FR-CGI-38-6-1",
        "date": "2026-01-01",
        "verbatim_excerpt": "Mark-to-market taxation of open derivative contracts at fiscal year-end"
      }
    ],
    "probe_script_path": "Required in CODE mode",
    "probe_output_path": "Required in CODE mode",
    "total_observed_gap": 100.0,
    "core_viability_at_zero_friction": 15.4,
    "measured_components": [
      {"component": "Execution turnover friction", "measured_impact": 88.0}
    ]
  },
  "proposals": [
    {
      "id": "LOT1_STATUTES",
      "hypothesis_key": "sasu_is_own_funds_cca",
      "lot": "Lot 1",
      "gate": "P1",
      "owner_seat": "CLO",
      "title": "Draft SASU IS Articles + Shareholder Loan (CCA) Convention",
      "kind": "LEGAL_STATUTORY_FOUNDATION",
      "requires_script_calc": true,
      "fact_verified": true,
      "touches_healthy_brick": false,
      "new_free_parameters_or_layers": 0,
      "post_hoc_or_wishful_tuning": false,
      "estimated_stake_pct": 30.0,
      "blocks_critical_gate": true,
      "stake_label": "0% social tax on compounding",
      "plain_sentence": "Written in the user's language: clear 1-sentence mechanism."
    }
  ]
}
```

### B. Permanently Bury a Failed Hypothesis (`ADD_02`)
Whenever an idea or patch fails empirical testing, bury it immediately so future sessions can never propose it again:
```bash
python "<skill-dir>/scripts/porte0_carte_decideur.py" record-dead-end \
  --ledger-dir "<ledger-dir>" \
  --key "luxembourg_amc_under_2m" \
  --title "Immediate Luxembourg FID + AMC wrapper under 2M EUR" \
  --reason "25k EUR/yr fixed fee drag exceeds PME corporate tax and blocks direct API access" \
  --metric "-7.1%/yr fee drag at 500k EUR"
```

---

## 3. Aeronautical Execution, Physical Hooks & Lossless Anchor (`zero_oubli_runner.py`)

### A. Initialize Lot 0 + Compile Initial `CONTEXT_ANCHOR.md`
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" init-lot0 \
  --project-dir "<project-dir>" \
  --ledger-dir "<ledger-dir>" \
  --spec "<scratch>/lot0_spec.json"
```

### B. Install Physical `PreToolUse` Firewall on New Projects (`ADD_01`)
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" install-hooks \
  --project-dir "<project-dir>" \
  --ledger-dir "<ledger-dir>"
```
- Safely skips if `<project-dir>/.agents/hooks.json` already exists (protecting bespoke project guards unless `--force` is passed).
- Physically blocks `write_file` / `edit_file` inside `<project-dir>` whenever `gate_P0_certified.json` is missing, a `sacred_file` is targeted, or an edit deletes any certified `test_*` function.

### C. Verify & Sign Gate `Pk` (`SHA-256` Blocking Gate)
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" verify-gate \
  --ledger-dir "<ledger-dir>" \
  --project-dir "<project-dir>" \
  --gate P1
```

### D. Recompile Lossless Primary-Source Anchor (`ADD_04`)
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" render-anchor \
  --ledger-dir "<ledger-dir>" \
  --pmo-dir "<optional-pmo-dir>"
```
Compiles `<ledger-dir>/CONTEXT_ANCHOR.md` directly from the raw JSON ledgers (`zero_oubli_ledger.json`, `dead_ends_registry.json`, `custom_profile.json`, `project-state.json`) — **zero recursive LLM summarization, preserving 100% atomic precision across unlimited iterations**.
