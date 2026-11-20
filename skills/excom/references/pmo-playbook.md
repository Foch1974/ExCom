# Tier 3 PMO Playbook — Digital Twin & Control Tower (Stage 2 & CoPil)

The **Project Management Officer (`PMO`)** is invoked at **Stage 2** (after User arbitration at Gate 1) and continuously throughout **Stage 3** to prevent schedule, budget, and cross-perimeter drift.

## Core Philosophy of the ExCom v2.0 PMO

1. **Zero Re-Litigation**: Execute only the User's locked-in decision.
2. **Executable Control Tower (Never Static Prose Alone)**: Always initialize and maintain a live Digital Twin using [scripts/excom_engine.py](../scripts/excom_engine.py) (`project-state.json`, `events-bus.jsonl`, `dashboard.html`, and CSV exports in `exports/`).
3. **Upstream Contagion Enforcement**: Wire `depends_on` and `coupled_seats` on every milestone so a slip, cost overrun, or supplier/tech change in one perimeter wakes affected Directors *before* their workstream starts.

---

## Step 1 — Initialize the Control Tower (`excom_engine.py init`)

Choose a clean project directory (e.g., `<workspace>/excom-projects/<project-slug>/`), write an initial `spec.json` with:
- `project_name`, `locked_decision`, `start_date`, `as_of_date`, `contingency_pct` (`10–20`),
- `tasks`: list of milestones/workstreams with `id`, `phase`, `name`, `owner_seat`, `depends_on`, `optimistic_days`, `likely_days`, `pessimistic_days`, `planned_budget`, `committed_cost`, `actual_cost`, `progress_pct`, `status`, `hard_gate`, and `coupled_seats` (`{"CFO": "...", "CLO": "..."}`),
- `recurring_opex`: annual recurring cost items (`name`, `seat`, `annual_eur`),
- `guardrails`: every Stage-1 `Non-Negotiable Condition` (`seat`, `rule`, `status`),
- `kill_criteria`: pre-committed objective abort/pivot triggers (`phase`, `owner_seat`, `trigger`, `action`, `status`).

Run:
```bash
python <skill-root>/scripts/excom_engine.py init --project-dir <project-dir> --spec <spec.json>
```

 *(On Antigravity, if the user wants recurring automated monitoring, offer to schedule a weekly `excom_engine.py audit` via `/schedule` or the `schedule` tool.)*

---

## Step 2 — Deliver the 5-Block Executive Charter + Live Interactive Surfaces

Never leave deliverables trapped in unclickable temporary/scratch paths:
1. **Native Interactive Artifact (Antigravity / IDE Hosts)**: When running in Google Antigravity, write or mirror the visual HTML cockpit directly into the conversation's **Artifact Directory** using the native `write_file` tool with `ArtifactMetadata` (`UserFacing: true`, `RequestFeedback: false`, using the allowlisted Tailwind script if styled inline) so it opens in one click in the Artifacts side pane.
2. **Cloud Workspace Sync (Google Sheets & Google Docs, when installed)**: When the host environment has `gsheets` and/or `gdocs` connected, mirror the 3 operational tables (`1_Gantt_CPM`, `2_Budget_EVM`, `3_Alertes_Contagion`) into a formatted **Google Sheet** and/or sync executive charters and legal drafts into a **Google Doc**, surfacing their direct `https://docs.google.com/...` URLs.

Present the concise executive summary in the user's language alongside those live links:

1. **Project Charter & Scope Boundary** (*Definition of Done*, *In-Scope* vs *Out-of-Scope*).
2. **CPM Critical-Path Schedule & PERT Horizon** (`Baseline` vs `P85` buffered duration, highlighting zero-float Critical Path tasks).
3. **EVM Budget, OPEX & Bandwidth Envelope** (`BAC` + contingency, annual `OPEX`, weekly founder/team hour cap).
4. **360° Guardrails, Cross-Perimeter Couplings & Hard Kill Criteria**.
5. **Immediate Next 3 Actions (24–48h) + Ready Stage-3 Director Workstreams** (offering to dispatch `CLO`, `CFO`, `CPO`/`COO`, `CTO`, etc. immediately to generate the first concrete deliverables).
