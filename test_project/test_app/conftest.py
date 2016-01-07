# -*- encoding: utf-8 -*-
import json

import pytest
from django.core.urlresolvers import reverse
from selenium.webdriver.support.select import Select
from django.conf import settings
from splinter.exceptions import ElementDoesNotExist

from multiseek.logic import DATE, AUTOCOMPLETE, RANGE, STRING, VALUE_LIST, get_registry


class MultiseekWebPage:
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
        ret['frame'] = frame
        ret['add_field'] = frame.children('fieldset')[0].children(
                "button#add_field")[0]
        ret['add_frame'] = frame.children('fieldset')[0].children(
                "button#add_frame")[0]
        ret['fields'] = frame.children('fieldset')[0].children(
                "div#field-list")[0].children()
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
            except ElementDoesNotExist, x:
                # prev-op may be None
                if elem != 'prev-op':
                    raise x
                e = None

            ret[elem] = e

        selected = Select(ret['type']).first_selected_option
        ret['selected'] = selected.text()

        inner_type = self.registry.field_by_name.get(selected.text()).type
        ret['inner_type'] = inner_type

        if inner_type in [STRING, VALUE_LIST]:
            ret['value_widget'] = element.find_element_by_id("value")

        elif inner_type == RANGE:
            ret['value_widget'] = [
                element.find_element_by_id("value_min"),
                element.find_element_by_id("value_max")]

        elif inner_type == DATE:
            ret['value_widget'] = [
                element.find_element_by_id("value"),
                element.find_element_by_id("value_max")]

        elif inner_type == AUTOCOMPLETE:
            ret['value_widget'] = element.find_element_by_id("value")

        else:
            raise NotImplementedError(inner_type)

        ret['value'] = self.browser.execute_script("""
            return $(arguments[0]).multiseekField('getValue');""", element)

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
        return self.execute_script(
                '''return $('#frame-0').multiseekFrame('serialize');''')

    def get_field_value(self, field):
        return self.execute_script("""
        return $("#%s").multiseekField("getValue");
        """ % field)

    def add_frame(self, frame="frame-0", prev_op=None):
        if not prev_op:
            return self.execute_script(
                    """$("#%s").multiseekFrame('addFrame');""" % frame)

        return self.execute_script("""
            $("#%s").multiseekFrame('addFrame', '%s');
        """ % (frame, prev_op))

    def add_field(self, frame, label, op, value):
        self.execute_script("""

        $("#%(frame)s").multiseekFrame("addField", "%(label)s", "%(op)s", %(value)s);
        """ % dict(frame=frame,
                   label=unicode(label),
                   op=unicode(op),
                   value=json.dumps(value)))

    def load_form_by_name(self, name):
        self.refresh()
        select = Select(self.find_element_by_jquery("#formsSelector"))
        select.select_by_visible_text(name)
        self.switch_to_alert().accept()
        self.refresh()

    def reset_form(self):
        self.find_element_by_id("resetFormButton").click()

@pytest.fixture
def multiseek_page(browser, live_server):
    browser.visit(live_server + reverse('multiseek:index'))
    registry = get_registry(settings.MULTISEEK_REGISTRY)
    return MultiseekWebPage(browser=browser, registry=registry, live_server=live_server)

@pytest.fixture
def multiseek_admin_page(browser, live_server):
    # XXX zaloguj browser jako administratora

    browser.visit(live_server + reverse('multiseek:index'))
    registry = get_registry(settings.MULTISEEK_REGISTRY)
    return MultiseekWebPage(browser=browser, registry=registry, live_server=live_server)
