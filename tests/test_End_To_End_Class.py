"""THIS SUITE SENDS SMS.

Never runs on a PR. regression.yml restricts PR runs to "smoke or regression", and
sms-guard.sh blocks an agent widening the marker expression without SBX_ALLOW_SMS=1.
"""
import pytest

from wizard_helpers import drive_to_otp_step


@pytest.mark.e2e
@pytest.mark.flaky(reruns=0)  # pytest.ini sets --reruns 2 globally. A retry here sends
                              # a SECOND real message that nobody counted. Every
                              # SMS-sending test in this repo carries this marker.
class TestEndToEnd:
    def test_full_onboarding_journey_reaches_otp_screen(self, page, base_url):
        drive_to_otp_step(page, base_url)
        page.click("[data-testid='send-code']")      # <- the real side effect
        page.wait_for_selector("[data-testid='otp-sent']")
        assert page.is_visible("[data-testid='otp-sent']")

    @pytest.mark.flaky(reruns=0)
    def test_valid_code_verifies(self, page, base_url):
        drive_to_otp_step(page, base_url)
        page.click("[data-testid='send-code']")      # <- the real side effect
        page.fill("[data-testid='input-otp']", "000000")
        page.click("[data-testid='verify']")
        assert page.is_visible("[data-testid='verified']")
