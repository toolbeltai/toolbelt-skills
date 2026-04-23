---
name: sql-analyst
description: >
  Upload a CSV and answer natural-language questions by generating and executing
  SQL. Covers totals, averages, group-by, filtering, and single-table joins on
  tabular data. Use when an agent has structured rows/columns and needs analytical
  answers — trends, breakdowns, comparisons, rankings. NOT for unstructured
  documents (use knowledge-graph or vector-search), lat/lon or WKT data (use
  geo-analyst), live streams (use streaming-analyst), or multi-table JOINs across
  independent datasets (use data-blend).
license: MIT
compatibility: >
  Requires a Toolbelt account (provision free at https://toolbelt.ai) and an
  MCP-compatible AI agent (Claude Code, Claude Desktop, OpenClaw, or any client
  that supports MCP server connections). MCP connection must be pre-established
  before invocation.
metadata:
  author: toolbeltai
  version: "1.0"
  homepage: "https://toolbelt.ai/docs/sql"
---

Upload tabular data and answer natural language questions about it using
Toolbelt MCP tools. Work through each phase in order without prompting for
user input. On unrecoverable error, emit a structured failure and halt.

## When Not To Use

- For unstructured text or documents — use `knowledge-graph` to extract entities and relationships.
- For real-time or streaming data — use `streaming-analyst` instead.
- For spatial data with lat/lon coordinates — use `geo-analyst` instead.

## Invocation Parameters

Extract these from the args string or conversation context before starting:

| Parameter | Required | Description |
|---|---|---|
| `namespace_id` | No | UUID of target namespace. Auto-select if omitted and only one exists; fail if ambiguous. |
| `csv_content` | No | Raw CSV text to upload. Uses the embedded sample dataset if omitted. |
| `asset_name` | No | Name for the uploaded table asset. Defaults to `sales-data`. |
| `question` | No | Natural language question to ask about the data. Defaults to `What is the total sales amount by region?` |

---

## Default Sample Data

If no `csv_content` is provided, use this sales dataset verbatim:

```
order_id,date,region,product,category,quantity,unit_price,amount,rep
1001,2024-01-05,Northeast,Widget Pro,Hardware,12,49.99,599.88,Alice Chen
1002,2024-01-08,Southeast,Gadget Basic,Software,5,29.99,149.95,Bob Martinez
1003,2024-01-12,Midwest,Widget Pro,Hardware,8,49.99,399.92,Carol Singh
1004,2024-01-15,West,Service Plan,Services,3,199.00,597.00,David Park
1005,2024-01-19,Northeast,Gadget Basic,Software,20,29.99,599.80,Alice Chen
1006,2024-01-22,West,Widget Pro,Hardware,6,49.99,299.94,Emma Lopez
1007,2024-02-03,Southeast,Service Plan,Services,2,199.00,398.00,Bob Martinez
1008,2024-02-07,Midwest,Gadget Plus,Software,15,79.99,1199.85,Frank Kim
1009,2024-02-11,Northeast,Widget Pro,Hardware,10,49.99,499.90,Alice Chen
1010,2024-02-14,West,Gadget Basic,Software,8,29.99,239.92,David Park
1011,2024-02-18,Southeast,Gadget Plus,Software,4,79.99,319.96,Carol Singh
1012,2024-02-21,Midwest,Service Plan,Services,1,199.00,199.00,Frank Kim
1013,2024-03-02,Northeast,Service Plan,Services,5,199.00,995.00,Alice Chen
1014,2024-03-06,West,Gadget Plus,Software,9,79.99,719.91,Emma Lopez
1015,2024-03-10,Southeast,Widget Pro,Hardware,7,49.99,349.93,Bob Martinez
1016,2024-03-14,Midwest,Gadget Basic,Software,11,29.99,329.89,Carol Singh
1017,2024-03-18,Northeast,Gadget Plus,Software,6,79.99,479.94,David Park
1018,2024-03-22,West,Service Plan,Services,4,199.00,796.00,Emma Lopez
1019,2024-03-25,Southeast,Widget Pro,Hardware,3,49.99,149.97,Frank Kim
1020,2024-03-28,Midwest,Widget Pro,Hardware,14,49.99,699.86,Carol Singh
```

Default `question`: `What is the total sales amount by region?`

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

---

## Phase 2: Upload CSV Data

Resolve `csv_content` (use parameter value or default sample above).
Resolve `asset_name` (use parameter value or default `sales-data`).

Call `toolbelt_save`:

```json
{
  "asset_type": "document",
  "namespace_id": "<namespace_id>",
  "name": "<asset_name>",
  "file_name": "<asset_name>.csv",
  "content": "<csv_content>",
  "content_encoding": "text",
  "data_format": "csv"
}
```

Record the returned `asset_id`.

---

## Phase 3: Poll for Ingestion

Call `toolbelt_jobs` with `{ "namespace_id": "<namespace_id>" }` every 10 seconds.

Wait for the `ingest` job for this asset to reach `completed`.

Typical duration: 15–60 seconds. Maximum wait: 3 minutes.

If the job reaches `failed` or the timeout elapses, emit structured failure and halt:
```
FAILURE: CSV ingestion did not complete.
Job status: <last observed status>
```

---

## Phase 4: Get Schema Context

Call `toolbelt_context` with `{ "namespace_id": "<namespace_id>" }`.

Locate the table corresponding to the uploaded asset (match by `asset_name` or
the table name returned from the save call). Record:
- `table_name`: the SQL table name for this asset
- `column_names`: list of columns in the table
- `row_count`: number of rows if provided in context

---

## Phase 5: Ask a Natural Language Question

Resolve `question` (use parameter value or default).

Call `toolbelt_search`:

```json
{
  "question": "<question>",
  "namespace_id": "<namespace_id>",
  "synthesize": true
}
```

Parse the response to extract:
- `answer`: the synthesized natural language answer
- `sql_generated`: the SQL query that was generated and executed
- `row_count`: number of rows returned by the SQL query
- `sources`: any cited source tables or assets

If `toolbelt_search` does not return SQL, try `toolbelt_sql` directly with a
query you write from the schema context:

```json
{
  "namespace_id": "<namespace_id>",
  "query": "SELECT region, SUM(amount) AS total_amount FROM <table_name> GROUP BY region ORDER BY total_amount DESC"
}
```

Record whichever path succeeded as `query_method` (`"search"` or `"direct_sql"`).

---

## Phase 6: Structured Output

After all phases complete, emit a single structured result:

```
RESULT:
  namespace_id: <uuid>
  asset_name: <name of uploaded table>
  table_name: <SQL table name>
  row_count_ingested: <rows in the table>
  phases_run: [0, 1, 2, 3, 4, 5]

  question: "<question asked>"
  query_method: "<'search' or 'direct_sql'>"
  sql_generated: |
    <SQL query that was generated or executed>
  row_count: <number of rows returned by the query>
  answer: |
    <synthesized answer>
  sources: [<cited tables or assets>]
```

---

## Tool Reference

| Phase | Tool(s) |
|---|---|
| 0. Verify connection | `toolbelt_list_namespaces` |
| 1. Resolve namespace | (from Phase 0 result) |
| 2. Upload CSV document | `toolbelt_save` |
| 3. Poll for ingestion | `toolbelt_jobs` |
| 4. Get schema context | `toolbelt_context` |
| 5. Ask question | `toolbelt_search`, `toolbelt_sql` (fallback) |
| 6. Emit result | (structured output) |
