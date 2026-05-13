# @toolbeltai/skills

> **Agents that remember. Together.**
> One skill, one command, your AI agent now has a shared brain for your
> data — vector, knowledge graph, SQL, geospatial, streaming — and
> remembers what it found across sessions, across agents.

[![npm version](https://img.shields.io/npm/v/@toolbeltai/skills.svg)](https://www.npmjs.com/package/@toolbeltai/skills)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Works with MCP](https://img.shields.io/badge/MCP-compatible-7c3aed.svg)](https://modelcontextprotocol.io)

```bash
npx @toolbeltai/skills install
```

That's it. No signup. No API keys. Your agent provisions a free Toolbelt
account on first use.

---

## What just happened

Once installed, your AI agent (Claude, Cursor, OpenClaw, ChatGPT, any
MCP client) reads the `/toolbelt` skill and goes from zero to connected
in one turn:

```
You:  "Find every mention of Q3 revenue in last week's emails."

Agent: [reads /toolbelt skill]
       [POST /api/onboard → gets a free Toolbelt account]
       [writes MCP config to ~/.claude/skills/]
       [calls toolbelt_search]

       Found 4 mentions across 3 emails. Top hit: Tuesday's board
       update, $14.2M Q3 (page 2). Recorded as finding #7 in your
       'inbox' namespace for the next agent.
```

Next session, a different agent — same shared brain. Findings compound.

## The pitch in 30 seconds

Most MCP servers are stateless query brokers. Your agent pulls data,
forgets, repeats. Toolbelt is the one where **findings, decisions, and
observations persist** — across sessions and across agents. One MCP
endpoint, every kind of data:

- **Vector search** over documents
- **Knowledge graph** of entities and relationships
- **SQL** over structured tables
- **Geospatial** queries (distance, containment, routing)
- **Streaming** sources (Kafka, real-time tables)
- **Timeline** — agents record what they found, future agents read it back

Stop wiring 6 MCP tools. Use 1.

## Install

### Any MCP-capable agent

```bash
npx @toolbeltai/skills install
```

Copies `toolbelt/SKILL.md` into `~/.claude/skills/toolbelt/` per the
[AgentSkills spec](https://agentskills.io). Restart your client; the
skill appears as `/toolbelt`.

### Via ClawHub

```bash
clawhub install @toolbeltai/toolbelt
```

Same skill, different channel.

## What you get

| | Anonymous | Verified | Pro | Team |
|---|:---:|:---:|:---:|:---:|
| **Price** | Free | Free (email) | $29 / mo | $89 / mo |
| **Calls / month** | 1,000 | 2,000 | 150,000 | 500,000 |
| **Storage** | — | 1 GB | 50 GB | 100 GB |
| **Namespaces** | 1 | 10 | 50 | Unlimited |

The skill provisions **Anonymous** automatically. Upgrade by:
- **Email claim** (Anonymous → Verified) — the skill prompts for an
  email, hits `POST /api/onboard/claim`, you click the verification
  link, done.
- **Pro / Team** — human-only Stripe checkout. The skill points you at
  <https://app.toolbelt.ai>.

## Works with

Claude Code · Claude Desktop · OpenClaw · Cursor · Gemini CLI · Codex
CLI · Windsurf · any MCP client.

## Why this design

**One skill, not seven.** Earlier versions of this package shipped a
playbook per capability (`/toolbelt-analyze`, `/toolbelt-find`, …).
That duplicated routing the MCP server already does better via tool
descriptions. The flagship skill handles discovery + onboarding once;
the agent picks the right MCP tool per task from the server's own
descriptions. Less to maintain, less to confuse a new user.

**Anonymous-first.** No signup wall. New users go from `npx install`
to a working agent in under 30 seconds. Upgrade only when the free
tier runs out.

**Two-version tracking.** The npm package version
(`@toolbeltai/skills@X.Y.Z`) is the install pin. The skill's own
version (inside `SKILL.md`) is the ClawHub registry version. They bump
independently. [Full rule.](./RELEASING.md#versioning)

## Share it

Toolbelt's real magic shows up when **multiple agents share state**:
- Your Claude Code agent records a finding via `toolbelt_record`.
- Your Cursor agent picks it up on its next turn via `toolbelt_timeline`.
- Your teammate's agent joins via `toolbelt_share` — same namespace,
  same brain.

Install it. Use it. Send it to a friend who's tired of agents that forget.

## Links

- Site — <https://toolbelt.ai>
- Docs — <https://toolbelt.ai/docs>
- App / billing — <https://app.toolbelt.ai>
- Contributing — [CONTRIBUTING.md](./CONTRIBUTING.md)
- Releasing — [RELEASING.md](./RELEASING.md)
- Support — <support@toolbelt.ai>

## License

MIT — see [LICENSE](./LICENSE).
