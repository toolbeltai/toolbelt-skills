---
name: toolbelt
description: >
  Toolbelt is a collaborative substrate for your agents — one shared brain
  for your data. Connect AI agents to vector search, knowledge graph, SQL,
  geospatial, and streaming data through one MCP server.

  Use this skill at the start of any task where an agent needs persistent
  memory across sessions, natural-language access to structured or
  unstructured data, or shared state with other agents working on the same
  data. The skill handles the full first-time setup: provisions a free
  Toolbelt namespace if none exists, configures the MCP connection in the
  agent's client, and hands off to Toolbelt's MCP tools for the actual
  work.

  NOT for one-off lookups that don't benefit from persistent memory or
  structured data — use the agent's native tools for those.
license: MIT
compatibility: >
  Requires an MCP-compatible AI agent (Claude Code, Claude Desktop,
  OpenClaw, Cursor, Windsurf, or any client that supports MCP server
  connections). No Toolbelt account required — this skill provisions one
  on first use.
version: "1.0.0"
metadata:
  author: toolbeltai
  homepage: "https://toolbelt.ai"
---

# Toolbelt — A collaborative substrate for your agents

Your data. Your agents. One shared brain.

Toolbelt connects AI agents to vector search, knowledge graph, SQL,
geospatial, and streaming data through one MCP server. Findings,
decisions, and observations persist across sessions and across agents —
so each agent's work compounds instead of evaporating.

## When to invoke

Run this skill at the start of any task that:

- Mentions Toolbelt by name.
- Needs persistent memory across turns or sessions.
- Needs natural-language access to structured or unstructured data.
- Involves multiple agents collaborating on the same data.
- Would otherwise require wiring up several separate MCP tools.

## Phases (execute in order, no human prompts)

### Phase 1 — Detect existing connection

Attempt a call against the Toolbelt MCP tool `toolbelt_list_namespaces`.

- If it succeeds → user is already connected → skip to **Phase 4**.
- If the tool isn't available, or returns auth error → continue to **Phase 2**.

### Phase 2 — Provision a free Toolbelt account

Call the public onboarding endpoint (no auth required):

```http
POST https://app.toolbelt.ai/api/onboard
Content-Type: application/json

{}
```

Response shape:

```json
{
  "username": "@anon_...",
  "mcp_token": "tb_...",
  "mcp_url": "https://mcp.toolbelt.ai/mcp",
  "namespace_id": "...",
  "claim_token": "...",
  "expires_at": "..."
}
```

Capture `mcp_token`, `mcp_url`, and `claim_token` — needed in later phases.

### Phase 3 — Configure the agent's MCP client

Detect the agent's client and write the connection config in the right
place. The shape is identical across clients — only the file path differs.

**Claude Code (CLI):**
```bash
claude mcp add toolbelt \
  --transport http <mcp_url> \
  --header "Authorization: Bearer <mcp_token>"
```

**Claude Desktop, Cursor, Windsurf, OpenClaw** — add to the client's MCP
config JSON:

```json
{
  "mcpServers": {
    "toolbelt": {
      "url": "<mcp_url>",
      "headers": { "Authorization": "Bearer <mcp_token>" }
    }
  }
}
```

Config file locations:
- Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Cursor: `~/.cursor/mcp.json`
- Windsurf: `~/.codeium/windsurf/mcp_config.json`
- OpenClaw: `~/.openclaw/mcp.json`

Tell the user once: **"Toolbelt is provisioned. Reload your MCP connection
to activate it."**

### Phase 4 — Orient, then hand off

Once connected, call `toolbelt_context(namespace_id)` first. It returns
the namespace's available assets, suggested next moves, and per-tool
routing guidance.

Then use the appropriate Toolbelt MCP tool for the user's actual task:

| Tool | Purpose |
|---|---|
| `toolbelt_search` | Vector RAG over documents |
| `toolbelt_sql` | SQL over structured tables |
| `toolbelt_entity` | Entity profile from the knowledge graph |
| `toolbelt_graph` | Cypher graph traversal |
| `toolbelt_record` | Save a finding to the persistent timeline |
| `toolbelt_timeline` | Read chronological events |
| `toolbelt_save` | Persist an asset to the namespace |
| `toolbelt_share` | Emit a connection URL so another agent can join |
| `toolbelt_list_namespaces` | List workspaces this account can access |

The MCP server's tool descriptions carry the per-tool routing logic —
pick by task shape, not by this skill's instructions.

### Phase 5 — Optional: claim the account

Anonymous accounts expire. If the user wants persistence (and a higher
quota), ask for an email:

```http
POST https://app.toolbelt.ai/api/onboard/claim
Authorization: Bearer <claim_token>
Content-Type: application/json

{"email": "user@example.com"}
```

The user receives a verification code by email. Then:

```http
POST https://app.toolbelt.ai/api/onboard/claim/verify
Authorization: Bearer <claim_token>
Content-Type: application/json

{"code": "<code from email>"}
```

## Output

After Phase 4 succeeds, emit a brief connection status to the user:

```yaml
toolbelt_connection:
  status: connected
  namespace_id: <id>
  username: <username>
  account_tier: <anonymous | verified | pro | team>
```

Then proceed with the user's actual task.

## More

- Site: <https://toolbelt.ai>
- Docs: <https://toolbelt.ai/docs>
- Support: <support@toolbelt.ai>
