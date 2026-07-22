# Releasing toolbelt-skills

This repo ships one flagship skill — `toolbelt` — through three channels.
All three are triggered by a single `package.json` version bump pushed
to `main`.

| Channel | Consumer | How it gets there |
|---|---|---|
| **npm** (`@toolbeltai/skills`) | Toolbelt CLI bundles + standalone installers | `publish-npm.yml` fires on version bump → `npm publish` → git tag pushed |
| **ClawHub** (`@toolbeltai/toolbelt`) | OpenClaw / Claude Desktop / Cursor / any registry browser | `publish-npm.yml` dispatches `publish.yml` → `clawhub publish --owner toolbeltai --version <skill_ver>` |
| **Smithery** (MCP server registry) | MCP client directories | `publish.yml` registers `mcp.toolbelt.ai/mcp` with Smithery (gated on `SMITHERY_TOKEN`) |

## Versioning

There are **two independent versions**, and they intentionally diverge.
This isn't a quirk — it's a deliberate choice driven by how npm and
ClawHub each pin their installs.

| Version | Source of truth | What it tracks |
|---|---|---|
| Package version | `package.json` `"version"` | The npm bundle. Bumps on every release of the package. |
| Per-skill version | `toolbelt/SKILL.md` top-level `version:` | The ClawHub registry version. Bumps only when the skill's playbook materially changes. |

Both are SemVer.

### Why they're independent

Once a skill is published to ClawHub at e.g. `2.0.0`, semver forbids
publishing `0.x` of the same slug. Forcing the skill version to track
the package version would either (a) require the package to start above
the highest skill version forever, or (b) force every skill to bump on
every package release even when its playbook didn't change. Both are
noise — keep them independent.

Practical implication: this repo only has one skill today, so the two
versions look similar in practice. If we ever add a second skill, each
will track its own ClawHub history independently of the npm package.

### When to bump

**Package version (`package.json`)** — *any* release of the bundle:

| Bump | Trigger |
|---|---|
| `PATCH` | Doc updates, installer fix, README polish, CI changes |
| `MINOR` | New skill added/removed, installer feature, backwards-compatible bundle change |
| `MAJOR` | Installer contract breaks (path layout, command names, env requirements) |

**Per-skill version (`SKILL.md`)** — only when *that skill's playbook*
changes:

| Bump | Trigger |
|---|---|
| `PATCH` | Wording polish, doc-style edits, no agent-observable change |
| `MINOR` | New optional inputs/outputs, expanded scope, backwards-compatible |
| `MAJOR` | Breaking change to inputs/outputs, the playbook is materially different, the skill was renamed |

If a skill's `SKILL.md` is byte-identical between two releases, its
version stays the same on both.

## Cutting a release

1. Edit `toolbelt/SKILL.md` if the playbook changed. Bump its top-level
   `version:` per the rules above.
2. Bump `"version"` in `package.json` per the rules above.
3. Run validation locally:

   ```bash
   .github/scripts/validate_skills.py
   ```

4. Commit and push to `main`:

   ```bash
   git commit -am "vX.Y.Z: <one-line summary>"
   git push
   ```

5. That's it. `publish-npm.yml` fires automatically:
   - Detects the version bump
   - Publishes `@toolbeltai/skills@vX.Y.Z` to npm
   - Pushes git tag `vX.Y.Z`
   - Dispatches `publish.yml` which runs `clawhub publish --owner
     toolbeltai --version <skill_ver>` for each skill directory under
     the `@toolbeltai` organization
   - Calls Smithery if `SMITHERY_TOKEN` is set

## Auth

`publish-npm.yml`:

- **Currently** uses `NPM_TOKEN` repo secret (classic auth) because the
  repo is private — npm's OIDC trusted publishing has inconsistent
  behavior on private repos.
- **Once the repo is public**, switch back to OIDC by re-adding
  `id-token: write` to the workflow's `permissions:` block and removing
  the `NODE_AUTH_TOKEN` env from the publish step. OIDC + `--provenance`
  give npm's "verified build" badge for free.

`publish.yml`:

- Uses `CLAWHUB_TOKEN` repo secret. The workflow runs
  `clawhub login --token "$CLAWHUB_TOKEN" --no-browser` once before
  publishing. The token is a personal token from the maintainer who
  owns the `@toolbeltai` org on ClawHub.

## Monitoring a release

```bash
gh run list --workflow=publish-npm.yml --limit 3 --repo toolbeltai/toolbelt-skills
gh run list --workflow=publish.yml --limit 3 --repo toolbeltai/toolbelt-skills
```

A green pair means npm + ClawHub both succeeded.

## "Version already exists" is fine

If you re-trigger `publish.yml` manually without bumping per-skill
versions, ClawHub returns `Uncaught ConvexError: Version already
exists`. This is the registry correctly refusing to overwrite a
published immutable version — not a failure to act on.

## "Rate limit: 5 new skills per hour"

ClawHub caps initial skill creations at 5/hour. Only the *first* publish
of a brand-new slug counts. Re-publishing existing slugs at a new
version is unmetered. If this ever bites us with a new skill rollout,
wait an hour and re-dispatch.

## Rolling back

Skills are immutable once published (semver guarantees). To pull back a
bad release:

1. **npm:** `npm deprecate @toolbeltai/skills@X.Y.Z "reason"`. Deprecated
   versions still install but emit a warning. Hard deletes only allowed
   within 72h of publish.
2. **ClawHub:** `clawhub hide toolbelt` removes the skill from search +
   browse; existing installs keep working. `clawhub unhide toolbelt`
   restores it. For a hard pull, `clawhub delete toolbelt`.
3. **Forward fix:** ship a patch release with the fix. That's the
   recommended path — roll-forward, not roll-back.

## Pre-release / dev

For testing workflow changes without affecting the published bundle:

- Edit + push to a feature branch. `publish-npm.yml` only fires on
  `main` pushes, so branches are safe.
- Use `gh workflow run publish.yml -f VERSION=v0.X.Y` to manually
  trigger the ClawHub publish path against a specific tag for testing.
