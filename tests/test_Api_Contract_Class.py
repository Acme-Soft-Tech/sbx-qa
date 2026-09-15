"""HTTP-level contract tests for the sbx-web API routes.

WHY THIS FILE EXISTS
--------------------
The UI suites deliberately stop short of "Send code", because pressing it sends an
SMS. That left the single riskiest path in the funnel — the call out to the upstream
lender API — covered only by the `e2e` marker, which is blocked on every PR.

The result was a suite that passed 6/6 while /api/otp was returning 500 in
production because RELINTEX_BASE_URL was unset. A green gate over a broken path is
worse than no gate.

The split in sbx-api is what makes this fixable: the SMS side effect lives in
/api/send-sms, while /api/otp only ASKS upstream for a code. So these tests exercise
the full chain — browser-facing route, upstreamFetch, upstream service — and touch
nothing that can send a message. No SMS risk, no marker widening.

Plain urllib on purpose: no browser needed, so these run in milliseconds and cannot
be blamed on Playwright flake.
"""
import json
import urllib.error
import urllib.request

import pytest


def _post(url: str, payload: dict | None, raw: str | None = None):
    data = raw.encode() if raw is not None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body or b"{}")
        except json.JSONDecodeError:
            return e.code, {"_raw": body.decode(errors="replace")}


@pytest.mark.regression
class TestApiContract:
    def test_health_is_dependency_free(self, base_url):
        with urllib.request.urlopen(f"{base_url}/api/health", timeout=30) as r:
            assert r.status == 200
            assert json.loads(r.read())["ok"] is True

    def test_otp_request_reaches_upstream(self, base_url):
        """The test that would have caught the unset RELINTEX_BASE_URL immediately.

        A 500 here means upstreamFetch threw — almost always a missing or wrong
        env var on the deployment, not a code defect.
        """
        status, body = _post(f"{base_url}/api/otp", {"session_id": "contract-test"})
        assert status == 200, f"upstream chain broken: {status} {body}"
        assert body.get("success") is True
        assert body.get("req_id")

    def test_otp_rejects_a_body_with_no_session_id(self, base_url):
        status, _ = _post(f"{base_url}/api/otp", {})
        assert status == 400

    def test_otp_survives_a_malformed_body(self, base_url):
        status, _ = _post(f"{base_url}/api/otp", None, raw="not json")
        assert status == 400

    def test_no_upstream_detail_leaks_to_the_client(self, base_url):
        """Whatever the outcome, the client must never see upstream internals."""
        status, body = _post(f"{base_url}/api/otp", {"session_id": "contract-test"})
        blob = json.dumps(body).lower()
        for leak in ("vercel.app", "econnrefused", "econnreset", "traceback", "bearer"):
            assert leak not in blob, f"response leaked {leak!r}: {body}"
