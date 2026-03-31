---
name: multi-agent-workspace
description: >
  Multi-agent collaboration demo via Toolbelt MCP. Uploads a shared document,
  generates a shareable asset URL, and emits connection instructions for a
  second agent to join the same namespace and query the same data. Demonstrates
  the collaboration story — two agents, one workspace — without requiring a
  second live MCP session.
license: MIT
compatibility: >
  Requires a Toolbelt account (provision free at https://toolbelt.ai) and an
  MCP-compatible AI agent (Claude Code, Claude Desktop, or any client that
  supports MCP server connections). MCP connection must be pre-established
  before invocation.
metadata:
  author: toolbeltai
  version: "1.0"
---

Set up a shared workspace and generate collaboration artifacts using Toolbelt
MCP tools. Work through each phase in order without prompting for user input.
On unrecoverable error, emit a structured failure and halt.

## Invocation Parameters

Extract these from the args string or conversation context before starting:

| Parameter | Required | Description |
|---|---|---|
| `namespace_id` | No | UUID of target namespace. Auto-select if omitted and only one exists; fail if ambiguous. |
| `document_content` | No | Raw text to upload as the shared document. Uses the embedded sample if omitted. |
| `document_name` | No | Name for the shared document asset. Defaults to `shared-workspace-doc`. |
| `expires_in_days` | No | Days until the share link expires. Defaults to `7`. |

---

## Default Sample Document

If no `document_content` is provided, use this research briefing verbatim:

```
Project Aurora: Q1 Research Briefing

This briefing summarizes findings from the Aurora team's Q1 initiative on
sustainable materials for industrial packaging.

Key findings:
- Bio-composite material BX-14 achieved 87% tensile strength retention after
  6 months in humid storage conditions, outperforming the baseline polymer by 22%.
- Pilot production run at the Riverside facility yielded 94% defect-free units,
  meeting the target threshold of 90% set by the operations team.
- Cost per unit for BX-14 is currently $0.42, compared to $0.31 for the baseline.
  The team projects cost parity by Q3 as production volume scales.

Risks identified:
- Supplier lead time for BX-14 precursors is 14 weeks, creating potential
  inventory gaps if demand spikes. Procurement has been notified.
- Field testing in sub-zero conditions (-15°C) is pending. Results expected by
  end of April.

Next steps:
- Dr. Maya Patel (materials lead) to complete cold-weather field tests by April 30.
- Operations team to submit revised unit cost forecast by April 15.
- Executive review scheduled for May 8, presenting go/no-go recommendation for
  full-scale production in Q3.

Prepared by: Aurora Research Team
Date: March 28, 2024
Classification: Internal — Project Team Only
```

---

## Phase 0: Verify Connection

Call `get_semantic_names` (no arguments) immediately.

- **If it succeeds:** proceed to Phase 1 using the returned namespaces.
- **If it fails:** emit structured failure and halt.

```
FAILURE: Toolbelt MCP connection is not established.
The MCP server must be connected before invoking this skill.
See: https://toolbelt.ai/docs/mcp for setup instructions.
```

---

## Phase 1: Resolve Namespace

Use the namespaces returned from Phase 0.

Resolution order:
1. If `namespace_id` was provided as a parameter, use it directly.
2. If only one namespace exists, use it.
3. If multiple exist and no `namespace_id` was specified, emit structured failure and halt.

```
FAILURE: Multiple namespaces found and none specified.
Available: [<list namespace display names and IDs>]
Re-invoke with namespace_id=<uuid>.
```

Store the resolved `namespace_id` and the namespace display name — both appear in the RESULT.

---

## Phase 2: Upload Shared Document

Resolve `document_content` (use parameter value or default sample above).
Resolve `document_name` (use parameter value or default `shared-workspace-doc`).

Call `toolbelt_save`:

```json
{
  "asset_type": "document",
  "namespace_id": "<namespace_id>",
  "name": "<document_name>",
  "file_name": "document.txt",
  "content": "<document_content>",
  "content_encoding": "text"
}
```

Record the returned `asset_id` — it is required for `toolbelt_share` in Phase 4.

---

## Phase 3: Poll for Ingestion

Call `toolbelt_jobs` with `{ "namespace_id": "<namespace_id>" }` every 10 seconds.

Wait for the `ingest` job to reach `completed`. Maximum wait: 3 minutes.

If the job reaches `failed` or the timeout elapses, emit structured failure and halt:
```
FAILURE: Document ingestion did not complete.
Job status: <last observed status>
```

---

## Phase 4: Generate Share URL

Call `toolbelt_share` with the `asset_id` from Phase 2:

```json
{
  "namespace_id": "<namespace_id>",
  "asset_id": "<asset_id>",
  "expiresInDays": <expires_in_days or 7>
}
```

Parse the response to extract:
- `share_url`: the shareable download/view link for the document
- `expires_at`: expiration date of the link (if returned)

If the call fails, emit structured failure and halt:
```
FAILURE: toolbelt_share failed.
Error: <error message>
```

---

## Phase 5: Structured Output

After all phases complete, emit a single structured result followed by
second-agent connection instructions.

```
RESULT:
  namespace_id: <uuid>
  namespace_name: <display name>
  document_name: <name of uploaded document>
  asset_id: <uuid of the uploaded asset>
  phases_run: [0, 1, 2, 3, 4]

  share_url: <URL returned by toolbelt_share>
  expires_in_days: <days until expiry>

  second_agent_instructions:
    connect_via: "MCP server configured to point at https://toolbelt.ai"
    namespace_id: <uuid>
    steps:
      1. "Configure the MCP server with your Toolbelt API key"
      2. "Pass namespace_id=<uuid> to scope the agent to this workspace"
      3. "Call toolbelt_context to see the shared document in the namespace"
      4. "Call toolbelt_search to ask questions about the shared document"
    note: "Both agents share the same namespace — any document, table, or query
           result one agent uploads is immediately visible to the other."
```

---

## Tool Reference

| Phase | Tool(s) |
|---|---|
| 0. Verify connection | `get_semantic_names` |
| 1. Resolve namespace | (from Phase 0 result) |
| 2. Upload document | `toolbelt_save` |
| 3. Poll for ingestion | `toolbelt_jobs` |
| 4. Generate share URL | `toolbelt_share` |
| 5. Emit result | (structured output) |
