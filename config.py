"""Environment-driven config. NO hardcoded default host — deliberately.

The real repo defaults to evafi.relintex.dev, and regression.yml carries a comment
explaining why passing an unset repo variable silently blanks it. A default that only
applies when the var is unset is a trap: CI passes an empty string, the host blanks,
and the suite reports green while testing nothing.

Gate G4 points this at a per-PR Vercel preview, so there is no sensible default anyway.
"""
import os


def _required(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        raise RuntimeError(
            f"{name} is not set.\n"
            f"The acceptance suite has no default host on purpose — it runs against a\n"
            f"per-PR preview URL. Set it explicitly:\n"
            f"  SBX_BASE_URL=https://sbx-web-<hash>.vercel.app pytest -m smoke"
        )
    return v.rstrip("/")


BASE_URL = _required("SBX_BASE_URL")
DB_URL = os.environ.get("SBX_DB_URL", "")
RUN_ID = os.environ.get("GITHUB_RUN_ID", "local")
HEADLESS = os.environ.get("SBX_HEADLESS", "1") == "1"
TIMEOUT_MS = int(os.environ.get("SBX_TIMEOUT_MS", "15000"))
