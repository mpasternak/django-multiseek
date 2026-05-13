"""Integration tests for the htmx example.

These run from ``examples/htmx/`` against the example's own ``example_project``
settings. The parent ``pyproject.toml`` already declares ``pytest-django`` and
``model_bakery`` as dev deps, so::

    cd examples/htmx
    uv run pytest

picks them up.
"""

import re

import pytest
from django.test import Client

from books.models import Author, Book, Language


@pytest.fixture
def books_db(db):
    """Seed the demo data — one matching book ("A book with a title") and
    several non-matching "Book no N" entries — and return them."""
    eng = Language.objects.create(name="english", description="English")
    smith = Author.objects.create(first_name="John", last_name="Smith")
    novak = Author.objects.create(first_name="Stephan", last_name="Novak")

    match_book = Book.objects.create(
        title="A book with a title",
        year=2013,
        language=eng,
        no_editors=1,
        available=True,
    )
    match_book.authors.add(smith)

    other_books = []
    for i in range(3):
        b = Book.objects.create(
            title=f"Book no {i}",
            year=1999,
            language=eng,
            no_editors=1,
            available=False,
        )
        b.authors.add(novak)
        other_books.append(b)

    return {"match": match_book, "others": other_books}


def _replay_submit_form(client, page_html, csrf):
    """Replay whatever the rendered <Send Query> form tells the browser to do.

    Parses method/action/inputs out of the first <form> on the page that
    posts to /multiseek/results/ (or GETs from it) and fires the equivalent
    request through Django's test client. This way the test exercises the
    real submission flow rather than a hand-coded approximation of it.
    """
    # Capture the entire <form …> opening tag's attributes first, then the
    # body. Doing this in two passes is more robust than trying to bind
    # `method=` and `action=` in a single regex (their order varies).
    form_match = re.search(
        r"<form\b(?P<open_attrs>[^>]*)>(?P<body>.*?)</form>",
        page_html,
        re.DOTALL,
    )
    while form_match and "/multiseek/results" not in form_match.group("open_attrs"):
        # The first <form> on the page might be unrelated (e.g. the "Reset"
        # form). Keep scanning until we find the one that points at results.
        form_match = re.search(
            r"<form\b(?P<open_attrs>[^>]*)>(?P<body>.*?)</form>",
            page_html[form_match.end() :],
            re.DOTALL,
        )
    assert form_match, "Send Query <form> not found on the page"

    open_attrs = form_match.group("open_attrs")
    action_m = re.search(r'\baction="([^"]+)"', open_attrs)
    assert action_m, "form has no action attribute"
    action = action_m.group(1)

    method = "get"
    method_m = re.search(r'\bmethod="(post|get)"', open_attrs, re.IGNORECASE)
    if method_m:
        method = method_m.group(1).lower()

    body = form_match.group("body")
    data = {}
    for inp in re.finditer(r'<input\b([^>]*)>', body):
        attrs_in = inp.group(1)
        name_m = re.search(r'\bname="([^"]+)"', attrs_in)
        value_m = re.search(r'\bvalue="([^"]*)"', attrs_in)
        if name_m:
            data[name_m.group(1)] = (value_m.group(1) if value_m else "").replace("&quot;", '"')

    if method == "post":
        return client.post(action, data=data, HTTP_X_CSRFTOKEN=csrf)
    return client.get(action, data=data)


@pytest.mark.django_db
def test_typing_a_value_then_submitting_actually_filters(books_db):
    """User flow:
    1. Open the form (default Title/contains/'' field is seeded into session).
    2. Type "title" in the Title value input (htmx posts to set_field_value).
    3. Click Send Query.

    The results page MUST filter by 'title' — i.e. show "A book with a title"
    and NOT show "Book no 0/1/2". Pre-fix the Send Query button posted a
    hidden <input name="json" value="…"> that was rendered at page-load with
    the empty value, overwriting the freshly-htmx-updated session.
    """
    client = Client()
    page = client.get("/multiseek/").content.decode()
    csrf = client.cookies["csrftoken"].value

    # Step 2: htmx writes value="title" to session.
    write = client.post(
        "/htmx/field-value/0.1/",
        data={"value": "title"},
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert write.status_code == 200

    # Step 3: click Send Query. The button fires an htmx GET to
    # /htmx/results/ which swaps the results fragment into the page.
    resp = client.get("/htmx/results/")
    assert resp.status_code == 200, resp.content[:500]

    content = resp.content.decode()
    assert "A book with a title" in content, (
        "the matching book should be in the filtered results"
    )
    for non_match in books_db["others"]:
        assert non_match.title not in content, (
            f"non-matching book {non_match.title!r} appeared — the submission "
            "did not actually filter (it likely posted a stale page-load json snapshot)"
        )
