#!/usr/bin/env node
/**
 * toolbelt-skills — install Toolbelt's skills into ~/.claude/skills/
 *
 * Usage:
 *   npx @toolbeltai/skills install       # copy skills (default)
 *   npx @toolbeltai/skills uninstall     # remove them
 *   npx @toolbeltai/skills list          # print what would be installed
 *   npx @toolbeltai/skills path          # print where they would go
 *
 * The @toolbeltai/cli package wraps this for its own install flow; this
 * CLI exists so the skills package stands on its own — anyone can install
 * without needing the Toolbelt CLI or hitting any Toolbelt-hosted service.
 *
 * Layout: skills install FLAT under ~/.claude/skills/ per AgentSkills spec
 * (agentskills.io) and Claude Code docs. An earlier version nested them
 * under ~/.claude/skills/toolbelt/; that broke discovery in OpenClaw and
 * was non-standard for Claude Code. We clean up the legacy dir on install.
 */
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync, statSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const PKG_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const TARGET = join(homedir(), '.claude', 'skills');
const LEGACY_NESTED_DIR = join(TARGET, 'toolbelt');

/** Any top-level directory containing a SKILL.md is a skill. */
function listSkills() {
  return readdirSync(PKG_ROOT, { withFileTypes: true })
    .filter((e) => e.isDirectory() && !e.name.startsWith('.') && e.name !== 'node_modules' && e.name !== 'bin' && e.name !== 'assets')
    .map((e) => e.name)
    .filter((name) => existsSync(join(PKG_ROOT, name, 'SKILL.md')));
}

function cleanupLegacy() {
  if (existsSync(LEGACY_NESTED_DIR)) {
    rmSync(LEGACY_NESTED_DIR, { recursive: true, force: true });
    console.log(`  migrated: removed legacy ~/.claude/skills/toolbelt/`);
  }
}

function cmdInstall() {
  const skills = listSkills();
  if (skills.length === 0) {
    console.error('  ✗ No skills found in package. This is a packaging bug — please report.');
    process.exit(1);
  }

  mkdirSync(TARGET, { recursive: true });
  cleanupLegacy();

  for (const name of skills) {
    const src = join(PKG_ROOT, name);
    const dst = join(TARGET, name);
    rmSync(dst, { recursive: true, force: true });
    cpSync(src, dst, { recursive: true });
    console.log(`  ✓ ${name}`);
  }
  // Optional assets (icons, tapes) — copy if present so popups render right.
  const assetsSrc = join(PKG_ROOT, 'assets');
  if (existsSync(assetsSrc) && statSync(assetsSrc).isDirectory()) {
    const assetsDst = join(TARGET, 'assets');
    rmSync(assetsDst, { recursive: true, force: true });
    cpSync(assetsSrc, assetsDst, { recursive: true });
  }

  console.log('');
  console.log(`  Installed ${skills.length} skills to ${TARGET}`);
  console.log('  Restart Claude Code to pick them up.');
}

function cmdUninstall() {
  // Remove installed skills and legacy nested dir.
  cleanupLegacy();
  const skills = listSkills();
  let removed = 0;
  for (const name of skills) {
    const dst = join(TARGET, name);
    if (existsSync(dst)) {
      rmSync(dst, { recursive: true, force: true });
      removed++;
    }
  }
  const assetsDst = join(TARGET, 'assets');
  if (existsSync(assetsDst)) {
    rmSync(assetsDst, { recursive: true, force: true });
  }
  if (removed === 0) {
    console.log('  (nothing to remove)');
  } else {
    console.log(`  Removed ${removed} skills from ${TARGET}`);
  }
}

function cmdList() {
  for (const name of listSkills()) console.log(`  ${name}`);
}

function cmdPath() {
  console.log(TARGET);
}

function usage() {
  console.log(`toolbelt-skills — install Toolbelt skills into ~/.claude/skills/

Usage:
  npx @toolbeltai/skills install       Install skills (default)
  npx @toolbeltai/skills uninstall     Remove skills
  npx @toolbeltai/skills list          List what would be installed
  npx @toolbeltai/skills path          Print target install path
`);
}

const cmd = process.argv[2] ?? 'install';
switch (cmd) {
  case 'install':
    cmdInstall();
    break;
  case 'uninstall':
    cmdUninstall();
    break;
  case 'list':
    cmdList();
    break;
  case 'path':
    cmdPath();
    break;
  case '-h':
  case '--help':
  case 'help':
    usage();
    break;
  default:
    console.error(`Unknown command: ${cmd}`);
    usage();
    process.exit(2);
}
