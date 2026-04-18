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

SemVer. Current scheme is flat — one version covers the whole skill set.

- `PATCH` — wording edits, doc fixes, demo-only asset updates
- `MINOR` — new skill added, backwards-compatible change to an existing skill
- `MAJOR` — breaking change to a skill's arguments or output contract, skill
  renamed or removed

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
