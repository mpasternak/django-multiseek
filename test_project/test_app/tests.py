import json

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

from . import multiseek_registry
from .models import Author, Language
from .testutil import select_select2_autocomplete, SequentialDialogHandler


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
    multiseek_page.page.reload()
    multiseek_page.page.wait_for_load_state("networkidle")
    assert "FOOBAR" in multiseek_page.page.content()


@pytest.mark.django_db
def test_multiseek(multiseek_page):
    field = multiseek_page.get_field(FIELD)
    assert field["selected"] == multiseek_page.registry.fields[0].label


@pytest.mark.django_db
def test_liveserver_picks_up_database_changes_direct(
    initial_data, page, live_server
):
    page.goto(live_server.url)
    assert "english" in page.content()

    n = Language.objects.all()[0]
    n.name = "FOOBAR"
    n.save()

    page.reload()
    page.wait_for_load_state("networkidle")
    assert "FOOBAR" in page.content()


@pytest.mark.django_db
def test_change_field(multiseek_page):
    field = multiseek_page.get_field(FIELD)
    field["type"].select_option(
        value=str(multiseek_registry.YearQueryObject.label)
    )

    field = multiseek_page.get_field(FIELD)
    assert field["inner_type"] == logic.RANGE
    assert len(field["value"]) == 2

    field["type"].select_option(
        value=str(multiseek_registry.LanguageQueryObject.label)
    )

    field = multiseek_page.get_field(FIELD)
    assert field["inner_type"] == logic.VALUE_LIST

    field["type"].select_option(
        value=str(multiseek_registry.AuthorQueryObject.label)
    )

    field = multiseek_page.get_field(FIELD)
    assert field["inner_type"] == logic.AUTOCOMPLETE


@pytest.mark.django_db
def test_serialize_form(multiseek_page):
    multiseek_page.page.reload()
    multiseek_page.page.wait_for_load_state("networkidle")

    frame = multiseek_page.get_frame("frame-0")
    frame["add_field"].click()
    frame["add_field"].click()
    frame["add_field"].click()

    frame["add_frame"].click()
    frame["add_frame"].click()

    for n in range(2, 5):
        field = multiseek_page.get_field("field-%i" % n)
        field["value_widget"].fill("aaapud!")

    field = multiseek_page.get_field("field-0")
    field["type"].select_option(
        value=str(multiseek_registry.YearQueryObject.label)
    )

    field = multiseek_page.get_field("field-0")
    field["value_widget"][0].fill("1999")
    field["value_widget"][1].fill("2000")

    field = multiseek_page.get_field("field-1")
    field["prev-op"].select_option(value="or")
    field["type"].select_option(
        value=str(multiseek_registry.LanguageQueryObject.label)
    )

    field = multiseek_page.get_field("field-1")
    field["value_widget"].select_option(value=str(_("english")))

    expected = [
        None,
        {
            "field": "Year",
            "operator": str(RANGE_OPS[0]),
            "value": "[1999,2000]",
            "prev_op": None,
        },
        {
            "field": "Language",
            "operator": str(EQUAL),
            "value": "english",
            "prev_op": OR,
        },
        {
            "field": "Title",
            "operator": str(CONTAINS),
            "value": "aaapud!",
            "prev_op": AND,
        },
        {
            "field": "Title",
            "operator": str(CONTAINS),
            "value": "aaapud!",
            "prev_op": AND,
        },
        [
            AND,
            {
                "field": "Title",
                "operator": str(CONTAINS),
                "value": "aaapud!",
                "prev_op": None,
            },
        ],
        [
            AND,
            {
                "field": "Title",
                "operator": str(CONTAINS),
                "value": "",
                "prev_op": None,
            },
        ],
    ]

    serialized = multiseek_page.serialize()
    assert serialized == expected

    for n in range(1, 6):
        field = multiseek_page.get_field("field-%i" % n)
        field["close-button"].click()

    multiseek_page.page.wait_for_timeout(2000)

    expected = [
        None,
        {
            "field": "Year",
            "operator": "in range",
            "value": "[1999,2000]",
            "prev_op": None,
        },
    ]
    serialized = multiseek_page.serialize()
    assert serialized == expected


