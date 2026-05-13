---
name: toolbelt-find
description: >
  Upload a document and retrieve passages by semantic similarity to a
  natural-language query. Ranks content by meaning, not keyword overlap. Use
  when an agent needs to ground answers in source documents (RAG), find related
  content, retrieve passages by concept, or answer "what does this doc say
  about X" where X isn't a verbatim phrase. NOT for exact keyword/regex search,
  structured table queries (use toolbelt-analyze), or entity-relationship extraction
  (use toolbelt-entities).
license: MIT
compatibility: >
  Requires a Toolbelt account (provision free at https://toolbelt.ai) and an
  MCP-compatible AI agent (Claude Code, Claude Desktop, OpenClaw, or any client
  that supports MCP server connections). MCP connection must be pre-established
  before invocation.
metadata:
  author: toolbeltai
  version: "1.0.0"
  homepage: "https://toolbelt.ai/docs/vectors"
---

Upload a document and retrieve semantically similar passages using Toolbelt MCP
tools. Work through each phase in order without prompting for user input. On
unrecoverable error, emit a structured failure and halt.

## When Not To Use

- For structured tabular data (CSV, SQL tables) — use `toolbelt-analyze` instead.
- For aggregate queries, counts, or filtering by exact values — use `toolbelt-analyze`; vector search ranks by meaning, not criteria.
- For entity and relationship extraction — use `toolbelt-entities` instead.
- When you need a synthesized answer that may draw on SQL tables — use `toolbelt-analyze` with `toolbelt_search` (hybrid routing) instead.

## How This Differs From `toolbelt_search`

`toolbelt_vectors` is **pure semantic similarity search** — it returns ranked
document passages by embedding distance. `toolbelt_search` uses **hybrid
routing** and may execute SQL, vector search, or both depending on the question.
Use this skill when you specifically want passage retrieval from documents.

## Invocation Parameters

Extract these from the args string or conversation context before starting:

| Parameter | Required | Description |
|---|---|---|
| `namespace_id` | No | UUID of target namespace. Auto-select if omitted and only one exists; fail if ambiguous. |
| `document_content` | No | Raw text to upload. Uses the embedded sample document if omitted. |
| `document_name` | No | Name for the document asset. Defaults to `toolbelt-find-sample`. |
| `question` | No | Natural language query to search for. Defaults to `What are the effects on coastal ecosystems?` |
| `skip_upload` | No | Set to `true` to skip Phases 2–3 and search existing namespace content. |

---

## Default Sample Document

If no `document_content` is provided, use the following text verbatim:

```
Global Climate Trends: 2024 Summary Report

Section 1: Surface Temperature Changes
Average global surface temperatures rose 1.4°C above pre-industrial levels in
2023, continuing a decades-long trend. The ten hottest years on record have all
occurred since 2010. Heat waves in Europe and North America broke records in
duration and intensity. Urban heat islands amplified these effects in densely
populated areas, with some cities recording nighttime lows 5°C above surrounding
rural areas.

Section 2: Sea Level and Ocean Systems
Global mean sea level rose 4.2mm in 2023, driven by thermal expansion and
accelerating ice sheet melt in Greenland and West Antarctica. Ocean acidity
increased 0.1 pH units since 1990, threatening calcifying marine organisms
including coral and shellfish. The Atlantic Meridional Overturning Circulation
showed continued weakening, with potential implications for European climate
stability and North Atlantic fisheries.

Section 3: Biodiversity and Ecosystem Impacts
Species range shifts accelerated as organisms tracked suitable climate envelopes
poleward and to higher elevations. Coral bleaching events affected over 60% of
the Great Barrier Reef for the fourth consecutive year. Migratory bird species
showed timing mismatches with peak insect abundance, reducing breeding success.
Boreal forest die-offs from drought stress and bark beetle outbreaks expanded
across Canada and Siberia, releasing stored carbon and reducing canopy cover.

Section 4: Freshwater Availability
Glacial retreat reduced dry-season freshwater availability for approximately 2
billion people dependent on glacial meltwater. Extended droughts in the American
Southwest and Mediterranean region drove groundwater depletion and crop failures.
Conversely, increased atmospheric moisture intensified precipitation events,
causing flooding in traditionally dry regions of sub-Saharan Africa and South Asia.

Section 5: Policy and Emissions Trajectories
Global CO2 emissions reached 37.4 billion metric tons in 2023, a record high
despite rapid renewable energy deployment. Solar and wind capacity additions
outpaced projections, but total energy demand growth offset efficiency gains.
Carbon capture projects remained far below the scale required by IPCC scenarios.
National commitments under the Paris Agreement, if fully implemented, are
projected to limit warming to 2.5°C — above the 1.5°C target.
```

Default `question`: `What are the effects on coastal ecosystems?`

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

## Phase 2: Upload Document

Skip this phase if `skip_upload` is `true`.

Resolve `document_content` (use parameter value or default sample above).
Resolve `document_name` (use parameter value or default `toolbelt-find-sample`).

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

Record the returned `asset_id`.

---

## Phase 3: Poll for Semantic Indexing

Skip this phase if `skip_upload` is `true`.

Call `toolbelt_jobs` with `{ "namespace_id": "<namespace_id>" }` every 10 seconds.

**Both** job stages must reach `completed` before proceeding:
- `ingest` — document parsed and stored
- `semantic` — embeddings generated and vector index populated

Vector search requires the `semantic` job to complete. Searching before it
finishes will return zero results.

Typical duration: 30–120 seconds. Maximum wait: 5 minutes.

If either job reaches `failed` or the timeout elapses, emit structured failure and halt:
```
FAILURE: Semantic indexing did not complete.
Job status: <last observed status for ingest and semantic jobs>
```

---

## Phase 4: Run Vector Search

Resolve `question` (use parameter value or default).

Call `toolbelt_vectors`:

```json
{
  "namespace_id": "<namespace_id>",
  "question": "<question>"
}
```

Parse the response:
- `results`: array of passage objects. Each passage may contain `text`, `content`, or `excerpt`.
- `result_count`: total number of results returned.
- `top_result`: the first (highest-ranked) passage — extract up to 300 characters.

If the call returns zero results and `skip_upload` was `true`, the namespace may
not contain any documents with semantic indexes. Emit a structured failure:
```
FAILURE: toolbelt_vectors returned zero results.
The namespace may not contain any semantically indexed documents.
Re-invoke without skip_upload=true to upload and index a document first.
```

If the call returns zero results after a fresh upload (Phases 2–3 completed),
emit structured failure and halt:
```
FAILURE: toolbelt_vectors returned zero results after indexing completed.
namespace_id: <uuid>
asset_id: <asset_id>
```

---

## Phase 5: Structured Output

After all phases complete, emit a single structured result:

```
RESULT:
  namespace_id: <uuid>
  document_name: <name of uploaded document, or "existing namespace content" if skip_upload>
  question: "<question asked>"
  phases_run: [0, 1, 2, 3, 4]  # or [0, 1, 4] if skip_upload

  vector_search:
    result_count: <integer>
    top_result: |
      <first ~300 chars of the highest-ranked passage>
    all_results:
      - rank: 1
        excerpt: "<first ~150 chars>"
      - rank: 2
        excerpt: "<first ~150 chars>"
      ... (up to 5 results)
```

---

## Tool Reference

| Phase | Tool(s) |
|---|---|
| 0. Verify connection | `toolbelt_list_namespaces` |
| 1. Resolve namespace | (from Phase 0 result) |
| 2. Upload document | `toolbelt_save` |
| 3. Poll for indexing | `toolbelt_jobs` |
| 4. Run vector search | `toolbelt_vectors` |
| 5. Emit result | (structured output) |
