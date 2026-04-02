---
name: data-blend
description: >
  Join and correlate multiple datasets in a single Toolbelt namespace without
  writing infrastructure code. Toolbelt is a multi-modal data platform combining
  SQL analytics, vector search, and real-time streaming. Uploads two or more CSV
  tables, then runs cross-table JOIN queries to surface relationships between
  datasets. Use when an AI agent needs to combine data from different sources —
  orders with customers, sensors with metadata, events with dimensions — and
  answer questions that span multiple tables.
license: MIT
compatibility: >
  Requires a Toolbelt account (provision free at https://toolbelt.ai) and an
  MCP-compatible AI agent (Claude Code, Claude Desktop, or any client that
  supports MCP server connections). MCP connection must be pre-established
  before invocation.
metadata:
  author: toolbeltai
  version: "1.0"
  openclaw:
    emoji: "🔀"
    homepage: "https://toolbelt.ai/docs/sql"
    skillKey: "data-blend"
---

Upload multiple tables and run cross-table JOIN queries using Toolbelt MCP tools.
Work through each phase in order without prompting for user input. On
unrecoverable error, emit a structured failure and halt.

## When Not To Use

- For a single table — use `sql-analyst` instead.
- For unstructured text or documents — use `knowledge-graph` instead.
- For streaming/real-time data — use `streaming-analyst` instead.
- For spatial data with lat/lon — use `geo-analyst` instead.

## Invocation Parameters

Extract these from the args string or conversation context before starting:

| Parameter | Required | Description |
|---|---|---|
| `namespace_id` | No | UUID of target namespace. Auto-select if omitted and only one exists; fail if ambiguous. |
| `table_a_content` | No | Raw CSV for the first table. Uses default `orders` sample if omitted. |
| `table_a_name` | No | Asset name for the first table. Defaults to `orders`. |
| `table_b_content` | No | Raw CSV for the second table. Uses default `customers` sample if omitted. |
| `table_b_name` | No | Asset name for the second table. Defaults to `customers`. |
| `join_query` | No | Custom SQL JOIN to execute in Phase 5. Uses default query if omitted. |
| `skip_upload` | No | Set to `true` to skip Phases 2–4 and query tables already in the namespace. |

---

## Default Sample Data

If no `table_a_content` is provided, use this orders dataset verbatim:

```
order_id,customer_id,product,category,quantity,amount,order_date
1001,C001,Widget Pro,Hardware,12,599.88,2024-01-05
1002,C003,Gadget Basic,Software,5,149.95,2024-01-08
1003,C002,Widget Pro,Hardware,8,399.92,2024-01-12
1004,C004,Service Plan,Services,3,597.00,2024-01-15
1005,C001,Gadget Basic,Software,20,599.80,2024-01-19
1006,C005,Widget Pro,Hardware,6,299.94,2024-01-22
1007,C003,Service Plan,Services,2,398.00,2024-02-03
1008,C002,Gadget Plus,Software,15,1199.85,2024-02-07
1009,C001,Widget Pro,Hardware,10,499.90,2024-02-11
1010,C004,Gadget Basic,Software,8,239.92,2024-02-14
1011,C005,Gadget Plus,Software,4,319.96,2024-02-18
1012,C002,Service Plan,Services,1,199.00,2024-02-21
1013,C001,Service Plan,Services,5,995.00,2024-03-02
1014,C005,Gadget Plus,Software,9,719.91,2024-03-06
1015,C003,Widget Pro,Hardware,7,349.93,2024-03-10
1016,C002,Gadget Basic,Software,11,329.89,2024-03-14
1017,C004,Gadget Plus,Software,6,479.94,2024-03-18
1018,C005,Service Plan,Services,4,796.00,2024-03-22
1019,C003,Widget Pro,Hardware,3,149.97,2024-03-25
1020,C002,Widget Pro,Hardware,14,699.86,2024-03-28
```

If no `table_b_content` is provided, use this customers dataset verbatim:

```
customer_id,name,region,segment,account_manager
C001,Meridian Corp,Northeast,Enterprise,Alice Chen
C002,Delta Systems,Midwest,Enterprise,Carol Singh
C003,Apex Solutions,Southeast,Mid-Market,Bob Martinez
C004,Crest Industries,West,Mid-Market,David Park
C005,Solaris Group,West,SMB,Emma Lopez
```

Default `join_query`:
```sql
SELECT
  c.segment,
  c.region,
  COUNT(o.order_id) AS order_count,
  ROUND(SUM(o.amount), 2) AS total_amount,
  ROUND(AVG(o.amount), 2) AS avg_order_value
FROM <orders_table> o
JOIN <customers_table> c ON o.customer_id = c.customer_id
GROUP BY c.segment, c.region
ORDER BY total_amount DESC
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

Store the resolved `namespace_id` — pass it to every subsequent tool call.

---

## Phase 2: Inspect Existing Tables

Skip this phase if `skip_upload` is `true` — go directly to Phase 5.

Call `toolbelt_context` with `{ "namespace_id": "<namespace_id>" }`.

Check whether tables matching `table_a_name` and `table_b_name` already exist:
- If both exist: skip Phases 3–4 and proceed to Phase 5 using their existing table names.
- If one or both are missing: upload the missing ones in Phase 3.

Store all resolved table names for use in Phase 5.

---

## Phase 3: Upload Missing Tables

For each table that does not already exist, call `toolbelt_save`:

```json
{
  "asset_type": "relational",
  "namespace_id": "<namespace_id>",
  "name": "<table_a_name or table_b_name>",
  "file_name": "<name>.csv",
  "content": "<csv_content>",
  "content_encoding": "text",
  "data_format": "csv"
}
```

Record each returned `asset_id`.

---

## Phase 4: Poll for Ingestion

Call `toolbelt_jobs` with `{ "namespace_id": "<namespace_id>" }` every 10 seconds.

Wait for the `ingest` job for each uploaded asset to reach `completed`. Typical duration: 15–60 seconds per table. Maximum wait: 3 minutes.

If any job reaches `failed` or the timeout elapses, emit structured failure and halt:
```
FAILURE: Table ingestion did not complete.
Asset: <table name>
Job status: <last observed status>
```

After all jobs complete, call `toolbelt_context` to retrieve the final SQL table names for all assets. Store as `table_a` and `table_b`.

---

## Phase 5: Run Blend Queries

Substitute `<orders_table>` and `<customers_table>` (or equivalent names) in all queries with the resolved table names from Phase 4 (or Phase 2 if skip_upload).

### Query 1 — Join summary (default or custom)

If `join_query` was provided, execute it directly. Otherwise execute the default query, substituting the resolved table names:

```json
{
  "namespace_id": "<namespace_id>",
  "query": "<join_query with table names substituted>"
}
```

Use `toolbelt_sql` for this call. Record:
- `join_rows`: number of rows returned
- `join_results`: up to 10 rows

### Query 2 — Row counts

Confirm both tables are populated:

```sql
SELECT '<table_a>' AS table_name, COUNT(*) AS row_count FROM <table_a>
UNION ALL
SELECT '<table_b>' AS table_name, COUNT(*) AS row_count FROM <table_b>
```

Record `row_counts` for each table.

### Query 3 — Unmatched rows check

Identify rows in table A with no match in table B (join integrity check):

```sql
SELECT COUNT(*) AS unmatched_count
FROM <table_a> a
LEFT JOIN <table_b> b ON a.<join_key> = b.<join_key>
WHERE b.<join_key> IS NULL
```

Infer `<join_key>` from the shared column names visible in the schema context. If no shared key can be inferred, skip this query and note it in the RESULT.

Record `unmatched_count`.

---

## Phase 6: Structured Output

After all phases complete, emit a single structured result:

```
RESULT:
  namespace_id: <uuid>
  phases_run: [0, 1, 2, 3, 4, 5]

  tables:
    table_a: <sql table name>
    table_b: <sql table name>
    row_counts:
      <table_a>: <count>
      <table_b>: <count>
    unmatched_rows: <count or "skipped — no shared key inferred">

  blend_query:
    sql: |
      <query executed>
    row_count: <join_rows>
    results:
      - <row 1>
      - <row 2>
      ... (up to 10 rows)
```

If any Phase 5 query fails, include `query_error: "<error>"` under that query's
section and continue. Only halt on Phase 0–3 failures.

---

## Tool Reference

| Phase | Tool(s) |
|---|---|
| 0. Verify connection | `get_semantic_names` |
| 1. Resolve namespace | (from Phase 0 result) |
| 2. Inspect existing tables | `toolbelt_context` |
| 3. Upload missing tables | `toolbelt_save` |
| 4. Poll for ingestion | `toolbelt_jobs`, `toolbelt_context` |
| 5. Run blend queries | `toolbelt_sql`, `toolbelt_execute` |
| 6. Emit result | (structured output) |
