#!/usr/bin/env python3
"""ExCom v3.2 — Aeronautical « Zero-Amnesia » Lot, SHA-256 Gate, KPI Circuit Breaker & Anchor Runner (en-US).

Deterministic execution spine across sequential Lots (Lot 0 .. Lot K) and blocking Gates (P0 .. PK):
  1. `init-lot0`         : Locks approved items, invariants, and sacred file SHA-256 hashes; certifies P0.
  2. `verify-gate`       : Enforces sequential gate order, sacred file integrity, AST Zero-Fake-Twin check,
                           Indelible Cumulative Test Suite, mandatory METIER clauses, and real test pass;
                           issues cryptographic `gate_<Pk>_certified.json` bound to `tree_sha256`.
  3. `status`            : Verifies live `tree_sha256` against certificates (catches unauthorized edits).
  4. `install-hooks`     : [ADD_01] Installs a physical `PreToolUse` firewall (`.agents/hooks.json`) on new
                           projects (never overwrites existing hooks without `--force`).
  5. `record-kpi`        : [EXCOM_V32_01] Appends empirical North-Star KPI runs to `kpi_history.json`,
                           tracks champion vs latest, flips empirical RAG to RED and trips the Clean-Room
                           Circuit Breaker on `>= 2` consecutive non-improving runs.
  6. `record-clean-room` : [EXCOM_V32_01] Certifies an isolated zero-history Clean-Room Audit on disk,
                           enforcing `100%` production file/deliverable coverage + verified probe output
                           before clearing the Plateau/Regression Circuit Breaker.
  7. `render-anchor`     : [ADD_04 + EXCOM_V32_04] Compiles `CONTEXT_ANCHOR.md` 100% deterministically from
                           primary JSON ledgers with Empirical KPI RAG override, `[STALE]` profile/equation
                           detection, and Scoped/Falsifiable Dead-Ends grouping.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional, Set


SCHEMA_VERSION = "3.2.0"

SKIP_DIRS: Set[str] = {
    ".git", "node_modules", "__pycache__", ".pytest_cache", ".venv", "venv",
    "dist", "build", "bin", "obj", ".agents", "excom-projects", "scratch",
}
ARCHIVE_PREFIXES = ("legacy", "archive", "backup", "deprecated", "old_")
PROD_CODE_EXTS: Set[str] = {".py", ".cs", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".sql", ".cpp", ".c", ".sol"}
METIER_DOC_EXTS: Set[str] = {".md", ".json", ".yaml", ".yml", ".csv", ".pdf", ".docx", ".xlsx"}

PRETOOL_GUARD_TEMPLATE = '''#!/usr/bin/env python3
"""ExCom Physical PreToolUse Firewall (Auto-Generated for Project Protection).

Blocks mutating file calls (`write_file`, `edit_file`, `Write`, `Edit`, `MultiEdit`) inside
the project root whenever:
  1. Gate P0 (`gate_P0_certified.json`) has not been initialized yet;
  2. Plateau/Regression Clean-Room Circuit Breaker is tripped (`clean_room_required == true`);
  3. Target path is a locked `sacred_file`;
  4. An edit removes any previously certified `test_*` function from the Indelible Test Suite.
