#!/usr/bin/env python3
"""RootCause Guard v3.2 — Deterministic AST Scanner, Blind-Spot Detector & Anti-Patch Autopsy Engine.

100% Python 3.8+ standard library. Strictly READ-ONLY on `--project-dir` (never writes
inside the target repository; stores ratchet ledgers under `--ledger-dir` or
`~/.gemini/antigravity/plugin_data/excom/ledgers/<project_slug>`).

Subcommands:
  1. `scan`            — Computes project AST/file fingerprint, detects topological drift, spots
                         patchwork (`boolean_hotspots`, denoised `entity_exceptions`, `hardcoded_exclusions`,
                         `magic_literals`, `fixed_caps`), AND surfaces structural blind spots (v3.2):
                           * `silent_discards`     (`_ = (param, ...)` throwing away live inputs)
                           * `frozen_state_latches` (one-shot zero/empty cache latches never refreshed)
                           * `stacked_clamps`      (advisory attenuation-chain heat map)
                           * `mock_schema_drift`   (test-injected structured keys absent from real data JSONs)
  2. `schema-parity`   — Dedicated Test-Mock vs Real-Data Schema Parity audit catching complacent twins.
  3. `diff-audit`      — Audits uncommitted `git diff` against HEAD via real AST comparison.
  4. `autopsy-gate`    — Enforces the 4 Iron Gates + 3-state foundation ceiling check.
  5. `ack-ratchet`     — Updates baseline ledger ONLY when explicitly authorized by the user.
  6. `register-domain` — Locks bespoke domain conservation equation & invariants (with run-id provenance).
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Set, Tuple


ENGINE_VERSION = "3.2.0"

SKIP_DIRS: Set[str] = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".venv", "venv", "env", "dist", "build",
    "bin", "obj", ".next", ".nuxt", ".turbo", "coverage", "excom-projects",
    "scratch", "tmp", "temp",
}

ARCHIVE_DIR_PREFIXES: Tuple[str, ...] = ("legacy", "archive", "backup", "deprecated", "old_")

CODE_EXTS: Set[str] = {".py", ".cs", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".sql", ".cpp", ".c", ".sol"}
DOC_EXTS: Set[str] = {".md", ".csv", ".json", ".yaml", ".yml", ".pdf", ".docx", ".xlsx"}

ALLOWED_TRIVIAL_NUMBERS: Set[float] = {
    -1.0, 0.0, 0.5, 1.0, 2.0, 10.0, 100.0, 252.0, 360.0, 365.0, 1000.0, 1e-6, 1e-8, 1e-9, 1e-12,
}

# Heuristic patterns for hardcoded entity/asset cherry-picking inside math/signal/risk functions
TICKER_RE = re.compile(r"^[A-Z0-9]{2,6}(?:-[A-Z]{3,4}|USDT|USD|EUR|PERP)?$")
STRUCTURED_PREFIX_KEY_RE = re.compile(r"^([A-Z]{2,5})_[A-Z0-9]{1,8}$")
EXCLUSION_VAR_RE = re.compile(
    r"(?:exclude|ban|block|skip|ignore|collinear|blacklist|drop|omit|forbid|disable)", re.IGNORECASE
)
TELEMETRY_OR_LOGGING_FN_PREFIXES: Tuple[str, ...] = (
    "_book_", "_log_", "log_", "report_", "format_", "summarize_", "summary_",
    "telemetry_", "classify_", "render_", "print_", "export_", "dump_", "display_",
)

# Denoised non-entity constants (enum tags, asset-class buckets, HTTP/order states, currencies)
NON_TICKER_CONSTS: Set[str] = {
    "OK", "ID", "GO", "NO", "NA", "TRUE", "FALSE", "NONE", "NULL", "UTF8",
    "JSON", "HTML", "CSV", "XML", "GET", "POST", "PUT", "DELETE", "HEAD",
    "INFO", "WARN", "ERROR", "DEBUG", "TODO", "DONE", "OPEN", "RED", "GREEN",
    "AMBER", "BUY", "SELL", "LONG", "SHORT", "FLAT", "CASH", "SPOT", "SWAP",
    "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "NOK", "SEK",
    "CNY", "HKD", "SGD", "DAILY", "HOUR", "MINUTE", "CLEAR", "PASS", "FAIL", "STOP",
    # Generic category / domain / pipeline / state tags (prevents 400+ false positives)
    "EQ", "FX", "BOND", "BONDS", "AGRI", "NRG", "PM", "IM", "METAL", "METALS",
    "MACRO", "EQUITY", "RATES", "CREDIT", "CRYPTO", "COMMOD", "PROD", "DEV",
    "TEST", "LIVE", "PAPER", "CLOUD", "LOCAL", "UTC", "NAV", "PNL", "GROSS",
    "NET", "FEE", "FEES", "SLIP", "COST", "RISK", "VOL", "BETA", "ALPHA",
    "SCORE", "RANK", "MOO", "MOC", "LMT", "MKT", "DAY", "GTC", "IOC", "FOK",
    "H1", "H4", "M5", "M15", "D1", "W1", "T0", "T1", "FAM", "FAM8", "C98", "C98E",
    "QMJ", "SMB", "HML", "UMD", "VIX", "RAW", "CLEAN", "HIGH", "LOW", "MID",
    "MAX", "MIN", "SUM", "AVG", "STD", "VAR", "ACTIVE", "PENDING", "FILLED",
    "CANCEL", "INVALID", "NEW", "OLD", "ALL", "ANY", "AUTO", "MANUAL",
    "BTCUSD", "ETHUSD", "SPY", "QQQ", "TLT", "IEF", "SHY", "TIP", "AGG", "LQD", "HYG",
}

NON_DATA_JSON_NAMES: Set[str] = {
    "package.json", "package-lock.json", "tsconfig.json", "plugin.json",
    "marketplace.json", "hooks.json", "baseline.json", "latest_scan.json",
    "custom_profile.json", "dead_ends_registry.json", "zero_oubli_ledger.json",
    "kpi_history.json", "clean_room_audit_report.json", "project-state.json",
    "pre_cloud_certified.json", "pre_paper_certified.json",
}

VALID_MECHANICAL_KINDS: Set[str] = {
    "PLUMBING_RUNTIME",
    "ACCOUNTING_DOUBLE_CHARGE",
    "EXECUTION_FRICTION",
    "UNIVERSE_WIRING",
    "DEAD_CODE_PURGE",
    "ABLATION_SIMPLIFICATION",
    "TEST_TWIN_PARITY",
    "SECURITY_HARDENING",
    "DATA_SCHEMA_FIX",
}

DOMAIN_PROFILES: Dict[str, Dict[str, Any]] = {
    "QUANT_TRADING": {
        "keywords": ["qcalgorithm", "quantconnect", "sharpe", "drawdown", "slippage", "backtest", "ccxt", "okx", "orderbook", "funding_rate", "margin"],
        "mass_balance_equation": "Gross_Signal_Alpha - Execution_Spread_Slippage - Commissions_Fees - Financing_Borrow_FX - Rejected_Or_Clipped_Orders == Net_Realized_PnL",
        "mandatory_brakes_checklist": [
            "Strict parity between research simulator and production/backtest runtime",
            "Zero double-charging or omitted execution frictions (spread, slippage, funding/borrow, FX)",
            "Audit of rejected, blocked, inverted, or artificially capped orders",
            "Theoretical zero-friction ceiling verified against North-Star target (not just > 0)",
        ],
    },
    "DATA_OR_ML_PIPELINE": {
        "keywords": ["bigquery", "pyspark", "dataframe", "sklearn", "torch", "xgboost", "lightgbm", "cross_val", "dbt", "dataform"],
        "mass_balance_equation": "Input_Rows_Or_Signal - Schema_Drops - Null_Filter_Losses - Leakage_Purge == Validated_Out_Of_Sample_Output",
        "mandatory_brakes_checklist": [
            "Zero temporal look-ahead or train/test contamination",
            "Row-count and accounting sum conservation across every join",
            "Out-of-sample lift exceeding a zero-parameter naive baseline",
        ],
    },
    "WEB_OR_SAAS_APP": {
        "keywords": ["fastapi", "flask", "django", "react", "nextjs", "stripe", "prisma", "sqlalchemy", "endpoint", "middleware"],
        "mass_balance_equation": "Total_Requests_Or_Latency == Auth_Time + Validation + DB_Query_Time + External_API_Time + Render_Time",
        "mandatory_brakes_checklist": [
            "Deterministic reproduction of error or latency bottleneck via measured probe",
            "Transactional integrity and write/payment idempotency",
            "Zero authentication or permission boundary bypass",
        ],
    },
    "GENERAL_SOFTWARE": {
        "keywords": [],
        "mass_balance_equation": "Observed_Defect_Or_Gap == Sum(Measured_Root_Causes) [>= 80% explained before any code edit]",
        "mandatory_brakes_checklist": [
            "Deterministic script reproduction measured on disk before any hypothesis",
            "Ablation check (removing legacy band-aids) before adding new conditional branches",
            "Zero arbitrary magic literals or unjustified boolean sprawl",
        ],
    },
    "NON_CODE_METIER": {
        "keywords": [],
        "mass_balance_equation": "Total_Project_Outcome == Net_Value_Drivers - TCO_All_In_Costs - Legal_Tax_Friction - Operational_LeadTime_Risk",
        "mandatory_brakes_checklist": [
            "Dated, verifiable statutory, regulatory, or vendor-quote sources (zero verbal guesswork)",
            "Full all-in TCO and hidden-friction model executed via script before irreversible commitment",
            "100% presence of mandatory protective clauses across every legal/operational deliverable",
        ],
    },
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def default_ledger_dir(project_dir: Path) -> Path:
    slug_hash = hashlib.sha256(str(project_dir.resolve()).lower().encode("utf-8")).hexdigest()[:10]
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", project_dir.resolve().name)
    base = Path.home() / ".gemini" / "antigravity" / "plugin_data" / "excom" / "ledgers"
    return base / f"{safe_name}_{slug_hash}"


def classify_file_role(rel_path: str, content_lower: str) -> str:
    p = rel_path.lower().replace("\\", "/")
    name = Path(p).name
    if (
        name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith("_gate.py")
        or name.endswith("_guard.py")
        or "/tests/" in f"/{p}"
        or "/test_harnesses/" in f"/{p}"
        or "/.agents/" in f"/{p}"
        or "/hooks/" in f"/{p}"
        or "probe" in name
        or "audit" in name
        or "verify" in name
        or "certify" in name
    ):
        return "PROBES_AND_TESTS"
    if any(k in name for k in ("config", "param", "const", "setting")):
        return "CONFIG_AND_CONSTANTS"
    if any(k in name for k in ("exec", "order", "broker", "router", "client", "exchange", "slippage", "fee")):
        return "EXECUTION_AND_FRICTION"
    if any(k in name for k in ("risk", "margin", "alloc", "sizing", "guard", "limit", "stop", "shield")):
        return "RISK_AND_SIZING"
    if any(k in name for k in ("eligib", "universe", "loader", "ingest", "feed", "data", "schema")):
        return "UNIVERSE_AND_INGESTION"
    if any(k in name for k in ("alpha", "signal", "strat", "model", "factor", "sniper", "medallion", "engine")):
        return "CORE_LOGIC_OR_SIGNAL"
    if "def test_" in content_lower or "unittest" in content_lower or "pytest" in content_lower:
        return "PROBES_AND_TESTS"
    return "CORE_LOGIC_OR_SIGNAL"


def count_bool_leaves(node: ast.AST) -> int:
    if isinstance(node, ast.BoolOp):
        return sum(count_bool_leaves(v) for v in node.values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return count_bool_leaves(node.operand)
    return 1


def extract_container_name(node: ast.AST) -> Optional[str]:
    """Extracts canonical variable/attribute name for subscripted dicts (e.g. `algo._fut_roll_yields` -> `_fut_roll_yields`)."""
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def test_checks_zero_or_empty_container(test_node: ast.AST) -> Tuple[Set[str], Set[str]]:
    """Detects zero-value sticky latches (`abs(x.get(...)) <= eps`) and missing-key guards (`k not in x`)."""
    sticky_zero: Set[str] = set()
    not_in_guards: Set[str] = set()
    for sub in ast.walk(test_node):
        if isinstance(sub, ast.Compare) and any(isinstance(op, (ast.LtE, ast.Eq)) for op in sub.ops):
            for inner in ast.walk(sub):
                if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute) and inner.func.attr == "get":
                    cname = extract_container_name(inner.func.value)
                    if cname:
                        sticky_zero.add(cname)
        elif isinstance(sub, ast.Compare) and any(isinstance(op, ast.NotIn) for op in sub.ops):
            for comp in sub.comparators:
                cname = extract_container_name(comp)
                if cname and cname.startswith("_"):
                    not_in_guards.add(cname)
    return sticky_zero, not_in_guards


def analyze_python_ast(source: str, rel_path: str, role: str) -> Dict[str, Any]:
    try:
        tree = ast.parse(source, filename=rel_path)
    except SyntaxError as exc:
        return {
            "parse_error": f"SyntaxError line {exc.lineno}: {exc.msg}",
            "functions": [],
            "boolean_hotspots": [],
            "elif_ladders": [],
            "entity_exceptions": [],
            "hardcoded_exclusions": [],
            "magic_literals": [],
            "fixed_caps": [],
            "silent_discards": [],
            "frozen_state_latches": [],
            "stacked_clamps": [],
        }

    is_test_or_cfg = role in ("PROBES_AND_TESTS", "CONFIG_AND_CONSTANTS")
    functions: List[str] = []
    boolean_hotspots: List[Dict[str, Any]] = []
    elif_ladders: List[Dict[str, Any]] = []
    entity_exceptions: List[Dict[str, Any]] = []
    hardcoded_exclusions: List[Dict[str, Any]] = []
    magic_literals: List[Dict[str, Any]] = []
    fixed_caps: List[Dict[str, Any]] = []
    silent_discards: List[Dict[str, Any]] = []
    stacked_clamps: List[Dict[str, Any]] = []

    # Track sticky zero-value latches and guarded vs unguarded container mutations
    sticky_zero_mutations: List[Dict[str, Any]] = []
    guarded_mutations: List[Dict[str, Any]] = []
    unguarded_mutated_containers: Set[str] = set()

    visited_if_chains: Set[int] = set()

    def is_telemetry_fn(fn_name: str) -> bool:
        low = fn_name.lower()
        return any(low.startswith(pref) for pref in TELEMETRY_OR_LOGGING_FN_PREFIXES)

    def check_exclusion_pair(tgt_node: ast.AST, val_node: ast.AST, lineno: int, fn_name: str) -> None:
        tname = tgt_node.id if isinstance(tgt_node, ast.Name) else (tgt_node.attr if isinstance(tgt_node, ast.Attribute) else "")
        if tname and EXCLUSION_VAR_RE.search(tname) and isinstance(val_node, (ast.Set, ast.List, ast.Tuple)):
            lits = [
                e.value.strip()
                for e in val_node.elts
                if isinstance(e, ast.Constant) and isinstance(e.value, str)
                and TICKER_RE.match(e.value.strip()) and e.value.strip() not in NON_TICKER_CONSTS
            ]
            if lits:
                hardcoded_exclusions.append({
                    "line": lineno,
                    "fn": fn_name,
                    "var": tname,
                    "literals": lits,
                })

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.fn_stack: List[str] = []
            self.fn_params_stack: List[Set[str]] = []
            self.const_assign_depth: int = 0
            self.sticky_zero_stack: List[Set[str]] = []
            self.zero_guard_stack: List[Set[str]] = []

        def _visit_fn(self, node: ast.AST, name: str, args_obj: ast.arguments) -> None:
            functions.append(name)
            params: Set[str] = set()
            for a in list(args_obj.posonlyargs) + list(args_obj.args) + list(args_obj.kwonlyargs):
                if a.arg not in ("self", "cls"):
                    params.add(a.arg)
            self.fn_stack.append(name)
            self.fn_params_stack.append(params)

            # Advisory stacked clamps counter per function
            if not is_test_or_cfg and role in ("RISK_AND_SIZING", "CORE_LOGIC_OR_SIGNAL", "EXECUTION_AND_FRICTION"):
                clamps = 0
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        if isinstance(sub.func, ast.Name) and sub.func.id in ("min", "max"):
                            clamps += 1
                        elif isinstance(sub.func, ast.Attribute) and sub.func.attr in ("clip", "minimum", "maximum"):
                            clamps += 1
                if clamps >= 8:
                    stacked_clamps.append({"line": getattr(node, "lineno", 1), "fn": name, "clamp_calls": clamps})

            self.generic_visit(node)
            self.fn_stack.pop()
            self.fn_params_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._visit_fn(node, node.name, node.args)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._visit_fn(node, node.name, node.args)

        def visit_Assign(self, node: ast.Assign) -> None:
            # 1. Silent parameter discard detector (`_ = param` or `_ = (p1, p2)`)
            if not is_test_or_cfg and self.fn_stack and self.fn_params_stack:
                cur_params = self.fn_params_stack[-1]
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == "_":
                        used = {n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)}
                        dropped = sorted(used & cur_params)
                        if dropped:
                            silent_discards.append({
                                "line": node.lineno,
                                "fn": self.fn_stack[-1],
                                "discarded_params": dropped,
                            })

            # 2. Hardcoded exclusion / ban / collinear set detector (supports single & tuple-unpack assignments)
            if not is_test_or_cfg and role in ("CORE_LOGIC_OR_SIGNAL", "RISK_AND_SIZING", "UNIVERSE_AND_INGESTION"):
                cur_fn = self.fn_stack[-1] if self.fn_stack else "<module>"
                for tgt in node.targets:
                    if isinstance(tgt, (ast.Tuple, ast.List)) and isinstance(node.value, (ast.Tuple, ast.List)):
                        for sub_t, sub_v in zip(tgt.elts, node.value.elts):
                            check_exclusion_pair(sub_t, sub_v, node.lineno, cur_fn)
                    else:
                        check_exclusion_pair(tgt, node.value, node.lineno, cur_fn)

            # 3. Guarded vs unguarded container subscript mutation (One-Shot Latch check)
            if not is_test_or_cfg and self.fn_stack:
                active_sticky: Set[str] = set().union(*self.sticky_zero_stack) if self.sticky_zero_stack else set()
                active_guards: Set[str] = set().union(*self.zero_guard_stack) if self.zero_guard_stack else set()
                for tgt in node.targets:
                    if isinstance(tgt, ast.Subscript):
                        cname = extract_container_name(tgt.value)
                        if cname and cname.startswith("_"):
                            if cname in active_sticky:
                                sticky_zero_mutations.append({
                                    "line": node.lineno,
                                    "fn": self.fn_stack[-1],
                                    "container": cname,
                                    "latch_kind": "STICKY_ZERO_GUARD",
                                })
                            elif cname in active_guards:
                                guarded_mutations.append({
                                    "line": node.lineno,
                                    "fn": self.fn_stack[-1],
                                    "container": cname,
                                    "latch_kind": "ONE_SHOT_NOT_IN_CACHE",
                                })
                            else:
                                unguarded_mutated_containers.add(cname)

            is_upper_const = (
                not self.fn_stack
                and all(isinstance(t, ast.Name) and t.id.isupper() for t in node.targets)
            )
            if is_upper_const:
                self.const_assign_depth += 1
                self.generic_visit(node)
                self.const_assign_depth -= 1
            else:
                self.generic_visit(node)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            is_upper_const = (
                not self.fn_stack
                and isinstance(node.target, ast.Name)
                and node.target.id.isupper()
            )
            if is_upper_const:
                self.const_assign_depth += 1
                self.generic_visit(node)
                self.const_assign_depth -= 1
            else:
                self.generic_visit(node)

        def visit_If(self, node: ast.If) -> None:
            leaves = count_bool_leaves(node.test)
            if leaves >= 6 and not is_test_or_cfg:
                boolean_hotspots.append({
                    "line": node.lineno,
                    "fn": self.fn_stack[-1] if self.fn_stack else "<module>",
                    "clauses": leaves,
                })

            if id(node) not in visited_if_chains:
                chain_len = 1
                cur: ast.If = node
                visited_if_chains.add(id(cur))
                while len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
                    cur = cur.orelse[0]
                    visited_if_chains.add(id(cur))
                    chain_len += 1
                if chain_len >= 5 and not is_test_or_cfg:
                    elif_ladders.append({
                        "line": node.lineno,
                        "fn": self.fn_stack[-1] if self.fn_stack else "<module>",
                        "branches": chain_len,
                    })

            # Visit test, then push sticky-zero / not-in container guards ONLY for the `body` (not `orelse`)
            self.visit(node.test)
            sticky_set, notin_set = test_checks_zero_or_empty_container(node.test) if (not is_test_or_cfg and self.fn_stack) else (set(), set())
            if sticky_set:
                self.sticky_zero_stack.append(sticky_set)
            if notin_set:
                self.zero_guard_stack.append(notin_set)
            for stmt in node.body:
                self.visit(stmt)
            if sticky_set:
                self.sticky_zero_stack.pop()
            if notin_set:
                self.zero_guard_stack.pop()
            for stmt in node.orelse:
                self.visit(stmt)

        def visit_Compare(self, node: ast.Compare) -> None:
            if (
                not is_test_or_cfg
                and self.fn_stack
                and not is_telemetry_fn(self.fn_stack[-1])
                and role in ("CORE_LOGIC_OR_SIGNAL", "RISK_AND_SIZING")
            ):
                for comp in [node.left, *node.comparators]:
                    if isinstance(comp, ast.Constant) and isinstance(comp.value, str):
                        val = comp.value.strip()
                        if TICKER_RE.match(val) and val not in NON_TICKER_CONSTS:
                            entity_exceptions.append({
                                "line": node.lineno,
                                "fn": self.fn_stack[-1],
                                "literal": val,
                            })
                    elif isinstance(comp, (ast.Tuple, ast.List, ast.Set)):
                        for elt in comp.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                val = elt.value.strip()
                                if TICKER_RE.match(val) and val not in NON_TICKER_CONSTS:
                                    entity_exceptions.append({
                                        "line": node.lineno,
                                        "fn": self.fn_stack[-1],
                                        "literal": val,
                                    })
            self.generic_visit(node)

        def visit_Subscript(self, node: ast.Subscript) -> None:
            if (
                not is_test_or_cfg
                and self.fn_stack
                and role in ("CORE_LOGIC_OR_SIGNAL", "RISK_AND_SIZING", "UNIVERSE_AND_INGESTION")
                and isinstance(node.slice, ast.Slice)
                and isinstance(node.slice.upper, ast.Constant)
                and isinstance(node.slice.upper.value, int)
                and node.slice.upper.value > 3
            ):
                fixed_caps.append({
                    "line": node.lineno,
                    "fn": self.fn_stack[-1],
                    "cap": node.slice.upper.value,
                })
            self.generic_visit(node)

        def visit_Constant(self, node: ast.Constant) -> None:
            if (
                not is_test_or_cfg
                and self.fn_stack
                and self.const_assign_depth == 0
                and isinstance(node.value, (int, float))
                and not isinstance(node.value, bool)
            ):
                fval = float(node.value)
                if fval not in ALLOWED_TRIVIAL_NUMBERS and abs(fval) not in ALLOWED_TRIVIAL_NUMBERS:
                    magic_literals.append({
                        "line": node.lineno,
                        "fn": self.fn_stack[-1],
                        "value": node.value,
                    })

    Visitor().visit(tree)

    # Combine explicit sticky-zero latches + one-shot not-in mutations never refreshed elsewhere
    seen_latch: Set[Tuple[str, int]] = set()
    frozen_state_latches: List[Dict[str, Any]] = []
    for sm in sticky_zero_mutations:
        key = (sm["container"], sm["line"])
        if key not in seen_latch:
            seen_latch.add(key)
            frozen_state_latches.append(sm)
    for gm in guarded_mutations:
        if gm["container"] not in unguarded_mutated_containers:
            key = (gm["container"], gm["line"])
            if key not in seen_latch:
                seen_latch.add(key)
                frozen_state_latches.append(gm)

    return {
        "parse_error": None,
        "functions": functions,
        "boolean_hotspots": boolean_hotspots,
        "elif_ladders": elif_ladders,
        "entity_exceptions": entity_exceptions,
        "hardcoded_exclusions": hardcoded_exclusions,
        "magic_literals": magic_literals,
        "fixed_caps": fixed_caps,
        "silent_discards": silent_discards,
        "frozen_state_latches": frozen_state_latches,
        "stacked_clamps": stacked_clamps,
    }


def extract_json_keys_recursive(obj: Any, out: Set[str], depth: int = 0) -> None:
    if depth > 4:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                out.add(k)
            if isinstance(v, dict):
                extract_json_keys_recursive(v, out, depth + 1)
    elif isinstance(obj, list) and obj:
        extract_json_keys_recursive(obj[0], out, depth + 1)


FSTRING_PREFIX_RE = re.compile(r"^([A-Z]{2,5})_$")


def extract_key_prefix_from_node(node: Optional[ast.AST]) -> Optional[Tuple[str, str]]:
    """Extracts (prefix, sample_key) from either `"RY_GC"` constants or `f"RY_{tk}"` f-strings."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        val = node.value.strip()
        m = STRUCTURED_PREFIX_KEY_RE.match(val)
        if m:
            return m.group(1), val
    elif isinstance(node, ast.JoinedStr) and node.values:
        first = node.values[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            m = FSTRING_PREFIX_RE.match(first.value.strip())
            if m:
                return m.group(1), f"{m.group(1)}_<dynamic>"
    return None


def analyze_mock_vs_real_schema_parity(project_dir: Path) -> Dict[str, Any]:
    """EXCOM_V32_05: Laser-precision detection of structured key prefixes injected by tests/gates
    AND queried by production code that have 0 occurrences in real data JSON files."""
    real_data_files = 0
    real_keys: Set[str] = set()
    real_prefixes: Set[str] = set()
    test_injected: Dict[str, Set[str]] = {}  # prefix -> set of "file:key"
    prod_queried: Dict[str, Set[str]] = {}   # prefix -> set of "file:key"

    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS
            and not d.startswith(".git")
            and not d.lower().startswith(ARCHIVE_DIR_PREFIXES)
        ]
        for fname in sorted(files):
            fp = Path(root) / fname
            rel = str(fp.relative_to(project_dir)).replace("\\", "/")
            low_name = fname.lower()

            # 1. Real data JSON corpus (ignore manifests/ledgers/tiny config jsons)
            if fp.suffix.lower() == ".json" and low_name not in NON_DATA_JSON_NAMES:
                if any(low_name.endswith(suf) for suf in ("_certified.json", "_graded.json", "_ledger.json", "_scan.json")):
                    continue
                try:
                    sz = fp.stat().st_size
                    if sz < 512 or sz > 8_000_000:
                        continue
                    data = json.loads(fp.read_text(encoding="utf-8", errors="replace"))
                    keys_here: Set[str] = set()
                    extract_json_keys_recursive(data, keys_here)
                    if keys_here:
                        real_data_files += 1
                        real_keys |= keys_here
                        for k in keys_here:
                            m = STRUCTURED_PREFIX_KEY_RE.match(k)
                            if m:
                                real_prefixes.add(m.group(1))
                except Exception:
                    continue

            # 2. Python files: inspect test-injected keys AND production lookups (`.get(...)` / subscript)
            elif fp.suffix.lower() == ".py":
                role = classify_file_role(rel, "")
                try:
                    src = fp.read_text(encoding="utf-8", errors="replace")
                    tree = ast.parse(src, filename=rel)
                except Exception:
                    continue

                if role == "PROBES_AND_TESTS":
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Dict):
                            for k in node.keys:
                                hit = extract_key_prefix_from_node(k)
                                if hit:
                                    test_injected.setdefault(hit[0], set()).add(f"{rel}:{hit[1]}")
                        elif isinstance(node, ast.Assign):
                            for tgt in node.targets:
                                if isinstance(tgt, ast.Subscript):
                                    hit = extract_key_prefix_from_node(tgt.slice)
                                    if hit:
                                        test_injected.setdefault(hit[0], set()).add(f"{rel}:{hit[1]}")
                else:
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args:
                            hit = extract_key_prefix_from_node(node.args[0])
                            if hit:
                                prod_queried.setdefault(hit[0], set()).add(f"{rel}:{hit[1]}")
                        elif isinstance(node, ast.Subscript):
                            hit = extract_key_prefix_from_node(node.slice)
                            if hit:
                                prod_queried.setdefault(hit[0], set()).add(f"{rel}:{hit[1]}")

    # High-precision intersection: structured key prefixes BOTH queried by production code AND mocked by tests/gates
    # yet completely absent (0 occurrences) from real data JSON files!
    ignored_prefixes = {"TEST", "FIX", "LOT", "GATE", "STEP", "MOCK", "CASE", "RUN", "ERR", "MSG", "HTTP", "ENV", "CFG", "VER"}
    drift_alerts: List[Dict[str, Any]] = []
    if real_data_files > 0:
        candidate_prefixes = sorted((set(test_injected.keys()) & set(prod_queried.keys())) - real_prefixes - ignored_prefixes)
        for pref in candidate_prefixes:
            t_refs = sorted(test_injected[pref])
            p_refs = sorted(prod_queried[pref])
            drift_alerts.append({
                "prefix": f"{pref}_*",
                "prod_lookups": p_refs[:6],
                "test_mock_injections": t_refs[:6],
                "occurrences_in_real_data_jsons": 0,
                "real_data_json_files_checked": real_data_files,
            })

    return {
        "real_data_json_files_checked": real_data_files,
        "real_structured_prefixes_found": sorted(real_prefixes)[:20],
        "mock_schema_drift_count": len(drift_alerts),
        "mock_schema_drift": drift_alerts,
    }


