import pytest


# https://github.com/pytest-dev/pytest-splinter/issues/158
#  AttributeError: module 'splinter.driver.webdriver.firefox' has no attribute 'WebDriverElement'


from pytest_splinter.webdriver_patches import patch_webdriver


@pytest.fixture(scope="session")
def browser_patches():
    patch_webdriver()
