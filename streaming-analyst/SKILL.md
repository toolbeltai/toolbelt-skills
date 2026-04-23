---
name: streaming-analyst
description: >
  Connect a live Kafka topic (or use built-in simulated data) and run windowed
  aggregations plus standard-deviation anomaly detection on the stream. Use when
  an agent needs to analyze real-time or time-series data — IoT sensor readings,
  event logs, security events, fleet telemetry, transaction feeds — and answer
  questions about rates, trends, and outliers over time windows. NOT for static
  tabular files (use sql-analyst) or document content (use vector-search).
license: MIT
compatibility: >
  Requires a Toolbelt account (provision free at https://toolbelt.ai) and an
  MCP-compatible AI agent (Claude Code, Claude Desktop, OpenClaw, or any client
  that supports MCP server connections). MCP connection must be pre-established
  before invocation. Kafka parameters are optional — omit them to run with
  simulated stream data.
metadata:
  author: toolbeltai
  version: "1.0"
  homepage: "https://toolbelt.ai/docs/streaming"
---

Connect a Kafka topic (or simulate one) and run real-time aggregation and
anomaly detection using Toolbelt MCP tools. Work through each phase in order
without prompting for user input. On unrecoverable error, emit a structured
failure and halt.

## When Not To Use

- For static batch tabular data — use `sql-analyst` instead.
- When real-time monitoring, windowed aggregation, or anomaly detection is not the goal.

## Invocation Parameters

Extract these from the args string or conversation context before starting:

| Parameter | Required | Description |
|---|---|---|
| `namespace_id` | No | UUID of target namespace. Auto-select if omitted and only one exists; fail if ambiguous. |
| `kafka_broker` | No | Kafka broker URL (e.g. `kafka-broker:9092`). Omit to use simulated stream data. |
| `kafka_topic` | No | Kafka topic name. Required if `kafka_broker` is provided. |
| `kafka_schema` | No | SQL column schema (e.g. `sensor_id VARCHAR(64), ts TIMESTAMP, value DOUBLE`). Defaults to IoT schema below. |
| `kafka_group_id` | No | Kafka consumer group ID. Omitted if not provided. |
| `anomaly_threshold` | No | Standard deviation multiplier for anomaly detection. Defaults to `2.0`. |

---

## Default Simulated Stream Data

When `kafka_broker` is not provided, upload this IoT sensor reading dataset as
a relational asset to simulate a stream snapshot. It includes planted anomalies
(readings > 2 standard deviations from mean) for detection validation.

```
sensor_id,ts,value,unit
sensor-01,2024-03-01 00:00:00,72.3,celsius
sensor-02,2024-03-01 00:00:00,71.8,celsius
sensor-03,2024-03-01 00:00:00,70.5,celsius
sensor-01,2024-03-01 00:01:00,72.6,celsius
sensor-02,2024-03-01 00:01:00,72.1,celsius
sensor-03,2024-03-01 00:01:00,71.0,celsius
sensor-01,2024-03-01 00:02:00,73.0,celsius
sensor-02,2024-03-01 00:02:00,71.5,celsius
sensor-03,2024-03-01 00:02:00,70.8,celsius
sensor-01,2024-03-01 00:03:00,72.8,celsius
sensor-02,2024-03-01 00:03:00,98.7,celsius
sensor-03,2024-03-01 00:03:00,71.2,celsius
sensor-01,2024-03-01 00:04:00,73.1,celsius
sensor-02,2024-03-01 00:04:00,72.4,celsius
sensor-03,2024-03-01 00:04:00,45.1,celsius
sensor-01,2024-03-01 00:05:00,72.5,celsius
sensor-02,2024-03-01 00:05:00,72.0,celsius
sensor-03,2024-03-01 00:05:00,71.5,celsius
sensor-01,2024-03-01 00:06:00,72.9,celsius
sensor-02,2024-03-01 00:06:00,71.7,celsius
sensor-03,2024-03-01 00:06:00,70.9,celsius
sensor-01,2024-03-01 00:07:00,126.4,celsius
sensor-02,2024-03-01 00:07:00,72.3,celsius
sensor-03,2024-03-01 00:07:00,71.8,celsius
sensor-01,2024-03-01 00:08:00,73.2,celsius
sensor-02,2024-03-01 00:08:00,71.9,celsius
sensor-03,2024-03-01 00:08:00,71.3,celsius
```

The three anomalies in this dataset:
- `sensor-02` at `00:03:00` — value `98.7` (spike high)
- `sensor-03` at `00:04:00` — value `45.1` (drop low)
- `sensor-01` at `00:07:00` — value `126.4` (extreme spike)

Default `kafka_schema` (used if broker is provided without schema):
```
sensor_id VARCHAR(64), ts TIMESTAMP, value DOUBLE, unit VARCHAR(32)
```

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

## Phase 2: Connect Stream Source

**If `kafka_broker` is provided:**

Call `toolbelt_connect`:
```json
{
  "source_type": "kafka",
  "namespace_id": "<namespace_id>",
  "location": "KAFKA://<kafka_broker>",
  "external_table_name": "<kafka_topic>",
  "asset_name": "<kafka_topic>",
  "kafka_column_definitions": "<kafka_schema or default schema>",
  "kafka_subscribe": true,
  "extra_options": { "kafka.group.id": "<kafka_group_id>" }
}
```

Omit `extra_options` if `kafka_group_id` was not provided.

Store the resulting table name as `stream_table`. Record `source_mode: "kafka"`.

**If `kafka_broker` is not provided (simulated stream):**

Upload the default sample data above as a document using `toolbelt_save`:

```json
{
  "asset_type": "document",
  "namespace_id": "<namespace_id>",
  "name": "stream-readings",
  "file_name": "stream-readings.csv",
  "content": "<default sample data above>",
  "content_encoding": "text",
  "data_format": "csv"
}
```

Record `source_mode: "simulated"`. Poll `toolbelt_jobs` every 10 seconds until
the `ingest` job reaches `completed`. Maximum wait: 3 minutes.

If the job reaches `failed` or the timeout elapses, emit structured failure and halt:
```
FAILURE: Stream data ingestion did not complete.
Job status: <last observed status>
```

Call `toolbelt_context` to get the table name. Store as `stream_table`.

---

## Phase 3: Confirm Data Arrival

Call `toolbelt_execute` to verify the stream table is queryable and report
the initial row count:

```sql
SELECT COUNT(*) AS row_count FROM <stream_table>
```

If this fails, emit structured failure and halt:
```
FAILURE: Stream table is not queryable.
Table: <stream_table>
Error: <error message>
```

Record `initial_row_count`. For simulated streams this is the full dataset.
For live Kafka streams, wait 30 seconds and poll again to observe growth:

```sql
SELECT COUNT(*) AS row_count FROM <stream_table>
```

Record `final_row_count`. If `final_row_count > initial_row_count`, set
`data_is_growing: true`. For simulated mode, set `data_is_growing: "simulated"`.

---

## Phase 4: Aggregation Queries

Run the following aggregation queries via `toolbelt_execute`. Substitute
`<stream_table>` with the resolved table name throughout.

### Query 1 — Per-sensor stats

Compute mean, min, max, and reading count per sensor:

```sql
SELECT
  sensor_id,
  COUNT(*) AS reading_count,
  ROUND(AVG(value), 2) AS avg_value,
  ROUND(MIN(value), 2) AS min_value,
  ROUND(MAX(value), 2) AS max_value
FROM <stream_table>
GROUP BY sensor_id
ORDER BY sensor_id ASC
```

Record `per_sensor_rows` (number of rows returned).

### Query 2 — 1-minute window aggregation

Aggregate readings into 1-minute windows using timestamp truncation:

```sql
SELECT
  sensor_id,
  DATETIME(ts, 'start of minute') AS window_start,
  COUNT(*) AS readings_in_window,
  ROUND(AVG(value), 2) AS avg_value
FROM <stream_table>
GROUP BY sensor_id, DATETIME(ts, 'start of minute')
ORDER BY window_start ASC, sensor_id ASC
LIMIT 20
```

If the database does not support `DATETIME(ts, 'start of minute')`, fall back to:
```sql
SELECT
  sensor_id,
  ts,
  value
FROM <stream_table>
ORDER BY ts ASC, sensor_id ASC
LIMIT 20
```

Record `window_rows` (number of rows returned).

---

## Phase 5: Anomaly Detection

Detect readings that deviate more than `anomaly_threshold` standard deviations
from the per-sensor mean. Run via `toolbelt_execute`:

```sql
SELECT
  r.sensor_id,
  r.ts,
  r.value,
  ROUND(stats.avg_val, 2) AS sensor_mean,
  ROUND(stats.std_val, 2) AS sensor_stddev,
  ROUND(ABS(r.value - stats.avg_val) / NULLIF(stats.std_val, 0), 2) AS z_score
FROM <stream_table> r
JOIN (
  SELECT
    sensor_id,
    AVG(value) AS avg_val,
    STDDEV(value) AS std_val
  FROM <stream_table>
  GROUP BY sensor_id
) stats ON r.sensor_id = stats.sensor_id
WHERE ABS(r.value - stats.avg_val) > (<anomaly_threshold> * stats.std_val)
ORDER BY z_score DESC
```

Substitute `<anomaly_threshold>` with the resolved value (default `2.0`).

If `STDDEV` is not supported, substitute with the population standard deviation
expression: `SQRT(AVG(value * value) - AVG(value) * AVG(value))`.

Record:
- `anomaly_count`: number of rows returned
- `anomalies`: list of `{ sensor_id, ts, value, z_score }` for each row

---

## Phase 6: Structured Output

Emit a single structured result after all phases complete:

```
RESULT:
  namespace_id: <uuid>
  stream_table: <table name>
  source_mode: <"kafka" or "simulated">
  phases_run: [0, 1, 2, 3, 4, 5]

  data_arrival:
    initial_row_count: <count>
    final_row_count: <count>
    data_is_growing: <true / false / "simulated">

  aggregation:
    per_sensor_rows: <count>
    window_rows: <count>

  anomaly_detection:
    threshold_stddev: <anomaly_threshold>
    anomaly_count: <count>
    anomalies:
      - sensor_id: <id>
        ts: <timestamp>
        value: <value>
        z_score: <z_score>
      ...
```

If any Phase 4–5 query fails, include `query_error: "<error>"` under that
section and continue. Only halt on Phase 0–2 failures.

---

## Tool Reference

| Phase | Tool(s) |
|---|---|
| 0. Verify connection | `toolbelt_list_namespaces` |
| 1. Resolve namespace | (from Phase 0 result) |
| 2. Connect stream | `toolbelt_connect` (Kafka) or `toolbelt_save` + `toolbelt_jobs` + `toolbelt_context` (simulated) |
| 3. Confirm data arrival | `toolbelt_execute` × 1–2 |
| 4. Aggregation queries | `toolbelt_execute` × 2 |
| 5. Anomaly detection | `toolbelt_execute` × 1 |
| 6. Emit result | (structured output) |
