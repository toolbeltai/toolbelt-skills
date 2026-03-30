# run-toolbelt evals

Smoke tests for the `run-toolbelt` skill. Tests are defined in `evals.json` following the [agentskills.io eval format](https://agentskills.io/skill-creation/evaluating-skills).

## Test cases

| ID | Covers | Phases expected |
|----|--------|-----------------|
| 1 | Connection + namespace inspect only | 0, 1, 2 |
| 2 | Inline document upload + question | 0, 1, 2, 3, 5 |
| 3 | URL-based PDF upload + question | 0, 1, 2, 3, 5 |

## Running an eval

Each eval is a Claude Code prompt. Run it with the skill loaded:

```
/run-toolbelt <paste the eval's prompt field>
```

Or invoke via subagent for isolation (recommended for benchmarking):

```
Execute this task with the run-toolbelt skill:
- Skill path: /path/to/run-toolbelt
- Task: <prompt>
- Save outputs to: evals-workspace/iteration-1/eval-<id>/with_skill/outputs/
```

## Grading

Check the skill's `RESULT` block against each assertion in `evals.json`. Record PASS/FAIL with evidence. See the [eval grading guide](https://agentskills.io/skill-creation/evaluating-skills#grading-outputs) for the grading.json format.

## Iteration workspace layout

```
run-toolbelt-workspace/
└── iteration-1/
    ├── eval-1-connection-check/
    │   └── with_skill/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    ├── eval-2-inline-doc-question/
    └── eval-3-url-doc-question/
```
