# -*- encoding: utf-8 -*-
from __future__ import print_function

import json
import time
from builtins import str as text

import pytest
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from model_bakery import baker
from multiseek import logic
from multiseek.logic import (
    AND,
    CONTAINS,
    EQUAL,
    MULTISEEK_ORDERING_PREFIX,
    MULTISEEK_REPORT_TYPE,
    OR,
    RANGE_OPS,
)
from multiseek.models import SearchForm
from multiseek.util import make_field
from multiseek.views import LAST_FIELD_REMOVE_MESSAGE
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import alert_is_present
from selenium.webdriver.support.wait import WebDriverWait

from . import multiseek_registry
from .models import Author, Language
from .testutil import select_select2_autocomplete, wait_for_page_load


class wait_for_alert(object):
    method_name = "until"

    def __init__(self, browser):
        self.browser = browser

    def __enter__(self):
        pass

    def __exit__(self, *_):
        wait = WebDriverWait(self.browser, 10)
        method = getattr(wait, self.method_name)
        method(alert_is_present())


class wait_until_no_alert(wait_for_alert):
    method_name = "until_not"


FRAME = "frame-0"
FIELD = "field-0"


@pytest.mark.django_db
def test_client_picks_up_database_changes_direct(initial_data, client):
    res = client.get("/multiseek/")
    assert "english" in res.content.decode(res.charset)

    n = Language.objects.all()[0]
    n.name = "FOOBAR"
    n.save()

    res = client.get("/multiseek/")
    assert "FOOBAR" in res.content.decode(res.charset)


@pytest.mark.django_db
def test_liveserver_picks_up_database_changes(multiseek_page):
    n = Language.objects.all()[0]
    n.name = "FOOBAR"
    n.save()
    with wait_for_page_load(multiseek_page.browser):
        multiseek_page.browser.reload()
    assert "FOOBAR" in multiseek_page.browser.html


@pytest.mark.django_db
def test_multiseek(multiseek_page):
    field = multiseek_page.get_field(FIELD)
    # On init, the first field will be selected
    assert field["selected"] == multiseek_page.registry.fields[0].label


@pytest.mark.django_db
def test_liveserver_picks_up_database_changes_direct(
    initial_data, browser, live_server
):
    with wait_for_page_load(browser):
        browser.visit(live_server.url)
    assert "english" in browser.html

    n = Language.objects.all()[0]
    n.name = "FOOBAR"
    n.save()

    with wait_for_page_load(browser):
        browser.reload()

    assert "FOOBAR" in browser.html


@pytest.mark.django_db
def test_change_field(multiseek_page):
    field = multiseek_page.get_field(FIELD)
    field["type"].find_by_value(text(multiseek_registry.YearQueryObject.label)).click()

    field = multiseek_page.get_field(FIELD)
    assert field["inner_type"] == logic.RANGE
    assert len(field["value"]) == 2

    field["type"].find_by_value(
        text(multiseek_registry.LanguageQueryObject.label)
    ).click()

    field = multiseek_page.get_field(FIELD)
    assert field["inner_type"] == logic.VALUE_LIST

    field["type"].find_by_value(
        text(multiseek_registry.AuthorQueryObject.label)
    ).click()

    field = multiseek_page.get_field(FIELD)
    assert field["inner_type"] == logic.AUTOCOMPLETE


