---
name: toolbelt-start
description: >
  Provision a Toolbelt namespace, ingest a document or Kafka stream, and answer
  a question end-to-end — autonomously, without human steps. Use when an agent
  needs to set up a fresh Toolbelt workspace, add assets from scratch, connect a
  streaming source, or run a complete ingest→query pipeline. NOT for querying
  data that is already ingested — use toolbelt-analyze, toolbelt-find, or
  toolbelt-entities for that.
license: MIT
compatibility: >
  Requires a Toolbelt account (provision free at https://toolbelt.ai) and an
  MCP-compatible AI agent (Claude Code, Claude Desktop, OpenClaw, or any client
  that supports MCP server connections). MCP connection must be pre-established
  before invocation.
version: "2.0.0"
metadata:
  author: toolbeltai
  homepage: "https://toolbelt.ai/docs/mcp"
---

Execute Toolbelt end-to-end autonomously using the Toolbelt MCP tools.
Work through each phase in order. Extract all required inputs from task parameters
or invocation context — do not prompt for user input. Progress through phases
without confirmation. On unrecoverable error, emit a structured failure and halt.

## When Not To Use

- When the Toolbelt MCP connection is not yet established — the connection must exist before invocation.
- When you only need to query data already in Toolbelt — use `toolbelt-analyze` instead.
- When you only need to upload and analyze a CSV — use `toolbelt-analyze` instead.

## Invocation Parameters

Extract these from the args string or conversation context before starting:

| Parameter | Required | Description |
|---|---|---|
| `namespace_id` | No | UUID of target namespace. Auto-select if omitted and only one exists; fail if ambiguous. |
| `document_content` | No* | Raw text content to upload as a document asset |
| `document_url` | No* | Public URL to a file (PDF, DOCX, etc.) to upload |
| `document_name` | No | Name for the document asset. Derive from URL filename or generate if omitted. |
| `kafka_broker` | No | Kafka broker URL (e.g. `kafka-broker:9092`) |
| `kafka_topic` | No | Kafka topic name |
| `kafka_schema` | No | SQL-style column schema (e.g. `id INTEGER, event VARCHAR(256), ts TIMESTAMP`) |
| `kafka_group_id` | No | Kafka consumer group ID |
| `question` | No | Question to ask over ingested data in Phase 5 |

*At least one of `document_content` or `document_url` is required to run Phase 3.
Skip Phase 3 if neither is provided. Skip Phase 4 if Kafka parameters are absent.
Skip Phase 5 if `question` is absent.

---

## Phase 0: Verify Connection

Call `toolbelt_list_namespaces` (no arguments) immediately.

- **If it succeeds:** proceed to Phase 1 using the returned namespaces.
- **If it fails:** emit structured failure and halt.

```
FAILURE: Toolbelt MCP connection is not established.
The MCP server must be connected before invoking this skill.
See: https://toolbelt.ai/docs/mcp for setup instructions.
```

Do not attempt reconnection or emit manual setup instructions. The connection
is an environment contract that must be satisfied before invocation.

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

Store the resolved `namespace_id` — pass it to every subsequent tool call.
Never use the display name as the ID.

---

## Phase 2: Inspect Current State

Call `toolbelt_context` with the resolved `namespace_id`.

Store the returned context internally:
- Relational tables (`relevant_tables`, `table_schemas`)
- Vector collections (`collections`)
- Domain summary and suggested prompts

Do not output a summary unless this is the only phase being run.

---

## Phase 3: Add a Document Asset

Skip this phase if neither `document_content` nor `document_url` was provided.

Derive `document_name` from URL filename if not provided. If content was provided
directly and no name exists, use `document-<ISO timestamp>`.

Call `toolbelt_save`:

**From text content:**
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

**From a public URL:**
```json
{
  "asset_type": "document",
  "namespace_id": "<namespace_id>",
  "name": "<document_name>",
  "file_name": "<filename from URL>",
  "file_url": "<document_url>"
}
```

### Poll for completion

Call `toolbelt_jobs` with `{ "namespace_id": "<namespace_id>" }` every 10 seconds.

Job chain: `ingest` (parse + store) → `semantic` (embed + extract entities). Both must reach `completed`.
Typical duration: 30–120 seconds. Maximum wait: 5 minutes.

If either job reaches `failed` or the timeout elapses, emit structured failure and halt:
```
FAILURE: Document ingestion did not complete.
Job status: <last observed status>
```

Once complete, call `toolbelt_context` again to confirm the new asset's table appears.
Record the new table name for use in Phase 5.

---

## Phase 4: Connect a Kafka Source

Skip this phase if `kafka_broker` or `kafka_topic` is absent.

Call `toolbelt_connect`:
```json
{
  "source_type": "kafka",
  "namespace_id": "<namespace_id>",
  "location": "KAFKA://<kafka_broker>",
  "external_table_name": "<kafka_topic>",
  "asset_name": "<kafka_topic>",
  "kafka_column_definitions": "<kafka_schema>",
  "kafka_subscribe": true,
  "extra_options": { "kafka.group.id": "<kafka_group_id>" }
}
```

Omit `extra_options` if `kafka_group_id` was not provided.

Verify the table is queryable with `toolbelt_sql`:
```json
{
  "namespace_id": "<namespace_id>",
  "query": "SELECT COUNT(*) FROM <kafka_topic> LIMIT 1"
}
```

If the query fails, emit structured failure and halt:
```
FAILURE: Kafka source connected but table is not queryable.
Query: SELECT COUNT(*) FROM <kafka_topic> LIMIT 1
Error: <error message>
```

---

## Phase 5: Ask a Question

Skip this phase if `question` was not provided.

Call `toolbelt_search`:
```json
{
  "question": "<question>",
  "namespace_id": "<namespace_id>",
  "synthesize": true
}
```

---

## Structured Output

After all phases complete, emit a single structured result:

```
RESULT:
  namespace_id: <uuid>
  phases_run: [0, 1, 2, ...]
  document_table: <table name, if Phase 3 ran>
  kafka_table: <table name, if Phase 4 ran>
  answer: |
    <synthesized answer from toolbelt_search, if Phase 5 ran>
  sql_generated: <SQL from search result, if any>
  sources: [<cited source documents, if any>]
```

---

## Tool Reference

| Phase | Tool(s) |
|---|---|
| 0. Verify connection | `toolbelt_list_namespaces` |
| 1. Resolve namespace | (from Phase 0 result) |
| 2. Inspect state | `toolbelt_context` |
| 3. Add document | `toolbelt_save`, `toolbelt_jobs`, `toolbelt_context` |
| 4. Connect Kafka | `toolbelt_connect`, `toolbelt_sql` |
| 5. Ask a question | `toolbelt_search` |
