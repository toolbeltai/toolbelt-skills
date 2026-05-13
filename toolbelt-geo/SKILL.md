---
name: toolbelt-geo
description: >
  GPU-accelerated geospatial analytics on Toolbelt — distance, point-in-polygon
  containment, nearest-neighbor, track creation, spatial joins. Upload lat/lon
  sensor readings or WKT geometries, then run spatial SQL queries. Use when an
  agent needs to answer geographic questions — how close is X to Y, which points
  fall inside a region, along which route, coverage overlap, or movement tracks
  from raw GPS. NOT for non-spatial tabular analysis (use toolbelt-analyze) or
  document content (use toolbelt-find).
license: MIT
compatibility: >
  Requires a Toolbelt account (provision free at https://toolbelt.ai) and an
  MCP-compatible AI agent (Claude Code, Claude Desktop, OpenClaw, or any client
  that supports MCP server connections). MCP connection must be pre-established
  before invocation.
metadata:
  author: toolbeltai
  version: "1.0.0"
  homepage: "https://toolbelt.ai/docs/geospatial"
---

Execute GPU-accelerated geospatial analytics end-to-end using Toolbelt MCP tools.
Work through each phase in order. Extract all required inputs from task parameters
or invocation context — do not prompt for user input. Progress through phases
without confirmation. On unrecoverable error, emit a structured failure and halt.

## When Not To Use

- For tabular data without lat/lon coordinates — use `toolbelt-analyze` instead.
- For unstructured text or documents — use `toolbelt-entities` instead.

## Invocation Parameters

Extract these from the args string or conversation context before starting:

| Parameter | Required | Description |
|---|---|---|
| `namespace_id` | No | UUID of target namespace. Auto-select if omitted and only one exists; fail if ambiguous. |
| `csv_content` | No | Raw CSV text with id, name, lat, lon columns. Uses default Tampa Bay sample if omitted. |
| `asset_name` | No | Name for the uploaded sensor table. Defaults to `sensor-locations`. |
| `zone_wkt` | No | WKT polygon for point-in-polygon query. Uses default Tampa downtown zone if omitted. |

---

## Default Sample Data

If no `csv_content` is provided, use this Tampa Bay area sensor dataset:

```
id,name,lat,lon
1,Sensor A,27.9506,-82.4572
2,Sensor B,27.9659,-82.4398
3,Sensor C,27.9881,-82.5014
4,Sensor D,27.9344,-82.5181
5,Sensor E,28.0080,-82.4271
6,Sensor F,27.9196,-82.3943
7,Sensor G,27.8772,-82.5236
8,Sensor H,28.0346,-82.4850
9,Sensor I,27.9712,-82.5489
10,Sensor J,27.9050,-82.4127
```

Default `zone_wkt` (downtown Tampa bounding polygon):
```
POLYGON((-82.4650 27.9400, -82.4350 27.9400, -82.4350 27.9700, -82.4650 27.9700, -82.4650 27.9400))
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

## Phase 2: Upload Sensor Data

Upload the CSV as a document using `toolbelt_save`:

```json
{
  "asset_type": "document",
  "namespace_id": "<namespace_id>",
  "name": "<asset_name or 'sensor-locations'>",
  "file_name": "sensor-locations.csv",
  "content": "<csv_content or default sample data above>",
  "content_encoding": "text",
  "data_format": "csv"
}
```

### Poll for ingestion

Call `toolbelt_jobs` with `{ "namespace_id": "<namespace_id>" }` every 10 seconds.

Wait for the `ingest` job to reach `completed`.

Typical duration: 15–60 seconds. Maximum wait: 3 minutes.

If the job reaches `failed` or the timeout elapses, emit structured failure and halt:
```
FAILURE: Sensor data ingestion did not complete.
Job status: <last observed status>
```

After completion, call `toolbelt_context` to retrieve the table name for the
uploaded asset. Store it as `sensor_table` for use in Phase 3.

---

## Phase 3: Run Geospatial Queries

Run all three queries using `toolbelt_sql`. Pass `namespace_id` and `query`
for each call. Collect results.

**Note:** `ST_DISTANCE`, `ST_CONTAINS`, and `ST_MAKELINE` are Kinetica-native geospatial
functions available through Toolbelt's GPU-accelerated query engine. They are not standard
SQL and will not work against other databases.

### Query 1 — Pairwise Distance

`ST_DISTANCE(lat1, lon1, lat2, lon2)` → meters between two WGS-84 points.

```sql
SELECT
  a.name AS sensor_a,
  b.name AS sensor_b,
  ROUND(ST_DISTANCE(a.lat, a.lon, b.lat, b.lon)) AS distance_m
FROM <sensor_table> a
JOIN <sensor_table> b ON a.id < b.id
ORDER BY distance_m ASC
LIMIT 10
```

Record: `distance_query_rows` (number of rows returned), `closest_pair` (sensor_a and sensor_b from the first row), `min_distance_m`.

### Query 2 — Point-in-Polygon

`ST_CONTAINS(wkt_polygon, lat, lon)` → 1 if point is inside the polygon.

```sql
SELECT
  id,
  name,
  lat,
  lon,
  ST_CONTAINS('<zone_wkt>', lat, lon) AS in_zone
FROM <sensor_table>
WHERE ST_CONTAINS('<zone_wkt>', lat, lon) = 1
```

Substitute `<zone_wkt>` with the provided or default WKT string.

Record: `in_zone_count` (number of sensors inside the polygon), `in_zone_sensors` (list of names).

### Query 3 — Track Line

`ST_MAKELINE(lat, lon ORDER BY id)` → linestring connecting all points in sequence.

```sql
SELECT
  ST_ASTEXT(ST_MAKELINE(lat, lon ORDER BY id ASC)) AS track_wkt,
  COUNT(*) AS point_count
FROM <sensor_table>
```

Record: `track_point_count`, `track_wkt_excerpt` (first 120 chars of the WKT).

---

## Phase 4: Structured Output

After all queries complete, emit a single structured result:

```
RESULT:
  namespace_id: <uuid>
  sensor_table: <table name>
  phases_run: [0, 1, 2, 3]
  row_count: <total rows in sensor table>

  distance_query:
    rows_returned: <distance_query_rows>
    closest_pair: "<sensor_a> → <sensor_b>"
    min_distance_m: <min_distance_m>

  point_in_polygon:
    zone_wkt: "<zone_wkt used>"
    in_zone_count: <count>
    in_zone_sensors: [<names>]

  track:
    point_count: <track_point_count>
    track_wkt_excerpt: "<first 120 chars>"
```

If any query fails, include `query_error: "<error>"` under that query's section
and continue with remaining queries. Only halt on Phase 0–2 failures.

---

## Tool Reference

| Phase | Tool(s) |
|---|---|
| 0. Verify connection | `toolbelt_list_namespaces` |
| 1. Resolve namespace | (from Phase 0 result) |
| 2. Upload sensor data | `toolbelt_save`, `toolbelt_jobs`, `toolbelt_context` |
| 3. Run geospatial queries | `toolbelt_sql` × 3 |
| 4. Emit result | (structured output) |
