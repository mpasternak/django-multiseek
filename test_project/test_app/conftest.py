# -*- encoding: utf-8 -*-
import json

import pytest
from django.conf import settings
from django.core.urlresolvers import reverse
from selenium.webdriver.support.select import Select
from splinter.exceptions import ElementDoesNotExist

from multiseek.logic import DATE, AUTOCOMPLETE, RANGE, STRING, VALUE_LIST, get_registry


class SplinterLoginMixin:
    def login(self, username="admin", password="password"):
        url = self.browser.url
        self.browser.visit(self.live_server + reverse("admin:login"))
        self.browser.fill('username', username)
        self.browser.fill('password', password)
        self.browser.find_by_css("input[type=submit]").click()
        self.browser.visit(url)


class MultiseekWebPage(SplinterLoginMixin):
    """Helper functions, that take care of the multiseek form web page
    """

    def __init__(self, registry, browser, live_server):
        self.browser = browser
        self.registry = registry
        self.live_server = live_server

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
        return self.browser.evaluate_script("$('#frame-0').multiseekFrame('serialize')")

    def get_field_value(self, field):
        return self.browser.evaluate_script('$("#%s").multiseekField("getValue")' % field)

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
                   label=unicode(label),
                   op=unicode(op),
                   value=json.dumps(value))

        self.browser.execute_script(code)

    def load_form_by_name(self, name):
        self.browser.reload()
        select = self.browser.find_by_id("formsSelector")
        for elem in select.find_by_tag('option'):
            if elem.text == name:
                elem.click()
                break
        self.accept_alert()
        self.browser.reload()

    def reset_form(self):
        self.browser.find_by_id("resetFormButton").click()

    def click_save_button(self):
        button = self.browser.find_by_id("saveFormButton").first
        button.type("\n")  # Keys.ENTER)

    def save_form_as(self, name):
        self.click_save_button()
        with self.browser.get_alert() as alert:
            alert.fill_with(name)
            alert.accept()

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
def multiseek_page(browser, live_server):
    browser.visit(live_server + reverse('multiseek:index'))
    registry = get_registry(settings.MULTISEEK_REGISTRY)
    return MultiseekWebPage(browser=browser, registry=registry, live_server=live_server)


@pytest.fixture
def multiseek_admin_page(multiseek_page, admin_user):
    multiseek_page.login("admin", "password")
    return multiseek_page


@pytest.fixture(scope='session')
def splinter_firefox_profile_preferences():
    return {
        "browser.startup.homepage": "about:blank",
        "startup.homepage_welcome_url": "about:blank",
        "startup.homepage_welcome_url.additional": "about:blank"
    }
