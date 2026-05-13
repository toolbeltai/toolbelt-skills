---
name: toolbelt-analyze
description: >
  Upload one or more CSV tables and answer natural-language questions by
  generating and executing SQL. Handles single-table analytics (totals,
  averages, group-by, filtering) AND multi-table JOINs across related
  datasets (orders + customers, sensors + metadata, events + dimensions).
  Use when an agent has structured rows/columns — one table or several
  that share a key — and needs analytical answers: trends, breakdowns,
  comparisons, rankings, correlations. NOT for unstructured documents
  (use toolbelt-find or toolbelt-entities), lat/lon or WKT data (use
  toolbelt-geo), or live streams (use toolbelt-stream).
license: MIT
compatibility: >
  Requires a Toolbelt account (provision free at https://toolbelt.ai) and an
  MCP-compatible AI agent (Claude Code, Claude Desktop, OpenClaw, or any client
  that supports MCP server connections). MCP connection must be pre-established
  before invocation.
version: "2.0.0"
metadata:
  author: toolbeltai
  homepage: "https://toolbelt.ai/docs/sql"
---

Upload one or more CSV tables and answer natural-language questions about
them using Toolbelt MCP tools. Handles both single-table queries and
multi-table JOINs on related datasets — pick the right approach based on
the uploaded data and the question. Work through each phase in order
without prompting for user input. On unrecoverable error, emit a
structured failure and halt.

## When Not To Use

- For unstructured text or documents — use `toolbelt-find` (retrieval) or `toolbelt-entities` (entity/relationship extraction).
- For real-time or streaming data — use `toolbelt-stream`.
- For spatial data with lat/lon coordinates — use `toolbelt-geo`.

## Invocation Parameters

Extract these from the args string or conversation context before starting:

| Parameter | Required | Description |
|---|---|---|
| `namespace_id` | No | UUID of target namespace. Auto-select if omitted and only one exists; fail if ambiguous. |
| `csv_inputs` | No | Array of `{ name, content }` objects for multi-table analysis (e.g. orders + customers). Preferred when two or more related CSVs need JOINs. |
| `csv_content` | No | Single CSV text (shorthand for `csv_inputs: [{ name: asset_name, content: ... }]`). |
| `asset_name` | No | Name for the single uploaded table (when `csv_content` is used). Defaults to `sales-data`. |
| `question` | No | Natural language question. Defaults vary by input shape (see below). |

If neither `csv_inputs` nor `csv_content` is provided, use the single built-in
sample dataset below with `asset_name = "sales-data"`.

The resolved list of uploads is called **`uploads`** for the rest of this
skill — each element has `{ name, content }`.

---

## Default Sample Data

If no inputs are provided, use this single sales dataset verbatim as
`uploads = [{ name: "sales-data", content: <csv below> }]`:

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

Default `question` for the single-table case:
`What is the total sales amount by region?`

For multi-table cases (`csv_inputs.length >= 2`) with no `question` provided,
ask the user to clarify — don't guess a default cross-table question.

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

## Phase 2: Upload Each CSV

Resolve `uploads` per the Invocation Parameters section.

**For each** `{ name, content }` in `uploads`, call `toolbelt_save`:

```json
{
  "asset_type": "document",
  "namespace_id": "<namespace_id>",
  "name": "<name>",
  "file_name": "<name>.csv",
  "content": "<content>",
  "content_encoding": "text",
  "data_format": "csv"
}
```

Collect the returned `asset_id` for each upload into an array `asset_ids`.
Track the upload count as `upload_count`.

If any `toolbelt_save` fails, emit structured failure naming which upload
failed and halt — partial multi-table ingests can't be joined.

---

## Phase 3: Poll for All Ingestions

Call `toolbelt_jobs` with `{ "namespace_id": "<namespace_id>" }` every 10 seconds.

Wait until **every** `ingest` job for the `asset_ids` from Phase 2 reaches `completed`.

Typical duration: 15–60 seconds per file. Maximum wait: 3 minutes total.

If any job reaches `failed` or the timeout elapses, emit structured failure:
```
FAILURE: Ingestion did not complete for <asset_name>.
Job status: <last observed status>
Completed so far: <N of M>
```

---

## Phase 4: Get Schema Context

Call `toolbelt_context` with `{ "namespace_id": "<namespace_id>" }`.

For each uploaded `asset_name` (from Phase 2), locate the corresponding
table in the returned context and record:
- `table_name`: the SQL table name
- `column_names`: columns in that table
- `row_count`: row count if provided

Store all of them in a `tables` array so Phase 5 can reason about JOINs.

---

## Phase 5: Answer the Question

Resolve `question` per the Invocation Parameters section.

**Decide on approach using `upload_count`:**

### If `upload_count == 1` (single-table analytics)

Prefer `toolbelt_search` (it routes through our hybrid + NL→SQL layer):

```json
{
  "question": "<question>",
  "namespace_id": "<namespace_id>",
  "synthesize": true
}
```

If `toolbelt_search` does not return SQL, fall back to `toolbelt_sql`
with a query you write from the single table's schema:

```json
{
  "namespace_id": "<namespace_id>",
  "query": "SELECT <...> FROM <table_name> ..."
}
```

### If `upload_count >= 2` (multi-table JOIN)

1. From the `tables` array collected in Phase 4, **identify candidate join
   keys** — columns that appear in two or more tables with compatible types
   and matching name patterns (e.g. `customer_id` in `orders` + `customers`).
2. Write a `SELECT` that JOINs on the identified key(s) and answers the
   user's question. Prefer explicit `JOIN ... ON ...` (never implicit join).
3. Call `toolbelt_sql` directly with the JOIN query:

```json
{
  "namespace_id": "<namespace_id>",
  "query": "SELECT a.<col>, SUM(b.<col>) FROM <t1> a JOIN <t2> b ON a.<key> = b.<key> GROUP BY a.<col>"
}
```

If no join key is identifiable, emit structured failure explaining which
tables were uploaded and asking the caller to supply a join key:
```
FAILURE: Uploaded tables have no obvious join key.
Tables and columns: [<summary>]
Re-invoke with a question that specifies which column(s) relate the tables.
```

### For either case, parse the result:

- `answer`: synthesized natural-language answer (if using `toolbelt_search`) or a one-sentence summary you compose from the rows (if using `toolbelt_sql` directly)
- `sql_generated`: the SQL that ran
- `row_count`: rows returned
- `sources`: cited tables/assets

Record the path used as `query_method` — `"search"` (NL→SQL via hybrid),
`"direct_sql_single"` (one-table direct), or `"direct_sql_join"` (multi-table JOIN).

---

## Phase 6: Structured Output

After all phases complete, emit a single structured result:

```
RESULT:
  namespace_id: <uuid>
  uploaded_tables:
    - asset_name: <name>
      table_name: <sql table name>
      column_names: [<list>]
      row_count_ingested: <rows>
  upload_count: <N>
  phases_run: [0, 1, 2, 3, 4, 5]

  question: "<question asked>"
  query_method: "<search | direct_sql_single | direct_sql_join>"
  sql_generated: |
    <SQL query executed>
  row_count: <rows returned>
  answer: |
    <natural-language answer>
  sources: [<tables cited>]
```

---

## Tool Reference

| Phase | Tool(s) |
|---|---|
| 0. Verify connection | `toolbelt_list_namespaces` |
| 1. Resolve namespace | (from Phase 0 result) |
| 2. Upload each CSV | `toolbelt_save` (once per input) |
| 3. Poll for ingestion | `toolbelt_jobs` |
| 4. Get schema context | `toolbelt_context` |
| 5. Answer | `toolbelt_search` (single-table NL path), `toolbelt_sql` (direct; required for JOINs) |
| 6. Emit result | (structured output) |

---

## Multi-Table Example

Invocation:
```
/toolbelt-analyze csv_inputs=[
  { name: "orders",    content: "order_id,customer_id,amount,..." },
  { name: "customers", content: "customer_id,region,tier,..." }
] question="Total amount by customer region"
```

Expected phases:
- Phase 2: `toolbelt_save` for `orders`, then `toolbelt_save` for `customers`
- Phase 3: poll both `ingest` jobs to completion
- Phase 4: context returns two tables; record both schemas
- Phase 5: identify `customer_id` as the join key, run
  `SELECT c.region, SUM(o.amount) FROM orders o JOIN customers c ON o.customer_id = c.customer_id GROUP BY c.region`
- Phase 6: structured result with `query_method = "direct_sql_join"` and both tables in `uploaded_tables`
