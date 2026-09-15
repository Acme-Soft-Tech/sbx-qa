"""Load a pytest JSON report into Postgres. The monitoring bands read test_runs.pass_rate.

Hosted, not local Docker: a baseline that only exists when a laptop is open cannot
drive anything.
"""
import json
import os
import sys

import psycopg

import config


def main(report_path: str = "report.json") -> int:
    if not config.DB_URL:
        print("SBX_DB_URL unset — skipping load", file=sys.stderr)
        return 0

    # This runs under `if: always()`, so a missing report means the suite died
    # before it could write one. That is already being reported as the suite's
    # failure; crashing here just buries it under a second, misleading traceback.
    if not os.path.exists(report_path):
        print(f"{report_path} not found — the suite produced no report; nothing to load",
              file=sys.stderr)
        return 0

    with open(report_path) as fh:
        report = json.load(fh)

    summary = report.get("summary", {})
    tests = report.get("tests", [])
    run_id = config.RUN_ID
    markers = os.environ.get("SBX_MARKERS", "")

    with psycopg.connect(config.DB_URL) as conn, conn.cursor() as cur:
        cur.execute(
            """insert into test_runs (run_id, suite, markers, base_url, finished_at,
                                      passed, failed, skipped)
               values (%s, %s, %s, %s, now(), %s, %s, %s)
               on conflict do nothing""",
            (run_id, "sbx-qa", markers, config.BASE_URL,
             summary.get("passed", 0), summary.get("failed", 0), summary.get("skipped", 0)),
        )
        for t in tests:
            cur.execute(
                """insert into test_results (run_id, nodeid, outcome, duration, message)
                   values (%s, %s, %s, %s, %s)""",
                (run_id, t.get("nodeid"), t.get("outcome"),
                 (t.get("call") or {}).get("duration"),
                 ((t.get("call") or {}).get("longrepr") or "")[:4000]),
            )
    print(f"loaded run {run_id}: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))
