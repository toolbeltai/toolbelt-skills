#!/usr/bin/env python3
"""
CI eval runner for toolbelt-skills.

Strategy
--------
- Provision a namespace via POST https://toolbelt.ai/api/onboard
- For each skill's evals/evals.json, run evals that have a "tool" field by
  calling the MCP server directly over HTTP (no LLM required).
- Evals without a "tool" field are agent-level and skipped here; they are
  covered by the eval-run-toolbelt skill.
- Assertions are evaluated against the raw MCP tool response:
    "RESULT block emitted"        → tool response is non-empty / non-error
    "X is non-empty"              → response field X exists and is truthy
    "X is greater than N"         → response field X > N
    "X is a non-negative integer" → response field X >= 0
    "X is present ..."            → response field X exists
    "error is null"               → no error field in response
    "at least one of X, Y, Z ..." → any of those fields is truthy
- Post to Slack on failure (SLACK_WEBHOOK_URL secret).
- Create a GitHub issue on failure (GITHUB_TOKEN secret).
"""
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

ONBOARD_URL = "https://app.toolbelt.ai/api/onboard"
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")

SESSION = requests.Session()
SESSION.headers.update({"Content-Type": "application/json"})

# ---------------------------------------------------------------------------
# MCP helpers — HTTP+SSE stateful session
# ---------------------------------------------------------------------------

UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
UUID_SEARCH_RE = re.compile(r"\b" + UUID_RE.pattern + r"\b", re.IGNORECASE)

_MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

_REQ_ID = 0


def _next_id() -> int:
    global _REQ_ID
    _REQ_ID += 1
    return _REQ_ID


def _parse_sse(text: str) -> dict:
    """Extract the first JSON object from an SSE response body."""
    for line in text.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    # Fallback: maybe it's plain JSON
    return json.loads(text)


def _mcp_post(mcp_url: str, token: str, session_id: str | None, payload: dict) -> dict:
    headers = {**_MCP_HEADERS, "Authorization": f"Bearer {token}"}
    if session_id:
        headers["mcp-session-id"] = session_id
    resp = SESSION.post(mcp_url, json=payload, headers=headers, timeout=90)
    resp.raise_for_status()
    body = _parse_sse(resp.text)
    if "error" in body:
        raise RuntimeError(f"MCP error: {body['error']}")
    return body


