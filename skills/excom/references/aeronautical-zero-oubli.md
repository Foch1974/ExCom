# Gate 0, Evidence Bindings, Post-Milestone Clean-Room Board, Physical Hooks & Aeronautical « Zero-Amnesia » Protocol (`v3.3`)

All CLI commands below use zero external dependencies (`Python 3.8+` stdlib) and render standard **US English (`en-US`)** visual chrome while keeping user-facing rationale strings in the user's language.

---

## 1. Structural Scan, Mock-vs-Real Schema Parity & Domain Registration (`root_cause_guard.py`)

### A. Read-Only AST & Blind-Spot Scan
```bash
python "<skill-dir>/scripts/root_cause_guard.py" scan \
  --project-dir "<project-dir>" \
  --ledger-dir "<ledger-dir>"
```
Surfaces both patchwork metrics (`boolean_hotspots`, denoised `entity_exceptions`, `hardcoded_exclusions`, `magic_literals`, `fixed_caps`) and **`v3.2` structural blind spots**:
- `silent_discards`: `_ = param` dropping live function inputs;
- `frozen_state_latches`: one-shot zero/empty cache latches mutated only inside zero/empty guards;
- `mock_schema_drift`: structured test-mock keys absent from real data JSON files;
- `stacked_clamps_advisory`: functions with `>= 8` stacked `min`/`max`/`clip` attenuation clamps.

### B. Dedicated Test-Mock vs Real-Data Schema Parity Audit
```bash
python "<skill-dir>/scripts/root_cause_guard.py" schema-parity \
  --project-dir "<project-dir>"
```

### C. Custom Domain Registration (with Run-ID Freshness Tracking)
```bash
python "<skill-dir>/scripts/root_cause_guard.py" register-domain \
  --project-dir "<project-dir>" \
  --ledger-dir "<ledger-dir>" \
  --domain "INDUSTRIAL_HARDWARE_BOM" \
  --verified-at-run-id "RUN_01" \
  --equation "Unit_Margin == Selling_Price - Landed_BOM - Tooling_Amortization - Customs_Logistics - Defect_Reserve" \
  --invariants "Dual-source critical components|Golden sample QA pass before mass PO|Zero uncapped supplier liability"
```

---

## 2. Gate 0 — Anti-Self-Certification Matrix, 3-State Ceiling & Falsifiable Dead-Ends (`porte0_carte_decideur.py`)

### A. Evaluate Options / Fixes at Gate 0 (with Programmatic Disk Binding Verification)
```bash
python "<skill-dir>/scripts/porte0_carte_decideur.py" evaluate \
  --input "<scratch>/gate0_input.json" \
  --ledger-dir "<ledger-dir>" \
  --strict-bindings \
  --auto-record-rejected \
  --json-out "<scratch>/gate0_graded.json"
```

#### Schema for `gate0_input.json` (`v3.2` — `CODE` & `METIER` Modes)
```json
{
  "project": "ProjectName",
  "mode": "CODE",
  "domain": "QUANT_TRADING",
  "project_invariants": [
    "Zero leverage while foundation is SUB-SCALE",
    "100% disk-verified evidence bindings"
  ],
  "context": {
    "project_dir": "/abs/path/to/project",
    "strict_bindings": true,
    "unresolved_foundational_brakes": true,
    "summary_note": "Fix mechanical brakes first; core ceiling is also below North-Star target.",
    "probe_script_path": "/abs/path/to/scratch/forensic_probe.py",
    "probe_output_path": "/abs/path/to/scratch/forensic_probe_out.json",
    "total_observed_gap": 100.0,
    "core_viability_at_zero_friction": 1.0,
    "north_star_metric_name": "Net_Sharpe",
    "north_star_target": 2.0,
    "theoretical_zero_friction_ceiling": 0.62,
    "latest_kpi_value": 0.21,
    "measured_components": [
      {"component": "Execution friction & frozen state", "measured_impact": 88.0}
    ]
  },
  "proposals": [
    {
      "id": "FIX_01",
      "hypothesis_key": "fix_daily_resolution_mismatch",
      "lot": "Lot 1",
      "gate": "P1",
      "owner_seat": "CTO",
      "title": "Align FX data resolution in main.py:L64 with hourly sentinel",
      "kind": "PLUMBING_RUNTIME",
      "fact_verified": true,
      "evidence_bindings": [
        {
          "type": "code",
          "file": "main.py",
          "line": 64,
          "window": 5,
          "expected_tokens": ["Resolution.DAILY"],
          "forbidden_tokens": ["Resolution.HOUR"]
        },
        {
          "type": "probe_json",
          "key": "probe3.implied_gross_sr",
          "max_val": 1.0
        }
      ],
      "touches_healthy_brick": false,
      "new_free_parameters_or_layers": 0,
      "post_hoc_or_wishful_tuning": false,
      "estimated_stake_pct": 25.0,
      "blocks_critical_gate": true,
      "stake_label": "+25% net uplift verified on probe",
      "plain_sentence": "Written in the user's language: clear 1-sentence economic mechanism."
    }
  ]
}
```
- **3-State Foundation Ceiling**:
  - `DEAD_FOUNDATION` (`core_viability <= 0` or `theoretical_zero_friction_ceiling <= 0`): Band-aids prohibited.
  - `SUB_SCALE_FOUNDATION` (`0 < theoretical_zero_friction_ceiling < north_star_target`): Unlocks `CORE_REDESIGN` / `SIGNAL_FORMULA` / `NEW_ALPHA_OR_VALUE_DRIVER`, suspends viable-core-only dead-ends, and **HARD-BLOCKS** `LEVERAGE_OR_SCALING_ON_CORE` (`amplifies_subscale_core: true`).
  - `VIABLE_FOUNDATION`: Enforces strict Brakes-First order.