def scan_workspace(project_dir: Path, custom_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    files_meta: Dict[str, Dict[str, Any]] = {}
    doc_files_meta: Dict[str, Dict[str, Any]] = {}
    corpus_sample: List[str] = []
    probe_contents: List[str] = []

    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS
            and not d.startswith(".git")
            and not d.lower().startswith(ARCHIVE_DIR_PREFIXES)
        ]
        for fname in sorted(files):
            fpath = Path(root) / fname
            ext = fpath.suffix.lower()
            if ext not in CODE_EXTS and ext not in DOC_EXTS:
                continue
            try:
                raw = fpath.read_bytes()
            except OSError:
                continue
            if len(raw) > 2_000_000:
                continue
            rel = str(fpath.relative_to(project_dir)).replace("\\", "/")
            sha = hashlib.sha256(raw).hexdigest()[:16]

            if ext not in CODE_EXTS:
                doc_files_meta[rel] = {"sha256": sha, "ext": ext, "bytes": len(raw), "role": "METIER_DOCUMENT"}
                if ext in (".md", ".json", ".yaml", ".yml"):
                    corpus_sample.append(raw.decode("utf-8", errors="replace").lower()[:3000])
                continue

            text = raw.decode("utf-8", errors="replace")
            low = text.lower()

            role = classify_file_role(rel, low)
            corpus_sample.append(low[:3000])
            if role == "PROBES_AND_TESTS":
                probe_contents.append(low)

            entry: Dict[str, Any] = {
                "sha256": sha,
                "ext": ext,
                "lines": text.count("\n") + 1,
                "role": role,
            }
            if ext == ".py":
                ast_info = analyze_python_ast(text, rel, role)
                entry["ast"] = {
                    "parse_error": ast_info["parse_error"],
                    "functions_count": len(ast_info["functions"]),
                    "boolean_hotspots_count": len(ast_info["boolean_hotspots"]),
                    "boolean_hotspots": ast_info["boolean_hotspots"][:10],
                    "elif_ladders_count": len(ast_info["elif_ladders"]),
                    "entity_exceptions_count": len(ast_info["entity_exceptions"]),
                    "entity_exceptions": ast_info["entity_exceptions"][:10],
                    "hardcoded_exclusions_count": len(ast_info["hardcoded_exclusions"]),
                    "hardcoded_exclusions": ast_info["hardcoded_exclusions"][:10],
                    "magic_literals_count": len(ast_info["magic_literals"]),
                    "magic_literals_sample": ast_info["magic_literals"][:12],
                    "fixed_caps_count": len(ast_info["fixed_caps"]),
                    "fixed_caps": ast_info["fixed_caps"][:10],
                    "silent_discards_count": len(ast_info["silent_discards"]),
                    "silent_discards": ast_info["silent_discards"][:10],
                    "frozen_state_latches_count": len(ast_info["frozen_state_latches"]),
                    "frozen_state_latches": ast_info["frozen_state_latches"][:10],
                    "stacked_clamps_count": len(ast_info["stacked_clamps"]),
                    "stacked_clamps": ast_info["stacked_clamps"][:10],
                }
            files_meta[rel] = entry

    joined_corpus = "\n".join(corpus_sample)
    if custom_profile:
        detected_domain = str(custom_profile.get("domain", "CUSTOM_DOMAIN"))
        eq = str(custom_profile.get("mass_balance_equation", DOMAIN_PROFILES["GENERAL_SOFTWARE"]["mass_balance_equation"]))
        brakes_list = list(custom_profile.get("mandatory_brakes_checklist", []))
    elif len(files_meta) == 0:
        detected_domain = "NON_CODE_METIER"
        eq = DOMAIN_PROFILES["NON_CODE_METIER"]["mass_balance_equation"]
        brakes_list = DOMAIN_PROFILES["NON_CODE_METIER"]["mandatory_brakes_checklist"]
    else:
        detected_domain = "GENERAL_SOFTWARE"
        best_hits = 0
        for dom, cfg in DOMAIN_PROFILES.items():
            if dom in ("GENERAL_SOFTWARE", "NON_CODE_METIER"):
                continue
            hits = sum(1 for kw in cfg["keywords"] if kw in joined_corpus)
            if hits > best_hits:
                best_hits = hits
                detected_domain = dom
        eq = DOMAIN_PROFILES[detected_domain]["mass_balance_equation"]
        brakes_list = DOMAIN_PROFILES[detected_domain]["mandatory_brakes_checklist"]

    joined_probes = "\n".join(probe_contents)
    unprobed_modules: List[str] = []
    for rel, meta in files_meta.items():
        if meta["role"] in ("EXECUTION_AND_FRICTION", "RISK_AND_SIZING", "CORE_LOGIC_OR_SIGNAL"):
            stem = Path(rel).stem.lower()
            if stem not in ("__init__", "main", "index") and stem not in joined_probes:
                unprobed_modules.append(rel)

    schema_parity = analyze_mock_vs_real_schema_parity(project_dir) if files_meta else {
        "real_data_json_files_checked": 0,
        "mock_schema_drift_count": 0,
        "mock_schema_drift": [],
    }

    tracked_files = files_meta if files_meta else doc_files_meta

    totals = {
        "code_files": len(files_meta),
        "metier_documents": len(doc_files_meta),
        "total_lines": sum(m.get("lines", 0) for m in files_meta.values()),
        "boolean_hotspots": sum(m.get("ast", {}).get("boolean_hotspots_count", 0) for m in files_meta.values()),
        "elif_ladders": sum(m.get("ast", {}).get("elif_ladders_count", 0) for m in files_meta.values()),
        "entity_exceptions": sum(m.get("ast", {}).get("entity_exceptions_count", 0) for m in files_meta.values()),
        "hardcoded_exclusions": sum(m.get("ast", {}).get("hardcoded_exclusions_count", 0) for m in files_meta.values()),
        "magic_literals": sum(m.get("ast", {}).get("magic_literals_count", 0) for m in files_meta.values()),
        "fixed_caps": sum(m.get("ast", {}).get("fixed_caps_count", 0) for m in files_meta.values()),
        "silent_discards": sum(m.get("ast", {}).get("silent_discards_count", 0) for m in files_meta.values()),
        "frozen_state_latches": sum(m.get("ast", {}).get("frozen_state_latches_count", 0) for m in files_meta.values()),
        "mock_schema_drift": schema_parity["mock_schema_drift_count"],
        "unprobed_critical_modules_count": len(unprobed_modules),
    }

    # Aggregate high-signal structural blind spots for immediate visibility
    blind_spots: Dict[str, Any] = {
        "silent_discards": [
            {"file": rel, **sd}
            for rel, meta in files_meta.items()
            for sd in meta.get("ast", {}).get("silent_discards", [])
        ][:20],
        "hardcoded_exclusions": [
            {"file": rel, **he}
            for rel, meta in files_meta.items()
            for he in meta.get("ast", {}).get("hardcoded_exclusions", [])
        ][:20],
        "frozen_state_latches": [
            {"file": rel, **fl}
            for rel, meta in files_meta.items()
            for fl in meta.get("ast", {}).get("frozen_state_latches", [])
        ][:20],
        "mock_schema_drift": schema_parity["mock_schema_drift"][:10],
        "stacked_clamps_advisory": [
            {"file": rel, **sc}
            for rel, meta in files_meta.items()
            for sc in meta.get("ast", {}).get("stacked_clamps", [])
        ][:15],
    }

    return {
        "engine_version": ENGINE_VERSION,
        "scanned_at": now_iso(),
        "project_dir": str(project_dir.resolve()),
        "mode": "CODE" if files_meta else "METIER",
        "detected_domain": detected_domain,
        "mass_balance_equation": eq,
        "mandatory_brakes_checklist": brakes_list,
        "totals": totals,
        "structural_blind_spots": blind_spots,
        "unprobed_critical_modules": unprobed_modules[:25],
        "files": tracked_files,
    }