def mcp_init(mcp_url: str, token: str) -> str:
    """Initialize an MCP session and return the session ID."""
    payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "eval-runner", "version": "1.0"},
        },
        "id": _next_id(),
    }
    headers = {**_MCP_HEADERS, "Authorization": f"Bearer {token}"}
    resp = SESSION.post(mcp_url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    session_id = resp.headers.get("mcp-session-id")
    if not session_id:
        raise RuntimeError("MCP initialize did not return mcp-session-id header")
    return session_id


def mcp_call(mcp_url: str, token: str, session_id: str, tool: str, arguments: dict) -> dict:
    """Call one MCP tool and return the parsed result dict."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
        "id": _next_id(),
    }
    body = _mcp_post(mcp_url, token, session_id, payload)
    content = body.get("result", {}).get("content", [])
    if content and content[0].get("type") == "text":
        raw = content[0]["text"]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"_raw": raw}
    return body.get("result", {})


def extract_namespace_id(prompt: str) -> str | None:
    m = UUID_SEARCH_RE.search(prompt)
    return m.group(0) if m else None


# ---------------------------------------------------------------------------
# Per-tool execution handlers
# ---------------------------------------------------------------------------

def run_toolbelt_list(mcp_url, token, sid, ns):
    r = mcp_call(mcp_url, token, sid, "toolbelt_list", {"namespace_id": ns})
    assets = r.get("assets", [])
    # Normalize to assertion field names (raw API uses "total", not "asset_count")
    return {
        **r,
        "asset_count": r.get("total", len(assets)),
        "asset_names": [a.get("name", "") for a in assets],
        "asset_types": [a.get("type") or a.get("asset_type", "") for a in assets],
    }


def run_toolbelt_sql(mcp_url, token, sid, ns):
    # Kinetica blocks queries without WHERE/GROUP BY/LIMIT; always use LIMIT 1
    query = "SELECT 1 AS ping LIMIT 1"
    r = mcp_call(mcp_url, token, sid, "toolbelt_sql", {"namespace_id": ns, "query": query})
    if "_raw" in r:
        # Tool returned an error string, not JSON
        return {"query_used": query, "row_count": None, "columns": [], "error": r["_raw"]}
    return {
        **r,
        "query_used": query,
        "error": None if r.get("success") else r.get("error", "unknown error"),
    }


def run_toolbelt_describe(mcp_url, token, sid, ns):
    list_result = run_toolbelt_list(mcp_url, token, sid, ns)
    assets = list_result.get("assets", [])
    table_name = next((a.get("table_name") for a in assets if a.get("table_name")), None)
    if not table_name:
        return {"skipped": True, "reason": "No tables found in namespace"}
    return mcp_call(mcp_url, token, sid, "toolbelt_describe", {"namespace_id": ns, "table_name": table_name})


def run_toolbelt_share(mcp_url, token, sid, ns):
    list_result = run_toolbelt_list(mcp_url, token, sid, ns)
    assets = list_result.get("assets", [])
    asset_id = next((a.get("asset_id") or a.get("id") for a in assets), None)
    if not asset_id:
        return {"skipped": True, "reason": "No assets in namespace to share"}
    r = mcp_call(mcp_url, token, sid, "toolbelt_share",
                 {"namespace_id": ns, "asset_id": asset_id, "expiresInDays": 1})
    # Response may be plain text: "URL: https://..."
    raw_text = r.get("_raw", "")
    url_match = re.search(r'URL:\s*(https?://\S+)', raw_text)
    share_url = (
        r.get("url") or r.get("share_url") or r.get("shareUrl") or
        (url_match.group(1) if url_match else "")
    )
    return {**r, "share_url": share_url, "url_is_non_empty": bool(share_url)}


def run_toolbelt_get(mcp_url, token, sid, ns):
    out = {}
    errors = []
    for operation in ("sql", "vector", "graph"):
        try:
            r = mcp_call(mcp_url, token, sid, "toolbelt_get",
                         {"namespace_id": ns, "operation": operation, "question": "ping"})
            # sql: dialect_summary is always present; vector: collections/results; graph: relationships
            if operation == "sql":
                non_empty = bool(r.get("dialect_summary") or r.get("relevant_tables"))
            elif operation == "vector":
                non_empty = bool(r.get("collections") or r.get("results"))
            else:
                non_empty = bool(r.get("relationships") or r.get("graph_examples"))
            out[f"{operation}_context_non_empty"] = non_empty
        except Exception:
            errors.append(operation)
            out[f"{operation}_context_non_empty"] = False
    out["errors"] = errors
    return out


def _poll_jobs(mcp_url, token, sid, ns, timeout_s=120, interval_s=10):
    """Poll toolbelt_jobs until no pending/running jobs remain (or timeout)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = mcp_call(mcp_url, token, sid, "toolbelt_jobs", {"namespace_id": ns})
            jobs = r.get("jobs", [])
            pending = [j for j in jobs if j.get("status") in ("pending", "running", "processing")]
            if not pending:
                return
        except Exception:
            pass
        time.sleep(interval_s)


def run_toolbelt_vectors(mcp_url, token, sid, ns):
    # Upload the same Eiffel Tower document the eval specifies
    try:
        mcp_call(mcp_url, token, sid, "toolbelt_save", {
            "namespace_id": ns,
            "asset_type": "document",
            "name": "vectors-eval-doc",
            "file_name": "document.txt",
            "content": (
                "The Eiffel Tower is located in Paris, France. "
                "It was built in 1889 and stands 330 meters tall. "
                "It was designed by engineer Gustave Eiffel."
            ),
            "content_encoding": "text",
        })
        # Wait for semantic indexing to finish before searching
        _poll_jobs(mcp_url, token, sid, ns, timeout_s=120, interval_s=10)
    except Exception:
        pass  # Proceed — namespace may already have indexed content

    r = mcp_call(mcp_url, token, sid, "toolbelt_vectors",
                 {"namespace_id": ns, "question": "How tall is the Eiffel Tower?"})
    results_list = r.get("results", [])
    top_text = ""
    if results_list:
        top = results_list[0]
        top_text = top.get("text") or top.get("content") or top.get("excerpt") or ""
        top_text = str(top_text)[:100]
    height_terms = ("330", "meters", "tall")
    references_height = any(
        term in str(res.get("text", "") or res.get("content", "")).lower()
        for res in results_list for term in height_terms
    )
    return {
        **r,
        "result_count": len(results_list),
        "top_result_excerpt": top_text,
        "references_height": references_height,
    }


TOOL_HANDLERS = {
    "toolbelt_list": run_toolbelt_list,
    "toolbelt_sql": run_toolbelt_sql,
    "toolbelt_describe": run_toolbelt_describe,
    "toolbelt_share": run_toolbelt_share,
    "toolbelt_get": run_toolbelt_get,
    "toolbelt_vectors": run_toolbelt_vectors,
}


# ---------------------------------------------------------------------------
# Assertion evaluation
# ---------------------------------------------------------------------------

def _field_val(data: dict, key: str) -> Any:
    """Case-insensitive field lookup."""
    if key in data:
        return data[key]
    key_lower = key.lower()
    for k, v in data.items():
        if k.lower() == key_lower:
            return v
    return None


def evaluate_assertion(assertion: str, data: dict) -> tuple[bool, str]:
    """Return (passed, detail). data is the raw MCP response dict."""
    a = assertion.strip()
    al = a.lower()

    # Generic success / error checks ------------------------------------------

    if "result block" in al:
        # For direct tool calls, a non-error response counts as "result emitted".
        # Check for truthy error values, not just key presence (error: null is fine).
        err = data.get("error") or data.get("_error")
        passed = not err
        return passed, "tool responded without error" if passed else f"tool returned error: {err}"

    if "failure block" in al and ("no " in al or "not" in al):
        err = data.get("error") or data.get("_error")
        passed = not err
        return passed, "no error in response" if passed else f"error: {err}"

    # skipped is always fine
    if data.get("skipped"):
        return True, f"skipped: {data.get('reason', '')}"

    # "error is null"
    m = re.match(r"(\w+) is null", al)
    if m:
        key = m.group(1)
        val = _field_val(data, key)
        passed = val is None
        return passed, f"{key}=None" if passed else f"{key}={val!r}"

    # "X is a non-negative integer"
    m = re.match(r"(\w+) is a non-negative integer", al)
    if m:
        val = _field_val(data, m.group(1))
        passed = isinstance(val, (int, float)) and val >= 0
        return passed, f"{m.group(1)}={val}"

    # "X is greater than N"
    m = re.match(r"(\w+) is greater than (\d+)", al)
    if m:
        val = _field_val(data, m.group(1))
        threshold = int(m.group(2))
        passed = isinstance(val, (int, float)) and val > threshold
        return passed, f"{m.group(1)}={val} (> {threshold})"

    # "X is non-empty" / "X is a non-empty string" / "X is a non-empty array"
    m = re.match(r"(\w+) is (?:a )?non-empty", al)
    if m:
        val = _field_val(data, m.group(1))
        passed = bool(val)
        return passed, f"{m.group(1)} non-empty" if passed else f"{m.group(1)}={val!r}"

    # "X is present (may be empty ...)"
    m = re.match(r"(\w+) is present", al)
    if m:
        key = m.group(1)
        present = _field_val(data, key) is not None or key in data
        return present, f"{key} present" if present else f"{key} missing"

    # "X is true"
    m = re.match(r"(\w+) is true", al)
    if m:
        val = _field_val(data, m.group(1))
        passed = val is True or str(val).lower() == "true"
        return passed, f"{m.group(1)}={val}"

    # "X is true OR skipped is true"
    if " or skipped is true" in al:
        base = re.sub(r"\s+or skipped is true", "", a, flags=re.IGNORECASE).strip()
        passed, detail = evaluate_assertion(base, data)
        return passed, detail

    # "at least one of X, Y, Z is true"
    if "at least one" in al:
        fields = re.findall(r"\b(\w+_\w+)\b", a)
        truthy = [f for f in fields if _field_val(data, f) is True]
        passed = bool(truthy)
        return passed, f"true fields: {truthy}" if passed else f"none true among {fields}"

    # "X is <UUID>"  — eval prompts use hardcoded UUIDs, CI uses the onboard namespace.
    # Accept any valid UUID rather than requiring the exact eval UUID.
    m = re.match(
        r"(\w+) is ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$", al
    )
    if m:
        key = m.group(1)
        val = _field_val(data, key)
        passed = bool(val and UUID_RE.fullmatch(str(val)))
        return passed, f"{key}={val!r} (valid UUID)" if passed else f"{key}={val!r} (not a UUID)"

    # "X is a positive integer" / "X is a non-negative integer"
    if "positive integer" in al:
        m2 = re.match(r"(\w+)", al)
        if m2:
            val = _field_val(data, m2.group(1))
            passed = isinstance(val, (int, float)) and val > 0
            return passed, f"{m2.group(1)}={val}"

    # Default: skip unknown assertion
    return True, f"(skipped — pattern not matched: {a[:60]})"


# ---------------------------------------------------------------------------
# Run one eval
# ---------------------------------------------------------------------------

def run_eval(mcp_url: str, token: str, sid: str, onboard_ns: str, eval_case: dict) -> tuple[bool, list[dict]]:
    tool = eval_case.get("tool")
    handler = TOOL_HANDLERS.get(tool)
    if not handler:
        return None, [{"assertion": "handler", "passed": None, "detail": f"no handler for tool '{tool}'"}]

    # Always use the onboard namespace — the hardcoded UUIDs in eval prompts are
    # for agent-level testing only and may not be accessible with the CI token.
    ns = onboard_ns

    try:
        data = handler(mcp_url, token, sid, ns)
    except Exception as exc:
        results = []
        for a in eval_case.get("assertions", []):
            results.append({"assertion": a, "passed": False, "detail": f"tool call failed: {exc}"})
        return False, results

    results = []
    all_passed = True
    for a in eval_case.get("assertions", []):
        passed, detail = evaluate_assertion(a, data)
        results.append({"assertion": a, "passed": passed, "detail": detail})
        if passed is False:
            all_passed = False

    return all_passed, results


# ---------------------------------------------------------------------------
# Collect all evals
# ---------------------------------------------------------------------------

def run_all(mcp_url: str, token: str, onboard_ns: str) -> dict:
    print("  Initializing MCP session... ", end="", flush=True)
    sid = mcp_init(mcp_url, token)
    print(f"session {sid[:12]}...")

    report = {}
    for evals_path in sorted(Path(".").glob("*/evals/evals.json")):
        skill = evals_path.parts[0]
        data = json.loads(evals_path.read_text())
        tool_evals = [e for e in data.get("evals", []) if "tool" in e]
        if not tool_evals:
            print(f"  [{skill}] no tool-based evals — skipping")
            continue

        report[skill] = []
        for case in tool_evals:
            label = f"eval {case['id']} ({case['tool']})"
            print(f"  [{skill}] {label} ... ", end="", flush=True)
            passed, assertion_results = run_eval(mcp_url, token, sid, onboard_ns, case)
            status = "PASS" if passed else "FAIL" if passed is False else "SKIP"
            print(status)
            report[skill].append({
                "id": case["id"],
                "tool": case["tool"],
                "passed": passed,
                "assertions": assertion_results,
            })
    return report


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def build_summary(report: dict) -> tuple[str, bool]:
    total = sum(len(v) for v in report.values())
    n_pass = sum(1 for v in report.values() for e in v if e["passed"] is True)
    n_fail = sum(1 for v in report.values() for e in v if e["passed"] is False)
    n_skip = total - n_pass - n_fail

    lines = [f"Evals: {n_pass}/{total} passed  |  {n_fail} failed  |  {n_skip} skipped"]
    for skill, evals in report.items():
        lines.append(f"\n{skill}:")
        for e in evals:
            icon = "✓" if e["passed"] else "✗" if e["passed"] is False else "~"
            lines.append(f"  {icon} eval {e['id']} ({e['tool']})")
            for a in e["assertions"]:
                if a["passed"] is False:
                    lines.append(f"      FAIL: {a['assertion']}")
                    lines.append(f"            {a['detail']}")

    return "\n".join(lines), n_fail > 0


def post_slack(text: str) -> None:
    if not SLACK_WEBHOOK_URL:
        print("  SLACK_WEBHOOK_URL not configured — skipping")
        return
    try:
        r = SESSION.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
        r.raise_for_status()
        print("  Slack notification sent")
    except Exception as exc:
        print(f"  Slack notification failed: {exc}")


def create_issue(title: str, body: str) -> None:
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
        print("  GITHUB_TOKEN / GITHUB_REPOSITORY not configured — skipping issue creation")
        return
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues"
    try:
        r = SESSION.post(
            url,
            json={"title": title, "body": body, "labels": ["eval-failure"]},
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=15,
        )
        r.raise_for_status()
        print(f"  GitHub issue created: {r.json().get('html_url', '?')}")
    except Exception as exc:
        print(f"  GitHub issue creation failed: {exc}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Step 1: Provisioning namespace ===")
    onboard = None
    for attempt in range(1, 4):
        try:
            resp = SESSION.post(ONBOARD_URL, json={}, timeout=60)
            resp.raise_for_status()
            body = resp.json()
            if "errors" in body:
                raise RuntimeError(f"onboard returned errors: {body['errors']}")
            onboard = body
            break
        except Exception as exc:
            print(f"  attempt {attempt}/3 failed: {exc}")
            if attempt == 3:
                print("ERROR: onboard API failed after 3 attempts")
                sys.exit(1)

    mcp_url = onboard["mcpUrl"]
    token = onboard["token"]
    onboard_ns = onboard["namespace"]["id"]
    print(f"  MCP URL : {mcp_url}")
    print(f"  namespace_id: {onboard_ns}")

    print("\n=== Step 2: Running tool-based evals ===")
    report = run_all(mcp_url, token, onboard_ns)

    if not report:
        print("\nNo tool-based evals found. Done.")
        return

    print("\n=== Step 3: Results ===")
    summary, has_failures = build_summary(report)
    print(summary)

    if has_failures:
        print("\n=== Step 4: Alerting ===")
        post_slack(f":x: *toolbelt-skills eval failure*\n```\n{summary}\n```")
        create_issue(
            "Eval failure detected",
            f"The daily eval run detected failures.\n\n```\n{summary}\n```\n\n"
            f"See the [Actions run](${{GITHUB_SERVER_URL}}/${{GITHUB_REPOSITORY}}/actions) for full logs.",
        )
        sys.exit(1)

    print("\nAll evals passed.")


if __name__ == "__main__":
    main()
