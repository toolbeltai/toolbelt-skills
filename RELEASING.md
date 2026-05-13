# Releasing toolbelt-skills

Skills are distributed through **three** channels on every release:

| Channel | Consumer | How it gets there |
|---|---|---|
| **GitHub tag** | `@toolbeltai/cli` via `giget` | `git tag vX.Y.Z && git push --tags` + GitHub Release |
| **ClawHub** | OpenClaw users | `.github/workflows/publish.yml` runs on release-published |
| **Smithery (MCP)** | MCP client directories | Same workflow, same trigger |

The CLI pins a specific tag at build time (see `packages/cli/src/skills/install.ts`
in the `toolbelt` repo). Users running `npx @toolbeltai/cli` get the exact skills
version that CLI was tested against — reproducible, upgradeable, revertible.

## Versioning

There are **two independent versions**, and they intentionally diverge:

| Version | Source of truth | What it tracks |
|---|---|---|
| Package version | `package.json` `"version"` | The npm bundle (`@toolbeltai/skills@X.Y.Z`). Bumps on every release of the bundle, regardless of which skills changed. |
| Per-skill version | each `SKILL.md` top-level `version:` | That specific skill's ClawHub release. Bumps **only when that skill's playbook changes**. |

Both are SemVer.

### Why they're independent

Once a skill is published to ClawHub at e.g. `2.0.0`, semver forbids
publishing `0.x` of the same slug. Tying every skill's version to the
package would either (a) force the package to start above the highest
skill version forever, or (b) force every skill to bump on every package
release even when nothing in that skill changed. Both are noise.

Treat them as separate streams:

- The package version is the **install version** — what a user pins via
  npm or what the Toolbelt CLI bundles.
- The per-skill version is the **registry version** — what shows on
  ClawHub per skill, what a user pins when they install a single skill
  directly via `clawhub install <slug>@X.Y.Z`.

### When to bump a `SKILL.md` version

Only when the skill's behavior or contract changes:

- `PATCH` — wording polish, doc-style edits, no agent-observable change.
- `MINOR` — new optional inputs/outputs, expanded scope (e.g. single→multi-CSV), backwards-compatible.
- `MAJOR` — breaking change to inputs/outputs, the skill's playbook is materially different, or the skill was renamed.

Do **not** bump the per-skill version just because the package version
moved. If a skill's `SKILL.md` is byte-identical between two releases,
its version stays the same on both.

### When to bump the package version

Any release of the bundle:

- `PATCH` — fixes inside the CLI installer, doc updates, one or more
  skills patched.
- `MINOR` — new skill added/removed, installer feature, any backwards-compatible bundle change.
- `MAJOR` — installer contract breaks (path layout, command names, env requirements).

### Publish flow with the two versions

The workflow [`publish.yml`](.github/workflows/publish.yml) extracts each
skill's own `version:` from its `SKILL.md` and passes it to
`clawhub publish --version "$SKILL_VER"`. The package version is used
separately by `publish-npm.yml` for the npm publish + git tag.

## Cutting a release

1. Update `CHANGELOG.md` with changes since last tag.
2. Run validation locally:
   ```bash
   .github/scripts/validate_skills.py
   ```
3. Tag and push:
   ```bash
   git tag -a v0.1.0 -m "Initial public release"
   git push origin v0.1.0
   ```
4. On GitHub, draft a release from the tag. **Publish** it — the
   [publish workflow](.github/workflows/publish.yml) fires automatically:
   - Every skill with a `SKILL.md` is uploaded to ClawHub via `clawhub publish`
   - The MCP server is registered with Smithery
5. Bump `SKILLS_REF` in the CLI's `packages/cli/src/skills/install.ts` to the
   new tag. Cut a matching CLI release (see toolbelt monorepo's own
   release doc).

## Pre-release / dev

For local development of the CLI against un-released skills, set
`SKILLS_REF = 'main'` in `install.ts` and re-build. Never publish an npm
release of `@toolbeltai/cli` with `SKILLS_REF` pointing at a branch.

## Rolling back

If a release breaks users:

1. Delete the GitHub Release (keeps the tag for the record).
2. Cut a new patch tag with the fix (e.g. `v0.1.1`).
3. Publish a new CLI release bumping `SKILLS_REF` to the patch tag.

ClawHub and Smithery entries stay at whatever was last published — users
with the new CLI get the new skills; users on the old CLI are unaffected.
