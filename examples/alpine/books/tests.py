"""Basic Playwright smoke test for the Alpine variant.

Alpine generates each field's value input with a uid-suffixed id
(`#value-<uid>`), so the selector matches the first such input.
"""

import pytest

from books.models import Author, Book, Language


@pytest.fixture
def books_fixture(db):
    eng = Language.objects.create(name="english", description="English")
    smith = Author.objects.create(first_name="John", last_name="Smith")
    novak = Author.objects.create(first_name="Stephan", last_name="Novak")

    match = Book.objects.create(
        title="Quick test book",
        year=2020,
        language=eng,
        no_editors=1,
        available=True,
    )
    match.authors.add(smith)

    other = Book.objects.create(
        title="A different book",
        year=2010,
        language=eng,
        no_editors=1,
        available=False,
    )
    other.authors.add(novak)
    return {"match": match, "other": other}


@pytest.mark.django_db(transaction=True)
def test_fill_value_and_submit_filters_results(live_server, page, books_fixture):
    page.goto(f"{live_server.url}/multiseek/")
    page.wait_for_load_state("networkidle")

    # Alpine bumps each field's input id with a uid suffix — match the first.
    page.locator("input[id^='value-']").first.wait_for(state="visible", timeout=5000)
    page.locator("input[id^='value-']").first.fill("test")
    page.locator("#sendQueryButton").click()

    iframe = page.frame_locator("#if")
    iframe.locator("text=Query: title contains").wait_for(timeout=10000)

    text = iframe.locator("body").inner_text()
    assert "Quick test book" in text
    assert "A different book" not in text
