import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.wait import WebDriverWait


class wait_for_page_load(object):
    def __init__(self, browser):
        self.browser = browser

    def __enter__(self):
        self.old_page = self.browser.find_by_tag("html")[0]._element

    def __exit__(self, *_):
        WebDriverWait(self.browser, 10).until(
            lambda driver: staleness_of(self.old_page)
        )


def wait_for(condition_function):
    start_time = time.time()
    while time.time() < start_time + 10:
        if condition_function():
            return True
        else:
            time.sleep(0.1)
    raise TimeoutError("Timeout waiting for {}".format(condition_function.__name__))


def show_element(browser, element):
    s = """
        // console.log('enter---');
        window.scrollTo(0, 0);
        var viewPortHeight = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
        // console.log(viewPortHeight);
        var elementTop = arguments[0].getBoundingClientRect().top;
        // console.log(elementTop);
        if (elementTop < (viewPortHeight/2)*0.5 || elementTop > (viewPortHeight/2)*1.5 ) {
            // console.log("scrolling");
            window.scrollTo(0, Math.max(0, elementTop-(viewPortHeight/2)));
            // console.log(Math.max(0, elementTop-(viewPortHeight/2)));
        }
        """
    return browser.execute_script(s, element._element)


def select_select2_autocomplete(browser, element, value):
    element.click()
    time.sleep(0.1)
    active = element.parent.switch_to.active_element
    active.send_keys(value)
    time.sleep(0.1)
    element.parent.switch_to.active_element.send_keys(Keys.ENTER)
    time.sleep(0.2)
