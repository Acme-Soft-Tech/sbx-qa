import pytest

from wizard_helpers import (
    current_step,
    drive_to_otp_step,
    fill_debt_step,
    fill_email_step,
    fill_name_step,
    open_funnel,
)


@pytest.mark.regression
class TestRegression:
    def test_all_four_steps_advance(self, page, base_url):
        open_funnel(page, base_url)
        fill_name_step(page)
        fill_email_step(page)
        fill_debt_step(page)
        assert current_step(page) == 4

    def test_reaches_otp_step_without_sending(self, page, base_url):
        """Stops short of Send code on purpose. Nothing here may send an SMS."""
        drive_to_otp_step(page, base_url)
        assert page.is_visible("[data-testid='step-otp']")

    def test_email_validation_blocks_advance(self, page, base_url):
        open_funnel(page, base_url)
        fill_name_step(page)
        page.fill("[data-testid='input-email']", "not-an-email")
        page.click("[data-testid='next']")
        assert current_step(page) == 2
