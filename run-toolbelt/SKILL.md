---
name: run-toolbelt
description: >
  End-to-end walkthrough for getting started with Toolbelt via MCP tools.
  Covers provisioning credentials, selecting a namespace, uploading documents,
  connecting a Kafka data source, and asking questions over the ingested data.
  Use when the user wants to try, demo, or onboard to Toolbelt for the first time,
  or when they want to add assets, connect a streaming source, or run queries
  through any MCP-capable agent.
license: MIT
compatibility: >
  Requires a Toolbelt account (provision free at https://toolbelt.ai) and an
  MCP-compatible AI agent (Claude Code, Claude Desktop, OpenClaw, or any client
  that supports MCP server connections).
metadata:
  author: toolbeltai
  version: "1.0"
---

Walk the user through Toolbelt end-to-end using the Toolbelt MCP tools.
Work through each phase in order. Ask the user for required inputs before calling tools.
Confirm completion of each phase before moving to the next.

---

## Phase 0: Provision Credentials

Check if the user already has a Toolbelt `mcpUrl` and `token`.

If not, provide two options:

**Option A — Terminal (fastest):**
```bash
curl --request POST \
  --url https://toolbelt.ai/api/onboard \
  --header 'content-type: application/json' \
  --data '{}'
```

**Option B — Browser:**
Visit https://toolbelt.ai and click **Try Now**.

Both return a response like:
```json
{
  "success": true,
  "user": { "id": "@anon_..." },
  "namespace": { "id": "ab2b1392-...", "name": "Default Workspace" },
  "mcpUrl": "https://edge-mcp.toolbelt.ai/...",
  "token": "tb_...",
  "expiresAt": "2026-..."
}
```

Save the `mcpUrl`, `token`, and `namespace.id`.

> **Important:** Trial instances expire after 72 hours. The user must visit https://toolbelt.ai with their token to claim a permanent account before then.

**Configuring your MCP client:**

| Client | How to configure |
|---|---|
| Claude Code | Add to `.claude/settings.json` → `mcpServers`: `{ "url": "<mcpUrl>", "headers": { "Authorization": "Bearer <token>" } }` |
| Claude Desktop | Add server entry in `claude_desktop_config.json` with `url` and `Authorization` header |
| OpenClaw | Paste `mcpUrl` as server URL; add `Authorization: Bearer <token>` as a custom header |
| Any MCP client | Server URL = `mcpUrl`, auth = `Bearer <token>` in the `Authorization` header |

Confirm MCP tools are reachable before proceeding.

---

## Phase 1: Confirm Namespace

Call `get_semantic_names` (no arguments) to retrieve the list of namespaces the user has access to.

Present the list to the user and ask which namespace to use.
If there is only one, confirm it and continue.

Store the chosen `namespace_id` (a UUID) — pass it to every subsequent tool call.
Never use the display name as the ID.

---

## Phase 2: Inspect Current State

Call `toolbelt_context` with the chosen `namespace_id`.

Summarize what already exists:
- Relational tables (from `relevant_tables` and `table_schemas`)
- Vector collections (from `collections`)
- Domain summary and any suggested prompts

This gives the user a baseline before adding anything new.

---

## Phase 3: Add a Document Asset

Ask the user for one of:
- **Text content** — paste or dictate the document text directly
- **Public URL** — a publicly accessible link to a file (PDF, DOCX, etc.)

Also ask for:
- A short asset name
- An optional description

Then call `toolbelt_save`:

**From text content:**
```json
{
  "asset_type": "document",
  "namespace_id": "<namespace_id>",
  "name": "<asset name>",
  "description": "<description>",
  "file_name": "document.txt",
  "content": "<text content>",
  "content_encoding": "text"
}
```

**From a public URL:**
```json
{
  "asset_type": "document",
  "namespace_id": "<namespace_id>",
  "name": "<asset name>",
  "description": "<description>",
  "file_name": "document.pdf",
  "file_url": "<public URL to file>"
}
```

After saving, poll `toolbelt_jobs` until the job chain completes:
```json
{ "namespace_id": "<namespace_id>" }
```

Job chain: `ingest` (parse + store) → `semantic` (embed + extract entities). Both must reach `completed`.
Typically takes 30–120 seconds. Poll every 10 seconds.

Once complete, call `toolbelt_context` again to confirm the new asset's table appears.

---

## Phase 4: Connect a Kafka Source

Ask the user for:
1. Kafka broker URL (e.g. `kafka-broker:9092`)
2. Topic name (e.g. `events`)
3. Column schema as a SQL-style string (e.g. `id INTEGER, event VARCHAR(256), ts TIMESTAMP`)
4. Consumer group ID (optional — pass as `extra_options: { "kafka.group.id": "<group>" }`)
5. Ingestion mode — **subscribe** (continuous streaming) or **one-shot** (load current messages and stop)

Then call `toolbelt_connect`:
```json
{
  "source_type": "kafka",
  "namespace_id": "<namespace_id>",
  "location": "KAFKA://<broker>",
  "external_table_name": "<topic name>",
  "asset_name": "<friendly name>",
  "kafka_column_definitions": "<SQL column list>",
  "kafka_subscribe": true
}
```

Verify the table is queryable with `toolbelt_execute`:
```json
{
  "namespace_id": "<namespace_id>",
  "query": "SELECT COUNT(*) FROM <external_table_name> LIMIT 1"
}
```

---

## Phase 5: Ask a Question

Ask the user what question they want answered — it can span documents, Kafka events, or both.

Call `toolbelt_search`:
```json
{
  "question": "<user's question>",
  "namespace_id": "<namespace_id>",
  "synthesize": true
}
```

Display the synthesized answer, including any SQL generated and source documents cited.

Offer next steps:
- **Raw SQL:** `toolbelt_execute` with `{ "namespace_id": "...", "query": "SELECT ..." }`
- **Schema exploration:** `toolbelt_context` to inspect tables and embeddings config
- **Vector search:** `toolbelt_vectors` with `{ "namespace_id": "...", "question": "..." }`
- **Graph traversal:** `toolbelt_graph` for entity relationship queries

---

## Summary

| Phase | Tool(s) |
|---|---|
| 0. Provision credentials | (curl or browser) |
| 1. Confirm namespace | `get_semantic_names` |
| 2. Inspect state | `toolbelt_context` |
| 3. Add document | `toolbelt_save`, `toolbelt_jobs`, `toolbelt_context` |
| 4. Connect Kafka | `toolbelt_connect`, `toolbelt_execute` |
| 5. Ask a question | `toolbelt_search` |
