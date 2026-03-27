# toolbelt-skills

Skill files for using [Toolbelt](https://toolbelt.ai) through any MCP-capable AI agent (Claude Code, Claude Desktop, OpenClaw, and others).

## What is Toolbelt?

Toolbelt gives AI agents intelligent data tools — semantic search, SQL execution, document ingestion, streaming data connections, and knowledge graph traversal — all exposed over the Model Context Protocol (MCP).

Get started at https://toolbelt.ai — no sign-up required, credentials provisioned in seconds.

## Prerequisites

1. **A Toolbelt account** — provision instantly:
   ```bash
   curl --request POST \
     --url https://toolbelt.ai/api/onboard \
     --header 'content-type: application/json' \
     --data '{}'
   ```
   Or visit https://toolbelt.ai and click **Try Now**.

2. **Your MCP client configured** with the `mcpUrl` and `token` from the response above.

> Trial instances expire after 72 hours. Visit https://toolbelt.ai with your token to claim a permanent account.

Skills follow the [Agent Skills specification](https://agentskills.io/specification) — each skill is a directory containing a `SKILL.md` file.

## Skills

| Directory | Slash Command | Description |
|---|---|---|
| `run-toolbelt/` | `/run-toolbelt` | Full onboarding walkthrough: add documents, connect Kafka, ask questions |

## Installation

### Claude Code

```bash
# Clone this repo
git clone https://github.com/toolbeltai/toolbelt-skills

# Symlink the skill directory into Claude Code's skills directory
ln -s "$(pwd)/toolbelt-skills/run-toolbelt" ~/.claude/skills/run-toolbelt
```

Then in Claude Code, run:
```
/run-toolbelt
```

### Claude Desktop

1. Open your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac)
2. Add the Toolbelt MCP server:
   ```json
   {
     "mcpServers": {
       "toolbelt": {
         "url": "<mcpUrl from onboard response>",
         "headers": {
           "Authorization": "Bearer <token from onboard response>"
         }
       }
     }
   }
   ```
3. Paste the contents of `run-toolbelt/SKILL.md` as a custom system prompt or skill in your client.

### OpenClaw (or any MCP client)

1. Add the Toolbelt MCP server using your `mcpUrl` as the server URL and `Bearer <token>` as the `Authorization` header.
2. Paste the contents of `run-toolbelt/SKILL.md` into a custom skill or system prompt slot.
3. Invoke it when you want to walk through the Toolbelt onboarding flow.

## Resources

- **Docs:** https://docs.toolbelt.ai
- **GitHub:** https://github.com/toolbeltai
- **Discord:** https://discord.gg/toolbelt
- **Website:** https://toolbelt.ai