"""
import ast
import json
from pathlib import Path
import sys

LEDGER_DIR = Path(r"__LEDGER_DIR__")
PROJECT_DIR = Path(r"__PROJECT_DIR__").resolve()
MUTATING_TOOLS = {"write_file", "edit_file", "Write", "Edit", "MultiEdit"}


def extract_tool_and_args(payload: dict) -> tuple[str, dict]:
    tool = str(payload.get("tool_name") or payload.get("toolName") or payload.get("tool") or "")
    args = payload.get("tool_input") or payload.get("toolInput") or payload.get("arguments") or payload.get("args") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except Exception:
            args = {}
    return tool, (args if isinstance(args, dict) else {})


def deny(reason: str) -> int:
    sys.stderr.write(f"[EXCOM PRETOOL FIREWALL BLOCKED] {reason}\\n")
    print(json.dumps({"decision": "block", "reason": reason}))
    return 2


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except Exception:
        return 0

    tool, args = extract_tool_and_args(payload)
    if tool not in MUTATING_TOOLS:
        return 0

    target_str = str(args.get("Path") or args.get("file_path") or args.get("path") or "").strip()
    if not target_str:
        return 0
    target = Path(target_str).resolve()

    try:
        rel = str(target.relative_to(PROJECT_DIR)).replace("\\\\", "/")
    except ValueError:
        return 0

    if rel.startswith((".agents/", "scratch/", "excom-projects/")):
        return 0

    # 0. Clean-Room Plateau/Regression Circuit Breaker check (EXCOM_V32_01)
    kpi_file = LEDGER_DIR / "kpi_history.json"
    if kpi_file.is_file():
        try:
            kpi = json.loads(kpi_file.read_text(encoding="utf-8"))
            if bool(kpi.get("clean_room_required", False)):
                return deny(
                    f"Cannot modify '{rel}' while Plateau/Regression Circuit Breaker is ACTIVE. "
                    "Complete a 100%-coverage isolated Clean-Room Audit (`zero_oubli_runner.py record-clean-room`) first."
                )
        except Exception:
            pass

    p0_cert = LEDGER_DIR / "gate_P0_certified.json"
    ledger_file = LEDGER_DIR / "zero_oubli_ledger.json"
    if not p0_cert.is_file() or not ledger_file.is_file():
        return deny(f"Cannot modify '{rel}' before Gate 0 & Lot 0 registration (`zero_oubli_runner.py init-lot0`).")

    ledger = json.loads(ledger_file.read_text(encoding="utf-8"))

    # 1. Sacred file lock
    sacred = {k.replace("\\\\", "/") for k in ledger.get("sacred_files_sha256", {}).keys()}
    if rel in sacred:
        return deny(f"File '{rel}' is a locked SACRED FILE (immutable SHA-256).")

    # 2. Indelible test suite protection against test_* deletion
    indelible = set(ledger.get("indelible_verified_tests", []))
    if indelible and target.suffix.lower() == ".py" and target.is_file():
        old_src = target.read_text(encoding="utf-8", errors="replace")
        new_content = args.get("Content") or args.get("content")
        if new_content is None and ("Target" in args or "old_string" in args):
            tgt_s = str(args.get("Target") or args.get("old_string") or "")
            rep_s = str(args.get("Replacement") or args.get("new_string") or "")
            if tgt_s and tgt_s in old_src:
                new_content = old_src.replace(tgt_s, rep_s)
        if isinstance(new_content, str):
            try:
                old_tree = ast.parse(old_src)
                new_tree = ast.parse(new_content)
                old_fns = {n.name for n in ast.walk(old_tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                new_fns = {n.name for n in ast.walk(new_tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                removed_indelible = sorted((old_fns & indelible) - new_fns)
                if removed_indelible:
                    return deny(f"Indelible Test Suite violation: attempt to delete certified test(s) {removed_indelible} in '{rel}'.")
            except SyntaxError:
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_test_or_harness_rel(rel_path: str) -> bool:
    p = rel_path.lower().replace("\\", "/")
    name = Path(p).name
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith("_gate.py")
        or name.endswith("_guard.py")
        or "/tests/" in f"/{p}"
        or "/test_harnesses/" in f"/{p}"
        or "/.agents/" in f"/{p}"
    )


def compute_workspace_tree_sha256(project_dir: Path, tracked_rel_paths: Optional[List[str]] = None) -> str:
    h = hashlib.sha256()
    if tracked_rel_paths:
        for rel in sorted(set(tracked_rel_paths)):
            fp = project_dir / rel
            if fp.is_file():
                h.update(rel.replace("\\", "/").encode("utf-8"))
                h.update(b"\0")
                h.update(fp.read_bytes())
                h.update(b"\0")
        return h.hexdigest()

    for root, dirs, files in os.walk(project_dir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith(".git"))
        for fn in sorted(files):
            fp = Path(root) / fn
            try:
                rel = str(fp.relative_to(project_dir)).replace("\\", "/")
                h.update(rel.encode("utf-8"))
                h.update(b"\0")
                h.update(fp.read_bytes())
                h.update(b"\0")
            except OSError:
                continue
    return h.hexdigest()


def discover_expected_production_files(project_dir: Path, ledger: Dict[str, Any]) -> List[str]:
    """Lists all production source files (CODE) or core deliverables (METIER) required for 100% Clean-Room Audit."""
    tracked = ledger.get("tracked_files", [])
    if tracked:
        prod = [
            rel.replace("\\", "/")
            for rel in tracked
            if not is_test_or_harness_rel(rel) and (project_dir / rel).is_file()
        ]
        if prod:
            return sorted(set(prod))

    mode = str(ledger.get("mode", "CODE")).upper()
    exts = PROD_CODE_EXTS if mode == "CODE" else METIER_DOC_EXTS
    found: List[str] = []
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = sorted(
            d for d in dirs
            if d not in SKIP_DIRS
            and not d.startswith(".git")
            and not d.lower().startswith(ARCHIVE_PREFIXES)
        )
        for fn in sorted(files):
            fp = Path(root) / fn
            if fp.suffix.lower() not in exts:
                continue
            rel = str(fp.relative_to(project_dir)).replace("\\", "/")
            if mode == "CODE" and is_test_or_harness_rel(rel):
                continue
            found.append(rel)
    return sorted(set(found))


def inspect_python_test_ast(test_file: Path, test_fn_name: str, required_prod_symbol: str) -> Dict[str, Any]:
    if not test_file.is_file():
        return {"ok": False, "reason": f"Test file not found: {test_file}"}
    source = test_file.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=str(test_file))
    except SyntaxError as exc:
        return {"ok": False, "reason": f"SyntaxError in {test_file.name}: {exc}"}

    all_test_fns: Set[str] = set()
    target_node: Optional[ast.AST] = None
    imported_or_used_names: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                all_test_fns.add(node.name)
            if node.name == test_fn_name:
                target_node = node
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_or_used_names.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_or_used_names.add(alias.name.split(".")[0])

    if target_node is None:
        return {"ok": False, "reason": f"Test function `{test_fn_name}` missing in {test_file.name}", "all_tests": all_test_fns}

    has_assert = False
    fn_used_names: Set[str] = set()
    for sub in ast.walk(target_node):
        if isinstance(sub, ast.Assert):
            has_assert = True
        elif isinstance(sub, ast.Call):
            if isinstance(sub.func, ast.Attribute) and sub.func.attr.startswith("assert"):
                has_assert = True
            elif isinstance(sub.func, ast.Name) and sub.func.id.startswith("assert"):
                has_assert = True
        if isinstance(sub, ast.Name):
            fn_used_names.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            fn_used_names.add(sub.attr)

    if not has_assert:
        return {"ok": False, "reason": f"Tautological test blocked: `{test_fn_name}` contains zero `assert` statements.", "all_tests": all_test_fns}

    if required_prod_symbol:
        all_refs = imported_or_used_names | fn_used_names
        if required_prod_symbol not in all_refs:
            return {
                "ok": False,
                "reason": f"Zero-Fake-Twin violation: `{test_fn_name}` does not invoke real production symbol `{required_prod_symbol}`.",
                "all_tests": all_test_fns,
            }

    return {"ok": True, "reason": "OK", "all_tests": all_test_fns}


def verify_metier_deliverable(project_dir: Path, item: Dict[str, Any]) -> Dict[str, Any]:
    rel = str(item.get("deliverable_path", "")).strip()
    if not rel:
        return {"ok": False, "reason": "Missing `deliverable_path` for METIER item."}
    fp = (project_dir / rel) if not Path(rel).is_absolute() else Path(rel)
    if not fp.is_file():
        return {"ok": False, "reason": f"Deliverable file missing on disk: {fp}"}
    min_bytes = int(item.get("min_bytes", 120))
    size = fp.stat().st_size
    if size < min_bytes:
        return {"ok": False, "reason": f"Deliverable below minimum byte threshold ({size} B < {min_bytes} B): {fp.name}"}
    text = fp.read_text(encoding="utf-8", errors="replace").lower()
    missing = [m for m in item.get("required_markers", []) if str(m).lower() not in text]
    if missing:
        return {"ok": False, "reason": f"Mandatory clauses/sections missing in {fp.name}: {missing}"}
    return {"ok": True, "reason": f"Verified ({size} bytes, 100% mandatory markers present)"}


def worst_rag(a: str, b: str) -> str:
    rank = {"GREEN": 0, "AMBER": 1, "RED": 2}
    ua = str(a or "GREEN").upper()
    ub = str(b or "GREEN").upper()
    return ua if rank.get(ua, 0) >= rank.get(ub, 0) else ub


def recompute_kpi_summary(kpi: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministically recomputes champion, non-improving streak, and Clean-Room Circuit Breaker state."""
    runs = kpi.get("runs", [])
    higher = bool(kpi.get("higher_is_better", True))
    if not runs:
        kpi["champion_run_id"] = None
        kpi["champion_value"] = None
        kpi["consecutive_non_improving_runs"] = 0
        kpi["clean_room_required"] = False
        kpi["empirical_rag"] = "GREEN"
        return kpi

    champ_id = str(runs[0]["run_id"])
    champ_val = float(runs[0]["value"])
    streak = 0
    for idx, r in enumerate(runs):
        val = float(r["value"])
        if idx == 0:
            r["improved_vs_champion"] = True
            champ_id = str(r["run_id"])
            champ_val = val
            streak = 0
            continue
        is_better = (val > champ_val + 1e-12) if higher else (val < champ_val - 1e-12)
        if is_better:
            champ_id = str(r["run_id"])
            champ_val = val
            streak = 0
            r["improved_vs_champion"] = True
        else:
            streak += 1
            r["improved_vs_champion"] = False

    latest_id = str(runs[-1]["run_id"])
    last_cr_id = str(kpi.get("last_clean_room_after_run_id", ""))
    cr_needed = (streak >= 2) and (last_cr_id != latest_id)

    kpi["champion_run_id"] = champ_id
    kpi["champion_value"] = champ_val
    kpi["latest_run_id"] = latest_id
    kpi["latest_value"] = float(runs[-1]["value"])
    kpi["consecutive_non_improving_runs"] = streak
    kpi["clean_room_required"] = cr_needed
    if cr_needed:
        kpi["empirical_rag"] = "RED"
    elif streak >= 1:
        kpi["empirical_rag"] = "AMBER"
    else:
        kpi["empirical_rag"] = "GREEN"
    return kpi


