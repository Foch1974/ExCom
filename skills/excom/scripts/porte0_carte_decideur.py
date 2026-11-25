#!/usr/bin/env python3
"""ExCom v3.2 — Gate 0: Universal Upfront Decision Matrix (en-US Visuals).

Evaluates strategic options, operational deliverables, or code fixes RIGHT AT ENTRY (Gate 0)
across BOTH `MODE = "CODE"` and `MODE = "METIER"` (Business/Legal/Tax/Real-Estate/Sourcing/Life).

Built-in Anti-Drift & Anti-Tunnel-Vision Locks (v3.2):
  - Clean-Room Circuit Breaker (EXCOM_V32_01):
      Reads `kpi_history.json` and `clean_room_audit_report.json` in `--ledger-dir`.
      If `consecutive_non_improving_runs >= 2` (plateau or regression loop) without a
      post-regression 100%-coverage isolated Clean-Room Audit registered on disk,
      Gate 0 HARD-BLOCKS (`exit 2`) incremental patching until a Clean-Room Audit runs.
  - 3-State Foundation Ceiling Gate (EXCOM_V32_02):
      1. `DEAD_FOUNDATION`      (`core_viability <= 0` or `theoretical_ceiling <= 0`): STOP/Redesign.
      2. `SUB_SCALE_FOUNDATION` (`0 < theoretical_ceiling < north_star_target`):
         Lifts any core-formula freeze, suspends viable-core-only dead-ends, and HARD-BLOCKS
         suicidal scaling/leverage band-aids on a sub-scale core.
      3. `VIABLE_FOUNDATION`    (`theoretical_ceiling >= north_star_target` or unconstrained > 0):
         Enforces strict Brakes-First order.
  - Anti-Self-Certification Evidence Bindings (EXCOM_V32_03):
      Verifies `evidence_bindings` mechanically on disk (`code` file:line token checks +
      `probe_json` key/value checks inside parsed `probe_output_path`), overriding LLM-claimed
      `fact_verified: true` whenever reality contradicts the claim.
  - Falsifiable, Scoped Dead-Ends (EXCOM_V32_04):
      Tags dead-ends as `ISOLATED_ABLATION` vs `CONFOUNDED_BUNDLE` (confounded failures emit
      a caution requiring isolated ablation rather than an eternal hard block), supports
      `validity_condition`, and exposes `reopen-dead-end` requiring a disk-verified counter-probe.
  - C4 Materiality (`>= 5%`) + Sovereign `🛑 STOP — DO NOT TOUCH` verdict.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple


ENGINE_VERSION = "3.2.0"

FOUNDATIONAL_KINDS: Set[str] = {
    # Software / Quant / Data foundational categories
    "PLUMBING_RUNTIME",
    "ACCOUNTING_DOUBLE_CHARGE",
    "EXECUTION_FRICTION",
    "UNIVERSE_WIRING",
    "DEAD_CODE_PURGE",
    "ABLATION_SIMPLIFICATION",
    "TEST_TWIN_PARITY",
    "SECURITY_HARDENING",
    "DATA_SCHEMA_FIX",
    # Business / Legal / Sourcing / Personal foundational categories
    "LEGAL_STATUTORY_FOUNDATION",
    "TAX_CASH_FOUNDATION",
    "CORE_VENDOR_QUALIFICATION",
    "OPERATIONAL_BOTTLENECK",
    "RISK_CONTINGENCY_SHIELD",
    "COMPLIANCE_MANDATORY",
    "MVP_CORE_SCOPE",
}

CORE_REDESIGN_KINDS: Set[str] = {
    "CORE_REDESIGN",
    "CORE_FORMULA",
    "SIGNAL_FORMULA",
    "NEW_ALPHA_OR_VALUE_DRIVER",
    "STRUCTURAL_ARCHITECTURE",
    "BUSINESS_MODEL_REDESIGN",
}

SUICIDAL_SCALING_KINDS: Set[str] = {
    "LEVERAGE_OR_SCALING_ON_CORE",
    "LEVERAGE_SCALING",
    "DEBT_OR_LEVERAGE_EXPANSION",
    "PREMATURE_SCALING",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_signature(text: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    stop = {"the", "and", "for", "with", "sur", "les", "des", "dans", "pour", "une", "par"}
    kept = [t for t in tokens if len(t) > 2 and t not in stop]
    return " ".join(sorted(set(kept))[:12])


def load_dead_ends(ledger_dir: Optional[Path]) -> Dict[str, Any]:
    if ledger_dir is None:
        return {"total_trials_count": 0, "dead_ends": []}
    fp = ledger_dir / "dead_ends_registry.json"
    if not fp.is_file():
        return {"total_trials_count": 0, "dead_ends": []}
    return json.loads(fp.read_text(encoding="utf-8"))


def save_dead_ends(ledger_dir: Path, data: Dict[str, Any]) -> Path:
    ledger_dir.mkdir(parents=True, exist_ok=True)
    fp = ledger_dir / "dead_ends_registry.json"
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return fp


def check_clean_room_circuit_breaker(ledger_dir: Optional[Path]) -> Dict[str, Any]:
    """EXCOM_V32_01: Blocks incremental Gate 0 patching on plateau/regression until Clean-Room Audit passes."""
    if ledger_dir is None:
        return {"blocked": False, "status": "NO_LEDGER_DIR", "details": ""}

    kpi_path = ledger_dir / "kpi_history.json"
    if not kpi_path.is_file():
        return {"blocked": False, "status": "NO_KPI_HISTORY", "details": ""}

    kpi = json.loads(kpi_path.read_text(encoding="utf-8"))
    consec = int(kpi.get("consecutive_non_improving_runs", 0))
    flagged = bool(kpi.get("clean_room_required", False))
    runs = kpi.get("runs", [])
    latest_run = runs[-1] if runs else {}
    latest_run_id = str(latest_run.get("run_id", ""))
    champion_id = str(kpi.get("champion_run_id", ""))
    champion_val = kpi.get("champion_value")
    latest_val = latest_run.get("value")
    metric_name = str(kpi.get("metric_name", "North-Star KPI"))

    needs_clean_room = flagged or (consec >= 2)
    if not needs_clean_room:
        return {
            "blocked": False,
            "status": "CLEAR",
            "consecutive_non_improving_runs": consec,
            "metric_name": metric_name,
            "champion_value": champion_val,
            "latest_value": latest_val,
            "details": "",
        }

    cr_path = ledger_dir / "clean_room_audit_report.json"
    if cr_path.is_file():
        cr = json.loads(cr_path.read_text(encoding="utf-8"))
        cr_cov = float(cr.get("coverage_pct", 0.0))
        cr_iso = bool(cr.get("isolated_zero_history", False))
        cr_run_id = str(cr.get("audited_after_run_id", ""))
        cr_probe = Path(str(cr.get("probe_output_path", "")))
        if cr_cov >= 100.0 and cr_iso and cr_run_id == latest_run_id and cr_probe.is_file():
            return {
                "blocked": False,
                "status": "CLEAN_ROOM_CERTIFIED",
                "consecutive_non_improving_runs": consec,
                "clean_room_audited_at": cr.get("recorded_at"),
                "details": f"Clean-Room Audit certified after run `{latest_run_id}` (100% file coverage).",
            }

    return {
        "blocked": True,
        "status": "BLOCKED_CLEAN_ROOM_REQUIRED",
        "consecutive_non_improving_runs": consec,
        "metric_name": metric_name,
        "champion_run_id": champion_id,
        "champion_value": champion_val,
        "latest_run_id": latest_run_id,
        "latest_value": latest_val,
        "details": (
            f"Plateau/Regression Circuit Breaker tripped: `{consec}` consecutive non-improving runs "
            f"on `{metric_name}` (champion `{champion_id}` = `{champion_val}` vs latest `{latest_run_id}` = `{latest_val}`). "
            f"Spawn an isolated zero-history Clean-Room auditor reading 100% of production files/deliverables "
            f"and certify via `zero_oubli_runner.py record-clean-room` before proposing further incremental fixes."
        ),
    }


def is_dead_end_suspended_by_subscale(de: Dict[str, Any], foundation_state: str) -> bool:
    """EXCOM_V32_04: Suspends dead-ends scoped strictly to viable-core freezes once core is proven sub-scale."""
    if foundation_state != "SUB_SCALE_FOUNDATION":
        return False
    scope = str(de.get("applies_only_when", "")).strip().upper()
    if scope == "VIABLE_FOUNDATION":
        return True
    cond = str(de.get("validity_condition", "")).lower()
    if any(k in cond for k in ("core_ceiling", "viable_foundation", "viable_core", "ceiling >= target", "signal_freeze")):
        return True
    # Backward-compatible check for legacy signal-freeze dead-ends when core ceiling is proven sub-scale
    key_and_title = f"{de.get('hypothesis_key', '')} {de.get('title', '')}".lower()
    if ("signal" in key_and_title or "formula" in key_and_title or "equation" in key_and_title) and (
        "freeze" in key_and_title or "record" in key_and_title or "c98" in key_and_title or "despite" in key_and_title
    ):
        return True
    return False


def match_dead_end(
    item: Dict[str, Any],
    dead_ends: List[Dict[str, Any]],
    foundation_state: str = "VIABLE_FOUNDATION",
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Returns (matched_entry, status_tag) where status_tag in {'ACTIVE_HARD', 'CONFOUNDED_CAUTION', 'SUSPENDED_SUBSCALE', None}."""
    item_key = str(item.get("hypothesis_key", "")).strip().lower()
    item_sig_tokens = set(normalize_signature(f"{item.get('title', '')} {item_key}").split())

    for de in dead_ends:
        if str(de.get("status", "ACTIVE")).upper() == "OVERTURNED":
            continue
        matched = False
        de_key = str(de.get("hypothesis_key", "")).strip().lower()
        if item_key and de_key and item_key == de_key:
            matched = True
        else:
            de_tokens = set(str(de.get("normalized_signature", "")).split())
            if len(item_sig_tokens) >= 3 and len(de_tokens) >= 3:
                overlap = len(item_sig_tokens & de_tokens) / max(1, min(len(item_sig_tokens), len(de_tokens)))
                if overlap >= 0.75:
                    matched = True

        if not matched:
            continue

        if is_dead_end_suspended_by_subscale(de, foundation_state):
            return de, "SUSPENDED_SUBSCALE"
        grade = str(de.get("evidence_grade", "ISOLATED_ABLATION")).strip().upper()
        if grade == "CONFOUNDED_BUNDLE":
            return de, "CONFOUNDED_CAUTION"
        return de, "ACTIVE_HARD"

    return None, None


