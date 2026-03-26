#!/usr/bin/env python3
"""
api_tester.py — Automatic HTTP tests (GET, POST, PUT, DELETE)
Usage: python api_tester.py [config_file.json]
"""

import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

# ── Terminal colors ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def color(text, code): return f"{code}{text}{RESET}"

# ── Run a single test ──────────────────────────────────────────────────────────
def run_test(test: dict) -> dict:
    name    = test.get("name", "Unnamed")
    method  = test.get("method", "GET").upper()
    url     = test.get("url", "")
    headers = test.get("headers", {})
    body    = test.get("body", None)
    expect  = test.get("expect", {})

    data = json.dumps(body).encode("utf-8") if body else None
    if data and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status      = resp.status
            resp_body   = resp.read().decode("utf-8", errors="replace")
            elapsed_ms  = int((time.time() - start) * 1000)
    except urllib.error.HTTPError as e:
        status      = e.code
        resp_body   = e.read().decode("utf-8", errors="replace")
        elapsed_ms  = int((time.time() - start) * 1000)
    except Exception as e:
        return {"name": name, "passed": False, "error": str(e), "status": None, "elapsed_ms": 0}

    # ── Assertions ─────────────────────────────────────────────────────────────
    failures = []

    expected_status = expect.get("status")
    if expected_status and status != expected_status:
        failures.append(f"status: expected {expected_status}, got {status}")

    for keyword in expect.get("body_contains", []):
        if keyword not in resp_body:
            failures.append(f"body does not contain: '{keyword}'")

    for keyword in expect.get("body_not_contains", []):
        if keyword in resp_body:
            failures.append(f"body contains unexpected value: '{keyword}'")

    max_ms = expect.get("max_ms")
    if max_ms and elapsed_ms > max_ms:
        failures.append(f"too slow: {elapsed_ms}ms > {max_ms}ms")

    return {
        "name":       name,
        "method":     method,
        "url":        url,
        "status":     status,
        "elapsed_ms": elapsed_ms,
        "passed":     len(failures) == 0,
        "failures":   failures,
        "response":   resp_body[:500] if expect.get("show_response") else None,
    }

# ── Print a test result ────────────────────────────────────────────────────────
def print_result(r: dict, index: int):
    icon   = color("✓", GREEN) if r["passed"] else color("✗", RED)
    status = color(str(r["status"]), CYAN) if r["status"] else color("ERROR", RED)
    ms     = f"{r['elapsed_ms']}ms"

    print(f"  {icon} [{index}] {color(r['name'], BOLD)}")
    if r.get("error"):
        print(f"       {color('→ ' + r['error'], RED)}")
    else:
        print(f"       {color(r['method'], YELLOW)} {r['url']}  —  {status}  ({ms})")
        for f in r.get("failures", []):
            print(f"       {color('⚠ ' + f, RED)}")
        if r.get("response"):
            print(f"       Response: {r['response'][:200]}")

# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "tests.json"

    try:
        with open(config_file, encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(color(f"File '{config_file}' not found.", RED))
        print("Create a tests.json file (see tests_example.json for syntax).")
        sys.exit(1)

    tests    = config.get("tests", [])
    base_url = config.get("base_url", "")
    # Prepend base_url if the test URL is relative
    for t in tests:
        if not t["url"].startswith("http"):
            t["url"] = base_url.rstrip("/") + "/" + t["url"].lstrip("/")

    print(f"\n{color('API TESTER', BOLD)}  —  {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
    print(f"  {len(tests)} test(s) loaded from {color(config_file, CYAN)}\n")

    results = []
    for i, test in enumerate(tests, 1):
        r = run_test(test)
        print_result(r, i)
        results.append(r)

    # ── Summary ────────────────────────────────────────────────────────────────
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed

    print(f"\n{'─'*50}")
    print(f"  {color(f'{passed} passed', GREEN)}  /  {color(f'{failed} failed', RED if failed else GREEN)}  out of {len(results)} tests")

    if config.get("output_json"):
        base, ext = config["output_json"].rsplit(".", 1) if "." in config["output_json"] else (config["output_json"], "json")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file  = f"{base}_{timestamp}.{ext}"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({"date": datetime.now().isoformat(), "results": results}, f, indent=2, ensure_ascii=False)
        print(f"  JSON report: {color(out_file, CYAN)}")

    print()
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
