# toolbelt-skills

> Give your AI agent a GPU-accelerated data workspace — SQL, vectors, graphs, geospatial, and streaming — in 10 seconds.

![run-toolbelt demo](assets/run-toolbelt-demo.gif)

![geo-analyst demo](assets/geo-analyst-demo.gif)

## Quick Start

```bash
curl -X POST https://toolbelt.ai/api/onboard | jq .mcpUrl
```

Paste the MCP URL into your agent. That's it.

## Skills

| Skill | Command | What It Does |
|-------|---------|-------------|
| [run-toolbelt](run-toolbelt/) | `/run-toolbelt` | Onboard, upload docs, connect data, ask questions |
| [geo-analyst](geo-analyst/) | `/geo-analyst` | GPU-accelerated geospatial analytics — spatial queries and map rendering |
| [knowledge-graph](knowledge-graph/) | `/knowledge-graph` | Auto-extract entities from docs, explore connections with Cypher |
| [multi-agent-workspace](multi-agent-workspace/) | `/multi-agent-workspace` | Create a shared workspace, generate a shareable MCP URL, demo multi-agent collaboration |
| [sql-analyst](sql-analyst/) | `/sql-analyst` | Upload a CSV, ask questions in plain English, get SQL + results |
| [streaming-analyst](streaming-analyst/) | `/streaming-analyst` | Connect a Kafka topic, watch data arrive, run aggregations, detect anomalies |
| [eval-run-toolbelt](eval-run-toolbelt/) | `/eval-run-toolbelt` | Run the eval suite and emit a graded benchmark report |

## Works With

Claude Code · OpenClaw · Cursor · Gemini CLI · Codex CLI · Windsurf · any MCP client

## Docs

https://docs.toolbelt.ai
