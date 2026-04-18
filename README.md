# @toolbeltai/skills

> Official Toolbelt skills for Claude Code and other MCP-capable agents —
> SQL, vectors, graphs, geospatial, streaming, all as named slash commands.

## Install (standalone)

```bash
npx @toolbeltai/skills install
```

Copies every skill to `~/.claude/skills/toolbelt/`. Restart Claude Code and
you'll see them as slash commands: `/run-toolbelt`, `/geo-analyst`, …

No account required; no network calls to Toolbelt. Skills work against any
Toolbelt MCP server (cloud or self-hosted).

## Install (via Toolbelt CLI)

If you want the skills **and** a preconfigured MCP connection in one step:

```bash
npx @toolbeltai/cli
```

Provisions an anonymous Toolbelt account, registers the MCP server in your
agent, and installs these skills — all at once.

## Skills

| Skill | Command | What it does |
| --- | --- | --- |
| [run-toolbelt](run-toolbelt/) | `/run-toolbelt` | Onboard, upload docs, connect data, ask questions |
| [geo-analyst](geo-analyst/) | `/geo-analyst` | GPU-accelerated geospatial — queries and map rendering |
| [knowledge-graph](knowledge-graph/) | `/knowledge-graph` | Auto-extract entities from docs, explore with Cypher |
| [multi-agent-workspace](multi-agent-workspace/) | `/multi-agent-workspace` | Shareable MCP URL for multi-agent collaboration |
| [sql-analyst](sql-analyst/) | `/sql-analyst` | Upload a CSV, ask plain English, get SQL + results |
| [streaming-analyst](streaming-analyst/) | `/streaming-analyst` | Connect Kafka, aggregate, detect anomalies |
| [vector-search](vector-search/) | `/vector-search` | Upload a document, retrieve semantically similar passages |
| [data-blend](data-blend/) | `/data-blend` | Combine multiple tables with cross-table JOINs |

## Works with

Claude Code · OpenClaw · Cursor · Gemini CLI · Codex CLI · Windsurf · any MCP client

## Commands

```bash
npx @toolbeltai/skills install       # install all skills
npx @toolbeltai/skills uninstall     # remove them
npx @toolbeltai/skills list          # list what would be installed
npx @toolbeltai/skills path          # print install target
```

## Docs

- Skill reference: <https://docs.toolbelt.ai>
- Toolbelt CLI: <https://github.com/toolbeltai/toolbelt>
- Releasing: [RELEASING.md](./RELEASING.md)
- Contributing: [CONTRIBUTING.md](./CONTRIBUTING.md)

## License

MIT — see [LICENSE](./LICENSE).
