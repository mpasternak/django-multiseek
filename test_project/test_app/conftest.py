# -*- encoding: utf-8 -*-
import json

import pytest
from django.conf import settings
from django.core.urlresolvers import reverse
from model_mommy import mommy
from selenium.webdriver.support.expected_conditions import staleness_of, \
    alert_is_present
from selenium.webdriver.support.ui import WebDriverWait
from splinter.exceptions import ElementDoesNotExist

from multiseek.logic import DATE, AUTOCOMPLETE, RANGE, STRING, VALUE_LIST, \
    get_registry
from .models import Language, Author, Book
import datetime
from builtins import str as text


class wait_for_page_load(object):
    def __init__(self, browser):
        self.browser = browser

    def __enter__(self):
        self.old_page = self.browser.find_by_tag('html')[0]._element

    def __exit__(self, *_):
        WebDriverWait(self.browser, 10).until(
            staleness_of(self.old_page)
        )


class SplinterLoginMixin:
    def login(self, username="admin", password="password"):
        url = self.browser.url
        with wait_for_page_load(self.browser):
            self.browser.visit(self.live_server_url + reverse("admin:login"))

        self.browser.fill('username', username)
        self.browser.fill('password', password)
        with wait_for_page_load(self.browser):
            self.browser.find_by_css("input[type=submit]").click()

        with wait_for_page_load(self.browser):
            self.browser.visit(url)


class MultiseekWebPage(SplinterLoginMixin):
    """Helper functions, that take care of the multiseek form web page
    """

    def __init__(self, registry, browser, live_server_url):
        self.browser = browser
        self.registry = registry
        self.live_server_url = live_server_url

    def get_frame(self, id):
        """Ta funkcja zwraca multiseekową "ramkę" po jej ID
        """
        frame = self.browser.find_by_id(id)
        ret = dict()
        ret['frame'] = frame[0]
        fieldset = frame.find_by_tag('fieldset')
        ret['add_field'] = fieldset.find_by_id("add_field")[0]
        ret['add_frame'] = fieldset.find_by_id("add_frame")[0]
        ret['fields'] = fieldset.find_by_id("field-list")[0]

        return ret

    def extract_field_data(self, element):
        """Ta funkcja zwraca słownik z wartościami dla danego pola w
        formularzu. Pole - czyli wiersz z kolejnymi selectami:

            pole przeszukiwane, operacja, wartość wyszukiwana,
            następna operacja, przycisk zamknięcia

        Z pomocniczych wartości, zwracanych w słowniku mamy 'type' czyli
        tekstowy typ, odpowiadający definicjom w bpp.multiseek.logic.fields.keys()

        Zwracana wartość słownika 'value' może być różna dla różnych typów
        pól (np dla multiseek.logic.RANGE jest to lista z wartościami z obu pól)
        """
        ret = {}

        for elem in ['type', 'op', 'prev-op', 'close-button']:
            try:
                e = element.find_by_id(elem)[0]
            except ElementDoesNotExist as x:
                # prev-op may be None
                if elem != 'prev-op':
                    raise x
                e = None

            ret[elem] = e

        selected = ret['type'].value
        ret['selected'] = selected

        inner_type = self.registry.field_by_name.get(selected).type
        ret['inner_type'] = inner_type

        if inner_type in [STRING, VALUE_LIST]:
            ret['value_widget'] = element.find_by_id("value")

        elif inner_type == RANGE:
            ret['value_widget'] = [
                element.find_by_id("value_min"),
                element.find_by_id("value_max")]

        elif inner_type == DATE:
            ret['value_widget'] = [
                element.find_by_id("value"),
                element.find_by_id("value_max")]

        elif inner_type == AUTOCOMPLETE:
            ret['value_widget'] = element.find_by_id("value")

        else:
            raise NotImplementedError(inner_type)

        code = '$("#%s").multiseekField("getValue")' % element['id']
        ret['value'] = self.browser.evaluate_script(code)

        if ret['inner_type'] in (DATE, AUTOCOMPLETE, RANGE):
            if ret['value']:
                ret['value'] = json.loads(ret['value'])
        return ret

    def get_field(self, id):
        field = self.browser.find_by_id(id)
        if len(field) != 1:
            raise Exception("field not found")
        return self.extract_field_data(field[0])

    def serialize(self):
        """Zwraca wartość funkcji serialize() dla formularza, w postaci
        listy -- czyli obiekt JSON"""
        return self.browser.evaluate_script(
            "$('#frame-0').multiseekFrame('serialize')")

    def get_field_value(self, field):
        return self.browser.evaluate_script(
            '$("#%s").multiseekField("getValue")' % field)

    def add_frame(self, frame="frame-0", prev_op=None):
        if not prev_op:
            return self.execute_script(
                """$("#%s").multiseekFrame('addFrame');""" % frame)

        return self.execute_script("""
            $("#%s").multiseekFrame('addFrame', '%s');
        """ % (frame, prev_op))

    def add_field(self, frame, label, op, value):
        code = """
        $("#%(frame)s").multiseekFrame("addField", "%(label)s", "%(op)s", %(value)s);
        """ % dict(frame=frame,
                   label=text(label),
                   op=text(op),
                   value=json.dumps(value))

        self.browser.execute_script(code)

    def load_form_by_name(self, name):
        with wait_for_page_load(self.browser):
            self.browser.reload()
        select = self.browser.find_by_id("formsSelector")
        for elem in select.find_by_tag('option'):
            if elem.text == name:
                elem.click()
                break
        WebDriverWait(self.browser, 10).until(alert_is_present())
        self.accept_alert()
        WebDriverWait(self.browser, 10).until_not(alert_is_present())
        self.browser.reload()

    def reset_form(self):
        self.browser.find_by_id("resetFormButton").click()

    def click_save_button(self):
        button = self.browser.find_by_id("saveFormButton").first
        button.click()  # type("\n")  # Keys.ENTER)

    def save_form_as(self, name):
        self.click_save_button()
        WebDriverWait(self.browser, 10).until(alert_is_present())
        with self.browser.get_alert() as alert:
            alert.fill_with(name)
            alert.accept()
        WebDriverWait(self.browser, 10).until_not(alert_is_present())

    def count_elements_in_form_selector(self, name):
        select = self.browser.find_by_id("formsSelector")
        assert select.visible == True
        passed = 0
        for option in select.find_by_tag("option"):
            if option.text == name:
                passed += 1
        return passed

    def accept_alert(self):
        with self.browser.get_alert() as alert:
            alert.accept()

    def dismiss_alert(self):
        with self.browser.get_alert() as alert:
            alert.dismiss()


