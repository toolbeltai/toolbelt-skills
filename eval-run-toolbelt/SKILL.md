---
name: eval-run-toolbelt
description: >
  Runs the run-toolbelt eval suite. Executes each test case in evals.json as an
  isolated subagent, grades the RESULT block against assertions, and emits a
  structured benchmark summary. Use to smoke test the run-toolbelt skill or
  validate changes before publishing a new version.
license: MIT
metadata:
  author: toolbeltai
  version: "1.0"
---

Run the `run-toolbelt` eval suite end-to-end. Execute each eval as an isolated
subagent, grade the output against its assertions, and emit a benchmark summary.

## Step 1: Load the eval definitions

Read the file at `run-toolbelt/evals/evals.json` in the current working directory.
Extract all evals. If the file cannot be read, halt and report the error.

## Step 2: Run each eval as an isolated subagent

For each eval in the list, spawn a subagent with this instruction:

```
You are running a smoke test of the run-toolbelt skill.

Your task:
<paste the eval's prompt field verbatim>

Instructions:
- You have access to the Toolbelt MCP tools (get_semantic_names, toolbelt_context,
  toolbelt_save, toolbelt_jobs, toolbelt_search, toolbelt_connect, toolbelt_execute).
- Follow the run-toolbelt SKILL.md exactly. Work through phases in order without
  asking for confirmation.
- Emit the structured RESULT block (or FAILURE block) when done.
- Do not add commentary beyond the RESULT/FAILURE block.
```

Run all evals concurrently where possible (evals with no shared state can run in parallel).
Capture the full output of each subagent.

## Step 3: Grade each eval

For each eval, check every assertion in its `assertions` array against the subagent output.

Grading rules:
- **PASS**: the output contains clear, concrete evidence the assertion is satisfied.
- **FAIL**: the assertion is not satisfied or the evidence is absent.
- Do not give benefit of the doubt — require actual evidence for a PASS.

For each assertion record:
- `passed`: true or false
- `evidence`: one sentence describing what in the output supports the verdict

## Step 4: Emit the benchmark report

Output a report in this format:

```
EVAL RESULTS: run-toolbelt
==========================

Eval 1 — <eval prompt summary>
  Status: PASS / FAIL / ERROR
  Assertions:
    [PASS] <assertion text> — <evidence>
    [FAIL] <assertion text> — <evidence or "not found">
  Pass rate: X/Y

Eval 2 — <eval prompt summary>
  ...

Eval 3 — <eval prompt summary>
  ...

SUMMARY
-------
Overall pass rate: X/Y assertions across all evals
Evals fully passing: N of 3
Evals with failures: N of 3

Failures to investigate:
  - Eval <id>, assertion: "<text>" — <evidence>
```

If any eval produced a FAILURE block instead of a RESULT block, count all its
assertions as failed and include the FAILURE reason in the report.
