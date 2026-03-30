# run-toolbelt

Autonomous end-to-end Toolbelt agent. Provisions a namespace, ingests documents, connects streaming data sources, and answers questions — all without human interaction.

Invoke via `/run-toolbelt` in Claude Code, or via the `Skill` tool in any MCP-capable agent.

---

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `namespace_id` | No | UUID of target namespace. Auto-selected if only one exists. |
| `document_content` | No* | Raw text to upload as a document |
| `document_url` | No* | Public URL to a file (PDF, DOCX, etc.) |
| `document_name` | No | Name for the asset. Derived from URL or auto-generated if omitted. |
| `kafka_broker` | No | Kafka broker URL (e.g. `kafka-broker:9092`) |
| `kafka_topic` | No | Kafka topic name |
| `kafka_schema` | No | SQL-style column schema (e.g. `id INTEGER, event VARCHAR(256), ts TIMESTAMP`) |
| `kafka_group_id` | No | Kafka consumer group ID |
| `question` | No | Question to answer over ingested data |

*At least one of `document_content` or `document_url` is required to run document ingestion. Phases are skipped if their required parameters are absent.

---

## Usage

### Smoke test — connection and namespace only

```
/run-toolbelt
```

Runs phases 0–2. Verifies the MCP connection is live and resolves your namespace. No data is written.

---

### Ingest a document and ask a question

```
/run-toolbelt document_url=https://example.com/report.pdf question="What are the key findings?"
```

```
/run-toolbelt document_content="Q1 revenue was $4.2M across three product lines." document_name="q1-summary" question="What was Q1 revenue?"
```

---

### Target a specific namespace

```
/run-toolbelt namespace_id=<uuid> document_url=https://example.com/report.pdf question="Summarize this."
```

Required when your account has multiple namespaces. Omit to auto-select when only one exists.

---

### Connect a Kafka source

```
/run-toolbelt kafka_broker=kafka-broker:9092 kafka_topic=events kafka_schema="id INTEGER, event VARCHAR(256), ts TIMESTAMP"
```

Connects the topic and verifies it is queryable. Combine with `question` to search over streaming data.

---

### Full pipeline

```
/run-toolbelt \
  namespace_id=<uuid> \
  document_url=https://example.com/report.pdf \
  kafka_broker=kafka-broker:9092 \
  kafka_topic=events \
  kafka_schema="id INTEGER, event VARCHAR(256), ts TIMESTAMP" \
  question="What events occurred after the report's cutoff date?"
```

Runs all phases: document ingestion, Kafka connection, and cross-source search.

---

### From another agent (Skill tool)

```javascript
{ skill: "run-toolbelt", args: "namespace_id=<uuid> document_url=https://... question=..." }
```

The skill emits a structured `RESULT:` block — parseable by the calling agent without human interpretation.

---

## Output

On success:

```
RESULT:
  namespace_id: <uuid>
  phases_run: [0, 1, 2, 3, 5]
  document_table: <table name>
  kafka_table: <table name, if Phase 4 ran>
  answer: |
    <synthesized answer>
  sql_generated: <SQL, if any>
  sources: [<cited documents>]
```

On failure:

```
FAILURE: <reason>
<diagnostic detail>
```

Failures are terminal — the skill halts and does not continue to subsequent phases.
