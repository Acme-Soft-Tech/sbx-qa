"""Assert that triage actually reached Linear — whichever path ran.

The previous check read a local triage-result.json, which only the deterministic
filer writes. The Claude path never produces one, so on that path the assertion
was either skipped or wrong. Worse, when the Claude step failed outright the whole
job stopped and nothing was filed at all — indistinguishable, from the outside,
from "the suite passed and there was nothing to file".

So ask Linear instead. It is the only thing that knows the truth.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

WINDOW_MINUTES = 15

QUERY = """query($teamId:ID!,$since:DateTimeOrDuration!){
  issues(filter:{ team:{ id:{ eq:$teamId } }, updatedAt:{ gt:$since } }, first:20){
    nodes { identifier title url createdAt updatedAt }
  }
}"""


def main() -> int:
    key = os.environ.get("LINEAR_API_KEY", "").strip()
    if not key:
        print("::error::LINEAR_API_KEY unset — cannot verify triage reached Linear")
        return 1

    since = (datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)).isoformat()
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=json.dumps({
            "query": QUERY,
            "variables": {"teamId": os.environ["LINEAR_TEAM_ID"], "since": since},
        }).encode(),
        headers={"Content-Type": "application/json", "Authorization": key},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)

    if body.get("errors"):
        print("::error::Linear query failed: " + body["errors"][0].get("message", "?"))
        return 1

    touched = body["data"]["issues"]["nodes"]
    if not touched:
        print(f"::error::The suite failed but no Linear issue was created or updated "
              f"in the last {WINDOW_MINUTES} minutes.")
        print("Triage did not reach Linear. From the outside this is indistinguishable")
        print("from a green suite, which is why it is asserted rather than assumed.")
        return 1

    print(f"triage reached Linear — {len(touched)} issue(s) touched in the last "
          f"{WINDOW_MINUTES} minutes:")
    for i in touched:
        print(f"  {i['identifier']}  {i['title'][:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