@pytest.fixture
def multiseek_page(browser, live_server, initial_data):
    browser.visit(live_server + reverse('multiseek:index'))
    registry = get_registry(settings.MULTISEEK_REGISTRY)
    page = MultiseekWebPage(browser=browser, registry=registry,
                            live_server_url=live_server.url)
    yield page
    page.browser.quit()

@pytest.fixture
def multiseek_admin_page(multiseek_page, admin_user):
    while "log in, then come back" in multiseek_page.browser.html:
        multiseek_page.login(admin_user.username, "password")
    return multiseek_page


@pytest.fixture(scope='session')
def splinter_firefox_profile_preferences():
    return {
        "browser.startup.homepage": "about:blank",
        "startup.homepage_welcome_url": "about:blank",
        "startup.homepage_welcome_url.additional": "about:blank"
    }


@pytest.fixture
def initial_data():
    eng = mommy.make(Language, name="english", description="English language")
    mommy.make(Language, name="polish", description="Polish language")
    a1 = mommy.make(Author, last_name="Smith", first_name="John")
    a2 = mommy.make(Author, last_name="Kovalsky", first_name="Ian")
    b1 = mommy.make(Book, title="A book with a title", year=2013, language=eng,
                    no_editors=5, last_updated=datetime.date(2013, 10, 22),
                    available=True)
    b2 = mommy.make(Book, title="Second book", year=2000, language=eng,
                    no_editors=5, last_updated=datetime.date(2013, 9, 22),
                    available=False)

    b1.authors.add(a1)
    b2.authors.add(a2)

    # Some more books by author 3 so we can test pagination...

    a3 = mommy.make(Author, last_name="Novak", first_name="Stephan")
    fr = mommy.make(Language, name="french", description="French language")
    for a in range(0, 50):
        b3 = mommy.make(Book, title="Book no %i" % a, year=1999, language=fr)
        b3.authors.add(a3)
                   