def resolve_dotted_json_key(data: Any, dotted_key: str) -> Tuple[bool, Any]:
    cur = data
    for part in dotted_key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return False, None
        else:
            return False, None
    return (cur is not None), cur


def verify_evidence_bindings(
    item: Dict[str, Any],
    ctx: Dict[str, Any],
    probe_json_cache: Dict[str, Any],
    strict_bindings: bool,
) -> Tuple[bool, List[str]]:
    """EXCOM_V32_03: Programmatically verifies code file:line tokens and probe JSON keys on disk."""
    bindings = item.get("evidence_bindings", [])
    if not isinstance(bindings, list):
        return False, ["`evidence_bindings` must be a JSON list of binding objects."]

    kind = str(item.get("kind", "")).strip().upper()
    if strict_bindings and not bindings and bool(item.get("fact_verified", True)) and kind in (FOUNDATIONAL_KINDS | CORE_REDESIGN_KINDS):
        return False, ["Strict Anti-Self-Certification active: missing `evidence_bindings` (code or probe_json)."]

    if not bindings:
        return True, []

    project_dir_str = str(ctx.get("project_dir", "")).strip()
    project_dir = Path(project_dir_str).resolve() if project_dir_str else None
    default_probe_out = str(ctx.get("probe_output_path", "")).strip()
    errors: List[str] = []

    for idx, b in enumerate(bindings):
        if not isinstance(b, dict):
            errors.append(f"Binding #{idx + 1} is not an object.")
            continue
        btype = str(b.get("type", "")).strip().lower()

        if btype == "code":
            raw_f = str(b.get("file", "")).strip()
            if not raw_f:
                errors.append(f"Code binding #{idx + 1} missing `file`.")
                continue
            fp = Path(raw_f)
            if not fp.is_absolute() and project_dir is not None:
                fp = (project_dir / fp).resolve()
            if not fp.is_file():
                errors.append(f"Code binding #{idx + 1}: file not found on disk: `{fp}`")
                continue
            src_lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
            line_no = int(b.get("line", 1))
            window = int(b.get("window", 10))
            lo = max(0, line_no - 1 - window)
            hi = min(len(src_lines), line_no + window)
            snippet = "\n".join(src_lines[lo:hi])

            for tok in b.get("expected_tokens", []):
                if str(tok) not in snippet:
                    errors.append(
                        f"Code mismatch in `{fp.name}:L{line_no}±{window}`: expected token `{tok}` NOT FOUND in real file."
                    )
            for tok in b.get("forbidden_tokens", []):
                if str(tok) in snippet:
                    errors.append(
                        f"Code contradiction in `{fp.name}:L{line_no}±{window}`: forbidden token `{tok}` PRESENT in real file."
                    )

        elif btype == "probe_json":
            key = str(b.get("key", "")).strip()
            pf_str = str(b.get("file", default_probe_out)).strip()
            if not key or not pf_str:
                errors.append(f"Probe JSON binding #{idx + 1} missing `key` or probe output path.")
                continue
            pf = Path(pf_str)
            if not pf.is_file():
                errors.append(f"Probe JSON binding #{idx + 1}: file not found `{pf}`.")
                continue
            cache_key = str(pf.resolve())
            if cache_key not in probe_json_cache:
                try:
                    probe_json_cache[cache_key] = json.loads(pf.read_text(encoding="utf-8"))
                except Exception as exc:
                    errors.append(f"Probe JSON binding #{idx + 1}: invalid JSON in `{pf.name}` ({exc}).")
                    continue
            found, val = resolve_dotted_json_key(probe_json_cache[cache_key], key)
            if not found:
                errors.append(f"Probe JSON mismatch in `{pf.name}`: key `{key}` missing or null.")
                continue
            if "equals" in b and val != b["equals"]:
                errors.append(f"Probe JSON mismatch `{key}`: expected `{b['equals']}`, actual `{val}`.")
            if "min_val" in b:
                try:
                    if float(val) < float(b["min_val"]):
                        errors.append(f"Probe JSON bound failed `{key}`: actual `{val}` < min `{b['min_val']}`.")
                except (TypeError, ValueError):
                    errors.append(f"Probe JSON `{key}` is non-numeric (`{val}`) for `min_val` check.")
            if "max_val" in b:
                try:
                    if float(val) > float(b["max_val"]):
                        errors.append(f"Probe JSON bound failed `{key}`: actual `{val}` > max `{b['max_val']}`.")
                except (TypeError, ValueError):
                    errors.append(f"Probe JSON `{key}` is non-numeric (`{val}`) for `max_val` check.")
        else:
            errors.append(f"Unsupported binding type `{btype}` (use `code` or `probe_json`).")

    return (len(errors) == 0), errors


