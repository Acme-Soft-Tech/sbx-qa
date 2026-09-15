"""PascalCase filename, one class per file — both are real conventions here."""
import pytest

from wizard_helpers import current_step, fill_name_step, open_funnel


@pytest.mark.smoke
class TestSmoke:
    def test_funnel_loads(self, page, base_url):
        open_funnel(page, base_url)
        assert page.title() != ""

    def test_first_step_is_name(self, page, base_url):
        open_funnel(page, base_url)
        assert current_step(page) == 1

    def test_name_step_advances(self, page, base_url):
        open_funnel(page, base_url)
        fill_name_step(page)
        assert current_step(page) == 2
