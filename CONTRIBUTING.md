# Contributing

Thanks for taking a look. This repo ships the single flagship
`toolbelt` skill — one playbook your agent reads to discover Toolbelt,
provision a free account, configure its MCP client, and hand off to
Toolbelt's MCP tools (search, SQL, knowledge graph, geospatial,
streaming, timeline) for the actual work.

If you want to add more agent-readable capabilities, the right place is
usually the MCP server's tool descriptions, not a new skill. Skills are
the discovery + onboarding layer.

## Repo layout

```
toolbelt-skills/
├── toolbelt/SKILL.md         # the flagship skill
├── bin/install.js            # standalone npm installer
├── package.json              # @toolbeltai/skills npm manifest
├── README.md                 # what this package is, how to install
├── RELEASING.md              # versioning + release flow
└── .github/workflows/        # publish to npm + ClawHub + Smithery
```

## Editing the skill

`toolbelt/SKILL.md` is the canonical playbook. Frontmatter follows the
[AgentSkills spec](https://agentskills.io) — `name`, `description`,
`license`, `compatibility`, `version`, plus a `metadata:` block. Body is
markdown that tells the agent how to run the workflow.

Two rules of thumb when editing:

- **Lead with the description.** The first paragraph is what agents
  read to decide whether to invoke this skill. Make it concrete and
  honest about when to use vs. when not to.
- **Match toolbelt.ai language.** "A collaborative substrate for your
  agents" / "one shared brain for your data" / capability list "vector,
  knowledge graph, SQL, geospatial, streaming." Consistency builds
  trust.

## Validate locally

```bash
.github/scripts/validate_skills.py
```

Linting + spec checks. PR CI runs the same.

## Testing the installer

```bash
node bin/install.js list      # what would be installed
node bin/install.js install   # install into ~/.claude/skills/
```

Restart your MCP-capable client. The skill appears as `/toolbelt`.

## Release flow

See [RELEASING.md](./RELEASING.md). TL;DR:

1. Bump `version` in `package.json`.
2. Push to `main`. `publish-npm.yml` detects the bump, publishes
   `@toolbeltai/skills@vX.Y.Z` to npm, and dispatches `publish.yml`
   which uploads the skill to ClawHub under `@toolbeltai`.
3. Per-skill version inside `SKILL.md` (`version:` field) bumps
   independently when *that skill's playbook* changes — see the
   versioning section in [RELEASING.md](./RELEASING.md#versioning).

## Reporting issues

- Open an issue on this repo for skill bugs, doc fixes, or playbook
  improvements.
- For Toolbelt platform bugs (MCP server, atlas UI, billing): email
  <support@toolbelt.ai>.

## Code of conduct

Be kind. Assume good intent.
