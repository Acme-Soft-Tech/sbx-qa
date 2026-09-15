import pytest

from wizard_helpers import (
    current_step,
    progress_step,
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

    def test_progress_bar_tracks_step(self, page, base_url):
        """The bar must not keep a counter of its own — it must agree with the funnel.

        Checked at two steps rather than one: a bar hardcoded to 1 would pass a
        single-step assertion.
        """
        open_funnel(page, base_url)
        assert progress_step(page) == current_step(page)
        fill_name_step(page)
        assert progress_step(page) == current_step(page)