@pytest.mark.django_db
def test_serialize_form(multiseek_page):
    with wait_for_page_load(multiseek_page.browser):
        multiseek_page.browser.reload()

    frame = multiseek_page.get_frame("frame-0")
    frame["add_field"].click()
    frame["add_field"].click()
    frame["add_field"].click()

    frame["add_frame"].click()
    frame["add_frame"].click()

    for n in range(2, 5):
        field = multiseek_page.get_field("field-%i" % n)
        field["value_widget"].type("aaapud!")

    field = multiseek_page.get_field("field-0")
    field["type"].find_by_value(text(multiseek_registry.YearQueryObject.label)).click()

    field = multiseek_page.get_field("field-0")
    field["value_widget"][0].type("1999")
    field["value_widget"][1].type("2000")

    field = multiseek_page.get_field("field-1")
    field["prev-op"].find_by_value("or").click()
    field["type"].find_by_value(
        text(multiseek_registry.LanguageQueryObject.label)
    ).click()

    field = multiseek_page.get_field("field-1")
    field["value_widget"].find_by_value(text(_(u"english"))).click()

    expected = [
        None,
        {
            u"field": u"Year",
            u"operator": text(RANGE_OPS[0]),
            u"value": u"[1999,2000]",
            u"prev_op": None,
        },
        {
            u"field": u"Language",
            u"operator": text(EQUAL),
            u"value": u"english",
            u"prev_op": OR,
        },
        {
            u"field": u"Title",
            u"operator": text(CONTAINS),
            u"value": u"aaapud!",
            u"prev_op": AND,
        },
        {
            u"field": u"Title",
            u"operator": text(CONTAINS),
            u"value": u"aaapud!",
            u"prev_op": AND,
        },
        [
            AND,
            {
                u"field": u"Title",
                u"operator": text(CONTAINS),
                u"value": u"aaapud!",
                u"prev_op": None,
            },
        ],
        [
            AND,
            {
                u"field": u"Title",
                u"operator": text(CONTAINS),
                u"value": u"",
                u"prev_op": None,
            },
        ],
    ]

    serialized = multiseek_page.serialize()
    assert serialized == expected

    for n in range(1, 6):
        field = multiseek_page.get_field("field-%i" % n)
        field["close-button"].click()
    time.sleep(2)

    expected = [
        None,
        {
            u"field": u"Year",
            u"operator": u"in range",
            u"value": u"[1999,2000]",
            u"prev_op": None,
        },
    ]
    serialized = multiseek_page.serialize()

    assert serialized == expected


@pytest.mark.django_db
def test_remove_last_field(multiseek_page):
    assert Language.objects.count()

    field = multiseek_page.get_field("field-0")
    field["close-button"].click()

    alert = multiseek_page.browser.get_alert()
    alert.text == LAST_FIELD_REMOVE_MESSAGE
    alert.accept()


@pytest.mark.django_db
def test_autocomplete_field(multiseek_page):
    assert Language.objects.count()

    field = multiseek_page.get_field(FIELD)
    field["type"].find_by_value(
        text(multiseek_registry.AuthorQueryObject.label)
    ).click()

    element = multiseek_page.browser.find_by_css(".select2-container")
    select_select2_autocomplete(multiseek_page.browser, element, "Smith")

    got = multiseek_page.serialize()
    expect = [
        None,
        make_field(
            multiseek_registry.AuthorQueryObject,
            text(EQUAL),
            str(Author.objects.filter(last_name="Smith")[0].pk),
            prev_op=None,
        ),
    ]

    assert got == expect


@pytest.mark.django_db
def test_autocomplete_field_bug(multiseek_page):
    """We fill autocomplete field with NOTHING, then we submit the form,
    then we reload the homepage, and by the time of writing, we see
    HTTP error 500, which is not what we need..."""

    field = multiseek_page.get_field(FIELD)
    field["type"].find_by_value(
        text(multiseek_registry.AuthorQueryObject.label)
    ).click()

    multiseek_page.browser.find_by_id("sendQueryButton").click()
    time.sleep(1)
    with wait_for_page_load(multiseek_page.browser):
        multiseek_page.browser.reload()
    assert "Server Error (500)" not in multiseek_page.browser.html


@pytest.mark.django_db
def test_autocomplete_field_bug_2(multiseek_page):
    """We fill autocomplete field with NOTHING, then we submit the form,
    then we reload the homepage, click the "add field button" and by the
    time of writing, we get a javascript error."""

    field = multiseek_page.get_field(FIELD)
    field["type"].find_by_value(
        text(multiseek_registry.AuthorQueryObject.label)
    ).click()

    multiseek_page.browser.find_by_id("sendQueryButton").click()
    time.sleep(1)
    with wait_for_page_load(multiseek_page.browser):
        multiseek_page.browser.reload()

    multiseek_page.browser.find_by_id("add_field").click()
    time.sleep(1)

    selects = [
        tag
        for tag in multiseek_page.browser.find_by_tag("select")
        if tag["id"] == "type"
    ]
    assert len(selects[0].find_by_tag("option")) != 0
    assert len(selects[1].find_by_tag("option")) != 0


