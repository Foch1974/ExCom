#!/usr/bin/env python3
"""ExCom v3.1 — Gate 0: Universal Upfront Decision Matrix (en-US Visuals).

Evaluates strategic options, operational deliverables, or code fixes RIGHT AT ENTRY (Gate 0)
across BOTH `MODE = "CODE"` and `MODE = "METIER"` (Business/Legal/Tax/Real-Estate/Sourcing/Life).

Built-in Anti-Drift Locks:
  - C1 (Verified Proof & Zero Mental Math — ADD_03):
      * CODE mode   : Requires disk-verified probe script + output explaining >= 80% of gap.
      * METIER mode : Requires structured provenance sources (`ref`, `url_or_file`, `date`,
                      `verbatim_excerpt`) + disk-verified `calc_script_path` whenever quantitative
                      financial projections (`requires_script_calc: true`) are claimed.
  - C2 (Foundations & Brakes First): Blocks secondary/exotic tweaks while core brakes remain open.
  - C3 (Zero Bloat & Dead-End Anti-Loop — ADD_02): 0 arbitrary free params/layers, plain 1-sentence
      rationale, AND cross-checks persistent `dead_ends_registry.json` to block recycled failures
      across sessions while tracking cumulative `N_trials`.
  - C4 (Materiality >= 5%): Distinguishes critical high-impact moves from minor optional hygiene.
  - 🛑 STOP Verdict: Halts further iterations when core brakes are clear and residual stake < 5%.
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


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


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


def match_dead_end(item: Dict[str, Any], dead_ends: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    item_key = str(item.get("hypothesis_key", "")).strip().lower()
    item_sig_tokens = set(normalize_signature(f"{item.get('title', '')} {item_key}").split())

    for de in dead_ends:
        de_key = str(de.get("hypothesis_key", "")).strip().lower()
        if item_key and de_key and item_key == de_key:
            return de
        de_tokens = set(str(de.get("normalized_signature", "")).split())
        if len(item_sig_tokens) >= 3 and len(de_tokens) >= 3:
            overlap = len(item_sig_tokens & de_tokens) / max(1, min(len(item_sig_tokens), len(de_tokens)))
            if overlap >= 0.75:
                return de
    return None


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


def verify_mode_evidence(payload: Dict[str, Any]) -> Dict[str, Any]:
    mode = str(payload.get("mode", "CODE")).strip().upper()
    ctx = payload.get("context", {}) or {}

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
        total_gap = abs(float(ctx.get("total_observed_gap", 0.0)))
        measured = ctx.get("measured_components", [])
        explained = sum(abs(float(m.get("measured_impact", 0.0))) for m in measured)
        explained_pct = round((explained / total_gap) * 100.0, 1) if total_gap > 1e-9 else 100.0
        core_viability = float(ctx.get("core_viability_at_zero_friction", 1.0))
        return {
            "mode": "CODE",
            "evidence_ok": disk_ok and (explained_pct >= 80.0 or total_gap <= 1e-9),
            "disk_ok": disk_ok,
            "explained_pct": explained_pct,
            "core_viability": core_viability,
            "source_errors": [],
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
        "core_viability": float(ctx.get("core_viability_at_zero_friction", 1.0)),
        "source_errors": src_errors,
    }


def evaluate_item(
    item: Dict[str, Any],
    ctx: Dict[str, Any],
    ev: Dict[str, Any],
    dead_ends: List[Dict[str, Any]],
) -> Dict[str, Any]:
    kind = str(item.get("kind", "SECONDARY_OPTIMIZATION")).strip().upper()
    has_brakes = bool(ctx.get("unresolved_foundational_brakes", False))

    # ADD_03 per-item optional calc script check
    item_calc_ok = True
    if bool(item.get("requires_script_calc", False)):
        cs = str(item.get("calc_script_path", ctx.get("calc_script_path", ""))).strip()
        item_calc_ok = bool(cs) and Path(cs).is_file()

    item_fact_ok = bool(item.get("fact_verified", True)) and ev["evidence_ok"] and item_calc_ok
    touches_healthy = bool(item.get("touches_healthy_brick", item.get("touches_already_positive_signal", False)))
    plain_why = str(item.get("plain_sentence", item.get("plain_economic_sentence", ""))).strip()
    new_params = int(item.get("new_free_parameters_or_layers", item.get("new_free_parameters", 0)))
    wishful_tuning = bool(item.get("post_hoc_or_wishful_tuning", item.get("post_hoc_window_tuning", False)))

    # ADD_02 Dead-End Graveyard match
    prior_dead_end = match_dead_end(item, dead_ends)

    stake_pct = float(item.get("estimated_stake_pct", item.get("estimated_stake_ratio_pct", 0.0)))
    blocks_gate = bool(item.get("blocks_critical_gate", item.get("blocks_mandatory_gate", False)))

    c1_ok = item_fact_ok and not touches_healthy
    c2_ok = False if (has_brakes and kind not in FOUNDATIONAL_KINDS) else True
    c3_ok = (new_params == 0) and (not wishful_tuning) and (len(plain_why) >= 15) and (prior_dead_end is None)
    c4_ok = (stake_pct >= 5.0) or blocks_gate

    if prior_dead_end is not None:
        verdict = f"❌ BLOCKED (DEAD-END {prior_dead_end.get('rejected_on', '')})"
    elif not c1_ok or not c2_ok or not c3_ok:
        verdict = "❌ OVERKILL / BLOCKED"
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
        "c3": "✅" if c3_ok else "❌",
        "c4": "✅" if c4_ok else "⚠️",
        "stake_pct": stake_pct,
        "stake_label": str(item.get("stake_label", f"{stake_pct:.1f}% stake")),
        "plain_why": plain_why,
        "dead_end_hit": prior_dead_end,
        "verdict": verdict,
        "raw": item,
    }


def cmd_evaluate(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    project = str(payload.get("project", "Project"))
    domain = str(payload.get("domain", "CUSTOM_PROJECT"))
    ctx = payload.get("context", {}) or {}
    ledger_dir = Path(args.ledger_dir).resolve() if args.ledger_dir else None

    de_store = load_dead_ends(ledger_dir)
    if ledger_dir is not None:
        de_store["total_trials_count"] = int(de_store.get("total_trials_count", 0)) + 1

    ev = verify_mode_evidence(payload)
    lines: List[str] = [
        f"## Gate 0 — Executive Decision Matrix (`{project}` · `{ev['mode']}` · `{domain}`)",
        "",
    ]

    if ev["mode"] == "CODE" and not ev["disk_ok"]:
        lines.append("> **❌ BLOCKED AT GATE 0 (MISSING DISK PROBE)** : Probe script or output file is missing on disk. Blind code speculation is strictly prohibited.")
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

    if ev["core_viability"] <= 0.0:
        lines.append(f"> **🛑 DEAD FOUNDATION AT ZERO FRICTION (`viability = {ev['core_viability']} <= 0`)** : The core engine fails even before costs/frictions. **Band-aids prohibited** — choose **Ablation (Delete)** or **Ground-Up Redesign**.")
        print("\n".join(lines))
        return 0

    proposals = payload.get("proposals", [])
    rows = [evaluate_item(it, ctx, ev, de_store.get("dead_ends", [])) for it in proposals]

    # Auto-bury newly rejected non-dead-end items if requested (`--auto-record-rejected`)
    if ledger_dir is not None:
        if args.auto_record_rejected:
            existing_sigs = {d.get("normalized_signature") for d in de_store.get("dead_ends", [])}
            for r in rows:
                if r["verdict"] == "❌ OVERKILL / BLOCKED":
                    sig = normalize_signature(f"{r['title']} {r['hypothesis_key']}")
                    if sig and sig not in existing_sigs:
                        de_store.setdefault("dead_ends", []).append({
                            "id": f"DE-{hashlib.sha256(sig.encode('utf-8')).hexdigest()[:6].upper()}",
                            "rejected_on": dt.date.today().isoformat(),
                            "hypothesis_key": r["hypothesis_key"] or r["id"],
                            "title": r["title"],
                            "normalized_signature": sig,
                            "failure_reason": r["plain_why"],
                        })
                        existing_sigs.add(sig)
        save_dead_ends(ledger_dir, de_store)

    has_brakes = bool(ctx.get("unresolved_foundational_brakes", False))
    max_stake = max([r["stake_pct"] for r in rows], default=0.0)
    any_crit_gate = any(bool(it.get("blocks_critical_gate", it.get("blocks_mandatory_gate", False))) for it in proposals)

    if not has_brakes and max_stake < 5.0 and not any_crit_gate:
        lines.append(f"> **🛑 SOVEREIGN VERDICT: STOP — DO NOT TOUCH** (`max residual stake = {max_stake:.1f}% < 5.0%`, `0` open foundational brake, `N_trials = {de_store.get('total_trials_count', 1)}`).")
        lines.append("> *Any further tweak at this stage introduces overfitting or unnecessary structural bloat.*")
        print("\n".join(lines))
        return 0

    n_go = sum(1 for r in rows if r["verdict"].startswith("✅"))
    n_opt = sum(1 for r in rows if r["verdict"].startswith("⚠️"))
    n_no = sum(1 for r in rows if r["verdict"].startswith("❌"))
    note = str(ctx.get("summary_note", "")).strip()

    lines.append(
        f"- **Gate 0 Summary** : `{n_go}` ✅ Critical | `{n_opt}` ⚠️ Minor | `{n_no}` ❌ Blocked "
        f"· **Trials Counter (`N_trials`)** : `{de_store.get('total_trials_count', 1)}` "
        f"· **Buried Dead-Ends** : `{len(de_store.get('dead_ends', []))}`"
    )
    lines.append(f"- **Active Foundational Brakes** : `{has_brakes}`" + (f" — {note}" if note else ""))

    invariants = payload.get("project_invariants", [])
    if invariants:
        lines.append("- **Project Invariants (Locked at Lot 0 on Go)** : " + " · ".join(f"`{inv}`" for inv in invariants))
    lines.append("")
    lines.append("| ID | Lot / Gate | Proposal & Rationale | `C1` Proof | `C2` Brakes First | `C3` Zero Bloat | `C4` Stake | Impact | Gate 0 Verdict |")
    lines.append("| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :--- | :--- |")
    for r in rows:
        de_note = ""
        if r["dead_end_hit"] is not None:
            de_note = f"<br>**[Dead-End Hit: {r['dead_end_hit'].get('failure_reason', '')}]**"
        lines.append(
            f"| **`{r['id']}`** | `{r['lot']}` (`{r['gate']}`) | **{r['title']}** *[{r['owner_seat']}]*<br>*({r['plain_why']})*{de_note} | "
            f"{r['c1']} | {r['c2']} | {r['c3']} | {r['c4']} | `{r['stake_label']}` | **{r['verdict']}** |"
        )

    print("\n".join(lines))
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({
                "project": project,
                "mode": ev["mode"],
                "domain": domain,
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
    entry = {
        "id": f"DE-{hashlib.sha256(sig.encode('utf-8')).hexdigest()[:6].upper()}",
        "rejected_on": dt.date.today().isoformat(),
        "hypothesis_key": args.key,
        "title": args.title,
        "normalized_signature": sig,
        "failure_reason": args.reason,
        "evidence_metric": args.metric,
    }
    de_store.setdefault("dead_ends", []).append(entry)
    out = save_dead_ends(ledger_dir, de_store)
    print(json.dumps({"status": "DEAD_END_BURIED_PERMANENTLY", "registry": str(out), "entry": entry}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ExCom v3.1 — Gate 0 Decision Matrix & Dead-End Anti-Loop")
    sub = p.add_subparsers(dest="cmd")

    p_eval = sub.add_parser("evaluate", help="Evaluate Gate 0 Decision Matrix")
    p_eval.add_argument("--input", required=True)
    p_eval.add_argument("--ledger-dir", default="")
    p_eval.add_argument("--json-out", default="")
    p_eval.add_argument("--auto-record-rejected", action="store_true")
    p_eval.set_defaults(func=cmd_evaluate)

    p_de = sub.add_parser("record-dead-end", help="Permanently bury a failed hypothesis/patch so AI never re-proposes it")
    p_de.add_argument("--ledger-dir", required=True)
    p_de.add_argument("--key", required=True)
    p_de.add_argument("--title", required=True)
    p_de.add_argument("--reason", required=True)
    p_de.add_argument("--metric", default="")
    p_de.set_defaults(func=cmd_record_dead_end)

    return p


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    # Backward compatibility: if invoked directly with `--input` without subcommand, route to `evaluate`
    argv = sys.argv[1:]
    if argv and argv[0].startswith("--"):
        argv = ["evaluate", *argv]
    ns = build_parser().parse_args(argv)
    if not getattr(ns, "cmd", None):
        build_parser().print_help()
        raise SystemExit(1)
    raise SystemExit(ns.func(ns))
