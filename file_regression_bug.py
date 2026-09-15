"""File a Linear bug from a failed run — with no model in the path.

The Claude triage job writes a better issue than this does. But it needs an
Anthropic key, and the thesis of Stage 6 is not "Claude writes a good bug report",
it is "work arrives in the queue that no human filed". That part is arithmetic and
a GraphQL call, so it should not depend on a model being available.

Runs when ANTHROPIC_API_KEY is absent. Deduplicates on a stable fingerprint in the
issue title so a suite failing five nights running produces one issue and four
comments, not five issues.
"""
import json
import os
import sys
import urllib.request

API = "https://api.linear.app/graphql"


def gql(query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": os.environ["LINEAR_API_KEY"],
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        raise RuntimeError(json.dumps(body["errors"])[:500])
    return body["data"]


SEARCH = """query($q: String!) {
  issueSearch(filter: {title: {containsIgnoreCase: $q}}, first: 5) {
    nodes { id identifier title state { type } }
  }
}"""

CREATE = """mutation($input: IssueCreateInput!) {
  issueCreate(input: $input) { success issue { id identifier url } }
}"""

COMMENT = """mutation($input: CommentCreateInput!) {
  commentCreate(input: $input) { success comment { id } }
}"""


def main(report_path: str = "report.json") -> int:
    with open(report_path) as fh:
        report = json.load(fh)

    failures = [t for t in report.get("tests", []) if t.get("outcome") == "failed"]
    if not failures:
        print("no failures — nothing to file")
        return 0

    # Stable fingerprint: the set of failing test ids, not the run number.
    nodeids = sorted(t["nodeid"] for t in failures)
    fingerprint = nodeids[0].split("::")[-1]
    title = f"[auto] Acceptance failure: {fingerprint}"

    run_url = (
        f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
        f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/"
        f"{os.environ.get('GITHUB_RUN_ID', '')}"
    )
    detail = "\n".join(f"- `{n}`" for n in nodeids)
    body = (
        f"Filed automatically by the acceptance run "
        f"(trigger: `{os.environ.get('TRIGGER', 'unknown')}`). **No human filed this.**\n\n"
        f"Failing tests ({len(nodeids)}):\n{detail}\n\n"
        f"- Run: {run_url}\n"
        f"- Base URL under test: `{os.environ.get('SBX_BASE_URL', 'unknown')}`\n\n"
        f"_Deterministic triage — no model in the path. A Claude-written diagnosis "
        f"would be richer; this exists so the loop closes without an Anthropic key._"
    )

    existing = gql(SEARCH, {"q": title})["issueSearch"]["nodes"]
    open_match = next((i for i in existing if i["state"]["type"] not in ("completed", "canceled")), None)

    if open_match:
        gql(COMMENT, {"input": {"issueId": open_match["id"], "body": f"Failed again.\n\n{body}"}})
        print(f"commented on existing {open_match['identifier']}")
        result = {"commented": open_match["identifier"]}
    else:
        created = gql(CREATE, {"input": {
            "teamId": os.environ["LINEAR_TEAM_ID"],
            "title": title,
            "description": body,
        }})["issueCreate"]
        issue = created["issue"]
        print(f"created {issue['identifier']}: {issue['url']}")
        result = {"created": issue["identifier"]}

    # The assertion the workflow checks. Without it this fails silently and looks
    # exactly like "no bugs were found".
    with open("triage-result.json", "w") as fh:
        json.dump(result, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))