@pytest.mark.django_db
def test_set_join(multiseek_page):
    multiseek_page.browser.find_by_id("add_field").click()
    multiseek_page.browser.execute_script(
        "$('#field-1').multiseekField('prevOperation').val('or')"
    )

    ret = multiseek_page.browser.evaluate_script(
        "$('#field-1').multiseekField('prevOperation').val()"
    )

    assert ret == "or"

    multiseek_page.add_field(
        FRAME,
        text(multiseek_page.registry.fields[0].label),
        text(multiseek_page.registry.fields[0].ops[0]),
        "",
    )

    multiseek_page.browser.execute_script(
        "$('#field-2').multiseekField('prevOperation').val('or')"
    )

    ret = multiseek_page.browser.evaluate_script(
        "$('#field-2').multiseekField('prevOperation').val()"
    )

    assert ret == "or"


@pytest.mark.django_db
def test_set_frame_join(multiseek_page):
    multiseek_page.browser.execute_script(
        """
    $("#frame-0").multiseekFrame('addFrame');
    $("#frame-0").multiseekFrame('addFrame', 'or');
    """
    )

    ret = multiseek_page.browser.evaluate_script(
        "$('#frame-2').multiseekFrame('getPrevOperationValue')"
    )

    assert ret == "or"


@pytest.mark.django_db
def test_add_field_value_list(multiseek_page):
    multiseek_page.add_field(
        FRAME,
        multiseek_registry.LanguageQueryObject.label,
        multiseek_registry.LanguageQueryObject.ops[1],
        text(_(u"polish")),
    )

    field = multiseek_page.get_field("field-1")
    assert field["type"].value == text(multiseek_registry.LanguageQueryObject.label)
    assert field["op"].value == text(multiseek_registry.LanguageQueryObject.ops[1])
    assert field["value"] == text(_(u"polish"))


@pytest.mark.django_db
def test_add_field_autocomplete(multiseek_page):
    multiseek_page.add_field(
        FRAME,
        multiseek_registry.AuthorQueryObject.label,
        multiseek_registry.AuthorQueryObject.ops[1],
        '[1,"John Smith"]',
    )

    value = multiseek_page.get_field_value("field-1")
    assert value == "1"


@pytest.mark.django_db
def test_add_field_string(multiseek_page):
    multiseek_page.add_field(
        FRAME,
        multiseek_registry.TitleQueryObject.label,
        multiseek_registry.TitleQueryObject.ops[0],
        "aaapud!",
    )

    field = multiseek_page.get_field_value("field-1")
    assert field == "aaapud!"


@pytest.mark.django_db
def test_add_field_range(multiseek_page):
    multiseek_page.add_field(
        FRAME,
        multiseek_registry.YearQueryObject.label,
        multiseek_registry.YearQueryObject.ops[0],
        "[1000, 2000]",
    )

    field = multiseek_page.get_field_value("field-1")
    assert field == "[1000,2000]"


@pytest.mark.django_db
def test_refresh_bug(multiseek_page):
    # There was a bug, that when you submit the form with "OR" operation,
    # and then you refresh the page, the operation is changed to "AND"

    frame = multiseek_page.get_frame("frame-0")
    frame["add_field"].click()

    field = multiseek_page.get_field("field-1")
    field["prev-op"].find_by_value(text(_("or"))).click()
    assert field["prev-op"].value == text(_("or"))

    button = multiseek_page.browser.find_by_id("sendQueryButton")
    button.click()

    time.sleep(0.5)

    multiseek_page.browser.reload()

    field = multiseek_page.get_field("field-1")
    assert field["prev-op"].value == text(_("or"))


@pytest.mark.django_db
def test_frame_bug(multiseek_page):
    multiseek_page.browser.find_by_id("add_frame").click()
    multiseek_page.browser.find_by_id("close-button").click()
    multiseek_page.browser.find_by_id("sendQueryButton").click()

    with multiseek_page.browser.get_iframe("if") as iframe:
        assert "Server Error (500)" not in iframe.html


@pytest.mark.django_db
def test_date_field(multiseek_page):
    field = multiseek_page.get_field("field-0")

    field["type"].find_by_value(
        text(multiseek_registry.DateLastUpdatedQueryObject.label)
    ).click()
    field["op"].find_by_value(
        text(multiseek_registry.DateLastUpdatedQueryObject.ops[6])
    ).click()

    expected = [
        None,
        {
            u"field": u"Last updated on",
            u"operator": u"in range",
            u"value": u'["",""]',
            u"prev_op": None,
        },
    ]
    assert multiseek_page.serialize() == expected

    field["op"].find_by_value(
        text(multiseek_registry.DateLastUpdatedQueryObject.ops[3])
    ).click()
    expected = [
        None,
        {
            u"field": u"Last updated on",
            u"operator": u"greater or equal to(female gender)",
            u"value": u'[""]',
            u"prev_op": None,
        },
    ]
    assert expected == multiseek_page.serialize()


