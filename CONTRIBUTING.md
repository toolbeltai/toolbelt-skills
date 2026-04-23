# Contributing

Thanks for taking a look. Skills here are the slash-command layer on top
of Toolbelt's MCP server — the UX sugar that turns raw tool calls into
named workflows your agent can invoke.

## Repo layout

Each skill is a top-level directory with a `SKILL.md`. The file is a
Claude-Code skill manifest — frontmatter + markdown body that defines how
the agent should run the workflow.

```
toolbelt-skills/
├── toolbelt-start/          # /toolbelt-start — onboarding walkthrough
├── toolbelt-geo/           # /toolbelt-geo — GPU geospatial analytics
├── toolbelt-entities/       # ...
├── ...
├── bin/install.js         # standalone installer
├── package.json           # npm manifest (@toolbeltai/skills)
└── .github/workflows/     # tag → npm; release → ClawHub + Smithery
```

## Adding a skill

1. Create a new top-level directory with a `SKILL.md`.
2. Add it to `files` in `package.json` so it's included in the published tarball.
3. Validate locally:
   ```bash
   .github/scripts/validate_skills.py
   ```
4. Open a PR. Reviewers will run the CI checks.

## Testing the installer

```bash
node bin/install.js list      # see skills that will install
node bin/install.js install   # install into ~/.claude/skills/
```

Then restart Claude Code — your new skill should appear as a slash command.

## Release flow

See [RELEASING.md](./RELEASING.md). TL;DR:

1. Bump `version` in `package.json`
2. Tag `vX.Y.Z` and push — `publish-npm.yml` fires, npm package publishes
3. Optionally publish a GitHub Release when we want ClawHub + Smithery too
   (deferred until leadership green-lights)

## Code of conduct

Be kind. Assume good intent. Report issues to <maintainers@toolbelt.ai>.
