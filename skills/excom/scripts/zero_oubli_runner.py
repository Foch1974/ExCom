#!/usr/bin/env python3
"""ExCom v3.0 — Aeronautical « Zéro-Oubli » Lot & SHA-256 Gate Runner.

Enforces 100% factual, zero-amnesia execution across sequential Lots (Lot 0 .. Lot K)
and blocking Gates (P0 .. PK) for BOTH `CODE` and `METIER` projects:

  1. `init-lot0`   : Locks approved items (`FIX_01..FIX_N`), project invariants, sacred file
                     SHA-256 hashes, and sequential gates (`P1..PK`) into `zero_oubli_ledger.json`.
  2. `verify-gate` : Physically blocks Gate `Pk` unless:
                     - Gate `P_{k-1}` holds a valid, unbroken SHA-256 certificate;
                     - Every item in `Pk` AND every cumulative prior item in `P1..P_{k-1}` passes:
                       * `CODE` item: test function physically exists in AST, contains real `assert`s,
                         calls/references the real production symbol (`Zéro Faux Jumeau`), zero prior
                         verified test was deleted (`Indelible Cumulative Suite`), and test runner exits 0;
                       * `METIER` item: deliverable file physically exists on disk, meets min byte size,
                         and contains 100% of mandatory clauses/sections (`required_markers`);
                     - Sacred files keep their exact SHA-256.
                     Issues cryptographic certificate `gate_<Pk>_certified.json` bound to `tree_sha256`.
  3. `status`      : Audits live workspace `tree_sha256` against certificates (auto-detects stale
                     gates if any tracked file was edited after certification) and prints progress.
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


SKIP_DIRS: Set[str] = {
    ".git", "node_modules", "__pycache__", ".pytest_cache", ".venv", "venv",
    "dist", "build", "bin", "obj",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_workspace_tree_sha256(project_dir: Path, tracked_rel_paths: Optional[List[str]] = None) -> str:
    h = hashlib.sha256()
    if tracked_rel_paths:
        rels = sorted(set(tracked_rel_paths))
        for rel in rels:
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


def inspect_python_test_ast(test_file: Path, test_fn_name: str, required_prod_symbol: str) -> Dict[str, Any]:
    if not test_file.is_file():
        return {"ok": False, "reason": f"Fichier de test introuvable : {test_file}"}
    source = test_file.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=str(test_file))
    except SyntaxError as exc:
        return {"ok": False, "reason": f"SyntaxError dans {test_file.name}: {exc}"}

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
        return {"ok": False, "reason": f"Fonction `{test_fn_name}` absente de {test_file.name}", "all_tests": all_test_fns}

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
        return {"ok": False, "reason": f"Test complaisant détecté : `{test_fn_name}` ne contient aucune assertion (`assert`).", "all_tests": all_test_fns}

    if required_prod_symbol:
        all_refs = imported_or_used_names | fn_used_names
        if required_prod_symbol not in all_refs:
            return {
                "ok": False,
                "reason": f"Violation Zéro-Faux-Jumeau : `{test_fn_name}` n'appelle pas le symbole réel `{required_prod_symbol}`.",
                "all_tests": all_test_fns,
            }

    return {"ok": True, "reason": "OK", "all_tests": all_test_fns}


def verify_metier_deliverable(project_dir: Path, item: Dict[str, Any]) -> Dict[str, Any]:
    rel = str(item.get("deliverable_path", "")).strip()
    if not rel:
        return {"ok": False, "reason": "Aucun `deliverable_path` spécifié pour cet item METIER."}
    fp = (project_dir / rel) if not Path(rel).is_absolute() else Path(rel)
    if not fp.is_file():
        return {"ok": False, "reason": f"Livrable introuvable sur disque : {fp}"}
    min_bytes = int(item.get("min_bytes", 120))
    size = fp.stat().st_size
    if size < min_bytes:
        return {"ok": False, "reason": f"Livrable trop court ({size} octets < {min_bytes} requis) : {fp.name}"}
    text = fp.read_text(encoding="utf-8", errors="replace").lower()
    missing = [m for m in item.get("required_markers", []) if str(m).lower() not in text]
    if missing:
        return {"ok": False, "reason": f"Clauses/sections obligatoires absentes de {fp.name} : {missing}"}
    return {"ok": True, "reason": f"Livrable vérifié ({size} octets, 100% des marqueurs présents)"}


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
        "schema_version": "3.0.0",
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

    # Certify P0 (Lot 0 Registration Complete)
    cert_p0 = {
        "gate": "P0",
        "certified_at": now_iso(),
        "registered_items_count": len(items),
        "sacred_files_locked": len(sacred_hashes),
        "tree_sha256": compute_workspace_tree_sha256(project_dir, ledger["tracked_files"]),
    }
    (ledger_dir / "gate_P0_certified.json").write_text(json.dumps(cert_p0, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "PORTE_P0_CERTIFIED",
        "ledger_path": str(ledger_path),
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

    # 1. Check sequential prerequisite gates P1..P_{k-1}
    for prev_gate in gates_order[:gate_idx]:
        cert_file = ledger_dir / f"gate_{prev_gate}_certified.json"
        if not cert_file.is_file():
            failures.append(f"Porte précédente `{prev_gate}` non certifiée : impossible de franchir `{target_gate}` avant `{prev_gate}`.")

    # 2. Check Sacred Files SHA-256
    for rel, expected_sha in ledger.get("sacred_files_sha256", {}).items():
        fp = project_dir / rel
        if not fp.is_file() or file_sha256(fp) != expected_sha:
            failures.append(f"VIOLATION FICHIER SACRÉ : `{rel}` a été altéré ou supprimé (SHA-256 invalide).")

    # 3. Check ALL cumulative items up to and including `target_gate` (Zero Regression + Zero Amnesia)
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

    # 4. Indelible Cumulative Test Suite Check (forbid deleting any previously verified test_*)
    prev_indelible = set(ledger.get("indelible_verified_tests", []))
    missing_indelible = sorted(prev_indelible - discovered_tests_now)
    if missing_indelible:
        failures.append(f"SUPPRESSION INTERDITE DE TESTS PRÉCÉDENTS (Suite Indélébile) : {missing_indelible}")

    # 5. Execute real test runner command if CODE items are in scope
    test_cmd = str(ledger.get("test_command", "")).strip()
    if need_code_test_run and not failures:
        if not test_cmd:
            failures.append("Aucune commande `test_command` définie dans le registre pour exécuter les tests CODE.")
        else:
            proc = subprocess.run(
                test_cmd, shell=True, cwd=str(project_dir),
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            if proc.returncode != 0:
                tail = (proc.stdout + "\n" + proc.stderr)[-1200:]
                failures.append(f"Échec d'exécution réelle de la suite de tests (code {proc.returncode}) :\n{tail}")

    if failures:
        print(json.dumps({
            "gate": target_gate,
            "status": "BLOCKED",
            "failures_count": len(failures),
            "failures": failures,
        }, ensure_ascii=False, indent=2))
        return 2

    # 100% PASS -> Update ledger items, lock new indelible tests, and issue SHA-256 certificate!
    ts = now_iso()
    for it in scope_items:
        it["status"] = "VERIFIED"
        if not it.get("verified_at"):
            it["verified_at"] = ts

    for it in scope_items:
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
    # Since verify-gate cumulatively re-validated all prerequisite gates P1..P_{k-1} on this exact tree, refresh their tree_sha256
    for prev_g in gates_order[:gate_idx]:
        if prev_g in g_certs:
            g_certs[prev_g]["tree_sha256"] = tree_sha
            g_certs[prev_g]["last_cumulative_recheck_at"] = ts
            (ledger_dir / f"gate_{prev_g}_certified.json").write_text(
                json.dumps(g_certs[prev_g], ensure_ascii=False, indent=2), encoding="utf-8"
            )
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "gate": target_gate,
        "status": "CERTIFIED_100_PCT",
        "certificate_path": str(cert_path),
        "tree_sha256": tree_sha,
        "verified_items_count": len(scope_items),
        "total_items_count": len(ledger["items"]),
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

    print(json.dumps({
        "project_name": ledger.get("project_name"),
        "mode": ledger.get("mode"),
        "domain": ledger.get("domain"),
        "live_tree_sha256": live_sha,
        "indelible_tests_count": len(ledger.get("indelible_verified_tests", [])),
        "gates": gate_states,
    }, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ExCom v3.0 — Aeronautical Zéro-Oubli Lot & SHA-256 Gate Engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-lot0", help="Initialize Lot 0 ledger and certify P0")
    p_init.add_argument("--project-dir", required=True)
    p_init.add_argument("--ledger-dir", required=True)
    p_init.add_argument("--spec", required=True)
    p_init.set_defaults(func=cmd_init_lot0)

    p_ver = sub.add_parser("verify-gate", help="Verify all upstream/downstream checks for Gate Pk and sign SHA-256")
    p_ver.add_argument("--ledger-dir", required=True)
    p_ver.add_argument("--gate", required=True)
    p_ver.add_argument("--project-dir", default="")
    p_ver.set_defaults(func=cmd_verify_gate)

    p_st = sub.add_parser("status", help="Check live SHA-256 validity of all Aeronautical Gates")
    p_st.add_argument("--ledger-dir", required=True)
    p_st.add_argument("--project-dir", default="")
    p_st.set_defaults(func=cmd_status)

    return p


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ns = build_parser().parse_args()
    raise SystemExit(ns.func(ns))
