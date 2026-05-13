# @toolbeltai/skills

The official skill for [Toolbelt](https://toolbelt.ai). Installs one
`/toolbelt` skill that any MCP-capable agent can use to connect to a
Toolbelt namespace and hand off to Toolbelt's MCP tools.

[![npm version](https://img.shields.io/npm/v/@toolbeltai/skills.svg)](https://www.npmjs.com/package/@toolbeltai/skills)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

## Install

```bash
npx @toolbeltai/skills install
```

Copies `toolbelt/SKILL.md` into `~/.claude/skills/toolbelt/` (flat
layout per the [AgentSkills spec](https://agentskills.io)). Restart your
client; the skill appears as `/toolbelt`.

No Toolbelt account required — the skill provisions one on first use.

## What the skill does

When an agent runs `/toolbelt` for the first time, it:

1. Checks for an existing Toolbelt MCP connection.
2. If none, calls the public `/api/onboard` endpoint to provision a
   free anonymous account.
3. Writes the MCP connection into the agent's client config.
4. Hands off to Toolbelt's MCP tools for the actual work.

Full playbook in [toolbelt/SKILL.md](toolbelt/SKILL.md).

## Works with

Claude Code · Claude Desktop · OpenClaw · Cursor · Gemini CLI · Codex
CLI · Windsurf · any MCP client.

## Commands

```bash
npx @toolbeltai/skills install       # install
npx @toolbeltai/skills uninstall     # remove
npx @toolbeltai/skills list          # show what would install
npx @toolbeltai/skills path          # print install target
```

## Links

- Site: <https://toolbelt.ai>
- Docs: <https://toolbelt.ai/docs>
- App / billing: <https://app.toolbelt.ai>
- Contributing: [CONTRIBUTING.md](./CONTRIBUTING.md)
- Releasing: [RELEASING.md](./RELEASING.md)
- Support: <support@toolbelt.ai>

## License

Apache 2.0 — see [LICENSE](./LICENSE).