def compile_lossless_anchor(ledger_dir: Path, pmo_dir: Optional[Path] = None) -> Path:
    """ADD_04 + EXCOM_V32_01/04: Compiles CONTEXT_ANCHOR.md strictly from raw primary JSON databases."""
    ledger_path = ledger_dir / "zero_oubli_ledger.json"
    de_path = ledger_dir / "dead_ends_registry.json"
    prof_path = ledger_dir / "custom_profile.json"
    kpi_path = ledger_dir / "kpi_history.json"
    cr_path = ledger_dir / "clean_room_audit_report.json"

    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.is_file() else {}
    de_store = json.loads(de_path.read_text(encoding="utf-8")) if de_path.is_file() else {"total_trials_count": 0, "dead_ends": []}
    prof = json.loads(prof_path.read_text(encoding="utf-8")) if prof_path.is_file() else {}
    kpi = recompute_kpi_summary(json.loads(kpi_path.read_text(encoding="utf-8"))) if kpi_path.is_file() else {}
    cr = json.loads(cr_path.read_text(encoding="utf-8")) if cr_path.is_file() else {}

    pmo_state: Dict[str, Any] = {}
    if pmo_dir and (pmo_dir / "project-state.json").is_file():
        pmo_state = json.loads((pmo_dir / "project-state.json").read_text(encoding="utf-8"))

    project_dir = Path(ledger["project_dir"]) if ledger.get("project_dir") else None
    live_sha = (
        compute_workspace_tree_sha256(project_dir, ledger.get("tracked_files") or None)
        if (project_dir and project_dir.is_dir())
        else "N/A"
    )

    lines: List[str] = [
        "# CONTEXT ANCHOR (Deterministic Primary-Source Snapshot — Zero Lossy Summarization)",
        f"- **Compiled At** : `{now_iso()}`",
        f"- **Project** : `{ledger.get('project_name', pmo_state.get('project_name', 'N/A'))}` (`{ledger.get('mode', 'N/A')}` · `{ledger.get('domain', prof.get('domain', 'N/A'))}`)",
        f"- **Live Workspace `tree_sha256`** : `{live_sha}`",
        f"- **Cumulative Trials (`N_trials`)** : `{de_store.get('total_trials_count', 0)}` · **Indelible Tests Locked** : `{len(ledger.get('indelible_verified_tests', []))}`",
    ]

    # Section 0: North-Star KPI Trajectory & Clean-Room Circuit Breaker (EXCOM_V32_01)
    if kpi and kpi.get("runs"):
        latest_run = kpi["runs"][-1]
        emp_rag = kpi.get("empirical_rag", "GREEN")
        cr_flag = bool(kpi.get("clean_room_required", False))
        rag_badge = f"{emp_rag} — PLATEAU/REGRESSION CIRCUIT BREAKER ACTIVE (CLEAN-ROOM AUDIT REQUIRED)" if cr_flag else emp_rag
        lines.extend([
            "",
            "## 0. North-Star KPI Trajectory & Clean-Room Circuit Breaker",
            f"- **Empirical RAG** : `{rag_badge}`",
            f"- **North-Star Metric (`{kpi.get('metric_name')}`)** : Target = `{kpi.get('target')}` · Champion = `{kpi.get('champion_value')}` (`{kpi.get('champion_run_id')}`) · Latest = `{kpi.get('latest_value')}` (`{kpi.get('latest_run_id')}`)",
            f"- **Consecutive Non-Improving Runs** : `{kpi.get('consecutive_non_improving_runs', 0)}` (Breaker threshold: `>= 2`)",
        ])
        ceil = latest_run.get("theoretical_ceiling")
        tgt = kpi.get("target")
        if ceil is not None and tgt is not None:
            higher = bool(kpi.get("higher_is_better", True))
            subscale = (float(ceil) < float(tgt)) if higher else (float(ceil) > float(tgt))
            if subscale:
                lines.append(
                    f"- **⚠️ SUB-SCALE FOUNDATION ALERT** : Theoretical zero-friction ceiling (`{ceil}`) < North-Star target (`{tgt}`). "
                    "Core redesign unlocked; scaling/leverage on current core is BLOCKED."
                )
        if cr:
            lines.append(
                f"- **Last Clean-Room Audit** : `{cr.get('recorded_at')}` · Auditor = `{cr.get('auditor_id')}` · "
                f"Coverage = `{cr.get('coverage_pct')}%` (`{cr.get('files_read_count')}/{cr.get('expected_files_count')}` files) · "
                f"After Run = `{cr.get('audited_after_run_id')}`"
            )

    # Section 1: Invariants & Stale Profile/Equation Detection (EXCOM_V32_04)
    profile_stale = False
    stale_reason = ""
    if prof and kpi and kpi.get("runs"):
        latest_run = kpi["runs"][-1]
        latest_id = str(latest_run.get("run_id", ""))
        prof_run = str(prof.get("verified_at_run_id", ""))
        prof_ts = str(prof.get("registered_at", ""))
        latest_ts = str(latest_run.get("recorded_at", ""))
        if prof_run and latest_id and prof_run != latest_id:
            profile_stale = True
            stale_reason = f"profile locked at run `{prof_run}`, latest run is `{latest_id}`"
        elif not prof_run and prof_ts and latest_ts and prof_ts < latest_ts:
            profile_stale = True
            stale_reason = f"profile dated `{prof_ts}` precedes latest KPI run `{latest_id}` (`{latest_ts}`)"

    lines.extend(["", "## 1. Immutable Project Invariants & Sacred Files"])
    if profile_stale:
        lines.append(f"- **⚠️ [STALE EQUATION / PROFILE — REFRESH REQUIRED]** : {stale_reason}. Re-verify conservation equation & invariants against latest telemetry.")
    if prof.get("mass_balance_equation"):
        stale_prefix = "[STALE] " if profile_stale else ""
        lines.append(f"- **Conservation Equation** : `{stale_prefix}{prof['mass_balance_equation']}`")
    for inv in ledger.get("project_invariants", []) or prof.get("mandatory_brakes_checklist", []):
        lines.append(f"- **Invariant** : {inv}")
    for sf, sha in ledger.get("sacred_files_sha256", {}).items():
        lines.append(f"- **Sacred File Locked** : `{sf}` (`sha256:{sha[:16]}...`)")

    lines.extend(["", "## 2. Aeronautical Lots & SHA-256 Gates Status (Exact Item Granularity)"])
    g_certs = ledger.get("gate_certificates", {})
    for g in ledger.get("gates_order", []):
        c = g_certs.get(g)
        st = "LOCKED_PENDING" if not c else ("CERTIFIED_VALID" if c.get("tree_sha256") == live_sha else "STALE_SHA256")
        lines.append(f"- **Gate `{g}`** : `{st}`")
    for it in ledger.get("items", []):
        target_ref = it.get("test_id") or it.get("deliverable_path") or ",".join(it.get("target_files", []))
        lines.append(f"  - `[{it['status']}]` **`{it['id']}`** (`{it['lot']}` / `{it['gate']}` · `{it['owner_seat']}`) : {it['title']} — ref: `{target_ref}`")

    # Section 3: Falsifiable, Scoped Dead-Ends Registry (EXCOM_V32_04)
    dead_ends = de_store.get("dead_ends", [])
    active_isolated = [d for d in dead_ends if str(d.get("status", "ACTIVE")).upper() != "OVERTURNED" and str(d.get("evidence_grade", "ISOLATED_ABLATION")).upper() != "CONFOUNDED_BUNDLE"]
    confounded_list = [d for d in dead_ends if str(d.get("status", "ACTIVE")).upper() != "OVERTURNED" and str(d.get("evidence_grade", "")).upper() == "CONFOUNDED_BUNDLE"]
    overturned_list = [d for d in dead_ends if str(d.get("status", "ACTIVE")).upper() == "OVERTURNED"]

    lines.extend(["", "## 3. Scoped & Falsifiable Dead-Ends Registry"])
    if not dead_ends:
        lines.append("- None recorded.")
    else:
        for de in active_isolated:
            em = de.get("evidence_metric")
            metric_tag = f" [{em}]" if em else ""
            vc = de.get("validity_condition")
            cond_tag = f" (valid while: {vc})" if vc else ""
            lines.append(f"- **[ACTIVE] `{de.get('id')}`** (`{de.get('rejected_on')}`) — *{de.get('title')}* : {de.get('failure_reason')}{metric_tag}{cond_tag}")
        for de in confounded_list:
            em = de.get("evidence_metric")
            metric_tag = f" [{em}]" if em else ""
            lines.append(f"- **[⚠️ CONFOUNDED — ISOLATE 1 CHANGE] `{de.get('id')}`** (`{de.get('rejected_on')}`) — *{de.get('title')}* : {de.get('failure_reason')}{metric_tag}")
        for de in overturned_list:
            lines.append(f"- **[OVERTURNED `{de.get('overturned_at', '')[:10]}`] `{de.get('id')}`** — *{de.get('title')}* : Reopened via `{Path(str(de.get('counter_probe_path', ''))).name}` ({de.get('overturned_reason', '')})")

    if pmo_state:
        evm = pmo_state.get("metrics", {}).get("evm", {})
        open_alerts = [a for a in pmo_state.get("alerts", []) if a.get("status") == "OPEN"]
        eff_rag = worst_rag(pmo_state.get("overall_rag", "GREEN"), kpi.get("empirical_rag", "GREEN"))
        lines.extend([
            "",
            "## 4. Live PMO Control Tower Telemetry",
            f"- **Effective RAG** : `{eff_rag}` (PMO=`{pmo_state.get('overall_rag')}`, Empirical KPI=`{kpi.get('empirical_rag', 'N/A')}`) · **Critical Path** : `{' -> '.join(pmo_state.get('metrics', {}).get('critical_path', []))}`",
            f"- **EVM** : `BAC = {evm.get('bac_eur', 0)} EUR` · `Committed = {evm.get('committed_eur', 0)} EUR` · `AC = {evm.get('ac_eur', 0)} EUR` · `CPI = {evm.get('cpi', 1.0)}` · `SPI = {evm.get('spi', 1.0)}`",
            f"- **Open Cross-Perimeter Alerts (`{len(open_alerts)}`)** :",
        ])
        for al in open_alerts:
            lines.append(f"  - `[{al.get('severity')}]` `{al.get('source_seat')} -> {','.join(al.get('target_seats', []))}` : {al.get('title')}")

    out_path = ledger_dir / "CONTEXT_ANCHOR.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def cmd_init_lot0(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    ledger_dir = Path(args.ledger_dir).resolve()
    ledger_dir.mkdir(parents=True, exist_ok=True)
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))

    sacred_hashes: Dict[str, str] = {}
    for rel in spec.get("sacred_files", []):
        fp = project_dir / rel
        if not fp.is_file():
            sys.exit(f"Lot 0 Error: sacred file '{rel}' does not exist in {project_dir}")
        sacred_hashes[rel] = file_sha256(fp)

    items: List[Dict[str, Any]] = []
    gates_order: List[str] = []
    for raw in spec.get("items", []):
        g = str(raw.get("gate", "P1"))
        if g not in gates_order:
            gates_order.append(g)
        items.append({
            "id": str(raw["id"]),
            "title": str(raw["title"]),
            "lot": str(raw.get("lot", "Lot 1")),
            "gate": g,
            "owner_seat": str(raw.get("owner_seat", "PMO")),
            "mode": str(raw.get("mode", spec.get("mode", "CODE"))).upper(),
            "target_files": raw.get("target_files", []),
            "test_file": raw.get("test_file", ""),
            "test_id": raw.get("test_id", ""),
            "production_symbol": raw.get("production_symbol", ""),
            "deliverable_path": raw.get("deliverable_path", ""),
            "required_markers": raw.get("required_markers", []),
            "min_bytes": int(raw.get("min_bytes", 120)),
            "status": "PENDING",
            "verified_at": None,
        })

    ledger = {
        "schema_version": SCHEMA_VERSION,
        "initialized_at": now_iso(),
        "project_name": spec.get("project_name", project_dir.name),
        "project_dir": str(project_dir),
        "mode": str(spec.get("mode", "CODE")).upper(),
        "domain": spec.get("domain", "CUSTOM"),
        "project_invariants": spec.get("project_invariants", []),
        "test_command": spec.get("test_command", ""),
        "tracked_files": spec.get("tracked_files", []),
        "sacred_files_sha256": sacred_hashes,
        "indelible_verified_tests": [],
        "gates_order": gates_order,
        "gate_certificates": {},
        "items": items,
    }
    ledger_path = ledger_dir / "zero_oubli_ledger.json"
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")

    cert_p0 = {
        "gate": "P0",
        "certified_at": now_iso(),
        "registered_items_count": len(items),
        "sacred_files_locked": len(sacred_hashes),
        "tree_sha256": compute_workspace_tree_sha256(project_dir, ledger["tracked_files"]),
    }
    (ledger_dir / "gate_P0_certified.json").write_text(json.dumps(cert_p0, ensure_ascii=False, indent=2), encoding="utf-8")
    anchor = compile_lossless_anchor(ledger_dir)

    print(json.dumps({
        "status": "GATE_P0_CERTIFIED",
        "ledger_path": str(ledger_path),
        "context_anchor_path": str(anchor),
        "items_registered": len(items),
        "gates_order": gates_order,
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_verify_gate(args: argparse.Namespace) -> int:
    ledger_dir = Path(args.ledger_dir).resolve()
    ledger_path = ledger_dir / "zero_oubli_ledger.json"
    if not ledger_path.is_file():
        sys.exit("Error: zero_oubli_ledger.json not found. Run `init-lot0` first.")

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    project_dir = Path(args.project_dir).resolve() if args.project_dir else Path(ledger["project_dir"])
    target_gate = args.gate
    gates_order: List[str] = ledger.get("gates_order", [])
    if target_gate not in gates_order:
        sys.exit(f"Error: gate '{target_gate}' not in ledger gates_order {gates_order}")

    gate_idx = gates_order.index(target_gate)
    failures: List[str] = []

    for prev_gate in gates_order[:gate_idx]:
        if not (ledger_dir / f"gate_{prev_gate}_certified.json").is_file():
            failures.append(f"Prerequisite gate `{prev_gate}` is not certified; cannot certify `{target_gate}` out of sequence.")

    for rel, expected_sha in ledger.get("sacred_files_sha256", {}).items():
        fp = project_dir / rel
        if not fp.is_file() or file_sha256(fp) != expected_sha:
            failures.append(f"SACRED FILE VIOLATION: `{rel}` was modified or deleted (SHA-256 mismatch).")

    active_gates = set(gates_order[: gate_idx + 1])
    scope_items = [it for it in ledger["items"] if it["gate"] in active_gates]
    discovered_tests_now: Set[str] = set()
    need_code_test_run = False

    for it in scope_items:
        if it["mode"] == "CODE":
            need_code_test_run = True
            tf = (project_dir / it["test_file"]) if not Path(it["test_file"]).is_absolute() else Path(it["test_file"])
            res = inspect_python_test_ast(tf, it["test_id"], it.get("production_symbol", ""))
            discovered_tests_now |= res.get("all_tests", set())
            if not res["ok"]:
                failures.append(f"[{it['id']} · {it['gate']}] {res['reason']}")
        else:
            res_m = verify_metier_deliverable(project_dir, it)
            if not res_m["ok"]:
                failures.append(f"[{it['id']} · {it['gate']}] {res_m['reason']}")

    prev_indelible = set(ledger.get("indelible_verified_tests", []))
    missing_indelible = sorted(prev_indelible - discovered_tests_now)
    if missing_indelible:
        failures.append(f"INDELIBLE TEST SUITE VIOLATION — deleted prior certified tests: {missing_indelible}")

    test_cmd = str(ledger.get("test_command", "")).strip()
    if need_code_test_run and not failures:
        if not test_cmd:
            failures.append("Missing `test_command` in ledger for executing CODE test suite.")
        else:
            proc = subprocess.run(
                test_cmd, shell=True, cwd=str(project_dir),
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            if proc.returncode != 0:
                tail = (proc.stdout + "\n" + proc.stderr)[-1200:]
                failures.append(f"Test runner failed with exit code {proc.returncode}:\n{tail}")

    if failures:
        print(json.dumps({"gate": target_gate, "status": "BLOCKED", "failures_count": len(failures), "failures": failures}, ensure_ascii=False, indent=2))
        return 2

    ts = now_iso()
    for it in scope_items:
        it["status"] = "VERIFIED"
        if not it.get("verified_at"):
            it["verified_at"] = ts
        if it["mode"] == "CODE" and it.get("test_id"):
            prev_indelible.add(it["test_id"])

    ledger["indelible_verified_tests"] = sorted(prev_indelible)
    tree_sha = compute_workspace_tree_sha256(project_dir, ledger.get("tracked_files") or None)
    cert = {
        "gate": target_gate,
        "status": "CERTIFIED_100_PCT",
        "certified_at": ts,
        "verified_items": [it["id"] for it in scope_items],
        "indelible_tests_locked": len(ledger["indelible_verified_tests"]),
        "tree_sha256": tree_sha,
    }
    cert_path = ledger_dir / f"gate_{target_gate}_certified.json"
    cert_path.write_text(json.dumps(cert, ensure_ascii=False, indent=2), encoding="utf-8")

    g_certs = ledger.setdefault("gate_certificates", {})
    g_certs[target_gate] = cert
    for prev_g in gates_order[:gate_idx]:
        if prev_g in g_certs:
            g_certs[prev_g]["tree_sha256"] = tree_sha
            g_certs[prev_g]["last_cumulative_recheck_at"] = ts
            (ledger_dir / f"gate_{prev_g}_certified.json").write_text(
                json.dumps(g_certs[prev_g], ensure_ascii=False, indent=2), encoding="utf-8"
            )
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    anchor = compile_lossless_anchor(ledger_dir)

    print(json.dumps({
        "gate": target_gate,
        "status": "CERTIFIED_100_PCT",
        "certificate_path": str(cert_path),
        "context_anchor_path": str(anchor),
        "tree_sha256": tree_sha,
        "verified_items_count": len(scope_items),
        "total_items_count": len(ledger["items"]),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_record_kpi(args: argparse.Namespace) -> int:
    """EXCOM_V32_01: Tracks North-Star KPI trajectory and triggers Plateau/Regression Clean-Room Circuit Breaker."""
    ledger_dir = Path(args.ledger_dir).resolve()
    ledger_dir.mkdir(parents=True, exist_ok=True)
    kpi_path = ledger_dir / "kpi_history.json"
    if kpi_path.is_file():
        kpi = json.loads(kpi_path.read_text(encoding="utf-8"))
    else:
        kpi = {
            "schema_version": SCHEMA_VERSION,
            "metric_name": args.metric_name,
            "target": float(args.target),
            "higher_is_better": not bool(args.lower_is_better),
            "runs": [],
        }

    kpi["metric_name"] = args.metric_name or kpi.get("metric_name", "North-Star KPI")
    if args.target is not None:
        kpi["target"] = float(args.target)
    if args.lower_is_better:
        kpi["higher_is_better"] = False

    entry: Dict[str, Any] = {
        "recorded_at": now_iso(),
        "run_id": args.run_id,
        "lot": args.lot,
        "value": float(args.value),
        "target": float(kpi["target"]),
        "changes_count": int(args.changes_count),
        "confounded": int(args.changes_count) > 1,
        "notes": args.notes,
    }
    if args.theoretical_ceiling is not None:
        entry["theoretical_ceiling"] = float(args.theoretical_ceiling)

    kpi.setdefault("runs", []).append(entry)
    kpi = recompute_kpi_summary(kpi)
    kpi_path.write_text(json.dumps(kpi, ensure_ascii=False, indent=2), encoding="utf-8")

    pmo_dir = Path(args.pmo_dir).resolve() if args.pmo_dir else None
    anchor = compile_lossless_anchor(ledger_dir, pmo_dir=pmo_dir)

    print(json.dumps({
        "status": "CLEAN_ROOM_CIRCUIT_BREAKER_TRIPPED" if kpi["clean_room_required"] else "KPI_RECORDED",
        "kpi_history_path": str(kpi_path),
        "context_anchor_path": str(anchor),
        "empirical_rag": kpi["empirical_rag"],
        "champion_run_id": kpi["champion_run_id"],
        "champion_value": kpi["champion_value"],
        "latest_run_id": kpi["latest_run_id"],
        "latest_value": kpi["latest_value"],
        "consecutive_non_improving_runs": kpi["consecutive_non_improving_runs"],
        "clean_room_required": kpi["clean_room_required"],
        "confounded_warning": entry["confounded"],
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_record_clean_room(args: argparse.Namespace) -> int:
    """EXCOM_V32_01: Certifies a 100%-coverage isolated Clean-Room Audit and clears the circuit breaker."""
    ledger_dir = Path(args.ledger_dir).resolve()
    project_dir = Path(args.project_dir).resolve()
    ledger_dir.mkdir(parents=True, exist_ok=True)

    if not args.isolated_zero_history:
        print(json.dumps({
            "status": "BLOCKED",
            "reason": "Clean-Room Audit MUST be executed by an isolated zero-history auditor (`--isolated-zero-history` required).",
        }, ensure_ascii=False, indent=2))
        return 2

    p_script = Path(args.probe_script).resolve()
    p_out = Path(args.probe_output).resolve()
    if not p_script.is_file() or not p_out.is_file() or p_out.stat().st_size <= 10:
        print(json.dumps({
            "status": "BLOCKED",
            "reason": f"Missing or empty Clean-Room deterministic probe on disk: script={p_script.is_file()}, output={p_out.is_file()}",
        }, ensure_ascii=False, indent=2))
        return 2

    # Load files read list
    raw_fr = args.files_read.strip()
    if raw_fr.startswith("@"):
        files_list = json.loads(Path(raw_fr[1:]).read_text(encoding="utf-8"))
    elif Path(raw_fr).is_file() and raw_fr.lower().endswith(".json"):
        files_list = json.loads(Path(raw_fr).read_text(encoding="utf-8"))
    else:
        files_list = [s.strip() for s in raw_fr.split(",") if s.strip()]

    verified_read_rel: Set[str] = set()
    missing_on_disk: List[str] = []
    for f in files_list:
        fp = Path(f)
        if not fp.is_absolute():
            fp = (project_dir / fp).resolve()
        else:
            fp = fp.resolve()
        if not fp.is_file():
            missing_on_disk.append(str(f))
            continue
        try:
            rel = str(fp.relative_to(project_dir)).replace("\\", "/")
            verified_read_rel.add(rel)
        except ValueError:
            verified_read_rel.add(fp.name)

    if missing_on_disk:
        print(json.dumps({
            "status": "BLOCKED",
            "reason": "Clean-Room files_read contains paths that do not exist on disk.",
            "missing_files": missing_on_disk,
        }, ensure_ascii=False, indent=2))
        return 2

    ledger_path = ledger_dir / "zero_oubli_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.is_file() else {"mode": "CODE", "tracked_files": []}
    expected_prod = discover_expected_production_files(project_dir, ledger)
    unread = sorted(set(expected_prod) - verified_read_rel)
    if expected_prod:
        coverage_pct = round(((len(expected_prod) - len(unread)) / len(expected_prod)) * 100.0, 2)
    else:
        coverage_pct = 100.0 if verified_read_rel else 0.0

    if coverage_pct < 100.0:
        print(json.dumps({
            "status": "BLOCKED_INCOMPLETE_COVERAGE",
            "coverage_pct": coverage_pct,
            "files_read_count": len(expected_prod) - len(unread),
            "expected_files_count": len(expected_prod),
            "unread_production_files": unread,
            "reason": "Clean-Room Audit requires 100% line-by-line coverage of all tracked production files/deliverables.",
        }, ensure_ascii=False, indent=2))
        return 2

    kpi_path = ledger_dir / "kpi_history.json"
    latest_run_id = ""
    if kpi_path.is_file():
        kpi = recompute_kpi_summary(json.loads(kpi_path.read_text(encoding="utf-8")))
        latest_run_id = str(kpi.get("latest_run_id", ""))
        kpi["last_clean_room_after_run_id"] = latest_run_id
        kpi = recompute_kpi_summary(kpi)
        kpi_path.write_text(json.dumps(kpi, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": now_iso(),
        "auditor_id": args.auditor_id,
        "isolated_zero_history": True,
        "audited_after_run_id": latest_run_id,
        "tree_sha256": compute_workspace_tree_sha256(project_dir, ledger.get("tracked_files") or None),
        "coverage_pct": coverage_pct,
        "files_read_count": len(expected_prod) if expected_prod else len(verified_read_rel),
        "expected_files_count": len(expected_prod),
        "files_read": sorted(verified_read_rel),
        "probe_script_path": str(p_script),
        "probe_output_path": str(p_out),
        "probe_output_sha256": file_sha256(p_out),
        "theoretical_ceiling": float(args.theoretical_ceiling) if args.theoretical_ceiling is not None else None,
        "findings_summary": args.findings_summary,
    }
    cr_path = ledger_dir / "clean_room_audit_report.json"
    cr_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    pmo_dir = Path(args.pmo_dir).resolve() if args.pmo_dir else None
    anchor = compile_lossless_anchor(ledger_dir, pmo_dir=pmo_dir)

    print(json.dumps({
        "status": "CLEAN_ROOM_AUDIT_CERTIFIED_100_PCT",
        "report_path": str(cr_path),
        "context_anchor_path": str(anchor),
        "coverage_pct": coverage_pct,
        "audited_after_run_id": latest_run_id,
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ledger_dir = Path(args.ledger_dir).resolve()
    ledger = json.loads((ledger_dir / "zero_oubli_ledger.json").read_text(encoding="utf-8"))
    project_dir = Path(args.project_dir).resolve() if args.project_dir else Path(ledger["project_dir"])
    live_sha = compute_workspace_tree_sha256(project_dir, ledger.get("tracked_files") or None)

    gate_states = []
    for g in ledger.get("gates_order", []):
        c = ledger.get("gate_certificates", {}).get(g)
        g_items = [it for it in ledger["items"] if it["gate"] == g]
        if not c:
            st = "LOCKED_PENDING"
        elif c.get("tree_sha256") != live_sha:
            st = "STALE_SHA256_REVERIFY_REQUIRED"
        else:
            st = "CERTIFIED_VALID"
        gate_states.append({
            "gate": g,
            "state": st,
            "verified": f"{sum(1 for i in g_items if i['status'] == 'VERIFIED')}/{len(g_items)}",
        })

    kpi_path = ledger_dir / "kpi_history.json"
    kpi = recompute_kpi_summary(json.loads(kpi_path.read_text(encoding="utf-8"))) if kpi_path.is_file() else {}
    anchor = compile_lossless_anchor(ledger_dir)
    print(json.dumps({
        "project_name": ledger.get("project_name"),
        "mode": ledger.get("mode"),
        "domain": ledger.get("domain"),
        "live_tree_sha256": live_sha,
        "indelible_tests_count": len(ledger.get("indelible_verified_tests", [])),
        "empirical_rag": kpi.get("empirical_rag", "N/A"),
        "clean_room_required": bool(kpi.get("clean_room_required", False)),
        "context_anchor_path": str(anchor),
        "gates": gate_states,
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_install_hooks(args: argparse.Namespace) -> int:
    """ADD_01: Installs physical PreToolUse hook into <project-dir>/.agents/hooks.json safely."""
    project_dir = Path(args.project_dir).resolve()
    ledger_dir = Path(args.ledger_dir).resolve()
    hooks_json_path = project_dir / ".agents" / "hooks.json"
    guard_py_path = project_dir / ".agents" / "hooks" / "excom_pretool_guard.py"

    if hooks_json_path.exists() and not args.force:
        print(json.dumps({
            "status": "SKIPPED_EXISTING_HOOKS_PROTECTED",
            "reason": f"{hooks_json_path} already exists; refusing to overwrite bespoke project firewall without --force.",
        }, ensure_ascii=False, indent=2))
        return 0

    guard_py_path.parent.mkdir(parents=True, exist_ok=True)
    guard_code = (
        PRETOOL_GUARD_TEMPLATE
        .replace("__LEDGER_DIR__", str(ledger_dir))
        .replace("__PROJECT_DIR__", str(project_dir))
    )
    guard_py_path.write_text(guard_code, encoding="utf-8")

    hooks_cfg = {
        "excom-zero-amnesia-firewall": {
            "enabled": True,
            "PreToolUse": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python .agents/hooks/excom_pretool_guard.py",
                            "timeout": 10,
                        }
                    ],
                }
            ],
        }
    }
    hooks_json_path.write_text(json.dumps(hooks_cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "PRETOOL_FIREWALL_INSTALLED",
        "hooks_json": str(hooks_json_path),
        "guard_script": str(guard_py_path),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_render_anchor(args: argparse.Namespace) -> int:
    ledger_dir = Path(args.ledger_dir).resolve()
    pmo_dir = Path(args.pmo_dir).resolve() if args.pmo_dir else None
    out = compile_lossless_anchor(ledger_dir, pmo_dir=pmo_dir)
    print(json.dumps({"status": "ANCHOR_COMPILED_LOSSLESS", "anchor_path": str(out)}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ExCom v3.2 — Aeronautical Lot, SHA-256 Gate, KPI Breaker & Lossless Anchor CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-lot0", help="Initialize Lot 0 ledger, certify P0, and compile lossless anchor")
    p_init.add_argument("--project-dir", required=True)
    p_init.add_argument("--ledger-dir", required=True)
    p_init.add_argument("--spec", required=True)
    p_init.set_defaults(func=cmd_init_lot0)

    p_ver = sub.add_parser("verify-gate", help="Verify cumulative checks for Gate Pk and sign tree_sha256")
    p_ver.add_argument("--ledger-dir", required=True)
    p_ver.add_argument("--gate", required=True)
    p_ver.add_argument("--project-dir", default="")
    p_ver.set_defaults(func=cmd_verify_gate)

    p_kpi = sub.add_parser("record-kpi", help="Record empirical North-Star KPI run and update Clean-Room Circuit Breaker")
    p_kpi.add_argument("--ledger-dir", required=True)
    p_kpi.add_argument("--run-id", required=True)
    p_kpi.add_argument("--metric-name", required=True)
    p_kpi.add_argument("--value", type=float, required=True)
    p_kpi.add_argument("--target", type=float, required=True)
    p_kpi.add_argument("--lower-is-better", action="store_true")
    p_kpi.add_argument("--theoretical-ceiling", type=float, default=None)
    p_kpi.add_argument("--lot", default="")
    p_kpi.add_argument("--changes-count", type=int, default=1)
    p_kpi.add_argument("--notes", default="")
    p_kpi.add_argument("--pmo-dir", default="")
    p_kpi.set_defaults(func=cmd_record_kpi)

    p_cr = sub.add_parser("record-clean-room", help="Certify a 100%-coverage isolated Clean-Room Audit to clear Circuit Breaker")
    p_cr.add_argument("--ledger-dir", required=True)
    p_cr.add_argument("--project-dir", required=True)
    p_cr.add_argument("--auditor-id", required=True)
    p_cr.add_argument("--files-read", required=True, help="Comma-separated paths or JSON file path listing read files")
    p_cr.add_argument("--probe-script", required=True)
    p_cr.add_argument("--probe-output", required=True)
    p_cr.add_argument("--findings-summary", required=True)
    p_cr.add_argument("--theoretical-ceiling", type=float, default=None)
    p_cr.add_argument("--isolated-zero-history", action="store_true")
    p_cr.add_argument("--pmo-dir", default="")
    p_cr.set_defaults(func=cmd_record_clean_room)

    p_st = sub.add_parser("status", help="Check live SHA-256 validity of all Aeronautical Gates & KPI RAG")
    p_st.add_argument("--ledger-dir", required=True)
    p_st.add_argument("--project-dir", default="")
    p_st.set_defaults(func=cmd_status)

    p_hk = sub.add_parser("install-hooks", help="Install physical PreToolUse firewall on a new project")
    p_hk.add_argument("--project-dir", required=True)
    p_hk.add_argument("--ledger-dir", required=True)
    p_hk.add_argument("--force", action="store_true")
    p_hk.set_defaults(func=cmd_install_hooks)

    p_an = sub.add_parser("render-anchor", help="Compile lossless primary-source CONTEXT_ANCHOR.md")
    p_an.add_argument("--ledger-dir", required=True)
    p_an.add_argument("--pmo-dir", default="")
    p_an.set_defaults(func=cmd_render_anchor)

    return p


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ns = build_parser().parse_args()
    raise SystemExit(ns.func(ns))
