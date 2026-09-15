"""conftest.py sits at the REPO ROOT, not in tests/.

This is a real convention from the source repo and it is load-bearing: fixtures
resolve differently if this moves, and the breakage is subtle rather than loud.
"""
import pytest
from playwright.sync_api import sync_playwright

import config


@pytest.fixture(scope="session")
def base_url():
    return config.BASE_URL


@pytest.fixture(scope="session")
def _browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.HEADLESS)
        yield browser
        browser.close()


@pytest.fixture
def page(_browser):
    context = _browser.new_context()
    context.set_default_timeout(config.TIMEOUT_MS)
    # Traces make the triage agent's Linear issue far better than a screenshot does.
    context.tracing.start(screenshots=True, snapshots=True)
    page = context.new_page()
    yield page
    context.tracing.stop(path=f"traces/{id(page)}.zip")
    context.close()