def compute_drift(current: Dict[str, Any], baseline: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if baseline is None:
        return {
            "has_prior_baseline": False,
            "drift_detected": True,
            "domain_changed": False,
            "added_modules": sorted(current["files"].keys()),
            "removed_modules": [],
            "modified_modules": [],
            "ratchet_violations": [],
            "auto_generated_probe_requirements": [
                f"Initialize deterministic probe covering `{m}`" for m in current["unprobed_critical_modules"][:10]
            ],
        }

    old_files = baseline.get("files", {})
    cur_files = current.get("files", {})
    added = sorted(set(cur_files) - set(old_files))
    removed = sorted(set(old_files) - set(cur_files))
    modified = sorted(k for k in (set(cur_files) & set(old_files)) if cur_files[k]["sha256"] != old_files[k]["sha256"])

    domain_changed = baseline.get("detected_domain") != current.get("detected_domain")
    old_t = baseline.get("ratchet_ceilings", baseline.get("totals", {}))
    cur_t = current["totals"]

    violations: List[str] = []
    for key, label in (
        ("boolean_hotspots", "Boolean sprawl hotspots (>=6 clauses / band-aids)"),
        ("entity_exceptions", "Hardcoded entity/ticker cherry-picks in core logic"),
        ("hardcoded_exclusions", "Hardcoded exclusion/ban literal sets in core logic"),
        ("fixed_caps", "Fixed integer slice caps restricting scalability"),
        ("magic_literals", "Free numeric magic literals inside functions"),
        ("silent_discards", "Silent parameter discards (`_ = param`) dropping live inputs"),
    ):
        if key not in old_t:
            continue
        prev_max = int(old_t.get(key, 0))
        now_val = int(cur_t.get(key, 0))
        if now_val > prev_max:
            violations.append(f"RATCHET VIOLATION [{label}]: increased from {prev_max} to {now_val} (+{now_val - prev_max})")

    auto_reqs: List[str] = []
    for m in added:
        role = cur_files[m]["role"]
        if role != "PROBES_AND_TESTS":
            auto_reqs.append(f"New module detected '{m}' ({role}): deterministic verification probe required before production.")
    if domain_changed:
        auto_reqs.append(
            f"Domain shift detected ({baseline.get('detected_domain')} -> {current.get('detected_domain')}): "
            "updated conservation equation activated automatically."
        )

    return {
        "has_prior_baseline": True,
        "baseline_scanned_at": baseline.get("scanned_at"),
        "drift_detected": bool(added or removed or modified or domain_changed),
        "domain_changed": domain_changed,
        "added_modules": added,
        "removed_modules": removed,
        "modified_modules": modified,
        "ratchet_violations": violations,
        "auto_generated_probe_requirements": auto_reqs,
    }


def cmd_scan(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        sys.exit(f"Error: project directory not found: {project_dir}")

    ledger_dir = Path(args.ledger_dir).resolve() if args.ledger_dir else default_ledger_dir(project_dir)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = ledger_dir / "baseline.json"
    latest_path = ledger_dir / "latest_scan.json"
    custom_prof_path = ledger_dir / "custom_profile.json"

    custom_prof = json.loads(custom_prof_path.read_text(encoding="utf-8")) if custom_prof_path.exists() else None
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else None
    current = scan_workspace(project_dir, custom_profile=custom_prof)
    drift = compute_drift(current, baseline)

    ratchet_keys = ("boolean_hotspots", "entity_exceptions", "hardcoded_exclusions", "fixed_caps", "magic_literals", "silent_discards")
    if baseline is None:
        current["ratchet_ceilings"] = {k: current["totals"][k] for k in ratchet_keys}
        baseline_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        prev_ceil = baseline.get("ratchet_ceilings", baseline.get("totals", {}))
        tightened = {
            k: min(int(prev_ceil.get(k, current["totals"][k])), int(current["totals"][k]))
            for k in ratchet_keys
        }
        current["ratchet_ceilings"] = tightened
        updated_base = dict(current)
        updated_base["ratchet_ceilings"] = tightened
        baseline_path.write_text(json.dumps(updated_base, ensure_ascii=False, indent=2), encoding="utf-8")

    latest_path.write_text(json.dumps({"scan": current, "drift": drift}, ensure_ascii=False, indent=2), encoding="utf-8")

    hotspot_files = []
    for rel, meta in current["files"].items():
        ast_m = meta.get("ast", {})
        score = (
            ast_m.get("boolean_hotspots_count", 0) * 3
            + ast_m.get("entity_exceptions_count", 0) * 3
            + ast_m.get("hardcoded_exclusions_count", 0) * 5
            + ast_m.get("silent_discards_count", 0) * 5
            + ast_m.get("frozen_state_latches_count", 0) * 4
            + ast_m.get("fixed_caps_count", 0) * 3
            + ast_m.get("elif_ladders_count", 0) * 2
        )
        if score > 0 or ast_m.get("magic_literals_count", 0) >= 5:
            hotspot_files.append({
                "file": rel,
                "role": meta["role"],
                "boolean_hotspots": ast_m.get("boolean_hotspots_count", 0),
                "entity_exceptions": ast_m.get("entity_exceptions_count", 0),
                "hardcoded_exclusions": ast_m.get("hardcoded_exclusions_count", 0),
                "silent_discards": ast_m.get("silent_discards_count", 0),
                "frozen_state_latches": ast_m.get("frozen_state_latches_count", 0),
                "fixed_caps": ast_m.get("fixed_caps_count", 0),
                "magic_literals": ast_m.get("magic_literals_count", 0),
            })
    hotspot_files.sort(
        key=lambda x: (x["hardcoded_exclusions"], x["silent_discards"], x["frozen_state_latches"], x["boolean_hotspots"]),
        reverse=True,
    )

    summary = {
        "engine_version": ENGINE_VERSION,
        "project_dir": str(project_dir),
        "ledger_dir": str(ledger_dir),
        "detected_domain": current["detected_domain"],
        "mass_balance_equation": current["mass_balance_equation"],
        "mandatory_brakes_checklist": current["mandatory_brakes_checklist"],
        "totals": current["totals"],
        "ratchet_ceilings": current["ratchet_ceilings"],
        "structural_blind_spots": current["structural_blind_spots"],
        "drift": drift,
        "top_patchwork_hotspots": hotspot_files[:10],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if drift["ratchet_violations"] else 0


def cmd_schema_parity(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        sys.exit(f"Error: project directory not found: {project_dir}")
    res = analyze_mock_vs_real_schema_parity(project_dir)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 1 if res["mock_schema_drift_count"] > 0 else 0


def cmd_diff_audit(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    try:
        proc = subprocess.run(
            ["git", "-C", str(project_dir), "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, check=True, encoding="utf-8"
        )
        changed = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    except Exception as exc:
        print(json.dumps({"error": f"Git diff unavailable: {exc}"}))
        return 1

    file_audits: List[Dict[str, Any]] = []
    violations: List[str] = []

    for rel in changed:
        cur_path = project_dir / rel
        if not cur_path.exists() or cur_path.suffix.lower() != ".py":
            continue
        cur_text = cur_path.read_text(encoding="utf-8", errors="replace")
        role = classify_file_role(rel, cur_text.lower())
        cur_ast = analyze_python_ast(cur_text, rel, role)

        head_proc = subprocess.run(
            ["git", "-C", str(project_dir), "show", f"HEAD:{rel}"],
            capture_output=True, text=True, encoding="utf-8"
        )
        if head_proc.returncode == 0:
            old_ast = analyze_python_ast(head_proc.stdout, rel, role)
        else:
            old_ast = {
                "boolean_hotspots": [], "entity_exceptions": [], "hardcoded_exclusions": [],
                "magic_literals": [], "fixed_caps": [], "silent_discards": [],
            }

        d_bool = len(cur_ast["boolean_hotspots"]) - len(old_ast["boolean_hotspots"])
        d_ent = len(cur_ast["entity_exceptions"]) - len(old_ast["entity_exceptions"])
        d_exc = len(cur_ast["hardcoded_exclusions"]) - len(old_ast["hardcoded_exclusions"])
        d_mag = len(cur_ast["magic_literals"]) - len(old_ast["magic_literals"])
        d_cap = len(cur_ast["fixed_caps"]) - len(old_ast["fixed_caps"])
        d_disc = len(cur_ast["silent_discards"]) - len(old_ast["silent_discards"])

        if d_bool > 0:
            violations.append(f"{rel}: +{d_bool} giant boolean tree(s) (>=6 clauses)")
        if d_ent > 0:
            violations.append(f"{rel}: +{d_ent} hardcoded entity/ticker exception(s)")
        if d_exc > 0:
            violations.append(f"{rel}: +{d_exc} hardcoded exclusion/ban set(s)")
        if d_cap > 0:
            violations.append(f"{rel}: +{d_cap} fixed integer slice cap(s)")
        if d_mag > 0:
            violations.append(f"{rel}: +{d_mag} free numeric magic literal(s) added")
        if d_disc > 0:
            violations.append(f"{rel}: +{d_disc} silent parameter discard(s) (`_ = param`) added")

        file_audits.append({
            "file": rel,
            "role": role,
            "delta_boolean_hotspots": d_bool,
            "delta_entity_exceptions": d_ent,
            "delta_hardcoded_exclusions": d_exc,
            "delta_magic_literals": d_mag,
            "delta_fixed_caps": d_cap,
            "delta_silent_discards": d_disc,
        })

    result = {
        "status": "BLOCKED" if violations else "CLEAN",
        "changed_files_count": len(changed),
        "python_files_audited": file_audits,
        "violations": violations,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if violations else 0


def cmd_autopsy_gate(args: argparse.Namespace) -> int:
    autopsy = json.loads(Path(args.autopsy).read_text(encoding="utf-8"))
    project_name = str(autopsy.get("project", "Project"))

    probe_script = Path(str(autopsy.get("probe_script_path", "")))
    probe_output = Path(str(autopsy.get("probe_output_path", "")))
    probe_verified = (
        bool(str(autopsy.get("probe_script_path", "")).strip())
        and bool(str(autopsy.get("probe_output_path", "")).strip())
        and probe_script.is_file()
        and probe_output.is_file()
        and probe_output.stat().st_size > 10
    )

    total_gap = abs(float(autopsy.get("total_observed_gap", 0.0)))
    core_viability = float(autopsy.get("core_viability_at_zero_friction", 1.0))
    ns_target = autopsy.get("north_star_target")
    theo_ceil = autopsy.get("theoretical_zero_friction_ceiling")
    sub_scale = (
        ns_target is not None
        and theo_ceil is not None
        and float(theo_ceil) > 0.0
        and float(theo_ceil) < float(ns_target)
    )

    components = autopsy.get("measured_components", [])
    explained_sum = sum(abs(float(c.get("measured_impact", 0.0))) for c in components)
    explained_pct = round((explained_sum / total_gap) * 100.0, 1) if total_gap > 1e-9 else 100.0

    mechanical_impact = sum(
        abs(float(c.get("measured_impact", 0.0)))
        for c in components
        if str(c.get("category", "")).upper() != "CORE_SIGNAL_DECAY"
    )
    mechanical_share_pct = round((mechanical_impact / max(total_gap, 1e-9)) * 100.0, 1) if total_gap > 1e-9 else 0.0
    max_residual_stake_pct = float(autopsy.get("max_residual_stake_pct", mechanical_share_pct))
    has_mechanical_brakes = (
        bool(autopsy.get("unresolved_mechanical_brakes", False))
        or (mechanical_share_pct >= 15.0 and max_residual_stake_pct >= 5.0)
    )

    lines: List[str] = [f"## RootCause Deterministic Autopsy — `{project_name}`", ""]

    if not probe_verified:
        lines.append("> **❌ BLOCKED (GATE A1 — MISSING DISK PROBE)** : Probe script or output file does not exist on disk. Diagnosing from code reading alone is strictly prohibited.")
        print("\n".join(lines))
        return 2

    if total_gap > 1e-9 and explained_pct < 80.0:
        lines.append(f"> **❌ BLOCKED (GATE A2 — INCOMPLETE AUTOPSY: `{explained_pct}%` explained < `80%` required)** : Measured components do not yet isolate the true root cause. Refine telemetry before proposing any code change.")
        print("\n".join(lines))
        return 2

    if core_viability <= 0.0:
        lines.append(f"> **🛑 DEAD FOUNDATION AT ZERO FRICTION (`zero-friction viability = {core_viability} <= 0`)** : The core brick fails even before execution costs/frictions. **Adding filters or band-aids is strictly prohibited.** Valid actions: **Ablation (Delete)** or **Ground-Up Redesign**.")
        print("\n".join(lines))
        return 0

    if not has_mechanical_brakes and not sub_scale and max_residual_stake_pct < 5.0:
        lines.append(f"> **🛑 SOVEREIGN VERDICT: STOP — DO NOT TOUCH** (`max residual stake = {max_residual_stake_pct:.1f}% < 5.0%`, `0` open mechanical brake, healthy core foundation).")
        lines.append("> *Any further modification at this stage introduces overfitting or peripheral churn. Code freeze recommended.*")
        print("\n".join(lines))
        return 0

    if sub_scale:
        lines.append(f"> **⚠️ SUB-SCALE FOUNDATION (`theoretical ceiling = {theo_ceil}` < `North-Star target = {ns_target}`)** : Core is positive (`> 0`) but structurally below target. Core redesign unlocked; leverage/scaling on sub-scale core blocked.")
        lines.append("")

    lines.append(f"- **Verified Disk Probe** : `{probe_script.name}` → `{probe_output.name}` (`{explained_pct}%` of gap explained)")
    lines.append(f"- **Zero-Friction Core Viability** : `{'SUB-SCALE' if sub_scale else 'POSITIVE'} ({core_viability})`")
    lines.append(f"- **Active Mechanical Brakes** : `{has_mechanical_brakes}` (`{mechanical_share_pct}%` of gap from mechanical frictions)")
    lines.append("")

    if args.proposals and Path(args.proposals).is_file():
        prop_data = json.loads(Path(args.proposals).read_text(encoding="utf-8"))
        proposals = prop_data.get("proposals", [])
        lines.append("| ID | Proposal | `C1` Probe & Intact Core | `C2` Brakes First | `C3` Zero Magic/Patch | `C4` Stake >= 5% | Ablation Checked | Verdict |")
        lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |")
        for p in proposals:
            kind = str(p.get("kind", "CORE_FORMULA")).upper()
            touches_pos = bool(p.get("touches_already_positive_signal", False))
            if sub_scale and kind in ("CORE_REDESIGN", "CORE_FORMULA", "SIGNAL_FORMULA", "NEW_ALPHA_OR_VALUE_DRIVER"):
                touches_pos = False
            new_params = int(p.get("new_free_parameters", 0))
            window_tune = bool(p.get("post_hoc_window_tuning", False))
            plain = str(p.get("plain_economic_sentence", "")).strip()
            stake = float(p.get("estimated_stake_ratio_pct", 0.0))
            blocks_gate = bool(p.get("blocks_mandatory_gate", False))
            ablation_ok = bool(p.get("ablation_tested", False)) or kind in ("DEAD_CODE_PURGE", "ABLATION_SIMPLIFICATION")

            c1 = probe_verified and not touches_pos
            c2 = True if (sub_scale and kind in ("CORE_REDESIGN", "CORE_FORMULA", "SIGNAL_FORMULA", "NEW_ALPHA_OR_VALUE_DRIVER")) else (
                False if (has_mechanical_brakes and kind not in VALID_MECHANICAL_KINDS) else True
            )
            c3 = (new_params == 0) and (not window_tune) and (len(plain) >= 15)
            c4 = (stake >= 5.0) or blocks_gate

            if not c1 or not c2 or not c3:
                verdict = "❌ BLOCKED (OVERKILL / PATCH)"
            elif not ablation_ok and bool(autopsy.get("target_module_has_hotspots", False)):
                verdict = "⚠️ RUN ABLATION TEST FIRST"
            elif c4:
                verdict = "✅ VALIDATED & CRITICAL"
            else:
                verdict = "⚠️ VALIDATED — MINOR"

            lines.append(
                f"| **`{p.get('id', 'FIX')}`** | **{p.get('title', '')}**<br>*({plain})* | "
                f"{'✅' if c1 else '❌'} | {'✅' if c2 else '❌'} | {'✅' if c3 else '❌'} | "
                f"{'✅' if c4 else '⚠️'} | {'✅' if ablation_ok else '⚠️'} | **{verdict}** |"
            )

    print("\n".join(lines))
    return 0


def cmd_ack_ratchet(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    ledger_dir = Path(args.ledger_dir).resolve() if args.ledger_dir else default_ledger_dir(project_dir)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    current = scan_workspace(project_dir)
    ratchet_keys = ("boolean_hotspots", "entity_exceptions", "hardcoded_exclusions", "fixed_caps", "magic_literals", "silent_discards")
    current["ratchet_ceilings"] = {k: current["totals"][k] for k in ratchet_keys}
    current["ratchet_ack"] = {"at": now_iso(), "user_reason": args.reason}
    (ledger_dir / "baseline.json").write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "RATCHET_REBASELINED_WITH_USER_CONSENT", "ceilings": current["ratchet_ceilings"]}, ensure_ascii=False, indent=2))
    return 0


def cmd_register_domain(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    ledger_dir = Path(args.ledger_dir).resolve() if args.ledger_dir else default_ledger_dir(project_dir)
    ledger_dir.mkdir(parents=True, exist_ok=True)
    invs = [s.strip() for s in args.invariants.split("|") if s.strip()]
    prof = {
        "registered_at": now_iso(),
        "verified_at_run_id": args.verified_at_run_id,
        "domain": args.domain,
        "mass_balance_equation": args.equation,
        "mandatory_brakes_checklist": invs,
    }
    out = ledger_dir / "custom_profile.json"
    out.write_text(json.dumps(prof, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "CUSTOM_DOMAIN_LOCKED", "profile_path": str(out), "profile": prof}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="RootCause Guard v3.2 — AST, Structural Blind-Spots, Schema Parity & Autopsy CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="Read-only AST, structural blind-spots & drift scan of any workspace")
    p_scan.add_argument("--project-dir", required=True)
    p_scan.add_argument("--ledger-dir", default="")
    p_scan.set_defaults(func=cmd_scan)

    p_sp = sub.add_parser("schema-parity", help="Audit test/gate mock keys against real data JSON files")
    p_sp.add_argument("--project-dir", required=True)
    p_sp.set_defaults(func=cmd_schema_parity)

    p_diff = sub.add_parser("diff-audit", help="Audit uncommitted git diff against HEAD via AST")
    p_diff.add_argument("--project-dir", required=True)
    p_diff.set_defaults(func=cmd_diff_audit)

    p_gate = sub.add_parser("autopsy-gate", help="Run 80% Mass-Balance, 3-State Foundation Ceiling, Ablation & STOP gates")
    p_gate.add_argument("--autopsy", required=True)
    p_gate.add_argument("--proposals", default="")
    p_gate.set_defaults(func=cmd_autopsy_gate)

    p_ack = sub.add_parser("ack-ratchet", help="Re-baseline ratchet ceilings ONLY after explicit user consent")
    p_ack.add_argument("--project-dir", required=True)
    p_ack.add_argument("--reason", required=True)
    p_ack.add_argument("--ledger-dir", default="")
    p_ack.set_defaults(func=cmd_ack_ratchet)

    p_reg = sub.add_parser("register-domain", help="Register custom domain physics & invariants for any bespoke project")
    p_reg.add_argument("--project-dir", required=True)
    p_reg.add_argument("--domain", required=True)
    p_reg.add_argument("--equation", required=True)
    p_reg.add_argument("--invariants", required=True, help="Pipe-separated (|) mandatory invariants")
    p_reg.add_argument("--verified-at-run-id", default="", help="Latest empirical run ID this profile was verified against")
    p_reg.add_argument("--ledger-dir", default="")
    p_reg.set_defaults(func=cmd_register_domain)

    return p


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    ns = parser.parse_args()
    raise SystemExit(ns.func(ns))