@pytest.mark.django_db
def test_remove_last_field(multiseek_page):
    assert Language.objects.count()

    field = multiseek_page.get_field("field-0")

    alert_messages = []

    def capture_alert(dialog):
        alert_messages.append(dialog.message)
        dialog.accept()

    multiseek_page.page.on("dialog", capture_alert)
    field["close-button"].click()
    multiseek_page.page.wait_for_timeout(1000)
    multiseek_page.page.remove_listener("dialog", capture_alert)
    assert len(alert_messages) == 1


@pytest.mark.django_db
def test_autocomplete_field(multiseek_page):
    assert Language.objects.count()

    field = multiseek_page.get_field(FIELD)
    field["type"].select_option(
        value=str(multiseek_registry.AuthorQueryObject.label)
    )

    select_select2_autocomplete(
        multiseek_page.page, ".select2-container", "Smith"
    )

    got = multiseek_page.serialize()
    expect = [
        None,
        make_field(
            multiseek_registry.AuthorQueryObject,
            str(EQUAL),
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
    field["type"].select_option(
        value=str(multiseek_registry.AuthorQueryObject.label)
    )

    multiseek_page.page.locator("#sendQueryButton").click()
    multiseek_page.page.wait_for_timeout(1000)
    multiseek_page.page.reload()
    multiseek_page.page.wait_for_load_state("networkidle")
    assert "Server Error (500)" not in multiseek_page.page.content()


@pytest.mark.django_db
def test_autocomplete_field_bug_2(multiseek_page):
    """We fill autocomplete field with NOTHING, then we submit the form,
    then we reload the homepage, click the "add field button" and by the
    time of writing, we get a javascript error."""

    field = multiseek_page.get_field(FIELD)
    field["type"].select_option(
        value=str(multiseek_registry.AuthorQueryObject.label)
    )

    multiseek_page.page.locator("#sendQueryButton").click()
    multiseek_page.page.wait_for_timeout(1000)
    multiseek_page.page.reload()
    multiseek_page.page.wait_for_load_state("networkidle")

    multiseek_page.page.locator("#add_field").click()
    multiseek_page.page.wait_for_timeout(1000)

    selects = multiseek_page.page.locator("select#type")
    assert selects.nth(0).locator("option").count() != 0
    assert selects.nth(1).locator("option").count() != 0


@pytest.mark.django_db
def test_set_join(multiseek_page):
    multiseek_page.page.locator("#add_field").click()
    multiseek_page.page.evaluate(
        "$('#field-1').multiseekField('prevOperation').val('or')"
    )

    ret = multiseek_page.page.evaluate(
        "$('#field-1').multiseekField('prevOperation').val()"
    )

    assert ret == "or"

    multiseek_page.add_field(
        FRAME,
        str(multiseek_page.registry.fields[0].label),
        str(multiseek_page.registry.fields[0].ops[0]),
        "",
    )

    multiseek_page.page.evaluate(
        "$('#field-2').multiseekField('prevOperation').val('or')"
    )

    ret = multiseek_page.page.evaluate(
        "$('#field-2').multiseekField('prevOperation').val()"
    )

    assert ret == "or"


@pytest.mark.django_db
def test_set_frame_join(multiseek_page):
    multiseek_page.page.evaluate(
        """
    $("#frame-0").multiseekFrame('addFrame');
    $("#frame-0").multiseekFrame('addFrame', 'or');
    """
    )

    ret = multiseek_page.page.evaluate(
        "$('#frame-2').multiseekFrame('getPrevOperationValue')"
    )

    assert ret == "or"


@pytest.mark.django_db
def test_add_field_value_list(multiseek_page):
    multiseek_page.add_field(
        FRAME,
        multiseek_registry.LanguageQueryObject.label,
        multiseek_registry.LanguageQueryObject.ops[1],
        str(_("polish")),
    )

    field = multiseek_page.get_field("field-1")
    assert field["type"].input_value() == str(
        multiseek_registry.LanguageQueryObject.label
    )
    assert field["op"].input_value() == str(
        multiseek_registry.LanguageQueryObject.ops[1]
    )
    assert field["value"] == str(_("polish"))


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
    field["prev-op"].select_option(value=str(_("or")))
    assert field["prev-op"].input_value() == str(_("or"))

    multiseek_page.page.locator("#sendQueryButton").click()
    multiseek_page.page.wait_for_timeout(500)

    multiseek_page.page.reload()
    multiseek_page.page.wait_for_load_state("networkidle")

    field = multiseek_page.get_field("field-1")
    assert field["prev-op"].input_value() == str(_("or"))


@pytest.mark.django_db
def test_frame_bug(multiseek_page):
    multiseek_page.page.locator("#add_frame").first.click()
    multiseek_page.page.locator("#close-button").first.click()
    multiseek_page.page.locator("#sendQueryButton").click()

    frame = multiseek_page.page.frame_locator("#if")
    body_text = frame.locator("body").text_content()
    assert "Server Error (500)" not in body_text

    # Wait for the iframe's request to fully complete before teardown
    # flushes the DB -- main page networkidle doesn't cover iframe requests.
    # The extra wait_for_timeout guards against a race where the browser
    # reports networkidle before the server finishes writing to the DB.
    iframe = multiseek_page.page.frame(name="list_frame")
    if iframe:
        iframe.wait_for_load_state("networkidle")
    multiseek_page.page.wait_for_timeout(500)


@pytest.mark.django_db
def test_date_field(multiseek_page):
    field = multiseek_page.get_field("field-0")

    field["type"].select_option(
        value=str(multiseek_registry.DateLastUpdatedQueryObject.label)
    )
    field = multiseek_page.get_field("field-0")
    field["op"].select_option(
        value=str(multiseek_registry.DateLastUpdatedQueryObject.ops[6])
    )

    expected = [
        None,
        {
            "field": "Last updated on",
            "operator": "in range",
            "value": '["",""]',
            "prev_op": None,
        },
    ]
    assert multiseek_page.serialize() == expected

    field["op"].select_option(
        value=str(multiseek_registry.DateLastUpdatedQueryObject.ops[3])
    )
    expected = [
        None,
        {
            "field": "Last updated on",
            "operator": "greater or equal to(female gender)",
            "value": '[""]',
            "prev_op": None,
        },
    ]
    assert expected == multiseek_page.serialize()


@pytest.mark.django_db
def test_removed_records(multiseek_page, live_server, initial_data):
    """Try to remove a record by hand and check if that fact is properly
    recorded."""

    multiseek_page.page.goto(live_server.url + "/multiseek/results")
    assert "A book with" in multiseek_page.page.content()
    assert "Second book" in multiseek_page.page.content()
    multiseek_page.page.evaluate(
        """$("a:contains('\\u274c')").first().click()"""
    )
    multiseek_page.page.wait_for_timeout(1000)

    multiseek_page.page.goto(live_server.url + "/multiseek/results")
    assert "A book with" in multiseek_page.page.content()
    assert "Second book" not in multiseek_page.page.content()
    assert (
        "1 record(s) has been removed manually"
        in multiseek_page.page.content()
    )

    multiseek_page.page.evaluate(
        """$("a:contains('\\u274c')").first().click()"""
    )
    multiseek_page.page.wait_for_timeout(1000)
    multiseek_page.page.evaluate(
        """$("a:contains('\\u274c')").first().click()"""
    )
    multiseek_page.page.wait_for_timeout(1000)
    multiseek_page.page.goto(live_server.url + "/multiseek/results")
    assert "A book with" in multiseek_page.page.content()
    assert "Second book" not in multiseek_page.page.content()
    assert (
        "1 record(s) has been removed manually"
        in multiseek_page.page.content()
    )


@pytest.mark.django_db
def test_form_save_anon_initial(multiseek_page):
    # Without SearchForm objects, the formsSelector is invisible
    assert not multiseek_page.page.locator("#formsSelector").is_visible()


@pytest.mark.django_db
def test_form_save_anon_initial_with_data(multiseek_page):
    baker.make(SearchForm, public=True)
    multiseek_page.page.reload()
    multiseek_page.page.wait_for_load_state("networkidle")
    assert multiseek_page.page.locator("#formsSelector").is_visible()


@pytest.mark.django_db
def test_form_save_anon_form_save_anonymous(multiseek_page):
    # Anonymous users cannot save forms:
    assert multiseek_page.page.locator("#saveFormButton").count() == 0


@pytest.mark.django_db
def test_form_save_anon_bug(multiseek_page):
    from playwright.sync_api import expect

    multiseek_page.page.locator("#add_frame").first.click()
    multiseek_page.page.locator("#add_field").first.click()
    field1 = multiseek_page.get_field("field-1")
    field1["close-button"].click()
    # The close triggers a jQuery fadeOut + DOM removal animation.
    # Use Playwright's retrying assertion to wait until the animation completes.
    expect(multiseek_page.page.locator("select#prev-op")).to_have_count(1)


@pytest.mark.django_db
def test_public_report_types_secret_report_invisible(multiseek_page):
    elem = multiseek_page.page.locator(
        "[name=_ms_report_type]"
    ).locator("option")
    assert elem.count() == 2


@pytest.mark.django_db
def test_logged_in_secret_report_visible(
    multiseek_admin_page, admin_user, initial_data
):
    elem = multiseek_admin_page.page.locator(
        "[name=_ms_report_type]"
    ).first.locator("option")
    assert elem.count() == 3


@pytest.mark.django_db
def test_save_form_logged_in(multiseek_admin_page, initial_data):
    assert multiseek_admin_page.page.locator("#saveFormButton").is_visible()


@pytest.mark.django_db
def test_save_form_server_error(multiseek_admin_page, initial_data):
    NAME = "testowy formularz"
    multiseek_admin_page.page.evaluate(
        "multiseek.SAVE_FORM_URL='/unexistent';"
    )

    # Save form -- prompt for name, then confirm public, then error alert
    handler = SequentialDialogHandler(multiseek_admin_page.page)
    handler.expect_prompt(NAME)   # Enter form name
    handler.expect_accept()       # Should it be public?
    handler.expect_accept()       # Error notification
    multiseek_admin_page.click_save_button()
    handler.wait_for_count(3)
    handler.detach()

    assert not multiseek_admin_page.page.locator("#formsSelector").is_visible()
    assert SearchForm.objects.all().count() == 0


@pytest.mark.django_db
def test_save_form_save(multiseek_admin_page, initial_data):
    page = multiseek_admin_page.page

    assert SearchForm.objects.all().count() == 0

    # Click save, then cancel the prompt
    handler = SequentialDialogHandler(page)
    handler.expect_dismiss()  # Cancel the prompt
    multiseek_admin_page.click_save_button()
    handler.wait_for_count(1)
    handler.detach()

    NAME = "testowy formularz"

    # Save the form
    # prompt(name) -> confirm(public?) -> alert(saved!)
    handler = SequentialDialogHandler(page)
    handler.expect_prompt(NAME)  # Enter form name
    handler.expect_accept()      # Should it be public? -> Yes
    handler.expect_accept()      # Form saved notification
    multiseek_admin_page.click_save_button()
    handler.wait_for_count(3)
    handler.detach()

    assert multiseek_admin_page.count_elements_in_form_selector(NAME) == 1
    assert SearchForm.objects.all().count() == 1

    # Save form under the SAME NAME
    # prompt(name) -> confirm(public?) -> confirm(overwrite?) -> alert(saved!)
    handler = SequentialDialogHandler(page)
    handler.expect_prompt(NAME)
    handler.expect_accept()      # public? -> Yes
    handler.expect_accept()      # overwrite? -> Yes
    handler.expect_accept()      # saved notification
    multiseek_admin_page.click_save_button()
    handler.wait_for_count(4)
    handler.detach()

    assert multiseek_admin_page.count_elements_in_form_selector(NAME) == 1
    assert SearchForm.objects.all().count() == 1

    # Save form under the SAME NAME again -- also accept overwrite
    handler = SequentialDialogHandler(page)
    handler.expect_prompt(NAME)
    handler.expect_accept()      # public? -> Yes
    handler.expect_accept()      # overwrite? -> Yes
    handler.expect_accept()      # saved notification
    multiseek_admin_page.click_save_button()
    handler.wait_for_count(4)
    handler.detach()

    assert SearchForm.objects.all().count() == 1
    assert SearchForm.objects.all()[0].public

    # Overwrite as NOT public
    handler = SequentialDialogHandler(page)
    handler.expect_prompt(NAME)
    handler.expect_dismiss()     # public? -> No
    handler.expect_accept()      # overwrite? -> Yes
    handler.expect_accept()      # saved notification
    multiseek_admin_page.click_save_button()
    handler.wait_for_count(4)
    handler.detach()

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

    field = multiseek_admin_page.extract_field_data("field-0")

    assert field["selected"] == str(
        multiseek_admin_page.registry.fields[2].label
    )
    assert field["value"][0] == 2000
    assert field["value"][1] == 2010

    # Test that after CANCEL the select returns to its initial value
    handler = SequentialDialogHandler(multiseek_admin_page.page)
    handler.expect_dismiss()  # Dismiss the "load form?" dialog

    multiseek_admin_page.page.locator("#formsSelector").select_option(label="lol")

    handler.wait_for_count(1)
    handler.detach()

    options = multiseek_admin_page.page.locator("#formsSelector option")
    is_selected = options.nth(0).evaluate("el => el.selected")
    assert is_selected


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
    elements = multiseek_admin_page.page.locator("[name=prev-op]")
    for i in range(elements.count()):
        elem = elements.nth(i)
        visibility = elem.evaluate(
            "el => getComputedStyle(el).visibility"
        )
        if visibility != "hidden":
            assert elem.input_value() == logic.OR


@pytest.mark.django_db
def test_save_ordering_direction(multiseek_admin_page, initial_data):
    elem_selector = "input[name=%s1_dir]" % MULTISEEK_ORDERING_PREFIX
    page = multiseek_admin_page.page

    page.locator(elem_selector).check()

    # Save form: prompt(name) -> confirm(public?) -> alert(saved!)
    handler = SequentialDialogHandler(page)
    handler.expect_prompt("foobar")
    handler.expect_accept()  # public? -> Yes
    handler.expect_accept()  # saved notification
    multiseek_admin_page.click_save_button()
    handler.wait_for_count(3)
    handler.detach()

    multiseek_admin_page.reset_form()
    multiseek_admin_page.load_form_by_name("foobar")
    assert page.locator("%s:checked" % elem_selector).count() == 1


@pytest.mark.django_db
def test_save_ordering_box(multiseek_admin_page, initial_data):
    elem_selector = "select[name=%s0]" % MULTISEEK_ORDERING_PREFIX
    page = multiseek_admin_page.page
    select = page.locator(elem_selector)
    assert not select.locator('option[value="2"]').evaluate("el => el.selected")

    select.select_option(value="2")

    # Save form: prompt(name) -> confirm(public?) -> alert(saved!)
    handler = SequentialDialogHandler(page)
    handler.expect_prompt("foobar")
    handler.expect_accept()
    handler.expect_accept()
    multiseek_admin_page.click_save_button()
    handler.wait_for_count(3)
    handler.detach()

    multiseek_admin_page.reset_form()
    multiseek_admin_page.load_form_by_name("foobar")

    select = page.locator(elem_selector)
    assert select.locator('option[value="2"]').evaluate("el => el.selected")


@pytest.mark.django_db
def test_save_report_type(multiseek_admin_page, initial_data):
    elem_selector = "select[name=%s]" % MULTISEEK_REPORT_TYPE
    page = multiseek_admin_page.page
    select = page.locator(elem_selector).first
    assert not select.locator('option[value="1"]').evaluate("el => el.selected")

    select.select_option(value="1")

    # Save form: prompt(name) -> confirm(public?) -> alert(saved!)
    handler = SequentialDialogHandler(page)
    handler.expect_prompt("foobar")
    handler.expect_accept()
    handler.expect_accept()
    multiseek_admin_page.click_save_button()
    handler.wait_for_count(3)
    handler.detach()

    multiseek_admin_page.reset_form()
    multiseek_admin_page.page.wait_for_timeout(1000)
    multiseek_admin_page.load_form_by_name("foobar")

    select = page.locator(elem_selector).first
    assert select.locator('option[value="1"]').evaluate("el => el.selected")
