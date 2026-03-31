---
name: knowledge-graph
description: >
  Automatic knowledge graph extraction and exploration via GLiNER + Cypher.
  Uploads a document, waits for entity extraction to complete, then explores
  the resulting knowledge graph — finding entities, relationships, and hidden
  connections the user didn't know about. Zero schema design required.
  Use when an AI agent needs to extract structured knowledge from unstructured
  text and explore it as a graph without any upfront ontology or configuration.
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

Extract a knowledge graph from a document and explore it autonomously using
Toolbelt MCP tools. Work through each phase in order without prompting for
user input. On unrecoverable error, emit a structured failure and halt.

## Invocation Parameters

Extract these from the args string or conversation context before starting:

| Parameter | Required | Description |
|---|---|---|
| `namespace_id` | No | UUID of target namespace. Auto-select if omitted and only one exists; fail if ambiguous. |
| `document_content` | No | Raw text to upload. Uses the embedded sample document if omitted. |
| `document_name` | No | Name for the document asset. Defaults to `kg-sample-doc`. |
| `cypher_query` | No | Custom Cypher query to run in Phase 5. Uses default discovery query if omitted. |

---

## Default Sample Document

If no `document_content` is provided, use the following text verbatim:

```
NovaTech Industries: Company Overview

NovaTech Industries was founded in 2018 by Dr. Elena Vasquez and Marcus Okafor
in Austin, Texas. The company specializes in next-generation industrial automation
hardware and AI-driven process control systems.

Dr. Elena Vasquez, Chief Executive Officer, previously led R&D at Siemens Energy
before co-founding NovaTech. Marcus Okafor, Chief Technology Officer, holds three
patents in embedded sensor design and was a principal engineer at Honeywell
Automation prior to joining the venture.

NovaTech's flagship product, the Sentinel-X200, is an industrial sensor array
that monitors temperature, vibration, and chemical composition simultaneously.
The Sentinel-X200 is manufactured at NovaTech's production facility in San
Antonio, Texas, and has been deployed at over 140 client sites worldwide. Key
clients include Pacific Rim Petrochemicals in Singapore, Northern Grid Energy
in Oslo, Norway, and Delta Fabrication Group in Detroit, Michigan.

In 2021, NovaTech acquired Axon Micro Systems, a startup based in Boulder,
Colorado, founded by Dr. Priya Nair. Axon Micro specialized in MEMS-based
pressure sensors. Following the acquisition, Dr. Nair joined NovaTech as VP
of Sensor Innovation and relocated to the Austin headquarters.

NovaTech's second product line, the Argus Platform, provides real-time analytics
for industrial IoT deployments. The Argus Platform integrates directly with the
Sentinel-X200 and supports connectivity to Siemens SCADA systems, Rockwell
Automation ControlLogix PLCs, and ABB Ability industrial cloud. The Argus Platform
is sold as a subscription service and is managed from NovaTech's cloud operations
center in Phoenix, Arizona.

The company raised a $45 million Series B in 2022, led by Meridian Growth Capital
and co-invested by Cascade Ventures. The funding round was used to expand the
San Antonio manufacturing facility and open a European sales office in Frankfurt,
Germany, led by regional director Thomas Brandt.

NovaTech employs 320 people across its Austin headquarters, San Antonio plant,
Phoenix operations center, and Frankfurt office. The company reported $62 million
in revenue for fiscal year 2023, with 40% of revenue from international markets.

Key partnerships include a joint development agreement with MIT's Advanced
Materials Lab, overseen by Professor Alan Chen, to develop next-generation
ceramic sensor substrates. NovaTech also holds a preferred supplier agreement
with Broadcom for embedded processing chips used in the Sentinel-X200.

In 2024, NovaTech announced the Sentinel-X300, the next-generation successor to
the X200, featuring AI-based anomaly detection co-developed with researchers at
UT Austin. The X300 is scheduled for commercial release in Q3 2025 and will be
manufactured at a new facility in Round Rock, Texas.
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
Never use the display name as the ID.

---

## Phase 2: Upload Document

Resolve `document_content` (use parameter value or default sample above).
Resolve `document_name` (use parameter value or default `kg-sample-doc`).

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

Record the returned `asset_id` for reference.

---

## Phase 3: Poll for Entity Extraction

Call `toolbelt_jobs` with `{ "namespace_id": "<namespace_id>" }` every 10 seconds.

Both job stages must reach `completed`:
- `ingest` — document parsed and stored
- `semantic` — embeddings generated and GLiNER entity extraction complete

Typical duration: 30–120 seconds. Maximum wait: 5 minutes.

If either job reaches `failed` or the timeout elapses, emit structured failure and halt:
```
FAILURE: Entity extraction did not complete.
Job status: <last observed status for ingest and semantic jobs>
```

Do not proceed to Phase 4 until **both** jobs are `completed`. The knowledge
graph is only available after the `semantic` job finishes — this is when GLiNER
runs and populates entity nodes and relationship edges.

---

## Phase 4: Confirm Knowledge Graph Exists

Call `toolbelt_context` with `{ "namespace_id": "<namespace_id>" }`.

Inspect the returned context for knowledge graph indicators:
- A `graph` or `knowledge_graph` section is present
- Entity or node counts are greater than zero

Record the graph summary for inclusion in the RESULT. If no graph section appears,
continue to Phase 5 — `toolbelt_graph describe` will confirm the actual state.

---

## Phase 5: Describe Extracted Entities

Call `toolbelt_graph` with `operation: "describe"`:

```json
{
  "operation": "describe",
  "namespace_id": "<namespace_id>"
}
```

Parse the response to extract:
- `graph_name`: the name of the knowledge graph (required for Phase 6 queries)
- `entity_count`: total number of entity nodes extracted
- `relationship_count`: total number of relationship edges extracted
- `entity_types`: list of distinct entity type labels (e.g. PERSON, ORG, LOCATION, PRODUCT)
- `sample_entities`: up to 5 example entity names from the response

Store `graph_name` — it is required as a parameter and as the prefix in every Cypher query.

If the call fails or returns no graphs, emit structured failure and halt:
```
FAILURE: toolbelt_graph describe failed or returned no graphs.
Error: <error message>
```

---

## Phase 6: Explore Connections

Surface the relationship data from the knowledge graph using two approaches in
order. Use whichever succeeds.

### Approach A — Cypher query (attempt first)

**Important:** Kinetica Cypher requires the query to begin with
`GRAPH <graph_name> MATCH ...`. The `graph_name` must come from the Phase 5
`describe` response.

If `graph_name` was returned in Phase 5, attempt:

```json
{
  "operation": "query",
  "namespace_id": "<namespace_id>",
  "graph_name": "<graph_name>",
  "query": "GRAPH <graph_name> MATCH (a)-[r]->(b) RETURN a.name AS source, label(a) AS source_type, type(r) AS relationship, b.name AS target, label(b) AS target_type ORDER BY source LIMIT 25"
}
```

If the Cypher query succeeds, record:
- `cypher_results`: rows returned (first 10)
- `result_count`: total rows
- `query_method`: `"cypher"`

### Approach B — Relationships from describe (fallback)

If Approach A fails (HTTP 5xx, no graph name available, or zero rows), extract
the relationship edges directly from the `describe` response returned in Phase 5.

The `describe` response from Toolbelt's GLiNER-extracted knowledge graph includes
`relationships` or `edges` arrays with `(source, relationship_type, target)` tuples.
Parse those and record:
- `cypher_results`: the relationship rows extracted from `describe` (first 10)
- `result_count`: total relationships from Phase 5 `relationship_count`
- `query_method`: `"describe_fallback"`

This fallback is expected for GLiNER-extracted knowledge graphs — Toolbelt stores
the KG in its internal Atlas layer, which is not always exposed as a queryable
Kinetica DIRECTED GRAPH object. Both approaches surface the same underlying data.

---

## Phase 7: Structured Output

After all phases complete, emit a single structured result:

```
RESULT:
  namespace_id: <uuid>
  document_name: <document name uploaded>
  phases_run: [0, 1, 2, 3, 4, 5, 6]

  knowledge_graph:
    entity_count: <integer from Phase 5>
    relationship_count: <integer from Phase 5>
    entity_types: [<list of type labels>]
    sample_entities: [<up to 5 entity names>]

  cypher_results:
    query_method: "<'cypher' or 'describe_fallback'>"
    query_used: "<cypher query executed, or 'toolbelt_graph describe' if fallback>"
    result_count: <integer>
    rows:
      - source: "<name>" relationship: "<type>" target: "<name>"
      - source: "<name>" relationship: "<type>" target: "<name>"
      ... (up to 10 rows)
```

If Phase 5 or 6 produced partial data (e.g., counts present but no rows), include
what is available and note the gap. Only halt on Phase 0–3 failures.

---

## Tool Reference

| Phase | Tool(s) |
|---|---|
| 0. Verify connection | `get_semantic_names` |
| 1. Resolve namespace | (from Phase 0 result) |
| 2. Upload document | `toolbelt_save` |
| 3. Poll for extraction | `toolbelt_jobs` |
| 4. Confirm KG exists | `toolbelt_context` |
| 5. Describe entities | `toolbelt_graph` (operation: describe) |
| 6. Explore with Cypher | `toolbelt_graph` (operation: query) |
| 7. Emit result | (structured output) |
