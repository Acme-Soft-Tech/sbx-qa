"""Shared funnel helpers. Tests import these — they never keep a local copy.

The source repo's 750-line test_dailyrun.py holds its own diverged copies of nineteen
of these, which is how the same helper ends up behaving differently in two suites.
"""
from playwright.sync_api import Page


def open_funnel(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/onboarding")
    page.wait_for_selector("[data-testid='step-name']")


def fill_name_step(page: Page, name: str = "Test User") -> None:
    page.fill("[data-testid='input-name']", name)
    page.click("[data-testid='next']")


def fill_email_step(page: Page, email: str = "test@example.com") -> None:
    page.fill("[data-testid='input-email']", email)
    page.click("[data-testid='next']")


def fill_debt_step(page: Page, amount: str = "25000") -> None:
    page.fill("[data-testid='input-debt']", amount)
    page.click("[data-testid='next']")


def drive_to_otp_step(page: Page, base_url: str) -> None:
    """Everything up to, but NOT including, pressing Send code.

    Stopping short of the send is what makes this safe to call from smoke and
    regression. Anything that presses Send code belongs in the e2e suite.
    """
    open_funnel(page, base_url)
    fill_name_step(page)
    fill_email_step(page)
    fill_debt_step(page)
    page.wait_for_selector("[data-testid='step-otp']")


def progress_step(page: Page) -> int:
    """Read the progress indicator's own idea of which step it is on.

    Reads data-step off [data-testid="progress"] — the contract pinned in
    sdlc/work/SBX-5/spec.md and asserted by a unit test in sbx-web, so a rename
    breaks there rather than here.

    Lives in wizard_helpers.py rather than inline in a test because AGENTS.md
    requires it: a helper copied into two suites is a helper that diverges.
    """
    return int(page.get_attribute("[data-testid='progress']", "data-step") or "0")


def current_step(page: Page) -> int:
    return int(page.get_attribute("[data-testid='funnel']", "data-step") or "0")
