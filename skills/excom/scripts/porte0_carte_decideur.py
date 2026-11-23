#!/usr/bin/env python3
"""ExCom v3.0 — Porte 0 : Universal Entry Decision Matrix (Carte de Pertinence Décideur).

Evaluates any set of strategic options, project deliverables, or technical fixes RIGHT AT
ENTRY (Porte 0) across BOTH:
  - `MODE = "CODE"`   (Quant trading, SaaS, AI/ML, Embedded, Robotics, General Software)
  - `MODE = "METIER"` (Corporate/Tax structuring, Real Estate, Sourcing, Legal, Life/Ops)

Enforces the 4 Universal Thermometers + Mandatory STOP Gate:
  - C1 (Preuve Factuelle)   : Disk-verified >=80% probe in CODE mode, or verified statutory/
                              quote/data sources in METIER mode — without breaking healthy bricks.
  - C2 (Fondations d'Abord) : Foundational/mechanical brakes first; blocks premature scaling,
                              exotic wrappers, or formula tweaks while core brakes remain open.
  - C3 (Zéro Usine à Gaz)   : 0 arbitrary free parameters / 0 unnecessary structural layers,
                              no post-hoc wishful tuning, plain 1-sentence human mechanism.
  - C4 (Matérialité >= 5%)  : >= 5% stake impact or critical gate unblocked (✅ vs ⚠️).
  - 🛑 STOP Gate            : Fires automatically when foundational brakes are resolved and no
                              item reaches >= 5% materiality (anti-overfitting / anti-churn).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Set


FOUNDATIONAL_KINDS: Set[str] = {
    # Code / Engineering foundational categories
    "PLUMBING_RUNTIME",
    "ACCOUNTING_DOUBLE_CHARGE",
    "EXECUTION_FRICTION",
    "UNIVERSE_WIRING",
    "DEAD_CODE_PURGE",
    "ABLATION_SIMPLIFICATION",
    "TEST_TWIN_PARITY",
    "SECURITY_HARDENING",
    "DATA_SCHEMA_FIX",
    # Business / Legal / Life / Operational foundational categories
    "LEGAL_STATUTORY_FOUNDATION",
    "TAX_CASH_FOUNDATION",
    "CORE_VENDOR_QUALIFICATION",
    "OPERATIONAL_BOTTLENECK",
    "RISK_CONTINGENCY_SHIELD",
    "COMPLIANCE_MANDATORY",
    "MVP_CORE_SCOPE",
}


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
        }

    # MODE == "METIER"
    sources = [str(s).strip() for s in ctx.get("verified_facts_or_sources", []) if str(s).strip()]
    return {
        "mode": "METIER",
        "evidence_ok": len(sources) >= 1,
        "sources_count": len(sources),
        "explained_pct": 100.0,
        "core_viability": float(ctx.get("core_viability_at_zero_friction", 1.0)),
    }


def evaluate_item(item: Dict[str, Any], ctx: Dict[str, Any], ev: Dict[str, Any]) -> Dict[str, Any]:
    kind = str(item.get("kind", "SECONDARY_OPTIMIZATION")).strip().upper()
    has_brakes = bool(ctx.get("unresolved_foundational_brakes", False))

    item_fact_ok = bool(item.get("fact_verified", True)) and ev["evidence_ok"]
    touches_healthy = bool(item.get("touches_healthy_brick", item.get("touches_already_positive_signal", False)))
    plain_why = str(item.get("plain_sentence", item.get("plain_economic_sentence", ""))).strip()
    new_params = int(item.get("new_free_parameters_or_layers", item.get("new_free_parameters", 0)))
    wishful_tuning = bool(item.get("post_hoc_or_wishful_tuning", item.get("post_hoc_window_tuning", False)))

    stake_pct = float(item.get("estimated_stake_pct", item.get("estimated_stake_ratio_pct", 0.0)))
    blocks_gate = bool(item.get("blocks_critical_gate", item.get("blocks_mandatory_gate", False)))

    c1_ok = item_fact_ok and not touches_healthy
    c2_ok = False if (has_brakes and kind not in FOUNDATIONAL_KINDS) else True
    c3_ok = (new_params == 0) and (not wishful_tuning) and (len(plain_why) >= 15)
    c4_ok = (stake_pct >= 5.0) or blocks_gate

    if not c1_ok or not c2_ok or not c3_ok:
        verdict = "❌ SURENCHÈRE / BLOQUÉ"
    elif c4_ok:
        verdict = "✅ FONDÉ & CRITIQUE"
    else:
        verdict = "⚠️ FONDÉ MAIS MINEUR"

    return {
        "id": str(item.get("id", "ITEM_?")),
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
        "stake_label": str(item.get("stake_label", f"{stake_pct:.1f} % enjeu")),
        "plain_why": plain_why,
        "verdict": verdict,
        "approved_candidate": verdict.startswith("✅") or verdict.startswith("⚠️"),
        "raw": item,
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="ExCom v3.0 — Porte 0 Universal Carte de Pertinence Décideur")
    p.add_argument("--input", required=True, help="Input JSON specification for Porte 0")
    p.add_argument("--json-out", default="", help="Optional output JSON path for downstream Lot 0 ingestion")
    args = p.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    project = str(payload.get("project", "Projet"))
    domain = str(payload.get("domain", "CUSTOM_PROJECT"))
    ctx = payload.get("context", {}) or {}
    ev = verify_mode_evidence(payload)

    lines: List[str] = [
        f"## Porte 0 — Carte de Pertinence Décideur (`{project}` · `{ev['mode']}` · `{domain}`)",
        "",
    ]

    # Gate 0A: Block unverified CODE diagnostics
    if ev["mode"] == "CODE" and not ev["disk_ok"]:
        lines.append("> **❌ BLOQUÉ EN PORTE 0 (PREUVE DISQUE MANQUANTE)** : Aucun script de sonde ni fichier de mesures vérifié sur disque. Interdiction de proposer un plan avant mesure réelle.")
        print("\n".join(lines))
        return 2

    if ev["mode"] == "CODE" and ev["explained_pct"] < 80.0:
        lines.append(f"> **❌ BLOQUÉ EN PORTE 0 (AUTOPSIE INCOMPLÈTE : `{ev['explained_pct']} %` < `80 %`)** : La cause racine n'est pas encore isolée. Affiner la sonde avant toute proposition.")
        print("\n".join(lines))
        return 2

    # Gate 0B: Dead foundation at zero friction
    if ev["core_viability"] <= 0.0:
        lines.append(f"> **🛑 FONDATION DÉFICITAIRE À NU (`viabilité hors friction = {ev['core_viability']} <= 0`)** : La base ne fonctionne pas même à coût nul. **Zéro rustine autorisée** — seules options : **Suppression (Ablation)** ou **Refonte complète**.")
        print("\n".join(lines))
        return 0

    proposals = payload.get("proposals", [])
    rows = [evaluate_item(it, ctx, ev) for it in proposals]

    has_brakes = bool(ctx.get("unresolved_foundational_brakes", False))
    max_stake = max([r["stake_pct"] for r in rows], default=0.0)
    any_crit_gate = any(bool(it.get("blocks_critical_gate", it.get("blocks_mandatory_gate", False))) for it in proposals)

    # Gate 0C: Sovereign STOP Verdict when nothing material remains
    if not has_brakes and max_stake < 5.0 and not any_crit_gate:
        lines.append(f"> **🛑 VERDICT SOUVERAIN : STOP — NE RIEN TOUCHER** (`enjeu max = {max_stake:.1f} % < 5 %`, `0` frein fondamental ouvert).")
        lines.append("> *Toute itération ou couche supplémentaire produirait de la suroptimisation (overfitting) ou une usine à gaz inutile.*")
        print("\n".join(lines))
        if args.json_out:
            Path(args.json_out).write_text(
                json.dumps({"project": project, "verdict_global": "STOP", "rows": rows}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return 0

    n_go = sum(1 for r in rows if r["verdict"].startswith("✅"))
    n_opt = sum(1 for r in rows if r["verdict"].startswith("⚠️"))
    n_no = sum(1 for r in rows if r["verdict"].startswith("❌"))
    note = str(ctx.get("summary_note", "")).strip()

    lines.append(f"- **Synthèse Porte 0** : `{n_go}` ✅ Fondés & Critiques | `{n_opt}` ⚠️ Mineurs/Optionnels | `{n_no}` ❌ Surenchère Bloquée")
    lines.append(f"- **Freins fondamentaux actifs** : `{has_brakes}`" + (f" — {note}" if note else ""))

    invariants = payload.get("project_invariants", [])
    if invariants:
        lines.append("- **Invariants sur-mesure du projet (verrouillés au Lot 0 si Go)** : " + " · ".join(f"`{inv}`" for inv in invariants))
    lines.append("")
    lines.append("| ID | Lot / Porte | Proposition (en clair) | `C1` Preuve | `C2` Fondations | `C3` Zéro Usine à Gaz | `C4` Enjeu | Impact | Verdict Porte 0 |")
    lines.append("| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :--- | :--- |")
    for r in rows:
        lines.append(
            f"| **`{r['id']}`** | `{r['lot']}` (`{r['gate']}`) | **{r['title']}** *[{r['owner_seat']}]*<br>*(Pourquoi : {r['plain_why']})* | "
            f"{r['c1']} | {r['c2']} | {r['c3']} | {r['c4']} | `{r['stake_label']}` | **{r['verdict']}** |"
        )

    print("\n".join(lines))
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({
                "project": project,
                "mode": ev["mode"],
                "domain": domain,
                "verdict_global": "ARBITRATION_READY",
                "project_invariants": invariants,
                "rows": rows,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