@pytest.mark.django_db
def test_removed_records(multiseek_page, live_server, initial_data):
    """Try to remove a record by hand and check if that fact is properly
    recorded."""

    multiseek_page.browser.visit(live_server + "/multiseek/results")
    assert "A book with" in multiseek_page.browser.html
    assert "Second book" in multiseek_page.browser.html
    multiseek_page.browser.execute_script("""$("a:contains('❌')").first().click()""")
    time.sleep(1)

    multiseek_page.browser.visit(live_server + "/multiseek/results")
    assert "A book with" in multiseek_page.browser.html
    assert "Second book" not in multiseek_page.browser.html
    assert "1 record(s) has been removed manually" in multiseek_page.browser.html

    multiseek_page.browser.execute_script("""$("a:contains('❌')").first().click()""")
    time.sleep(1)
    multiseek_page.browser.execute_script("""$("a:contains('❌')").first().click()""")
    time.sleep(1)
    multiseek_page.browser.visit(live_server + "/multiseek/results")
    assert "A book with" in multiseek_page.browser.html
    assert "Second book" not in multiseek_page.browser.html
    assert "1 record(s) has been removed manually" in multiseek_page.browser.html


@pytest.mark.django_db
def test_form_save_anon_initial(multiseek_page):
    # Without SearchForm objects, the formsSelector is invisible
    elem = multiseek_page.browser.find_by_id("formsSelector")
    assert not elem.visible


@pytest.mark.django_db
def test_form_save_anon_initial_with_data(multiseek_page):
    baker.make(SearchForm, public=True)
    multiseek_page.browser.reload()
    elem = multiseek_page.browser.find_by_id("formsSelector")
    assert elem.visible


@pytest.mark.django_db
def test_form_save_anon_form_save_anonymous(multiseek_page):
    # Anonymous users cannot save forms:
    assert len(multiseek_page.browser.find_by_id("saveFormButton")) == 0


@pytest.mark.django_db
def test_form_save_anon_bug(multiseek_page):
    multiseek_page.browser.find_by_id("add_frame").click()
    multiseek_page.browser.find_by_id("add_field").click()
    field1 = multiseek_page.get_field("field-1")
    field1["close-button"].click()
    time.sleep(1)
    selects = multiseek_page.browser.find_by_tag("select")
    prevops = [x for x in selects if x["id"] == "prev-op"]
    assert len(prevops) == 1


@pytest.mark.django_db
def test_public_report_types_secret_report_invisible(multiseek_page):
    elem = multiseek_page.browser.find_by_name("_ms_report_type").find_by_tag("option")
    assert len(elem) == 2


@pytest.mark.django_db
def test_logged_in_secret_report_visible(
    multiseek_admin_page, admin_user, initial_data
):
    elem = multiseek_admin_page.browser.find_by_name("_ms_report_type")
    elem = elem.first.find_by_tag("option")
    assert len(elem) == 3


@pytest.mark.django_db
def test_save_form_logged_in(multiseek_admin_page, initial_data):
    assert multiseek_admin_page.browser.find_by_id("saveFormButton").visible


@pytest.mark.django_db
def test_save_form_server_error(multiseek_admin_page, initial_data):
    NAME = "testowy formularz"
    multiseek_admin_page.browser.execute_script(
        "multiseek.SAVE_FORM_URL='/unexistent';"
    )
    browser = multiseek_admin_page.browser

    # Zapiszmy formularz
    multiseek_admin_page.save_form_as(NAME)

    # ... pytanie, czy ma być publiczny:
    WebDriverWait(browser, 10).until(alert_is_present())
    multiseek_admin_page.browser.get_alert().accept()
    time.sleep(1)

    # ... po chwili informacja, że BŁĄD!
    WebDriverWait(browser, 10).until(alert_is_present())
    multiseek_admin_page.browser.get_alert().accept()
    WebDriverWait(browser, 10).until_not(alert_is_present())

    # ... i selector się NIE pojawia:
    assert not multiseek_admin_page.browser.find_by_id("formsSelector").visible
    # ... i w bazie też PUSTKA:
    assert SearchForm.objects.all().count() == 0