### B. Record a Scoped Dead-End or Confounded Caution (`EXCOM_V32_04`)
```bash
python "<skill-dir>/scripts/porte0_carte_decideur.py" record-dead-end \
  --ledger-dir "<ledger-dir>" \
  --key "drop_inv_sigma_router" \
  --title "Remove /sig[act] scaling inside spectral router" \
  --evidence-grade CONFOUNDED_BUNDLE \
  --validity-condition "Re-test in isolation without simultaneous equity changes" \
  --reason "Tested inside a 3-change bundle; isolated macro telemetry actually improved" \
  --metric "Macro C98E +2335 vs +1356"
```
- Use `--evidence-grade ISOLATED_ABLATION` **only** when a single isolated change failed empirically.
- Use `--evidence-grade CONFOUNDED_BUNDLE` when `> 1` behavioral edits shipped together — Gate 0 emits **`⚠️ CAUTION (ISOLATE 1 CHANGE)`** instead of a permanent dogma block.
- Use `--applies-only-when VIABLE_FOUNDATION` on freeze rules that must automatically suspend if the core is later proven `SUB_SCALE_FOUNDATION`.

### C. Overturn / Reopen a Buried Dead-End on Counter-Proof (`EXCOM_V32_04`)
```bash
python "<skill-dir>/scripts/porte0_carte_decideur.py" reopen-dead-end \
  --ledger-dir "<ledger-dir>" \
  --id "DE-3B3758" \
  --reason "Isolated forensic probe proved /sig[act] destroyed -41.9% of Macro C98E" \
  --counter-probe-path "<scratch>/forensic_probe_out.json"
```

---

## 3. Aeronautical Execution, KPI Circuit Breaker, Clean-Room Certifier & Lossless Anchor (`zero_oubli_runner.py`)

### A. Initialize Lot 0 + Compile Initial `CONTEXT_ANCHOR.md`
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" init-lot0 \
  --project-dir "<project-dir>" \
  --ledger-dir "<ledger-dir>" \
  --spec "<scratch>/lot0_spec.json"
```

### B. Install Physical `PreToolUse` Firewall (`ADD_01` + Clean-Room Breaker)
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" install-hooks \
  --project-dir "<project-dir>" \
  --ledger-dir "<ledger-dir>"
```
- Safely skips if `<project-dir>/.agents/hooks.json` already exists (unless `--force`).
- Physically blocks `write_file` / `edit_file` inside `<project-dir>` whenever `gate_P0_certified.json` is missing, **`clean_room_required == true`** (Plateau/Regression Circuit Breaker tripped), a `sacred_file` is targeted, or an edit deletes any certified `test_*` function.

### C. Verify & Sign Gate `Pk` (`SHA-256` Blocking Gate)
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" verify-gate \
  --ledger-dir "<ledger-dir>" \
  --project-dir "<project-dir>" \
  --gate P1
```

### D. Record Empirical North-Star KPI Run / Stage-Gate (`EXCOM_V33_01`)
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" record-kpi \
  --ledger-dir "<ledger-dir>" \
  --run-id "RUN_04" \
  --lot "Lot 3" \
  --metric-name "Net_Sharpe" \
  --value 0.68 \
  --target 2.0 \
  --clean-room-policy EVERY_MAJOR_MILESTONE \
  --theoretical-ceiling 0.85 \
  --changes-count 1 \
  --notes "Post-backtest empirical run awaiting independent 3-agent Clean-Room Board report"
```
- **Default Policy (`EVERY_MAJOR_MILESTONE`)**: Immediately sets `clean_room_required = true` after **every** major run/stage-gate (threshold = `1`) so an isolated Multi-Agent Clean-Room Board authors the executive report before the builder/PMO can open the next Gate 0. (Lightweight continuous-ops projects may opt into `--clean-room-policy PLATEAU_2`.)
- On `>= 2` consecutive non-improving runs vs champion, Empirical RAG escalates to **`RED`**.

### E. Certify Isolated Multi-Agent Clean-Room Board (`EXCOM_V33_01`)
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" record-clean-room \
  --ledger-dir "<ledger-dir>" \
  --project-dir "<project-dir>" \
  --auditor-id "clean-room-board-run-04" \
  --panel-auditors "code_plumbing:sub-1,math_ceiling:sub-2,devil_twins:sub-3" \
  --files-read "<scratch>/files_read.json" \
  --probe-script "<scratch>/clean_room_probe.py" \
  --probe-output "<scratch>/clean_room_probe_out.json" \
  --report-path "<deliverables>/CleanRoom_Board_Report_Run04.md" \
  --dissenting-vetoes "VETO on premature leverage while core ceiling < target" \
  --theoretical-ceiling 0.85 \
  --findings-summary "3-agent Clean-Room Board audited 100% of files and authored Executive Report" \
  --isolated-zero-history
```

### F. Recompile Lossless Primary-Source Anchor (`ADD_04`)
```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" render-anchor \
  --ledger-dir "<ledger-dir>" \
  --pmo-dir "<optional-pmo-dir>"
```
Compiles `<ledger-dir>/CONTEXT_ANCHOR.md` deterministically from primary JSON ledgers (`kpi_history.json`, `clean_room_audit_report.json`, `zero_oubli_ledger.json`, `dead_ends_registry.json`, `custom_profile.json`, `project-state.json`) — **zero recursive LLM summarization**, live **Empirical RAG override**, and automatic **`[STALE]`** profile/equation alerts.
