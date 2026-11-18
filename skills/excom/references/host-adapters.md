# Host Platform Execution Adapters (Cross-Agent Compatibility)

`ExCom` is an open `SKILL.md` package designed to run across **Google Antigravity**, **Claude Code**, **OpenAI Codex**, **Cursor**, **Gemini CLI**, and standard chat environments.

Because subagents execute **concurrently**, mobilizing a complete **6-to-12 seat Dual-Circle ExCom** (*Domain Drivers + 360° Risk Shield + 3 Wildcards*) takes virtually the same wall-clock latency as running 4 seats—while eliminating Financial, Legal, Operational, Technical, and Human blind spots.

---

## Adapter A — Native Parallel Subagents / Workflows (Preferred)

Use this path whenever your agent environment exposes a multi-agent workflow engine or parallel subagent tool:

### 1. Google Antigravity (`run_workflow` or `invoke_subagent`)
Prefer `run_workflow` with `parallel(...)` and a structured JSON schema so all summoned seats run concurrently in isolated contexts:

```python
MEMO_SCHEMA = {
    "type": "object",
    "properties": {
        "circle": {"type": "string", "enum": ["DOMAIN_DRIVER", "RISK_SHIELD", "WILDCARD"]},
        "seat": {"type": "string"},
        "stance": {"type": "string", "enum": ["CLEAR", "GO", "CONDITIONAL GO", "NO-GO / VETO"]},
        "core_analysis": {
            "type": "string",
            "description": "If CLEAR: <=25-word 1-line sign-off. Otherwise: <=120-word concrete analysis.",
        },
        "signature_angle": {"type": "string"},
        "non_negotiable": {"type": "string"},
    },
    "required": ["circle", "seat", "stance", "core_analysis", "non_negotiable"],
}

phase("Round 1 — Blind Parallel ExCom & 360° Risk Audit")
memos = await parallel(
    seats,
    lambda s: agent(
        prompt=s["brief"],
        schema=MEMO_SCHEMA,
        role=f"[{s['circle']}] {s['title']}",
    ),
)
for m in memos:
    log(m)
```
- Pass the full decision context, user language requirement, domain lens (`Corporate` vs `Personal / Life`), circle assignment (`DOMAIN_DRIVER`, `RISK_SHIELD`, or `WILDCARD`), and that specific seat's mandate from `wildcards.md` / `c-suite-roster.md` inside `s["brief"]`.
- Explicitly instruct `RISK_SHIELD` seats in `s["brief"]`: *"If your domain has no material threat or hidden friction on this decision, return `stance: 'CLEAR'` with a single 1-line safeguard instead of inventing filler objections."*
- If a Round-2 clash is needed between opposing seats (e.g., a `NO-GO / VETO` from `CFO` or `CLO` vs `GO` from `CPO` / `OPTIMIST`), run a brief `Phase 2 — Clash` passing only the conflicting Round-1 memos to those specific seats.

### 2. Claude Code (`Task` Subagents)
- Emit **all** `Task` tool calls for the summoned ExCom seats (Domain Drivers + 360° Risk Shield + 3 Wildcards) **in a single assistant turn** so Claude Code executes them concurrently with isolated context windows.
- Give each `Task` a self-contained prompt containing: (a) the framed decision + facts, (b) the user's language, (c) that single seat's mandate & red line, and (d) the Two-Tier Memo Contract (`CLEAR` in 1 line if green; otherwise `GO` / `CONDITIONAL GO` / `NO-GO / VETO` in `<= 150 words` with 1 `Non-Negotiable Condition`).

### 3. OpenAI Codex / Cursor / Other Multi-Agent CLIs
- Spawn one parallel subagent/worker per summoned seat with isolated prompts following the exact same Two-Tier Memo Contract above, then synthesize as CEO once all workers return.

---

## Adapter B — Strict Compartmentalized Fallback (Single-Agent Environments)

If—and **only** if—your current runtime has **no** subagent or workflow tool (e.g., web chat, standard IDE chat without subagents, or subagents disabled):

1. Still audit **all 3 Circles** (*Domain Drivers*, the *5-Vector Risk Shield [Financial, Legal, Operational, Human, Systemic/Cyber]*, and the *3 Wildcards*)—never drop Finance, Legal, or Ops to save space.
2. Apply the **`CLEAR` Fast-Signoff Rule** strictly: clear green risk vectors in 1 compact line, and dedicate full analytical depth (`<= 150 words` per seat) to the seats with genuine levers, tensions, conditions, or vetoes.
3. Require `DEVIL` to argue the sharpest pre-mortem failure chain, `OPTIMIST` to push the 10x asymmetric lever, and `OUTSIDER` to propose a non-obvious third door before stepping back into the `CEO` synthesis.