@pytest.mark.django_db
def test_save_form_save(multiseek_admin_page, initial_data):
    browser = multiseek_admin_page.browser

    assert SearchForm.objects.all().count() == 0

    # multiseek_admin_page.browser.reload()
    with wait_for_alert(browser):
        multiseek_admin_page.click_save_button()
    with wait_until_no_alert(browser):
        multiseek_admin_page.dismiss_alert()
    # Anulowanie nie powinno wyświetlić następnego formularza

    NAME = "testowy formularz"

    # Zapiszmy formularz
    multiseek_admin_page.save_form_as(NAME)
    # ... pytanie, czy ma być publiczny:
    WebDriverWait(browser, 10).until(alert_is_present())
    with wait_until_no_alert(browser):
        multiseek_admin_page.accept_alert()

    # ... po chwili informacja, że zapisano
    WebDriverWait(browser, 10).until(alert_is_present())
    with wait_until_no_alert(browser):
        multiseek_admin_page.accept_alert()

    # ... i nazwa pojawia się w selectorze
    assert multiseek_admin_page.count_elements_in_form_selector(NAME) == 1
    # ... i w bazie:
    assert SearchForm.objects.all().count() == 1

    # Zapiszmy formularz pod TĄ SAMĄ NAZWĄ
    multiseek_admin_page.save_form_as(NAME)

    # ... pytanie, czy ma być publiczny:
    WebDriverWait(browser, 10).until(alert_is_present())
    with wait_until_no_alert(browser):
        multiseek_admin_page.accept_alert()

    # ... po chwili informacja, że jest już taki w bazie i czy nadpisać?
    WebDriverWait(browser, 10).until(alert_is_present())
    with wait_until_no_alert(browser):
        multiseek_admin_page.accept_alert()
    # ... po chwili informacja, że zapisano:
    WebDriverWait(browser, 10).until(alert_is_present())
    with wait_until_no_alert(browser):
        multiseek_admin_page.accept_alert()

    # ... i nazwa pojawia się w selectorze
    assert multiseek_admin_page.count_elements_in_form_selector(NAME) == 1
    # ... i w bazie jest nadal jeden
    assert SearchForm.objects.all().count() == 1

    # Zapiszmy formularz pod TĄ SAMĄ NAZWĄ ale już NIE nadpisujemy
    multiseek_admin_page.save_form_as(NAME)

    # ... pytanie, czy ma być publiczny:
    WebDriverWait(browser, 10).until(alert_is_present())
    with wait_until_no_alert(browser):
        multiseek_admin_page.accept_alert()

    # ... po chwili informacja, że jest już taki w bazie i czy nadpisać?
    WebDriverWait(browser, 10).until(alert_is_present())
    with wait_until_no_alert(browser):
        multiseek_admin_page.accept_alert()

    # ... po chwili informacja, że ZAPISANY
    WebDriverWait(browser, 10).until(alert_is_present())
    with wait_until_no_alert(browser):
        multiseek_admin_page.accept_alert()

    # ... i w bazie jest nadal jeden
    assert SearchForm.objects.all().count() == 1
    # Sprawdźmy, czy jest publiczny
    assert SearchForm.objects.all()[0].public

    # Nadpiszmy formularz jako nie-publiczny
    multiseek_admin_page.save_form_as(NAME)

    # ... pytanie, czy ma być publiczny:
    WebDriverWait(browser, 10).until(alert_is_present())
    with wait_until_no_alert(browser):
        multiseek_admin_page.dismiss_alert()

    # ... po chwili informacja, że jest już taki w bazie i czy nadpisać?
    WebDriverWait(browser, 10).until(alert_is_present())
    with wait_until_no_alert(browser):
        multiseek_admin_page.accept_alert()

    # ... po chwili informacja, że zapisano:
    WebDriverWait(browser, 10).until(alert_is_present())
    with wait_until_no_alert(browser):
        multiseek_admin_page.accept_alert()
    # ... i jest to już NIE-publiczny:
    assert not SearchForm.objects.all()[0].public


