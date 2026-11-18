# Host Platform Execution Adapters (Cross-Agent Compatibility)

`ExCom` is an open `SKILL.md` package designed to run across **Google Antigravity**, **Claude Code**, **OpenAI Codex**, **Cursor**, **Gemini CLI**, and standard chat environments.

To guarantee **true Round-1 cognitive independence** (preventing early anchors from biasing later advisors), dispatch all summoned seats using the highest-isolation mechanism supported by your current runtime:

---

## Adapter A — Native Parallel Subagents / Workflows (Preferred)

Use this path whenever your agent environment exposes a multi-agent workflow engine or parallel subagent tool:

### 1. Google Antigravity (`run_workflow` or `invoke_subagent`)
Prefer `run_workflow` with `parallel(...)` and a structured JSON schema so all 5–7 summoned advisors run concurrently in isolated contexts:

```python
MEMO_SCHEMA = {
    "type": "object",
    "properties": {
        "seat": {"type": "string"},
        "stance": {"type": "string", "enum": ["GO", "CONDITIONAL GO", "NO-GO / VETO"]},
        "core_analysis": {"type": "string"},
        "signature_angle": {"type": "string"},
        "non_negotiable": {"type": "string"},
    },
    "required": ["seat", "stance", "core_analysis", "signature_angle", "non_negotiable"],
}

phase("Round 1 — Blind ExCom Deliberation")
memos = await parallel(
    seats,
    lambda s: agent(
        prompt=s["brief"],
        schema=MEMO_SCHEMA,
        role=s["title"],
    ),
)
for m in memos:
    log(m)
```
- Pass the full decision context, user language requirement, domain lens (`Corporate` vs `Personal / Life`), and that specific seat's mandate from `wildcards.md` / `c-suite-roster.md` inside `s["brief"]` (isolated agents do not see the parent conversation or each other).
- If a Round-2 clash is needed between two opposing seats, run a brief `Phase 2 — Clash` passing only the two conflicting Round-1 memos to those two seats.

### 2. Claude Code (`Task` Subagents)
- Emit **all** `Task` tool calls for the 5–7 summoned ExCom seats **in a single assistant turn** so Claude Code executes them concurrently with isolated context windows.
- Give each `Task` a self-contained prompt containing: (a) the framed decision + facts, (b) the user's language, (c) that single seat's mandate & red line, and (d) the `<= 150-word` Memo Contract (`Stance`, `Core Analysis`, `Signature Angle`, `Non-Negotiable Condition`).

### 3. OpenAI Codex / Cursor / Other Multi-Agent CLIs
- Spawn one parallel subagent/worker per summoned seat with isolated prompts following the exact same self-contained Memo Contract above, then synthesize as CEO once all workers return.

---

## Adapter B — Strict Compartmentalized Fallback (Single-Agent Environments)

If—and **only** if—your current runtime has **no** subagent or workflow tool (e.g., web chat, standard IDE chat without subagents, or subagents disabled):

1. Explicitly commit to **zero cross-contamination** before generating memos.
2. Generate each summoned seat's memo strictly from that seat's incentive structure and Red Line—forcing genuine disagreement rather than polite convergence.
3. Require at least `DEVIL` to argue the strongest possible `NO-GO / VETO` or `CONDITIONAL GO` pre-mortem, `OPTIMIST` to push the 10x asymmetric lever, and `OUTSIDER` to propose a non-obvious third option before stepping back into the `CEO` synthesis.
