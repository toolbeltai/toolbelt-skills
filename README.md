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

### Claude Desktop / Claude Code

1. Go to **Settings > Connectors > Add custom connector**
2. Paste the server URL: `https://mcp.toolbelt.ai/mcp`
3. Under **Advanced**, set **Client ID** to `toolbelt-mcp`
4. Sign in with your email when prompted

### Cursor / Windsurf / Other MCP Clients

1. In your Toolbelt namespace, click **Generate MCP URL** to get a token-authenticated URL
2. Add it to your MCP config:
   ```json
   {
     "mcpServers": {
       "toolbelt": {
         "url": "<your MCP URL>"
       }
     }
   }
   ```

## Resources

- **Docs:** https://docs.toolbelt.ai
- **GitHub:** https://github.com/toolbeltai
- **Discord:** https://discord.gg/toolbelt
- **Website:** https://toolbelt.ai