@pytest.mark.django_db
def test_load_form(multiseek_admin_page, initial_data):
    fld = make_field(
        multiseek_admin_page.registry.fields[2],
        multiseek_admin_page.registry.fields[2].ops[1],
        json.dumps([2000, 2010]),
    )
    SearchForm.objects.create(
        name="lol",
        owner=User.objects.create(username="foo", password="bar"),
        public=True,
        data=json.dumps({"form_data": [None, fld]}),
    )
    multiseek_admin_page.load_form_by_name("lol")

    field = multiseek_admin_page.extract_field_data(
        multiseek_admin_page.browser.find_by_id("field-0")
    )

    assert field["selected"] == text(multiseek_admin_page.registry.fields[2].label)
    assert field["value"][0] == 2000
    assert field["value"][1] == 2010

    # Przetestuj, czy po ANULOWANIU select wróci do pierwotnej wartości
    elem = multiseek_admin_page.browser.find_by_id("formsSelector").first
    elem.find_by_text("lol").click()
    multiseek_admin_page.dismiss_alert()

    elem = multiseek_admin_page.browser.find_by_id("formsSelector").find_by_tag(
        "option"
    )
    assert elem[0].selected


@pytest.mark.django_db
def test_bug_2(multiseek_admin_page, initial_data):
    f = multiseek_admin_page.registry.fields[0]
    v = multiseek_admin_page.registry.fields[0].ops[0]
    value = "foo"

    field = make_field(f, v, value, OR)

    form = [None, field, [OR, field, field, field], [OR, field, field, field]]

    data = json.dumps({"form_data": form})

    user = User.objects.create(username="foo", password="bar")

    SearchForm.objects.create(name="bug-2", owner=user, public=True, data=data)
    multiseek_admin_page.load_form_by_name("bug-2")
    elements = multiseek_admin_page.browser.find_by_css("[name=prev-op]")
    for elem in elements:
        if elem.css("visibility") != "hidden":
            assert elem.value == logic.OR


@pytest.mark.django_db
def test_save_ordering_direction(multiseek_admin_page, initial_data):
    elem = "input[name=%s1_dir]" % MULTISEEK_ORDERING_PREFIX
    browser = multiseek_admin_page.browser

    browser.find_by_css(elem).type(Keys.SPACE)
    multiseek_admin_page.save_form_as("foobar")
    # Should the dialog be public?
    WebDriverWait(browser, 10).until(alert_is_present())
    multiseek_admin_page.accept_alert()
    WebDriverWait(browser, 10).until_not(alert_is_present())

    # Form saved success
    WebDriverWait(browser, 10).until(alert_is_present())
    multiseek_admin_page.accept_alert()
    WebDriverWait(browser, 10).until_not(alert_is_present())

    multiseek_admin_page.reset_form()
    multiseek_admin_page.load_form_by_name("foobar")
    assert len(multiseek_admin_page.browser.find_by_css("%s:checked" % elem)) == 1


@pytest.mark.django_db
def test_save_ordering_box(multiseek_admin_page, initial_data):
    elem = "select[name=%s0]" % MULTISEEK_ORDERING_PREFIX
    browser = multiseek_admin_page.browser
    select = browser.find_by_css(elem)
    option = select.find_by_css('option[value="2"]')
    assert not option.selected

    option.click()
    multiseek_admin_page.save_form_as("foobar")
    WebDriverWait(browser, 10).until(alert_is_present())
    multiseek_admin_page.accept_alert()
    WebDriverWait(browser, 10).until_not(alert_is_present())

    WebDriverWait(browser, 10).until(alert_is_present())
    multiseek_admin_page.accept_alert()
    WebDriverWait(browser, 10).until_not(alert_is_present())

    multiseek_admin_page.reset_form()
    multiseek_admin_page.load_form_by_name("foobar")

    select = multiseek_admin_page.browser.find_by_css(elem)
    option = select.find_by_css('option[value="2"]')
    assert option.selected


@pytest.mark.django_db
def test_save_report_type(multiseek_admin_page, initial_data):
    elem = "select[name=%s]" % MULTISEEK_REPORT_TYPE
    select = multiseek_admin_page.browser.find_by_css(elem).first
    option = select.find_by_css('option[value="1"]')
    assert not option.selected

    option.click()
    multiseek_admin_page.save_form_as("foobar")
    browser = multiseek_admin_page.browser
    WebDriverWait(browser, 10).until(alert_is_present())
    multiseek_admin_page.accept_alert()
    WebDriverWait(browser, 10).until_not(alert_is_present())
    WebDriverWait(browser, 10).until(alert_is_present())
    multiseek_admin_page.accept_alert()
    WebDriverWait(browser, 10).until_not(alert_is_present())
    multiseek_admin_page.reset_form()
    time.sleep(1)
    multiseek_admin_page.load_form_by_name("foobar")

    select = multiseek_admin_page.browser.find_by_css(elem).first
    option = select.find_by_css('option[value="1"]')
    assert option.selected