def validate_structured_sources(raw_sources: List[Any]) -> Tuple[bool, int, List[str]]:
    """ADD_03: Enforces dated, traceable provenance objects in METIER mode."""
    valid_count = 0
    errors: List[str] = []
    for idx, src in enumerate(raw_sources):
        if not isinstance(src, dict):
            errors.append(f"Source #{idx + 1} is a bare string; must be an object with ref, url_or_file, date, verbatim_excerpt.")
            continue
        ref = str(src.get("ref", "")).strip()
        loc = str(src.get("url_or_file", "")).strip()
        date_s = str(src.get("date", "")).strip()
        excerpt = str(src.get("verbatim_excerpt", "")).strip()
        if not (ref and loc and len(date_s) >= 7 and len(excerpt) >= 8):
            errors.append(f"Source '{ref or idx + 1}' missing mandatory field (ref, url_or_file, YYYY-MM-DD date, or verbatim_excerpt).")
            continue
        if not loc.startswith(("http://", "https://", "statute:")) and not Path(loc).exists():
            errors.append(f"Local source file does not exist on disk: {loc}")
            continue
        valid_count += 1
    return (valid_count >= 1 and len(errors) == 0), valid_count, errors


def classify_foundation_state(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """EXCOM_V32_02: 3-state physical foundation ceiling classification."""
    core_viab = float(ctx.get("core_viability_at_zero_friction", 1.0))
    ns_target = ctx.get("north_star_target")
    theo_ceil = ctx.get("theoretical_zero_friction_ceiling")
    metric_label = str(ctx.get("north_star_metric_name", "North-Star Metric"))

    ns_target_f = float(ns_target) if ns_target is not None else None
    theo_ceil_f = float(theo_ceil) if theo_ceil is not None else None

    if core_viab <= 0.0 or (theo_ceil_f is not None and theo_ceil_f <= 0.0):
        state = "DEAD_FOUNDATION"
    elif ns_target_f is not None and theo_ceil_f is not None and theo_ceil_f < ns_target_f:
        state = "SUB_SCALE_FOUNDATION"
    else:
        state = "VIABLE_FOUNDATION"

    return {
        "foundation_state": state,
        "core_viability": core_viab,
        "north_star_metric_name": metric_label,
        "north_star_target": ns_target_f,
        "theoretical_zero_friction_ceiling": theo_ceil_f,
        "latest_kpi_value": float(ctx["latest_kpi_value"]) if ctx.get("latest_kpi_value") is not None else None,
    }


def verify_mode_evidence(payload: Dict[str, Any]) -> Dict[str, Any]:
    mode = str(payload.get("mode", "CODE")).strip().upper()
    ctx = payload.get("context", {}) or {}
    f_info = classify_foundation_state(ctx)

    if mode == "CODE":
        p_script = Path(str(ctx.get("probe_script_path", "")))
        p_out = Path(str(ctx.get("probe_output_path", "")))
        disk_ok = (
            bool(str(ctx.get("probe_script_path", "")).strip())
            and bool(str(ctx.get("probe_output_path", "")).strip())
            and p_script.is_file()
            and p_out.is_file()
            and p_out.stat().st_size > 10
        )
        json_parse_err = ""
        if disk_ok and p_out.suffix.lower() == ".json":
            try:
                parsed = json.loads(p_out.read_text(encoding="utf-8"))
                if not parsed:
                    disk_ok = False
                    json_parse_err = f"Probe JSON `{p_out.name}` is empty."
            except Exception as exc:
                disk_ok = False
                json_parse_err = f"Probe JSON `{p_out.name}` failed to parse: {exc}"

        total_gap = abs(float(ctx.get("total_observed_gap", 0.0)))
        measured = ctx.get("measured_components", [])
        explained = sum(abs(float(m.get("measured_impact", 0.0))) for m in measured)
        explained_pct = round((explained / total_gap) * 100.0, 1) if total_gap > 1e-9 else 100.0
        return {
            "mode": "CODE",
            "evidence_ok": disk_ok and (explained_pct >= 80.0 or total_gap <= 1e-9),
            "disk_ok": disk_ok,
            "explained_pct": explained_pct,
            "source_errors": [json_parse_err] if json_parse_err else [],
            **f_info,
        }

    # MODE == "METIER" (ADD_03 strict provenance check)
    raw_sources = ctx.get("verified_sources", [])
    src_ok, valid_n, src_errors = validate_structured_sources(raw_sources)
    calc_script_str = str(ctx.get("calc_script_path", "")).strip()
    calc_out_str = str(ctx.get("calc_output_path", "")).strip()
    requires_calc = bool(ctx.get("requires_financial_calc", False))
    calc_ok = True
    if requires_calc:
        calc_ok = (
            bool(calc_script_str)
            and bool(calc_out_str)
            and Path(calc_script_str).is_file()
            and Path(calc_out_str).is_file()
            and Path(calc_out_str).stat().st_size > 5
        )
        if not calc_ok:
            src_errors.append("Zero-Mental-Math violation: `requires_financial_calc` is true, but `calc_script_path` or `calc_output_path` is missing on disk.")

    return {
        "mode": "METIER",
        "evidence_ok": src_ok and calc_ok,
        "sources_count": valid_n,
        "calc_ok": calc_ok,
        "explained_pct": 100.0,
        "source_errors": src_errors,
        **f_info,
    }


def evaluate_item(
    item: Dict[str, Any],
    ctx: Dict[str, Any],
    ev: Dict[str, Any],
    dead_ends: List[Dict[str, Any]],
    probe_json_cache: Dict[str, Any],
    strict_bindings: bool,
) -> Dict[str, Any]:
    kind = str(item.get("kind", "SECONDARY_OPTIMIZATION")).strip().upper()
    has_brakes = bool(ctx.get("unresolved_foundational_brakes", False))
    f_state = ev["foundation_state"]

    # ADD_03 per-item optional calc script check
    item_calc_ok = True
    if bool(item.get("requires_script_calc", False)):
        cs = str(item.get("calc_script_path", ctx.get("calc_script_path", ""))).strip()
        item_calc_ok = bool(cs) and Path(cs).is_file()

    # EXCOM_V32_03 programmatic evidence bindings verification (overrides LLM self-certification!)
    bindings_ok, binding_errors = verify_evidence_bindings(item, ctx, probe_json_cache, strict_bindings)

    item_fact_ok = bool(item.get("fact_verified", True)) and ev["evidence_ok"] and item_calc_ok and bindings_ok
    touches_healthy = bool(item.get("touches_healthy_brick", item.get("touches_already_positive_signal", False)))
    # EXCOM_V32_02: When foundation is proven SUB_SCALE, redesigning core is explicitly authorized!
    if f_state == "SUB_SCALE_FOUNDATION" and kind in CORE_REDESIGN_KINDS:
        touches_healthy = False

    plain_why = str(item.get("plain_sentence", item.get("plain_economic_sentence", ""))).strip()
    new_params = int(item.get("new_free_parameters_or_layers", item.get("new_free_parameters", 0)))
    wishful_tuning = bool(item.get("post_hoc_or_wishful_tuning", item.get("post_hoc_window_tuning", False)))

    # EXCOM_V32_02: Block suicidal leverage/scaling on a sub-scale core
    suicidal_scaling = (
        f_state == "SUB_SCALE_FOUNDATION"
        and (kind in SUICIDAL_SCALING_KINDS or bool(item.get("amplifies_subscale_core", False)))
    )

    # EXCOM_V32_04: Scoped & Falsifiable Dead-End check
    prior_dead_end, de_status = match_dead_end(item, dead_ends, foundation_state=f_state)
    hard_de_block = (de_status == "ACTIVE_HARD")
    confounded_de_caution = (de_status == "CONFOUNDED_CAUTION")
    isolated_ablation_plan = bool(item.get("isolated_ablation_plan", False))

    stake_pct = float(item.get("estimated_stake_pct", item.get("estimated_stake_ratio_pct", 0.0)))
    blocks_gate = bool(item.get("blocks_critical_gate", item.get("blocks_mandatory_gate", False)))

    c1_ok = item_fact_ok and not touches_healthy
    if suicidal_scaling:
        c2_ok = False
    elif f_state == "SUB_SCALE_FOUNDATION" and kind in CORE_REDESIGN_KINDS:
        c2_ok = True
    else:
        c2_ok = False if (has_brakes and kind not in FOUNDATIONAL_KINDS) else True

    c3_ok = (new_params == 0) and (not wishful_tuning) and (len(plain_why) >= 15) and (not hard_de_block)
    c4_ok = (stake_pct >= 5.0) or blocks_gate

    if hard_de_block and prior_dead_end is not None:
        verdict = f"❌ BLOCKED (DEAD-END {prior_dead_end.get('rejected_on', '')})"
    elif suicidal_scaling:
        verdict = "❌ BLOCKED (SUICIDAL SCALING ON SUB-SCALE CORE)"
    elif not bindings_ok:
        verdict = "❌ BLOCKED (EVIDENCE BINDING MISMATCH)"
    elif not c1_ok or not c2_ok or not c3_ok:
        verdict = "❌ OVERKILL / BLOCKED"
    elif confounded_de_caution and not isolated_ablation_plan:
        verdict = "⚠️ CAUTION (PRIOR FAILURE CONFOUNDED — ISOLATE 1 CHANGE)"
    elif c4_ok:
        verdict = "✅ VALIDATED & CRITICAL"
    else:
        verdict = "⚠️ VALIDATED — MINOR"

    return {
        "id": str(item.get("id", "ITEM_?")),
        "hypothesis_key": str(item.get("hypothesis_key", "")),
        "title": str(item.get("title", "")),
        "kind": kind,
        "lot": str(item.get("lot", "Lot 1")),
        "gate": str(item.get("gate", "P1")),
        "owner_seat": str(item.get("owner_seat", "PMO")),
        "c1": "✅" if c1_ok else "❌",
        "c2": "✅" if c2_ok else "❌",
        "c3": "✅" if c3_ok else ("⚠️" if confounded_de_caution else "❌"),
        "c4": "✅" if c4_ok else "⚠️",
        "stake_pct": stake_pct,
        "stake_label": str(item.get("stake_label", f"{stake_pct:.1f}% stake")),
        "plain_why": plain_why,
        "dead_end_hit": prior_dead_end,
        "dead_end_status": de_status,
        "binding_errors": binding_errors,
        "verdict": verdict,
        "raw": item,
    }


def cmd_evaluate(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    project = str(payload.get("project", "Project"))
    domain = str(payload.get("domain", "CUSTOM_PROJECT"))
    ctx = payload.get("context", {}) or {}
    ledger_dir = Path(args.ledger_dir).resolve() if args.ledger_dir else None
    strict_bindings = bool(args.strict_bindings or ctx.get("strict_bindings", False))

    # EXCOM_V32_01: Check Clean-Room Circuit Breaker BEFORE allowing any incremental Gate 0 pass!
    breaker = check_clean_room_circuit_breaker(ledger_dir)
    lines: List[str] = [
        f"## Gate 0 — Executive Decision Matrix (`{project}` · `{str(payload.get('mode', 'CODE')).upper()}` · `{domain}`)",
        "",
    ]
    if breaker["blocked"]:
        lines.append("> **❌ BLOCKED AT GATE 0 (PLATEAU / REGRESSION CIRCUIT BREAKER — CLEAN-ROOM AUDIT REQUIRED)**")
        lines.append(f"> {breaker['details']}")
        lines.append("> *Incremental patching is physically halted until an isolated Clean-Room auditor certifies 100% file coverage via `zero_oubli_runner.py record-clean-room`.*")
        print("\n".join(lines))
        return 2

    de_store = load_dead_ends(ledger_dir)
    if ledger_dir is not None:
        de_store["total_trials_count"] = int(de_store.get("total_trials_count", 0)) + 1

    ev = verify_mode_evidence(payload)

    if ev["mode"] == "CODE" and not ev["disk_ok"]:
        lines.append("> **❌ BLOCKED AT GATE 0 (MISSING OR INVALID DISK PROBE)** : Probe script or output file is missing/corrupt on disk. Blind code speculation is strictly prohibited.")
        for err in ev["source_errors"]:
            lines.append(f"> - {err}")
        print("\n".join(lines))
        return 2

    if ev["mode"] == "CODE" and ev["explained_pct"] < 80.0:
        lines.append(f"> **❌ BLOCKED AT GATE 0 (INCOMPLETE AUTOPSY: `{ev['explained_pct']}%` < `80%`)** : Root cause is not sufficiently isolated. Refine telemetry before proposing fixes.")
        print("\n".join(lines))
        return 2

    if ev["mode"] == "METIER" and not ev["evidence_ok"]:
        lines.append("> **❌ BLOCKED AT GATE 0 (UNVERIFIED PROVENANCE OR MENTAL MATH)** :")
        for err in ev["source_errors"]:
            lines.append(f"> - {err}")
        print("\n".join(lines))
        return 2

    if ev["foundation_state"] == "DEAD_FOUNDATION":
        lines.append(
            f"> **🛑 DEAD FOUNDATION AT ZERO FRICTION (`viability = {ev['core_viability']} <= 0`)** : "
            "The core engine fails even before costs/frictions. **Band-aids prohibited** — choose **Ablation (Delete)** or **Ground-Up Redesign**."
        )
        print("\n".join(lines))
        return 0

    probe_json_cache: Dict[str, Any] = {}
    proposals = payload.get("proposals", [])
    rows = [
        evaluate_item(it, ctx, ev, de_store.get("dead_ends", []), probe_json_cache, strict_bindings)
        for it in proposals
    ]

    # Auto-bury newly rejected non-dead-end items if requested (`--auto-record-rejected`)
    if ledger_dir is not None:
        if args.auto_record_rejected:
            existing_sigs = {
                d.get("normalized_signature")
                for d in de_store.get("dead_ends", [])
                if str(d.get("status", "ACTIVE")).upper() != "OVERTURNED"
            }
            for r in rows:
                if r["verdict"] in ("❌ OVERKILL / BLOCKED", "❌ BLOCKED (SUICIDAL SCALING ON SUB-SCALE CORE)"):
                    sig = normalize_signature(f"{r['title']} {r['hypothesis_key']}")
                    if sig and sig not in existing_sigs:
                        de_store.setdefault("dead_ends", []).append({
                            "id": f"DE-{hashlib.sha256(sig.encode('utf-8')).hexdigest()[:6].upper()}",
                            "status": "ACTIVE",
                            "evidence_grade": "ISOLATED_ABLATION",
                            "rejected_on": dt.date.today().isoformat(),
                            "hypothesis_key": r["hypothesis_key"] or r["id"],
                            "title": r["title"],
                            "normalized_signature": sig,
                            "validity_condition": str(r["raw"].get("validity_condition", "")),
                            "failure_reason": r["plain_why"],
                        })
                        existing_sigs.add(sig)
        save_dead_ends(ledger_dir, de_store)

    has_brakes = bool(ctx.get("unresolved_foundational_brakes", False))
    max_stake = max([r["stake_pct"] for r in rows], default=0.0)
    any_crit_gate = any(bool(it.get("blocks_critical_gate", it.get("blocks_mandatory_gate", False))) for it in proposals)

    if not has_brakes and ev["foundation_state"] == "VIABLE_FOUNDATION" and max_stake < 5.0 and not any_crit_gate:
        lines.append(
            f"> **🛑 SOVEREIGN VERDICT: STOP — DO NOT TOUCH** (`max residual stake = {max_stake:.1f}% < 5.0%`, "
            f"`0` open foundational brake, `N_trials = {de_store.get('total_trials_count', 1)}`)."
        )
        lines.append("> *Any further tweak at this stage introduces overfitting or unnecessary structural bloat.*")
        print("\n".join(lines))
        return 0

    n_go = sum(1 for r in rows if r["verdict"].startswith("✅"))
    n_opt = sum(1 for r in rows if r["verdict"].startswith("⚠️"))
    n_no = sum(1 for r in rows if r["verdict"].startswith("❌"))
    note = str(ctx.get("summary_note", "")).strip()

    if ev["foundation_state"] == "SUB_SCALE_FOUNDATION":
        lines.append(
            f"> **⚠️ SUB-SCALE FOUNDATION DETECTED (`{ev['north_star_metric_name']}` theoretical zero-friction ceiling = "
            f"`{ev['theoretical_zero_friction_ceiling']}` < North-Star target = `{ev['north_star_target']}`)** : "
            "Core engine is positive (`> 0`) but structurally incapable of reaching the target via plumbing tweaks alone. "
            "**Core redesign is unlocked; suicidal scaling/leverage on this core is hard-blocked.**"
        )
        lines.append("")

    if ev["north_star_target"] is not None and ev["latest_kpi_value"] is not None:
        lines.append(
            f"- **North-Star Gap (`{ev['north_star_metric_name']}`)** : "
            f"Latest = `{ev['latest_kpi_value']}` vs Target = `{ev['north_star_target']}` "
            f"· **Foundation State** : `{ev['foundation_state']}`"
        )

    active_de_count = sum(1 for d in de_store.get("dead_ends", []) if str(d.get("status", "ACTIVE")).upper() != "OVERTURNED")
    lines.append(
        f"- **Gate 0 Summary** : `{n_go}` ✅ Critical | `{n_opt}` ⚠️ Minor/Caution | `{n_no}` ❌ Blocked "
        f"· **Trials Counter (`N_trials`)** : `{de_store.get('total_trials_count', 1)}` "
        f"· **Active Dead-Ends** : `{active_de_count}` "
        f"· **Strict Evidence Bindings** : `{strict_bindings}`"
    )
    lines.append(f"- **Active Foundational Brakes** : `{has_brakes}`" + (f" — {note}" if note else ""))

    # Strawman padding transparency check
    blocked_rows = [r for r in rows if r["verdict"].startswith("❌")]
    if blocked_rows and all(r["dead_end_status"] == "ACTIVE_HARD" for r in blocked_rows):
        lines.append("- **Audit Note** : All `❌` rows matched previously buried dead-ends (verify fresh counter-hypotheses were also stress-tested).")

    invariants = payload.get("project_invariants", [])
    if invariants:
        lines.append("- **Project Invariants (Locked at Lot 0 on Go)** : " + " · ".join(f"`{inv}`" for inv in invariants))
    lines.append("")
    lines.append("| ID | Lot / Gate | Proposal & Rationale | `C1` Proof | `C2` Brakes First | `C3` Zero Bloat | `C4` Stake | Impact | Gate 0 Verdict |")
    lines.append("| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :--- | :--- |")
    for r in rows:
        extra_notes: List[str] = []
        if r["binding_errors"]:
            extra_notes.append(f"**[Binding Error: {'; '.join(r['binding_errors'])}]**")
        if r["dead_end_hit"] is not None:
            tag = r["dead_end_status"]
            de_reason = r["dead_end_hit"].get("failure_reason", "")
            if tag == "ACTIVE_HARD":
                extra_notes.append(f"**[Dead-End Hit ({r['dead_end_hit'].get('id')}): {de_reason}]**")
            elif tag == "CONFOUNDED_CAUTION":
                extra_notes.append(f"**[Confounded Prior Failure ({r['dead_end_hit'].get('id')}): isolate 1 change at a time — {de_reason}]**")
            elif tag == "SUSPENDED_SUBSCALE":
                extra_notes.append(f"**[Dead-End {r['dead_end_hit'].get('id')} Suspended: Foundation proven SUB-SCALE]**")
        extra_html = ("<br>" + "<br>".join(extra_notes)) if extra_notes else ""
        lines.append(
            f"| **`{r['id']}`** | `{r['lot']}` (`{r['gate']}`) | **{r['title']}** *[{r['owner_seat']}]*<br>*({r['plain_why']})*{extra_html} | "
            f"{r['c1']} | {r['c2']} | {r['c3']} | {r['c4']} | `{r['stake_label']}` | **{r['verdict']}** |"
        )

    print("\n".join(lines))
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({
                "engine_version": ENGINE_VERSION,
                "project": project,
                "mode": ev["mode"],
                "domain": domain,
                "foundation_state": ev["foundation_state"],
                "n_trials": de_store.get("total_trials_count", 1),
                "verdict_global": "ARBITRATION_READY",
                "project_invariants": invariants,
                "rows": rows,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return 0


def cmd_record_dead_end(args: argparse.Namespace) -> int:
    ledger_dir = Path(args.ledger_dir).resolve()
    de_store = load_dead_ends(ledger_dir)
    sig = normalize_signature(f"{args.title} {args.key}")
    grade = str(args.evidence_grade).strip().upper()
    entry = {
        "id": f"DE-{hashlib.sha256(sig.encode('utf-8')).hexdigest()[:6].upper()}",
        "status": "ACTIVE",
        "evidence_grade": grade,
        "rejected_on": dt.date.today().isoformat(),
        "hypothesis_key": args.key,
        "title": args.title,
        "normalized_signature": sig,
        "validity_condition": args.validity_condition,
        "applies_only_when": str(args.applies_only_when).strip().upper(),
        "failure_reason": args.reason,
        "evidence_metric": args.metric,
    }
    de_store.setdefault("dead_ends", []).append(entry)
    out = save_dead_ends(ledger_dir, de_store)
    status_lbl = "CONFOUNDED_CAUTION_RECORDED" if grade == "CONFOUNDED_BUNDLE" else "DEAD_END_BURIED_SCOPED"
    print(json.dumps({"status": status_lbl, "registry": str(out), "entry": entry}, ensure_ascii=False, indent=2))
    return 0


def cmd_reopen_dead_end(args: argparse.Namespace) -> int:
    """EXCOM_V32_04: Overturns a buried dead-end strictly upon disk-verified counter-evidence."""
    ledger_dir = Path(args.ledger_dir).resolve()
    counter_probe = Path(args.counter_probe_path).resolve()
    if not counter_probe.is_file() or counter_probe.stat().st_size <= 10:
        sys.exit(f"Reopen Denied: counter-probe file missing or empty on disk: {counter_probe}")

    de_store = load_dead_ends(ledger_dir)
    target_id = str(args.id).strip().upper()
    matched = None
    for de in de_store.get("dead_ends", []):
        if str(de.get("id", "")).strip().upper() == target_id:
            matched = de
            break
    if matched is None:
        sys.exit(f"Reopen Error: dead-end ID `{target_id}` not found in {ledger_dir / 'dead_ends_registry.json'}")

    matched["status"] = "OVERTURNED"
    matched["overturned_at"] = now_iso()
    matched["overturned_reason"] = args.reason
    matched["counter_probe_path"] = str(counter_probe)
    matched["counter_probe_sha256"] = file_sha256(counter_probe)

    out = save_dead_ends(ledger_dir, de_store)
    print(json.dumps({
        "status": "DEAD_END_OVERTURNED_WITH_COUNTER_PROOF",
        "registry": str(out),
        "entry": matched,
    }, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ExCom v3.2 — Gate 0 Decision Matrix, Evidence Binding & Anti-Dogma CLI")
    sub = p.add_subparsers(dest="cmd")

    p_eval = sub.add_parser("evaluate", help="Evaluate Gate 0 Decision Matrix")
    p_eval.add_argument("--input", required=True)
    p_eval.add_argument("--ledger-dir", default="")
    p_eval.add_argument("--json-out", default="")
    p_eval.add_argument("--auto-record-rejected", action="store_true")
    p_eval.add_argument("--strict-bindings", action="store_true", help="Require programmatic evidence_bindings on foundational/core proposals")
    p_eval.set_defaults(func=cmd_evaluate)

    p_de = sub.add_parser("record-dead-end", help="Record a failed hypothesis (isolated dead-end or confounded caution)")
    p_de.add_argument("--ledger-dir", required=True)
    p_de.add_argument("--key", required=True)
    p_de.add_argument("--title", required=True)
    p_de.add_argument("--reason", required=True)
    p_de.add_argument("--metric", default="")
    p_de.add_argument("--evidence-grade", choices=["ISOLATED_ABLATION", "CONFOUNDED_BUNDLE"], default="ISOLATED_ABLATION")
    p_de.add_argument("--validity-condition", default="", help="Condition under which this dead-end remains valid")
    p_de.add_argument("--applies-only-when", default="", help="Optional scope: VIABLE_FOUNDATION or empty for always")
    p_de.set_defaults(func=cmd_record_dead_end)

    p_ro = sub.add_parser("reopen-dead-end", help="Overturn a previously buried dead-end using a disk-verified counter-probe")
    p_ro.add_argument("--ledger-dir", required=True)
    p_ro.add_argument("--id", required=True, help="Dead-end ID (e.g. DE-3B3758)")
    p_ro.add_argument("--reason", required=True)
    p_ro.add_argument("--counter-probe-path", required=True, help="Path to disk-verified counter-evidence probe output")
    p_ro.set_defaults(func=cmd_reopen_dead_end)

    return p


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    argv = sys.argv[1:]
    if argv and argv[0].startswith("--"):
        argv = ["evaluate", *argv]
    ns = build_parser().parse_args(argv)
    if not getattr(ns, "cmd", None):
        build_parser().print_help()
        raise SystemExit(1)
    raise SystemExit(ns.func(ns))
