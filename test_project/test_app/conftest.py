import json
import datetime

import pytest
from django.conf import settings
from django.urls import reverse
from model_bakery import baker
from django.utils.translation import gettext_lazy as _

from multiseek.logic import (
    DATE,
    AUTOCOMPLETE,
    RANGE,
    STRING,
    VALUE_LIST,
    get_registry,
)
from .models import Language, Author, Book
from .testutil import SequentialDialogHandler


class MultiseekWebPage:
    """Helper functions for interacting with the multiseek form web page."""

    def __init__(self, registry, page, live_server_url):
        self.page = page
        self.registry = registry
        self.live_server_url = live_server_url

    def login(self, username="admin", password="password"):
        url = self.page.url
        self.page.goto(self.live_server_url + reverse("admin:login"))
        self.page.locator("[name=username]").fill(username)
        self.page.locator("[name=password]").fill(password)
        self.page.locator("input[type=submit]").click()
        self.page.wait_for_load_state("networkidle")
        self.page.goto(url)

    def get_frame(self, id):
        frame = self.page.locator(f"#{id}")
        # Use child combinators to target only THIS frame's buttons,
        # not those of nested sub-frames (which appear earlier in DOM).
        buttons = self.page.locator(f"#{id} > fieldset > .button-group")
        return {
            "frame": frame,
            "add_field": buttons.locator("#add_field"),
            "add_frame": buttons.locator("#add_frame"),
            "fields": self.page.locator(f"#{id} > fieldset > #field-list"),
        }

    def extract_field_data(self, element_id):
        element = self.page.locator(f"#{element_id}")
        ret = {}

        for elem_id in ["type", "op", "prev-op", "close-button"]:
            loc = element.locator(f"#{elem_id}")
            if loc.count() > 0:
                ret[elem_id] = loc.first
            elif elem_id == "prev-op":
                ret[elem_id] = None
            else:
                raise Exception(f"Element #{elem_id} not found in #{element_id}")

        selected = ret["type"].input_value()
        ret["selected"] = selected

        inner_type = self.registry.field_by_name.get(selected).type
        ret["inner_type"] = inner_type

        if inner_type in [STRING, VALUE_LIST]:
            ret["value_widget"] = element.locator("#value")
        elif inner_type == RANGE:
            ret["value_widget"] = [
                element.locator("#value_min"),
                element.locator("#value_max"),
            ]
        elif inner_type == DATE:
            ret["value_widget"] = [
                element.locator("#value"),
                element.locator("#value_max"),
            ]
        elif inner_type == AUTOCOMPLETE:
            ret["value_widget"] = element.locator("#value")
        else:
            raise NotImplementedError(inner_type)

        code = f'$("#{element_id}").multiseekField("getValue")'
        ret["value"] = self.page.evaluate(code)

        if ret["inner_type"] in (DATE, AUTOCOMPLETE, RANGE):
            if ret["value"]:
                ret["value"] = json.loads(ret["value"])
        return ret

    def get_field(self, id):
        loc = self.page.locator(f"#{id}")
        if loc.count() != 1:
            raise Exception(f"field #{id} not found")
        return self.extract_field_data(id)

    def serialize(self):
        return self.page.evaluate(
            "$('#frame-0').multiseekFrame('serialize')"
        )

    def get_field_value(self, field):
        return self.page.evaluate(
            f'$("#{field}").multiseekField("getValue")'
        )

    def add_frame(self, frame="frame-0", prev_op=None):
        if not prev_op:
            return self.page.evaluate(
                f"""$("#{frame}").multiseekFrame('addFrame');"""
            )
        return self.page.evaluate(
            f"""$("#{frame}").multiseekFrame('addFrame', '{prev_op}');"""
        )

    def add_field(self, frame, label, op, value):
        code = """
        $("#%(frame)s").multiseekFrame("addField", "%(label)s", "%(op)s", %(value)s);
        """ % dict(
            frame=frame,
            label=str(label),
            op=str(op),
            value=json.dumps(value),
        )
        self.page.evaluate(code)

    def load_form_by_name(self, name):
        self.page.reload()
        self.page.wait_for_load_state("networkidle")

        handler = SequentialDialogHandler(self.page)
        handler.expect_accept()  # "Are you sure you want to load?"

        # Selecting the option triggers loadForm() which calls confirm()
        # and on accept, navigates via location.href -> server redirects back.
        with self.page.expect_navigation(wait_until="networkidle"):
            self.page.locator("#formsSelector").select_option(label=name)
            handler.wait_for_count(1)

        handler.detach()

    def reset_form(self):
        self.page.locator("#resetFormButton").click()

    def click_save_button(self):
        self.page.locator("#saveFormButton").first.click()

    def save_form_as(self, name):
        handler = SequentialDialogHandler(self.page)
        handler.expect_prompt(name)  # "Enter form name"
        self.click_save_button()
        handler.wait_for_count(1)
        handler.detach()

    def count_elements_in_form_selector(self, name):
        select = self.page.locator("#formsSelector")
        assert select.is_visible()
        options = select.locator("option")
        count = 0
        for i in range(options.count()):
            if options.nth(i).text_content() == name:
                count += 1
        return count

    def accept_next_dialog(self):
        """Register a one-shot handler to accept the next dialog."""
        self.page.once("dialog", lambda d: d.accept())

    def dismiss_next_dialog(self):
        """Register a one-shot handler to dismiss the next dialog."""
        self.page.once("dialog", lambda d: d.dismiss())


@pytest.fixture
def multiseek_page(page, live_server, initial_data):
    page.goto(live_server.url + reverse("multiseek:index"))
    registry = get_registry(settings.MULTISEEK_REGISTRY)
    yield MultiseekWebPage(
        page=page, registry=registry, live_server_url=live_server.url
    )


@pytest.fixture
def multiseek_admin_page(multiseek_page, admin_user):
    multiseek_page.login(admin_user.username, "password")
    return multiseek_page


@pytest.fixture
def initial_data():
    eng = baker.make(Language, name=_("english"), description="English language")
    baker.make(Language, name=_("polish"), description="Polish language")
    a1 = baker.make(Author, last_name="Smith", first_name="John")
    a2 = baker.make(Author, last_name="Kovalsky", first_name="Ian")
    b1 = baker.make(
        Book,
        title="A book with a title",
        year=2013,
        language=eng,
        no_editors=5,
        last_updated=datetime.date(2013, 10, 22),
        available=True,
    )
    b2 = baker.make(
        Book,
        title="Second book",
        year=2000,
        language=eng,
        no_editors=5,
        last_updated=datetime.date(2013, 9, 22),
        available=False,
    )

    b1.authors.add(a1)
    b2.authors.add(a2)

    a3 = baker.make(Author, last_name="Novak", first_name="Stephan")
    fr = baker.make(Language, name="french", description="French language")
    for a in range(0, 50):
        b3 = baker.make(Book, title="Book no %i" % a, year=1999, language=fr)
        b3.authors.add(a3)
