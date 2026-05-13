# @toolbeltai/skills

> Official skill for Toolbelt — A collaborative substrate for your agents.
> One skill, full onboarding, then hand off to Toolbelt's MCP tools.

## Install (standalone)

```bash
npx @toolbeltai/skills install
```

Copies the skill to `~/.claude/skills/` (flat, per the AgentSkills spec).
Restart Claude Code and you'll see it as `/toolbelt`.

No account required; the skill provisions one on first use.

## Install (via Toolbelt CLI)

```bash
npx @toolbeltai/cli
```

Same outcome via the Toolbelt CLI wrapper.

## Skill

| Skill | Command | What it does |
| --- | --- | --- |
| [toolbelt](toolbelt/) | `/toolbelt` | Detects or provisions a Toolbelt connection, configures the agent's MCP client, then hands off to Toolbelt's MCP tools (search, SQL, entity, record, timeline, save). |

Once connected, the actual capabilities (vector search, knowledge graph,
SQL, geospatial, streaming) live in the Toolbelt MCP server's tools —
the agent picks the right tool per task from their descriptions.

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
