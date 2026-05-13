# @toolbeltai/skills

> Official Toolbelt skills for Claude Code and other MCP-capable agents —
> SQL, vectors, graphs, geospatial, streaming, all as named slash commands.

## Install (standalone)

```bash
npx @toolbeltai/skills install
```

Copies every skill to `~/.claude/skills/` (flat, per the AgentSkills spec).
Restart Claude Code and you'll see them as slash commands: `/toolbelt-start`,
`/toolbelt-geo`, …

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
| [toolbelt-start](toolbelt-start/) | `/toolbelt-start` | Onboard end-to-end — provision, ingest, first query |
| [toolbelt-analyze](toolbelt-analyze/) | `/toolbelt-analyze` | Upload 1+ CSVs, ask in plain English, get SQL answers (single-table or multi-table JOIN) |
| [toolbelt-find](toolbelt-find/) | `/toolbelt-find` | Upload a document, retrieve passages by semantic similarity |
| [toolbelt-entities](toolbelt-entities/) | `/toolbelt-entities` | Auto-extract entities and relationships from docs, explore with Cypher |
| [toolbelt-geo](toolbelt-geo/) | `/toolbelt-geo` | GPU-accelerated geospatial — distance, containment, routing, map rendering |
| [toolbelt-stream](toolbelt-stream/) | `/toolbelt-stream` | Connect Kafka, aggregate over windows, detect anomalies |
| [toolbelt-invite](toolbelt-invite/) | `/toolbelt-invite` | Emit a connection URL so another agent can join this workspace |

## Works with

Claude Code · OpenClaw · Cursor · Gemini CLI · Codex CLI · Windsurf · any MCP client

## Commands

```bash
npx @toolbeltai/skills install       # install all skills
npx @toolbeltai/skills uninstall     # remove them
npx @toolbeltai/skills list          # list what would be installed
npx @toolbeltai/skills path          # print install target
```

## Versioning

The npm package version (`@toolbeltai/skills@X.Y.Z`) and each skill's
ClawHub version (`SKILL.md` top-level `version:`) are **independent** and
bumped separately — see [RELEASING.md](./RELEASING.md#versioning) for the
full rule. TL;DR: only bump a skill's version when *that skill* changes.

## Docs

- Skill reference: <https://docs.toolbelt.ai>
- Toolbelt CLI: <https://github.com/toolbeltai/toolbelt>
- Releasing: [RELEASING.md](./RELEASING.md)
- Contributing: [CONTRIBUTING.md](./CONTRIBUTING.md)

## License

MIT — see [LICENSE](./LICENSE).
