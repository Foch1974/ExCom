# Clean-Room Zero-History Audit Playbook (`ExCom v3.2`)

## Why Clean-Room Audits Exist

Long iterative threads accumulate **local-diff tunnel vision**: after 2+ incremental patches, an agent naturally focuses on the last diff, trusts its own previous summaries, defends sunk-cost design choices, and measures gaps only against the previous run instead of the **North-Star Target**.

`ExCom v3.2` solves this mechanically via the **Plateau/Regression Circuit Breaker**:
- Whenever `zero_oubli_runner.py record-kpi` records **`>= 2` consecutive non-improving runs** (against the project's champion North-Star KPI), `kpi_history.json` sets `clean_room_required = true`, flips `CONTEXT_ANCHOR.md` to **`RED`**, and **physically blocks** both `porte0_carte_decideur.py evaluate` and the `PreToolUse` firewall until an isolated Clean-Room Audit is certified on disk via `zero_oubli_runner.py record-clean-room`.
- A Clean-Room Audit should ALSO be triggered voluntarily on: (a) initial takeover of a legacy codebase/project, and (b) immediately before any irreversible scaling, capital leverage, or legal/contractual commitment.

---

## Mandatory Clean-Room Subagent Prompt Contract

Spawn a **fresh isolated subagent** (`invoke_subagent` / `Task` / new session with **ZERO prior conversation history**). Give it ONLY:
1. The project directory path and the North-Star Target (`metric_name`, `target`, current `champion` vs `latest`).
2. Read-only access to the repository / deliverables and existing ledger files.
3. The **5-Point Clean-Room Audit Mandate** below (never leak your own pet hypotheses or excuses from the previous thread!).

```text
ROLE: Isolated Clean-Room Chief Systems Auditor (Zero Prior Chat History, Zero Complacency).
MODE: STRICTLY READ-ONLY — Do NOT modify any project file.

MANDATE:
1. 100% COVERAGE READING: Read EVERY production source file (CODE) or EVERY core deliverable (METIER)
   line-by-line from start to finish — never rely solely on prior executive reports or summaries.
2. AUTOMATED STRUCTURAL SCAN: Run `root_cause_guard.py scan` and `root_cause_guard.py schema-parity`
   to surface silent parameter discards (`_ = param`), one-shot frozen-state latches, hardcoded
   exclusions, stacked clamp hotspots, and test-mock vs real-data schema drift.
3. END-TO-END BOTTLENECK & ATTENUATION FUNNEL (Deterministic Script on Disk):
   Write and execute a reproducible Python probe script measuring the full chain:
   - CODE mode   : Raw Input / Universe -> Feature/Signal Dimensionality (effective rank / collinearity)
                   -> Zero-Friction Theoretical Ceiling vs North-Star Target -> Stacked Clamps / Filters /
                   Caps / Latency / Cost Attenuation -> Net Realized Output.
   - METIER mode : Raw Revenue / Value Drivers -> Structural Unit Economics Ceiling vs North-Star Target
                   -> Hidden Regulatory / Tax / Vendor / Lead-Time Friction Stack -> Net All-In Outcome.
4. COMPLACENT TEST / MODEL PARITY AUDIT:
   Verify whether local test suites, mocks, or spreadsheet models inject synthetic data keys,
   unrealistic drift/growth assumptions, or Goodhart thresholds that diverge from real production data
   and secretly force destructive workarounds in production.
5. DOGMA & DEAD-END FALSIFICATION:
   Cross-check existing `CONTEXT_ANCHOR.md` invariants and `dead_ends_registry.json` entries against
   raw ground-truth telemetry: flag any stale equation, factually inaccurate prior Gate 0 claim, or
   confounded multi-change dead-end that deserves isolated re-testing or reopening.

OUTPUT CONTRACT:
- Exact list of every production file read (100% coverage required for certification).
- Path to the deterministic probe script and parsed JSON output written to disk.
- Explicit verdict on Foundation State (`DEAD_FOUNDATION`, `SUB_SCALE_FOUNDATION`, or `VIABLE_FOUNDATION`)
  with quantified `theoretical_zero_friction_ceiling` vs `north_star_target`.
- Ranked list of newly uncovered Level-A (hidden bugs/brakes) and Level-B (structural ceiling gaps)
  with exact `file:line` and `probe_json_key` bindings.
```

---

## Certifying the Clean-Room Audit & Clearing the Circuit Breaker

Once the isolated auditor completes and writes its probe script + JSON output to disk, register the certification:

```bash
python "<skill-dir>/scripts/zero_oubli_runner.py" record-clean-room \
  --ledger-dir "<ledger-dir>" \
  --project-dir "<project-dir>" \
  --auditor-id "<subagent-conversation-id>" \
  --files-read "<scratch>/clean_room_files_read.json" \
  --probe-script "<scratch>/clean_room_probe.py" \
  --probe-output "<scratch>/clean_room_probe_results.json" \
  --theoretical-ceiling 0.62 \
  --findings-summary "Uncovered 7 hidden code brakes and proved core ceiling 0.62 < 2.0 target" \
  --isolated-zero-history
```

`zero_oubli_runner.py` mechanically refuses certification (`exit 2`) if:
- `--isolated-zero-history` is omitted;
- Any file listed in `--files-read` does not exist on disk;
- Coverage of tracked production files/deliverables is `< 100%`;
- The deterministic probe script or JSON output is missing/empty on disk.
